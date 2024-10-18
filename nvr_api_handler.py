import asyncio
import logging
from io import BytesIO
from datetime import datetime
import os
import time
from hikvisionapi import AsyncClient as HikvisionClient
import aiohttp
from config import USERS, MAIN_FTP_DIRECTORY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NVRAPIHandler:
    def __init__(self, device_type, ip, port, username, password, user_id, stream='main'):
        self.device_type = device_type.lower()
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.user_id = user_id
        self.stream = stream.lower()
        self.client = None
        self.session = None

    async def connect(self):
        try:
            if self.device_type == 'hikvision':
                return await self._connect_hikvision()
            elif self.device_type == 'dahua':
                return await self._connect_dahua()
            else:
                raise ValueError(f"Unsupported device type: {self.device_type}")
        except Exception as e:
            logging.error(f"Failed to connect to {self.device_type} NVR at {self.ip}:{self.port}: {str(e)}")
            return False

    async def _connect_hikvision(self):
        url = f'http://{self.ip}:{self.port}'
        try:
            self.client = HikvisionClient(url, self.username, self.password, timeout=30)
            await self.client.System.deviceInfo(method='get')
            logging.info(f"Successfully connected to Hikvision NVR at {self.ip}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Hikvision NVR at {self.ip}:{self.port}: {str(e)}")
            return False

    async def _connect_dahua(self):
        self.session = aiohttp.ClientSession()
        url = f'http://{self.ip}:{self.port}/cgi-bin/global.login?userName={self.username}&password={self.password}'
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    logging.info(f"Successfully connected to Dahua NVR at {self.ip}:{self.port}")
                    return True
                else:
                    logging.error(f"Failed to connect to Dahua NVR at {self.ip}:{self.port}")
                    return False
        except Exception as e:
            logging.error(f"Error connecting to Dahua NVR at {self.ip}:{self.port}: {str(e)}")
            return False

    async def get_device_info(self):
        if self.device_type == 'hikvision':
            return await self._get_device_info_hikvision()
        elif self.device_type == 'dahua':
            return await self._get_device_info_dahua()

    async def _get_device_info_hikvision(self):
        try:
            response = await self.client.System.deviceInfo(method='get')
            logging.info(f"Hikvision device info for {self.ip}: {response}")
            return response
        except Exception as e:
            logging.error(f"Error getting Hikvision device info for {self.ip}: {str(e)}")
            return None

    async def _get_device_info_dahua(self):
        try:
            url = f'http://{self.ip}:{self.port}/cgi-bin/magicBox.cgi?action=getSystemInfo'
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    logging.info(f"Dahua device info for {self.ip}: {data}")
                    return data
                else:
                    logging.error(f"Failed to get Dahua device info for {self.ip}")
                    return None
        except Exception as e:
            logging.error(f"Error getting Dahua device info for {self.ip}: {str(e)}")
            return None

    async def get_latest_event_image(self):
        if self.device_type == 'hikvision':
            return await self._get_latest_event_image_hikvision()
        elif self.device_type == 'dahua':
            return await self._get_latest_event_image_dahua()

    async def _get_latest_event_image_hikvision(self):
        try:
            async for event in self.client.Event.notification.alertStream(method='get', type='stream'):
                if 'EventNotificationAlert' in event:
                    channel = int(event['EventNotificationAlert'].get('channelID', '1'))
                    image_data = await self._get_channel_image_hikvision(channel * 100)
                    if image_data:
                        return image_data, event
            return None, None
        except Exception as e:
            logging.error(f"Error getting latest event from Hikvision NVR {self.ip}: {str(e)}")
            return None, None

    async def _get_latest_event_image_dahua(self):
        try:
            url = f'http://{self.ip}:{self.port}/cgi-bin/eventManager.cgi?action=getEventIndexes&code=AllEvent'
            async with self.session.get(url) as response:
                if response.status == 200:
                    event_data = await response.text()
                    event_lines = event_data.split('\n')
                    if event_lines:
                        latest_event = event_lines[-1]
                        channel = 1  # Adjust this based on how Dahua reports the channel
                        image_data = await self._get_channel_image_dahua(channel)
                        if image_data:
                            return image_data, latest_event
            return None, None
        except Exception as e:
            logging.error(f"Error getting latest event from Dahua NVR {self.ip}: {str(e)}")
            return None, None

    async def _get_channel_image_hikvision(self, channel):
        try:
            image = BytesIO()
            async for chunk in self.client.Streaming.channels[channel].picture(method='get', type='opaque_data'):
                if chunk:
                    image.write(chunk)
            image.seek(0)
            return image.getvalue()
        except Exception as e:
            logging.error(f"Error getting image for channel {channel} from Hikvision NVR {self.ip}: {str(e)}")
            return None

    async def _get_channel_image_dahua(self, channel):
        try:
            url = f'http://{self.ip}:{self.port}/cgi-bin/snapshot.cgi?channel={channel}'
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logging.error(f"Failed to get image for channel {channel} from Dahua NVR {self.ip}")
                    return None
        except Exception as e:
            logging.error(f"Error getting image for channel {channel} from Dahua NVR {self.ip}: {str(e)}")
            return None

    async def check_connection(self):
        return await self.connect()

    async def close(self):
        if self.device_type == 'dahua' and self.session:
            await self.session.close()

async def process_nvr_events(image_queue):
    nvr_handlers = {}

    # Initialize NVR handlers and check connections
    for user_id, user_data in USERS.items():
        if 'NVR_DEVICES' in user_data:
            nvr_handlers[user_id] = []
            for device in user_data['NVR_DEVICES']:
                handler = NVRAPIHandler(
                    device['type'],
                    device['ip'],
                    device['port'],
                    device['username'],
                    device['password'],
                    user_id,
                    device.get('stream', 'main')
                )
                if await handler.check_connection():
                    nvr_handlers[user_id].append(handler)
                    logging.info(f"Successfully connected to {device['type']} NVR at {device['ip']} for user {user_id}")
                else:
                    logging.warning(f"Skipping NVR device {device['ip']} for user {user_id} due to connection failure")

    if not nvr_handlers:
        logging.warning("No NVR handlers were successfully initialized. Check NVR configurations.")
        return

    try:
        while True:
            for user_id, handlers in nvr_handlers.items():
                for handler in handlers:
                    image_data, event = await handler.get_latest_event_image()
                    if image_data:
                        # Save image to user's directory
                        user_directory = os.path.join(MAIN_FTP_DIRECTORY, user_id)
                        os.makedirs(user_directory, exist_ok=True)
                        image_filename = f"{handler.device_type}_{handler.stream}_image_{int(time.time())}.jpg"
                        image_path = os.path.join(user_directory, image_filename)
                        
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        # Queue image for processing
                        await image_queue.put((image_path, USERS[user_id], True))
                        logging.info(f"Queued {handler.stream} stream image from {handler.device_type} NVR at {handler.ip} for user {user_id}")
                        
                        # Log the event details
                        if event:
                            logging.info(f"Event details for {handler.ip}: {event}")
                    else:
                        logging.debug(f"No new events from {handler.device_type} NVR at {handler.ip} for user {user_id}")

            await asyncio.sleep(10)  # Wait for 10 seconds before checking again
    except asyncio.CancelledError:
        logging.info("NVR event processing was cancelled")
    except Exception as e:
        logging.error(f"Unexpected error in NVR event processing: {str(e)}")
    finally:
        # Close all sessions when done
        for handlers in nvr_handlers.values():
            for handler in handlers:
                await handler.close()

async def start_nvr_processing(image_queue):
    while True:
        try:
            await process_nvr_events(image_queue)
        except Exception as e:
            logging.error(f"Error in NVR processing: {str(e)}")
            await asyncio.sleep(60)  # Wait for 1 minute before retrying