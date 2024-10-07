import os
import logging
import time
from threading import Thread
from config import USERS, FTP_HOST, FTP_PORT, MAIN_FTP_DIRECTORY, MAX_IMAGE_QUEUE, POSITIVE_PHOTOS_DIRECTORY
from ftp_server import create_ftp_server
from improved_image_processor import start_image_processing_system, shutdown_image_processing

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='ftp_server.log',
                    filemode='a')

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Number of image processing threads
NUM_IMAGE_PROCESSING_THREADS = 12

def create_user_directories():
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        os.makedirs(user_directory, exist_ok=True)
        logging.info(f"Created or verified directory for user {user_data['FTP_USER']}: {user_directory}")

def process_leftover_images(image_queue):
    leftover_images = []
    for user_id, user_data in USERS.items():
        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
        for root, _, files in os.walk(user_directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.join(root, file)
                    leftover_images.append((file_path, user_data))
                    logging.info(f"Found leftover image: {file_path}")
    
    if leftover_images:
        image_queue.put_many(leftover_images)
        logging.info(f"Queued {len(leftover_images)} leftover images for processing")
    else:
        logging.info("No leftover images found")

def main():
    # Create main FTP directory if it doesn't exist
    os.makedirs(MAIN_FTP_DIRECTORY, exist_ok=True)
    logging.info(f"Main FTP directory verified: {MAIN_FTP_DIRECTORY}")
    
    # Create user directories
    create_user_directories()
    
    # Start the image processing system
    image_queue, stop_event = start_image_processing_system(NUM_IMAGE_PROCESSING_THREADS)
    logging.info(f"Image processing system started with {NUM_IMAGE_PROCESSING_THREADS} threads")
    
    # Process any leftover images in user folders
    process_leftover_images(image_queue)
    
    # Create and start the FTP server
    server = create_ftp_server(FTP_HOST, FTP_PORT, image_queue)
    logging.info(f"FTP server is starting on {FTP_HOST}:{FTP_PORT}")
    server.start()
    
    # Create error_images directory
    error_images_dir = os.path.join(MAIN_FTP_DIRECTORY, 'error_images')
    os.makedirs(error_images_dir, exist_ok=True)
    logging.info(f"Error images directory verified: {error_images_dir}")
    
    # Create positive_photos directory
    os.makedirs(POSITIVE_PHOTOS_DIRECTORY, exist_ok=True)
    logging.info(f"Positive photos directory verified: {POSITIVE_PHOTOS_DIRECTORY}")
    
    logging.info("Main thread is now waiting. Press Ctrl+C to stop the server.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Server stopping...")
        shutdown_image_processing(stop_event)
        # Here you would also add code to stop the FTP server
    finally:
        logging.info("Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()