import asyncio
import logging
from io import BytesIO
from datetime import datetime
import os
from hikvisionapi import AsyncClient
import urllib3

# Disable SSL warnings (only use this in testing environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# NVR connection details
NVR_IP = 'kantoor.spoorvat.co.za'
NVR_PORT = 8095
NVR_USERNAME = 'admin'
NVR_PASSWORD = 'Werianip1'

async def test_nvr_connection():
    url = f'http://{NVR_IP}:{NVR_PORT}'
    try:
        client = AsyncClient(url, NVR_USERNAME, NVR_PASSWORD, timeout=30)
        logging.info(f"Successfully created client for NVR at {url}")
        return client
    except Exception as e:
        logging.error(f"Failed to create client for NVR at {url}: {str(e)}")
        return None

async def get_device_info(client):
    try:
        response = await client.System.deviceInfo(method='get')
        logging.info(f"Device info: {response}")
        return response
    except Exception as e:
        logging.error(f"Error getting device info: {str(e)}")
        return None

async def get_events(client):
    try:
        logging.info("Starting event stream...")
        async for event in client.Event.notification.alertStream(method='get', type='stream'):
            logging.info(f"Received data from event stream: {event}")
            yield event
    except Exception as e:
        logging.error(f"Error in event stream: {str(e)}")

async def get_channel_image(client, channel):
    try:
        image = BytesIO()
        async for chunk in client.Streaming.channels[channel].picture(method='get', type='opaque_data'):
            if chunk:
                image.write(chunk)
        image.seek(0)
        return image.getvalue()
    except Exception as e:
        logging.error(f"Error getting image for channel {channel}: {str(e)}")
        return None

async def capture_and_save_image(client, channel, image_prefix):
    logging.info(f"Attempting to capture image from channel {channel}...")
    image_data = await get_channel_image(client, channel)
    if image_data:
        os.makedirs('test_images', exist_ok=True)
        image_path = os.path.join('test_images', f'{image_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_data)
        logging.info(f"Image saved to {image_path}")
        return True
    else:
        logging.warning(f"Failed to capture {image_prefix} image.")
        return False

async def event_listener(client, timeout):
    event_detected = False
    try:
        async with asyncio.timeout(timeout):
            async for event in get_events(client):
                event_detected = True
                if 'EventNotificationAlert' in event:
                    channel = int(event['EventNotificationAlert'].get('channelID', '1'))
                    await capture_and_save_image(client, channel * 100, 'event_image')
                else:
                    logging.info(f"Received non-event data: {event}")
    except asyncio.TimeoutError:
        logging.info(f"Event listening timed out after {timeout} seconds.")
    except Exception as e:
        logging.error(f"Error during event listening: {str(e)}")
    return event_detected

async def main():
    client = await test_nvr_connection()
    if not client:
        return

    device_info = await get_device_info(client)
    if not device_info:
        logging.error("Failed to retrieve device info")
        return

    logging.info("Starting event listener for 30 seconds...")
    event_detected = await event_listener(client, 30)

    if not event_detected:
        logging.info("No events detected. Capturing a test image.")
        await capture_and_save_image(client, 101, 'test_image')

    logging.info("Script execution completed.")

if __name__ == "__main__":
    asyncio.run(main())