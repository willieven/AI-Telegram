import os
import time
from threading import Thread
from logging.handlers import TimedRotatingFileHandler
import logging
import sqlite3

from config import USERS, FTP_HOST, FTP_PORT, MAIN_FTP_DIRECTORY, MAX_IMAGE_QUEUE, POSITIVE_PHOTOS_DIRECTORY
from ftp_server import create_ftp_server
from improved_image_processor import start_image_processing_system, shutdown_image_processing
from telepot.loop import MessageLoop
from image_processor import bot, handle_telegram_command

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

        # Subclass TimedRotatingFileHandler to add size limit
        class SizedTimedRotatingFileHandler(TimedRotatingFileHandler):
            def __init__(self, *args, **kwargs):
                self.max_bytes = kwargs.pop("maxBytes", 0)
                TimedRotatingFileHandler.__init__(self, *args, **kwargs)

            def shouldRollover(self, record):
                if self.max_bytes > 0:
                    msg = "%s\n" % self.format(record)
                    self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
                    if self.stream.tell() + len(msg) >= self.max_bytes:
                        return 1
                t = int(time.time())
                if t >= self.rolloverAt:
                    return 1
                return 0

        # Use our custom handler with a 10MB size limit
        file_handler = SizedTimedRotatingFileHandler(
            filename=log_file,
            when="H",
            interval=1,
            backupCount=0,
            encoding='utf-8',
            maxBytes=10*1024*1024  # 10 MB size limit
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

def process_leftover_images(image_queue):
    leftover_images = []
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        for root, _, files in os.walk(user_directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.join(root, file)
                    leftover_images.append((file_path, user_data, True))  # Add True for delete_after_processing
                    logger.info(f"Found leftover image: {file_path}")
    
    if leftover_images:
        for image in leftover_images:
            image_queue.put(image)
        logger.info(f"Queued {len(leftover_images)} leftover images for processing")
    else:
        logger.info("No leftover images found")

def main():
    # Create main FTP directory if it doesn't exist
    os.makedirs(MAIN_FTP_DIRECTORY, exist_ok=True)
    logger.info(f"Main FTP directory verified: {MAIN_FTP_DIRECTORY}")
    
    # Create user directories
    create_user_directories()
    
    # Start the image processing system
    image_queue, stop_event = start_image_processing_system(NUM_IMAGE_PROCESSING_THREADS)
    logger.info(f"Image processing system started with {NUM_IMAGE_PROCESSING_THREADS} threads")
    
    # Process any leftover images in user folders
    process_leftover_images(image_queue)
    
    # Create and start the FTP server
    server = create_ftp_server(FTP_HOST, FTP_PORT, image_queue)
    logger.info(f"FTP server is starting on {FTP_HOST}:{FTP_PORT}")
    server.start()  # This starts the server in its own thread
    
    # Create error_images directory
    error_images_dir = os.path.join(MAIN_FTP_DIRECTORY, 'error_images')
    os.makedirs(error_images_dir, exist_ok=True)
    logger.info(f"Error images directory verified: {error_images_dir}")
    
    # Create positive_photos directory
    os.makedirs(POSITIVE_PHOTOS_DIRECTORY, exist_ok=True)
    logger.info(f"Positive photos directory verified: {POSITIVE_PHOTOS_DIRECTORY}")
    
    # Start the Telegram message handler
    MessageLoop(bot, handle_telegram_command).run_as_thread()
    logger.info("Telegram message handler started")
    
    logger.info("Main thread is now waiting. Press Ctrl+C to stop the server.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Server stopping...")
        shutdown_image_processing(stop_event)
        # Note: We're not explicitly stopping the FTP server here because
        # the implementation doesn't seem to provide a stop method.
        # The process termination should stop it.
    finally:
        logger.info("Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()