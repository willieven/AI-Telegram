import os
import logging
import time
from threading import Thread, Event
from queue import Queue, Empty, Full
import sqlite3
from datetime import datetime
import traceback

from config import MAX_IMAGE_QUEUE, MAIN_FTP_DIRECTORY
from image_processor import process_image

class PersistentQueue:
    def __init__(self, db_path, max_size):
        self.db_path = db_path
        self.max_size = max_size
        self.memory_queue = Queue(maxsize=max_size)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS image_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    user_settings TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def put(self, item):
        try:
            self.memory_queue.put_nowait(item)
        except Full:
            self.persist_to_db(item)

    def persist_to_db(self, item):
        image_path, user_settings = item
        with self.conn:
            self.conn.execute('INSERT INTO image_queue (image_path, user_settings) VALUES (?, ?)',
                              (image_path, str(user_settings)))
        logging.info(f"Image {image_path} persisted to database due to full queue")

    def get(self):
        try:
            return self.memory_queue.get_nowait()
        except Empty:
            return self.get_from_db()

    def get_from_db(self):
        with self.conn:
            cursor = self.conn.execute('SELECT id, image_path, user_settings FROM image_queue ORDER BY timestamp ASC LIMIT 1')
            row = cursor.fetchone()
            if row:
                self.conn.execute('DELETE FROM image_queue WHERE id = ?', (row[0],))
                return row[1], eval(row[2])  # Convert string back to dict
        return None

    def qsize(self):
        return self.memory_queue.qsize() + self.db_size()

    def db_size(self):
        with self.conn:
            cursor = self.conn.execute('SELECT COUNT(*) FROM image_queue')
            return cursor.fetchone()[0]

class ImageProcessorThread(Thread):
    def __init__(self, queue, stop_event):
        Thread.__init__(self)
        self.queue = queue
        self.stop_event = stop_event
        self.daemon = True

    def run(self):
        while not self.stop_event.is_set():
            try:
                item = self.queue.get()
                if item is None:
                    time.sleep(1)
                    continue
                
                image_path, user_settings = item
                process_image(image_path, user_settings)
            except Empty:
                time.sleep(1)  # Wait a bit if the queue is empty
            except Exception as e:
                logging.error(f"Error in image processor thread: {str(e)}")
                logging.error(traceback.format_exc())
                time.sleep(5)  # Wait a bit before continuing to prevent rapid error loops

def monitor_threads(threads, queue, stop_event):
    while not stop_event.is_set():
        for i, thread in enumerate(threads):
            if not thread.is_alive():
                logging.warning(f"Image processor thread {i} died. Restarting...")
                threads[i] = ImageProcessorThread(queue, stop_event)
                threads[i].start()
        time.sleep(10)  # Check every 10 seconds

def start_image_processing(num_threads):
    db_path = os.path.join(MAIN_FTP_DIRECTORY, 'image_queue.db')
    queue = PersistentQueue(db_path, MAX_IMAGE_QUEUE)
    stop_event = Event()
    
    threads = []
    for _ in range(num_threads):
        processor_thread = ImageProcessorThread(queue, stop_event)
        processor_thread.start()
        threads.append(processor_thread)
    
    # Start the monitoring thread
    monitor_thread = Thread(target=monitor_threads, args=(threads, queue, stop_event))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return queue, stop_event

def log_queue_size(queue):
    queue_size = queue.qsize()
    logging.info(f"Current image queue size: {queue_size}")
    if queue_size > MAX_IMAGE_QUEUE * 0.8:
        logging.warning(f"Image queue is getting full. Current size: {queue_size}")

def start_image_processing_system(num_threads):
    queue, stop_event = start_image_processing(num_threads)
    
    # Start a thread to periodically log queue size
    def queue_size_logger():
        while not stop_event.is_set():
            log_queue_size(queue)
            time.sleep(300)  # Log every 5 minutes

    logger_thread = Thread(target=queue_size_logger)
    logger_thread.daemon = True
    logger_thread.start()
    
    logging.info(f"Image processing system started with {num_threads} threads")
    return queue, stop_event

def shutdown_image_processing(stop_event):
    stop_event.set()
    logging.info("Shutting down image processing system...")
    time.sleep(5)  # Give threads time to finish
    logging.info("Image processing system shut down.")