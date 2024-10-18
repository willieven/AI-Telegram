import os
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import signal
from datetime import datetime

from config import USERS, FTP_HOST, FTP_PORT, MAIN_FTP_DIRECTORY, MAX_IMAGE_QUEUE, POSITIVE_PHOTOS_DIRECTORY
from ftp_server import create_ftp_server
from improved_image_processor import start_image_processing_system, shutdown_image_processing
from image_processor import bot, handle_telegram_command, check_and_auto_arm, redis_client, set_armed_status
from nvr_api_handler import start_nvr_processing

# Number of image processing threads
NUM_IMAGE_PROCESSING_THREADS = 12

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'ftp_server.log')

        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)
        logger.info("File logging initialized.")
    except Exception as e:
        logger.warning(f"Unable to set up file logging: {e}")
        logger.warning("Continuing with console logging only.")

    return logger

logger = setup_logging()

def create_user_directories():
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        os.makedirs(user_directory, exist_ok=True)
        logger.info(f"Created or verified directory for user {user_data['FTP_USER']}: {user_directory}")

async def process_leftover_images(image_queue):
    leftover_images = []
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        for root, _, files in os.walk(user_directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.join(root, file)
                    leftover_images.append((file_path, user_data, True))
                    logger.info(f"Found leftover image: {file_path}")
    
    if leftover_images:
        for image in leftover_images:
            await image_queue.put(image)
        logger.info(f"Queued {len(leftover_images)} leftover images for processing")
    else:
        logger.info("No leftover images found")

async def auto_arm_checker():
    while True:
        for user, user_settings in USERS.items():
            check_and_auto_arm(user, user_settings)
        await asyncio.sleep(30)  # Check every 30 seconds

async def start_telegram_handler():
    async def message_loop_handler():
        offset = 0
        while True:
            try:
                updates = await bot.get_updates(offset=offset, timeout=10)
                for update in updates:
                    offset = update['update_id'] + 1
                    if 'message' in update:
                        await handle_telegram_command(update['message'])
            except Exception as e:
                logger.error(f"Error in Telegram message loop: {str(e)}")
                await asyncio.sleep(1)

    telegram_task = asyncio.create_task(message_loop_handler())
    logger.info("Telegram message handler started")
    return telegram_task

def initialize_redis_armed_status():
    for user, user_settings in USERS.items():
        if redis_client.get(f"user_armed_status:{user}") is None:
            set_armed_status(user, user_settings['ARMED'])
            logger.info(f"Initialized armed status for user {user} in Redis")

async def main():
    # Create main FTP directory if it doesn't exist
    os.makedirs(MAIN_FTP_DIRECTORY, exist_ok=True)
    logger.info(f"Main FTP directory verified: {MAIN_FTP_DIRECTORY}")
    
    # Create user directories
    create_user_directories()
    
    # Initialize Redis armed status
    initialize_redis_armed_status()
    
    # Start the image processing system
    image_queue, stop_event = start_image_processing_system(NUM_IMAGE_PROCESSING_THREADS)
    logger.info(f"Image processing system started with {NUM_IMAGE_PROCESSING_THREADS} threads")
    
    # Process any leftover images in user folders
    await process_leftover_images(image_queue)
    
    # Create and start the FTP server
    ftp_server = create_ftp_server(FTP_HOST, FTP_PORT, image_queue)
    ftp_server_task = asyncio.create_task(ftp_server.start())
    logger.info(f"FTP server is starting on {FTP_HOST}:{FTP_PORT}")
    
    # Create error_images directory
    error_images_dir = os.path.join(MAIN_FTP_DIRECTORY, 'error_images')
    os.makedirs(error_images_dir, exist_ok=True)
    logger.info(f"Error images directory verified: {error_images_dir}")
    
    # Create positive_photos directory
    os.makedirs(POSITIVE_PHOTOS_DIRECTORY, exist_ok=True)
    logger.info(f"Positive photos directory verified: {POSITIVE_PHOTOS_DIRECTORY}")
    
    # Start the Telegram message handler
    telegram_task = await start_telegram_handler()
    
    # Start the auto-arm checker
    auto_arm_task = asyncio.create_task(auto_arm_checker())
    logger.info("Auto-arm checker started")
    
    # Start the NVR event processing
    nvr_task = asyncio.create_task(start_nvr_processing(image_queue))
    logger.info("NVR event processing started")

    # Setup graceful shutdown
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    
    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down...")
        ftp_server_task.cancel()
        telegram_task.cancel()
        auto_arm_task.cancel()
        nvr_task.cancel()
        shutdown_image_processing(stop_event)
        
        # Wait for tasks to complete
        await asyncio.gather(ftp_server_task, telegram_task, auto_arm_task, nvr_task, return_exceptions=True)
        
        logger.info("Cleanup complete. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())