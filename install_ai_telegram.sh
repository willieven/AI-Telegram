#!/bin/bash

# One-Click Installation Script for AI-Telegram FTP Server (Ubuntu 24.04 compatible)

set -e

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Update system and install dependencies
echo "Updating system and installing dependencies..."
apt-get update
apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git libgl1 libglib2.0-0 redis-server

# Install system dependencies for OpenCV
apt-get install -y libgl1 libglib2.0-0

# Clone the repository
echo "Cloning the repository..."
git clone https://github.com/willieven/AI-Telegram.git /opt/ftp-server
cd /opt/ftp-server

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies in the virtual environment
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Download YOLO model
echo "Downloading YOLO model..."
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt -O /opt/ftp-server/yolov8l.pt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /opt/ftp-server/FTP /opt/ftp-server/positive_photos /opt/ftp-server/logs
chmod 755 /opt/ftp-server/FTP /opt/ftp-server/positive_photos /opt/ftp-server/logs

# Configure Redis
echo "Configuring Redis..."
read -p "Enter a strong password for Redis: " redis_password
sed -i "s/# requirepass foobared/requirepass $redis_password/" /etc/redis/redis.conf
systemctl restart redis-server

# Prompt user for configuration
echo "Please enter the following configuration details:"
read -p "Telegram Bot Token: " telegram_bot_token

# Update config.py with user input
sed -i "s/TELEGRAM_BOT_TOKEN = '.*'/TELEGRAM_BOT_TOKEN = '$telegram_bot_token'/" /opt/ftp-server/config.py
sed -i "s/REDIS_PASSWORD = '.*'/REDIS_PASSWORD = '$redis_password'/" /opt/ftp-server/config.py

# Create systemd service file
echo "Creating systemd service..."
cat << EOF > /etc/systemd/system/ai-telegram-ftp.service
[Unit]
Description=AI-Telegram FTP Server
After=network.target

[Service]
ExecStart=/opt/ftp-server/venv/bin/python /opt/ftp-server/main.py
WorkingDirectory=/opt/ftp-server
Restart=always
User=root
Group=root
Environment=PATH=/opt/ftp-server/venv/bin:/usr/bin:/usr/local/bin
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/opt/ftp-server/logs/ai-telegram-ftp.log
StandardError=append:/opt/ftp-server/logs/ai-telegram-ftp.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "Enabling and starting the service..."
systemctl daemon-reload
systemctl enable ai-telegram-ftp.service
systemctl start ai-telegram-ftp.service

# Configure firewall
echo "Configuring firewall..."
ufw allow 2121/tcp

echo "Installation complete! AI-Telegram FTP Server is now running."
echo "Please check the logs at /opt/ftp-server/logs/ai-telegram-ftp.log for any issues."
echo "Remember to update the USERS dictionary in /opt/ftp-server/config.py with your user configurations."
echo "You may need to restart the service after updating the config: sudo systemctl restart ai-telegram-ftp.service"

# Deactivate virtual environment
deactivate