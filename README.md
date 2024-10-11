# AI-Telegram

# Ubuntu Installation Guide for AI-Telegram FTP Server

This guide provides step-by-step instructions for installing and configuring the AI-Telegram FTP Server with image processing capabilities on a fresh Ubuntu server.

## Prerequisites

- A clean Ubuntu server (20.04 LTS or later recommended)
- Root or sudo access to the server
- Basic knowledge of Linux command line

## Installation Steps

1. **Update the system**

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install required system dependencies**

   ```bash
   sudo apt install -y python3 python3-pip git libgl1-mesa-glx libglib2.0-0 redis-server
   ```

3. **Clone the repository**

   ```bash
   sudo git clone https://github.com/yourusername/AI-Telegram.git /opt/ftp-server
   cd /opt/ftp-server
   ```

4. **Install Python dependencies**

   ```bash
   sudo pip3 install -r requirements.txt
   ```

5. **Configure the application**

   Edit the `config.py` file to set up your FTP users, Telegram bot token, and other settings:

   ```bash
   sudo nano /opt/ftp-server/config.py
   ```

   Make sure to update the following:
   - `TELEGRAM_BOT_TOKEN`
   - `USERS` dictionary with your user configurations
   - `REDIS_PASSWORD` (generate a strong password)

6. **Set up Redis**

   Edit the Redis configuration file:

   ```bash
   sudo nano /etc/redis/redis.conf
   ```

   Find the `# requirepass foobared` line and replace it with:

   ```
   requirepass your_strong_password_here
   ```

   Restart Redis:

   ```bash
   sudo systemctl restart redis-server
   ```

7. **Create necessary directories**

   ```bash
   sudo mkdir -p /opt/ftp-server/FTP /opt/ftp-server/positive_photos /opt/ftp-server/logs
   sudo chmod 755 /opt/ftp-server/FTP /opt/ftp-server/positive_photos /opt/ftp-server/logs
   ```

8. **Download YOLO model**

   ```bash
   sudo wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt -O /opt/ftp-server/yolov8l.pt
   ```

9. **Create a systemd service file**

   ```bash
   sudo nano /etc/systemd/system/ai-telegram-ftp.service
   ```

   Add the following content:

   ```ini
   [Unit]
   Description=AI-Telegram FTP Server
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /opt/ftp-server/main.py
   WorkingDirectory=/opt/ftp-server
   Restart=always
   User=root
   Group=root
   Environment=PATH=/usr/bin:/usr/local/bin
   Environment=PYTHONUNBUFFERED=1
   StandardOutput=append:/opt/ftp-server/logs/ai-telegram-ftp.log
   StandardError=append:/opt/ftp-server/logs/ai-telegram-ftp.log

   [Install]
   WantedBy=multi-user.target
   ```

10. **Enable and start the service**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable ai-telegram-ftp.service
    sudo systemctl start ai-telegram-ftp.service
    ```

11. **Check the service status**

    ```bash
    sudo systemctl status ai-telegram-ftp.service
    ```

12. **Monitor the logs**

    ```bash
    sudo tail -f /opt/ftp-server/logs/ai-telegram-ftp.log
    ```

## Firewall Configuration

If you're using UFW (Uncomplicated Firewall), allow the FTP port:

```bash
sudo ufw allow 2121/tcp
```

## Updating the Application

To update the application in the future:

1. Stop the service:
   ```bash
   sudo systemctl stop ai-telegram-ftp.service
   ```

2. Pull the latest changes:
   ```bash
   cd /opt/ftp-server
   sudo git pull
   ```

3. Install any new dependencies:
   ```bash
   sudo pip3 install -r requirements.txt
   ```

4. Start the service:
   ```bash
   sudo systemctl start ai-telegram-ftp.service
   ```

## Troubleshooting

- If you encounter any issues, check the logs at `/opt/ftp-server/logs/ai-telegram-ftp.log`
- Ensure all paths in the `config.py` file are correct
- Verify that the Redis password in `config.py` matches the one set in `/etc/redis/redis.conf`

For any persistent issues, please refer to the project's GitHub issues page or contact the maintainer.