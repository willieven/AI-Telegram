import os
import logging
import cv2
import numpy as np
from ultralytics import YOLO
import telepot
import shutil
from datetime import datetime
import requests
import time
import threading
import json
from pathlib import Path
import fcntl
import sys
import redis

from config import YOLO_MODEL, TELEGRAM_BOT_TOKEN, POSITIVE_PHOTOS_DIRECTORY, SAVE_POSITIVE_PHOTOS, MAIN_FTP_DIRECTORY, GLOBAL_WATERMARK_TEXT, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from utils import is_within_working_hours

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

# Initialize YOLO model
model = YOLO(YOLO_MODEL)

# Initialize Telegram bot
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)

# SIGNL4 alert rate limiting
ALERT_COOLDOWN = 300  # 5 minutes

def get_lock(lock_name, expire=60):
    return redis_client.set(f"lock:{lock_name}", "locked", nx=True, ex=expire)

def get_last_alert_time(user):
    return redis_client.get(f"last_alert:{user}")

def set_last_alert_time(user, timestamp):
    redis_client.set(f"last_alert:{user}", timestamp)

def ensure_single_instance():
    global lock_file
    lock_file = open("/tmp/ai_telegram_lock", "w")
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Another instance is already running. Exiting.")
        sys.exit(1)

def add_watermark(image, user_settings):
    height, width = image.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    watermark_text = user_settings.get('WATERMARK_TEXT', GLOBAL_WATERMARK_TEXT)
    watermark_text = watermark_text.format(username=user_settings['FTP_USER'], timestamp=timestamp)
    
    text_size = cv2.getTextSize(watermark_text, font, font_scale, font_thickness)[0]
    
    position = (width - text_size[0] - 10, height - 10)
    
    overlay = image.copy()
    cv2.rectangle(overlay, (position[0] - 5, position[1] - text_size[1] - 5),
                  (width, height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
    
    cv2.putText(image, watermark_text, position, font, font_scale, (255, 255, 255), font_thickness)
    
    return image

def detect_objects(image_path, user_settings):
    try:
        image = cv2.imread(image_path)
        results = model(image)
        
        detections = {
            'person': [],
            'vehicle': [],
            'animal': []
        }
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls]
                
                if class_name == 'person' and user_settings['ENABLE_PERSON_DETECTION'] and conf > user_settings['PERSON_CONFIDENCE_THRESHOLD']:
                    detections['person'].append((box.xyxy[0].tolist(), conf))
                elif class_name in ['car', 'truck', 'bus', 'vehicle'] and user_settings['ENABLE_VEHICLE_DETECTION'] and conf > user_settings['VEHICLE_CONFIDENCE_THRESHOLD']:
                    detections['vehicle'].append((box.xyxy[0].tolist(), conf))
                elif class_name in ['cow', 'sheep', 'horse', 'dog', 'cat', 'animal'] and user_settings['ENABLE_ANIMAL_DETECTION'] and conf > user_settings['ANIMAL_CONFIDENCE_THRESHOLD']:
                    detections['animal'].append((box.xyxy[0].tolist(), conf))
        
        return detections, image
    except Exception as e:
        logging.error(f"Error during object detection: {str(e)}")
        return None, None

def draw_detections(image, detections):
    for category, objects in detections.items():
        for (bbox, conf) in objects:
            x1, y1, x2, y2 = map(int, bbox)
            if category == 'person':
                color = (0, 255, 0)  # Green for persons
            elif category == 'vehicle':
                color = (255, 0, 0)  # Blue for vehicles
            else:
                color = (0, 0, 255)  # Red for animals
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{category} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    return image

def send_signl4_alert(image_path, detection_message, user_settings):
    if 'SIGNL4_SECRET' not in user_settings or not user_settings['SIGNL4_SECRET']:
        logging.info(f"Skipping SIGNL4 alert for {user_settings['FTP_USER']} - No SIGNL4 secret configured")
        return

    current_time = time.time()
    ftp_user = user_settings['FTP_USER']
    
    lock_name = f"signl4_alert:{ftp_user}"
    if not get_lock(lock_name, expire=ALERT_COOLDOWN):
        logging.info(f"Skipping SIGNL4 alert for {ftp_user} - Rate limited or another alert is being processed")
        return

    try:
        last_alert = get_last_alert_time(ftp_user)
        if last_alert and current_time - float(last_alert) < ALERT_COOLDOWN:
            logging.info(f"Skipping SIGNL4 alert for {ftp_user} due to rate limiting")
            return

        files = {
            'Image': ('image.jpg', open(image_path, 'rb'), 'image/jpeg')
        }
        data = {
            'Title': f"Intrusion Detection Alert for {ftp_user}",
            'Message': detection_message,
            'Severity': 'High'
        }

        response = requests.post(
            user_settings['SIGNL4_SECRET'],
            files=files,
            data=data
        )

        if response.status_code == 200:
            logging.info(f"SIGNL4 alert sent successfully for {ftp_user}")
            set_last_alert_time(ftp_user, str(current_time))
        else:
            logging.error(f"Failed to send SIGNL4 alert for {ftp_user}: {response.text}")

    except Exception as e:
        logging.error(f"Error sending SIGNL4 alert for {ftp_user}: {str(e)}")
    finally:
        if 'Image' in files and hasattr(files['Image'][1], 'close'):
            files['Image'][1].close()
        # Note: We're not releasing the lock here. It will expire after ALERT_COOLDOWN seconds.

def process_image(image_path, user_settings, delete_after_processing=False):
    logging.info(f"Starting to process image: {image_path}")
    logging.info(f"User settings: {user_settings}")

    if not is_within_working_hours(user_settings):
        logging.info(f"Image {image_path} received outside working hours. Deleting without processing.")
        cleanup_files(image_path, MAIN_FTP_DIRECTORY)
        return

    detections, image = detect_objects(image_path, user_settings)
    if detections is None or image is None:
        logging.error(f"Failed to process image: {image_path}")
        cleanup_files(image_path, MAIN_FTP_DIRECTORY)
        return

    detected_objects = []
    if user_settings['ENABLE_PERSON_DETECTION'] and detections['person']:
        detected_objects.append('person')
    if user_settings['ENABLE_VEHICLE_DETECTION'] and detections['vehicle']:
        detected_objects.append('vehicle')
    if user_settings['ENABLE_ANIMAL_DETECTION'] and detections['animal']:
        detected_objects.append('animal')

    if detected_objects:
        if SAVE_POSITIVE_PHOTOS:
            save_positive_photo(image_path, user_settings['FTP_USER'])

        marked_image = draw_detections(image.copy(), detections)
        marked_image = add_watermark(marked_image, user_settings)
        marked_image_path = image_path.replace('.jpg', '_marked.jpg')
        cv2.imwrite(marked_image_path, marked_image)

        detection_message = f"Detected: {', '.join(detected_objects)}"
        send_telegram_image(marked_image_path, detection_message, user_settings['TELEGRAM_CHAT_ID'])
        
        send_signl4_alert(marked_image_path, detection_message, user_settings)

        logging.info(f"{detection_message} in {image_path}. Marked image sent to Telegram and SIGNL4 (if configured).")

        cleanup_files(marked_image_path, MAIN_FTP_DIRECTORY)
    else:
        logging.info(f"No relevant objects detected in {image_path}.")
    
    if delete_after_processing:
        cleanup_files(image_path, MAIN_FTP_DIRECTORY)
        logging.info(f"Deleted processed file: {image_path}")
    else:
        logging.info(f"Retained processed file: {image_path}")

    logging.info(f"Finished processing image: {image_path}")

def cleanup_files(file_path, base_directory):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
    
    directory = os.path.dirname(file_path)
    while directory != base_directory:
        if not os.listdir(directory):
            os.rmdir(directory)
            logging.info(f"Removed empty directory: {directory}")
            directory = os.path.dirname(directory)
        else:
            break

def send_telegram_image(image_path, caption, chat_id):
    try:
        with open(image_path, 'rb') as image_file:
            bot.sendPhoto(chat_id, image_file, caption=caption)
        logging.info(f"Image sent successfully: {image_path}")
    except Exception as e:
        logging.error(f"Error sending image to Telegram: {str(e)}")

def save_positive_photo(image_path, username):
    try:
        user_positive_dir = os.path.join(POSITIVE_PHOTOS_DIRECTORY, username)
        os.makedirs(user_positive_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{os.path.basename(image_path)}"
        new_path = os.path.join(user_positive_dir, new_filename)

        shutil.copy2(image_path, new_path)
        logging.info(f"Original image with positive detection saved: {new_path}")
    except Exception as e:
        logging.error(f"Error saving original image with positive detection: {str(e)}")

# Ensure single instance is running
ensure_single_instance()

# If this script is run directly, you might want to add some initialization or testing code here
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Image processor initialized and ready.")
    # You could add some test code here if needed