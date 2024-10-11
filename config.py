# config.py

# FTP Server Settings
FTP_HOST = '0.0.0.0'  # Listen on all available interfaces
FTP_PORT = 2121  # Choose a port for your FTP server
MAIN_FTP_DIRECTORY = '/opt/ftp-server/FTP'  # Main directory for all user folders

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = '5779264529:AAEQkuymXy_og2CYamJp-t-Wkb7YdcGKLP4'

# YOLO Model Settings
YOLO_MODEL = 'yolov8l.pt'  # Path to the YOLO model file

# Image Processing Settings
MAX_IMAGE_QUEUE = 300  # Maximum number of images to queue for processing
SAVE_POSITIVE_PHOTOS = False  # Server-wide option to save positive detection photos
POSITIVE_PHOTOS_DIRECTORY = '/opt/ftp-server/positive_photos'  # Directory to save positive detection photos

# Watermark Settings
WATERMARK_TEXT = "Powered by Spoorvat AI"  # Global watermark text template

# User-specific settings
USERS = {
    'user1': {
        'FTP_USER': 'willie',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1002043093608',
        'SIGNL4_SECRET': 'https://connect.signl4.com/webhook/qi773gtvnb',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.5,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.3,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '19:00',
        'WORKING_END_TIME': '05:00'
    },
    'user2': {
        'FTP_USER': 'naboom',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1002321492260',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '19:00',
        'WORKING_END_TIME': '05:00'
    },
    'user3': {
        'FTP_USER': 'spoorvat',
        'FTP_PASS': 'ftp1234',
        'TELEGRAM_CHAT_ID': '-1001927072285',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user4': {
        'FTP_USER': 'shumbas',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001865781462',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user5': {
        'FTP_USER': 'dlu',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001475761590',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user6': {
        'FTP_USER': 'hendrik',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001556195386',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user7': {
        'FTP_USER': 'dlu2',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001648808667',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user8': {
        'FTP_USER': 'gpf',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001982091507',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user9': {
        'FTP_USER': 'gpf2',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001948635960',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user10': {
        'FTP_USER': 'roedtan',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001809519424',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user11': {
        'FTP_USER': 'hanglip',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001969769395',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user12': {
        'FTP_USER': 'crecy',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001922434570',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user13': {
        'FTP_USER': 'nyl',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001931015653',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user14': {
        'FTP_USER': 'single',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001658934697',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user15': {
        'FTP_USER': 'sterkover',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001997988193',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user16': {
        'FTP_USER': 'sterkpole',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1002141916709',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user17': {
        'FTP_USER': 'anker',
        'FTP_PASS': '12345',
        'TELEGRAM_CHAT_ID': '-1002080032559',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.2,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.2,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user18': {
        'FTP_USER': 'ari',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001955579905',
        'SIGNL4_SECRET': 'https://connect.signl4.com/webhook/qi773gtvnb',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.4,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '19:00',
        'WORKING_END_TIME': '04:30'
    },
    'user19': {
        'FTP_USER': 'danie',
        'FTP_PASS': 'danie12345',
        'TELEGRAM_CHAT_ID': '-1002347900410',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': False,
        'PERSON_CONFIDENCE_THRESHOLD': 0.6,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.7,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.5,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user20': {
        'FTP_USER': 'koos',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1002343302824',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.2,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.2,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user21': {
        'FTP_USER': 'koosboma',
        'FTP_PASS': 'Werianip1',
        'TELEGRAM_CHAT_ID': '-1001870975453',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.2,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.2,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    },
    'user22': {
        'FTP_USER': 'zimbi',
        'FTP_PASS': 'zimbi123',
        'TELEGRAM_CHAT_ID': '-1002389227208',
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': False,
        'ENABLE_ANIMAL_DETECTION': False,
        'PERSON_CONFIDENCE_THRESHOLD': 0.4,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.2,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.2,
        'WORKING_START_TIME': '00:00',
        'WORKING_END_TIME': '23:59'
    }
}

# Explanations of settings:
# FTP_HOST: The IP address the FTP server will listen on. '0.0.0.0' means all available interfaces.
# FTP_PORT: The port number the FTP server will use.
# MAIN_FTP_DIRECTORY: The main directory where all user folders will be created.
# TELEGRAM_BOT_TOKEN: The API token for your Telegram bot (same for all users).
# YOLO_MODEL: The filename or path to the YOLOv8 model file.
# MAX_IMAGE_QUEUE: The maximum number of images that can be queued for processing to prevent memory issues.

# For each user in the USERS dictionary:
# FTP_USER: Username for FTP authentication.
# FTP_PASS: Password for FTP authentication.
# TELEGRAM_CHAT_ID: The chat ID where the bot will send messages for this user.
# ENABLE_PERSON_DETECTION: Set to True to detect persons in images.
# ENABLE_VEHICLE_DETECTION: Set to True to detect vehicles in images.
# ENABLE_ANIMAL_DETECTION: Set to True to detect animals in images.
# PERSON_CONFIDENCE_THRESHOLD: The minimum confidence score for a person detection to be considered valid.
# VEHICLE_CONFIDENCE_THRESHOLD: The minimum confidence score for a vehicle detection to be considered valid.
# ANIMAL_CONFIDENCE_THRESHOLD: The minimum confidence score for an animal detection to be considered valid.
# WORKING_START_TIME: The time when the system should start processing images for this user (24-hour format).
# WORKING_END_TIME: The time when the system should stop processing images for this user (24-hour format).