# AI-Telegram FTP Server Installation Instructions

Follow these step-by-step instructions to install the AI-Telegram FTP Server on your Ubuntu system.

## Prerequisites

- A clean Ubuntu server (20.04 LTS or later recommended)
- Root or sudo access to the server
- Basic knowledge of Linux command line

## Installation Steps

1. **Create the installation script**

   First, create a new file named `install_ai_telegram.sh` in your home directory or any directory where you have write permissions.

   ```bash
   nano install_ai_telegram.sh
   ```

   Copy and paste the entire installation script into this file. The script content should be the same as the one provided in the "Ubuntu One-Click Installation Script for AI-Telegram FTP Server" artifact.

   After pasting the script, save the file and exit the text editor. In nano, you can do this by pressing `Ctrl+X`, then `Y`, and finally `Enter`.

2. **Make the script executable**

   To make the installation script executable, run the following command:

   ```bash
   chmod +x install_ai_telegram.sh
   ```

   This command gives the script execution permissions, allowing you to run it.

3. **Run the script with sudo**

   Execute the installation script with sudo privileges using the following command:

   ```bash
   sudo ./install_ai_telegram.sh
   ```

   This will start the installation process. The script will prompt you for necessary information during the installation.

4. **Follow the prompts**

   During the installation, you'll be asked to provide the following information:
   - A strong password for Redis
   - Your Telegram Bot Token

   Make sure to have this information ready before starting the installation.

5. **Wait for the installation to complete**

   The script will update your system, install dependencies, configure the server, and start the AI-Telegram FTP service. This process may take several minutes.

6. **Post-installation steps**

   After the script finishes, you'll need to:
   
   a. Update the USERS dictionary in the configuration file:
      ```bash
      sudo nano /opt/ftp-server/config.py
      ```
      Find the USERS dictionary and update it with your user configurations.

   b. Restart the service to apply changes:
      ```bash
      sudo systemctl restart ai-telegram-ftp.service
      ```

7. **Verify the installation**

   Check if the service is running:
   ```bash
   sudo systemctl status ai-telegram-ftp.service
   ```

   You should see that the service is active and running.

8. **Check the logs**

   If you encounter any issues or want to monitor the server's activity, check the logs:
   ```bash
   sudo tail -f /opt/ftp-server/logs/ai-telegram-ftp.log
   ```

## Troubleshooting

- If you encounter any permission issues, make sure you're running the script with sudo.
- If the service fails to start, check the logs for any error messages.
- Ensure that your firewall allows traffic on port 2121 (or whichever port you've configured for FTP).

## Security Notes

- Always use strong, unique passwords for Redis and FTP users.
- Regularly update your system and the AI-Telegram FTP Server to ensure you have the latest security patches.
- Consider using a firewall to restrict access to your server.

For any persistent issues or questions, please refer to the project's documentation or contact the maintainer.