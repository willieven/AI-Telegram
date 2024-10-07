import os
import logging
import cv2
import numpy as np
from ultralytics import YOLO
import telepot
import shutil
from datetime import datetime
from config import YOLO_MODEL, TELEGRAM_BOT_TOKEN, POSITIVE_PHOTOS_DIRECTORY, SAVE_POSITIVE_PHOTOS, MAIN_FTP_DIRECTORY

# Initialize YOLO model
model = YOLO(YOLO_MODEL)

# Initialize Telegram bot
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)

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
                elif class_name in ['cow', 'sheep', 'horse', 'dog', 'cat', 'animal'] and user_settings['ENABLE_VEHICLE_ANIMAL_DETECTION'] and conf > user_settings['ANIMAL_CONFIDENCE_THRESHOLD']:
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

def check_vehicle_animal_proximity(vehicles, animals, distance_threshold):
    for vehicle in vehicles:
        v_x1, v_y1, v_x2, v_y2 = vehicle[0]
        v_center = ((v_x1 + v_x2) / 2, (v_y1 + v_y2) / 2)
        
        for animal in animals:
            a_x1, a_y1, a_x2, a_y2 = animal[0]
            a_center = ((a_x1 + a_x2) / 2, (a_y1 + a_y2) / 2)
            
            distance = np.sqrt((v_center[0] - a_center[0])**2 + (v_center[1] - a_center[1])**2)
            
            if distance < distance_threshold:
                return True
    
    return False

def process_image(image_path, user_settings):
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
    if user_settings['ENABLE_VEHICLE_ANIMAL_DETECTION'] and check_vehicle_animal_proximity(detections['vehicle'],
                                                                                           detections['animal'],
                                                                                           user_settings['VEHICLE_ANIMAL_DISTANCE_THRESHOLD']):
        detected_objects.append('vehicle with animal')

    if detected_objects:
        # Save original image if positive detection and SAVE_POSITIVE_PHOTOS is enabled
        if SAVE_POSITIVE_PHOTOS:
            save_positive_photo(image_path, user_settings['FTP_USER'])

        # Create marked image for Telegram
        marked_image = draw_detections(image.copy(), detections)
        marked_image_path = image_path.replace('.jpg', '_marked.jpg')
        cv2.imwrite(marked_image_path, marked_image)

        detection_message = f"Detected: {', '.join(detected_objects)}"
        send_telegram_image(marked_image_path, detection_message, user_settings['TELEGRAM_CHAT_ID'])
        logging.info(f"{detection_message} in {image_path}. Marked image sent to Telegram.")

        cleanup_files(image_path, MAIN_FTP_DIRECTORY)
        cleanup_files(marked_image_path, MAIN_FTP_DIRECTORY)
    else:
        logging.info(f"No relevant objects detected in {image_path}.")
        cleanup_files(image_path, MAIN_FTP_DIRECTORY)

def cleanup_files(file_path, base_directory):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
    
    # Clean up empty directories
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
        # Create user-specific directory within POSITIVE_PHOTOS_DIRECTORY
        user_positive_dir = os.path.join(POSITIVE_PHOTOS_DIRECTORY, username)
        os.makedirs(user_positive_dir, exist_ok=True)

        # Generate a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{os.path.basename(image_path)}"
        new_path = os.path.join(user_positive_dir, new_filename)

        # Copy the original file to the new location
        shutil.copy2(image_path, new_path)
        logging.info(f"Original image with positive detection saved: {new_path}")
    except Exception as e:
        logging.error(f"Error saving original image with positive detection: {str(e)}")