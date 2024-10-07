import os
import socket
from threading import Thread, Lock
import logging
from datetime import datetime
import time
from config import USERS, MAIN_FTP_DIRECTORY, FTP_HOST
from utils import is_within_working_hours

USER_LOOKUP = {user_data['FTP_USER']: (user_id, user_data) for user_id, user_data in USERS.items()}

class ClientSession:
    def __init__(self, username, main_ip):
        self.username = username
        self.main_ip = main_ip
        self.additional_ips = set()
        self.last_activity = time.time()

    def update_activity(self, ip):
        self.last_activity = time.time()
        if ip != self.main_ip:
            self.additional_ips.add(ip)

class FTPServer(Thread):
    def __init__(self, host, port, image_queue):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.image_queue = image_queue
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.active_sessions = {}
        self.session_lock = Lock()

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        logging.info(f"FTP server listening on {self.host}:{self.port}")
        while True:
            try:
                conn, addr = self.sock.accept()
                logging.info(f"New connection from {addr[0]}:{addr[1]}")
                client_thread = Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
            except Exception as e:
                logging.error(f"Failed to establish connection with client: {str(e)}")

    def handle_client(self, conn, addr):
        data_sock = None
        pasv_sock = None
        conn.send(b'220 Welcome to FTP server\r\n')
        current_directory = '/'
        user_settings = None
        current_user = None
        rest_position = 0
        transfer_type = 'I'
        utf8_enabled = False
        rename_from = None
        session = None

        def log_command(cmd, arg=''):
            nonlocal session
            ip = addr[0]
            if session:
                session.update_activity(ip)
                if ip in session.additional_ips:
                    logging.info(f"Command from additional IP for user '{session.username}': {ip}:{addr[1]} - {cmd} {arg}")
                else:
                    logging.debug(f"Received command from {ip}:{addr[1]}: {cmd} {arg}")
            else:
                logging.debug(f"Received command from {ip}:{addr[1]}: {cmd} {arg}")

        def enter_passive_mode():
            nonlocal pasv_sock
            if pasv_sock:
                pasv_sock.close()
            pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pasv_sock.bind((self.host, 0))
            pasv_sock.listen(1)
            pasv_ip, pasv_port = pasv_sock.getsockname()
            pasv_ip = FTP_HOST if FTP_HOST != '0.0.0.0' else conn.getsockname()[0]
            ip_parts = pasv_ip.split('.')
            port_part1, port_part2 = divmod(pasv_port, 256)
            return f'227 Entering Passive Mode ({",".join(ip_parts)},{port_part1},{port_part2})'

        while True:
            try:
                data = conn.recv(1024).decode('utf-8' if utf8_enabled else 'ascii', errors='replace').strip()
                if not data:
                    logging.info(f"Client {addr[0]}:{addr[1]} disconnected")
                    break
                cmd = data.split(' ')[0].upper()
                arg = ' '.join(data.split(' ')[1:])

                log_command(cmd, arg)

                if cmd == 'USER':
                    if arg in USER_LOOKUP:
                        conn.send(b'331 User name okay, need password\r\n')
                        current_user = arg
                    else:
                        conn.send(b'530 User not found\r\n')
                        logging.warning(f"Failed login attempt: Unknown user '{arg}' from {addr[0]}:{addr[1]}")
                elif cmd == 'PASS':
                    if current_user and USER_LOOKUP[current_user][1]['FTP_PASS'] == arg:
                        user_id, user_settings = USER_LOOKUP[current_user]
                        user_settings = user_settings.copy()
                        user_settings['FTP_DIRECTORY'] = os.path.join(MAIN_FTP_DIRECTORY, user_id)
                        conn.send(b'230 User logged in, proceed\r\n')
                        with self.session_lock:
                            session = ClientSession(current_user, addr[0])
                            self.active_sessions[current_user] = session
                        logging.info(f"User '{current_user}' logged in from {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'530 Login incorrect\r\n')
                        logging.warning(f"Failed login attempt: Incorrect password for user '{current_user}' from {addr[0]}:{addr[1]}")
                        break
                elif cmd == 'SYST':
                    conn.send(b'215 UNIX Type: L8\r\n')
                elif cmd == 'FEAT':
                    features = [
                        '211-Features:',
                        ' PASV',
                        ' UTF8',
                        ' MLSD',
                        ' SIZE',
                        ' REST STREAM',
                        ' MDTM',
                        ' MFMT',
                        ' TVFS',
                        ' AVBL',
                        ' EPRT',
                        ' EPSV',
                        ' ESTP',
                        '211 End'
                    ]
                    conn.send('\r\n'.join(features).encode() + b'\r\n')
                elif cmd == 'PWD':
                    conn.send(f'257 "{current_directory}" is current directory\r\n'.encode(
                        'utf-8' if utf8_enabled else 'ascii'))
                elif cmd == 'CWD':
                    new_dir = os.path.normpath(os.path.join(current_directory, arg))
                    full_path = os.path.join(user_settings['FTP_DIRECTORY'], new_dir.lstrip('/'))
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        current_directory = new_dir
                        conn.send(b'250 Directory successfully changed\r\n')
                        logging.info(f"Directory changed to {full_path} for {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'550 Failed to change directory\r\n')
                        logging.warning(f"Failed to change directory to {full_path} for {addr[0]}:{addr[1]}: Directory does not exist")
                elif cmd == 'CDUP':
                    new_dir = os.path.normpath(os.path.join(current_directory, '..'))
                    full_path = os.path.join(user_settings['FTP_DIRECTORY'], new_dir.lstrip('/'))
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        current_directory = new_dir
                        conn.send(b'250 Directory successfully changed\r\n')
                        logging.info(f"Directory changed to parent: {full_path} for {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'550 Failed to change directory\r\n')
                        logging.warning(f"Failed to change to parent directory {full_path} for {addr[0]}:{addr[1]}: Directory does not exist")
                elif cmd == 'TYPE':
                    if arg in ['A', 'I']:
                        transfer_type = arg
                        conn.send(f'200 Type set to {arg}\r\n'.encode())
                    else:
                        conn.send(b'504 Command not implemented for that parameter\r\n')
                elif cmd == 'PASV':
                    pasv_response = enter_passive_mode()
                    conn.send(pasv_response.encode() + b'\r\n')
                    logging.info(f"Entered passive mode: {pasv_response} for {addr[0]}:{addr[1]}")
                elif cmd == 'EPSV':
                    if pasv_sock:
                        pasv_sock.close()
                    pasv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    pasv_sock.bind((self.host, 0))
                    pasv_sock.listen(1)
                    _, port = pasv_sock.getsockname()
                    epsv_response = f'229 Entering Extended Passive Mode (|||{port}|)'
                    conn.send(epsv_response.encode() + b'\r\n')
                    logging.info(f"Entered extended passive mode: {epsv_response} for {addr[0]}:{addr[1]}")
                elif cmd in ['LIST', 'MLSD', 'NLST', 'RETR', 'STOR']:
                    if not pasv_sock:
                        conn.send(b'425 Use PASV first\r\n')
                        logging.warning(f"Data transfer command {cmd} received before PASV for {addr[0]}:{addr[1]}")
                        continue

                    conn.send(b'150 Opening data connection\r\n')
                    try:
                        data_sock, data_addr = pasv_sock.accept()
                        logging.info(f"Data connection established from {data_addr[0]}:{data_addr[1]}")

                        if cmd in ['LIST', 'MLSD', 'NLST']:
                            directory = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'))
                            for item in os.listdir(directory):
                                item_path = os.path.join(directory, item)
                                stats = os.stat(item_path)
                                last_modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y%m%d%H%M%S.000')
                                size = stats.st_size
                                is_dir = 'dir' if os.path.isdir(item_path) else 'file'
                                if cmd == 'MLSD':
                                    list_item = f"type={is_dir};size={size};modify={last_modified}; {item}\r\n"
                                elif cmd == 'NLST':
                                    list_item = f"{item}\r\n"
                                else:  # LIST
                                    perms = 'drwxr-xr-x' if is_dir == 'dir' else '-rw-r--r--'
                                    list_item = f"{perms} 1 owner group {size:8d} {last_modified[4:6]}-{last_modified[6:8]} {last_modified[:4]} {item}\r\n"
                                data_sock.sendall(list_item.encode('utf-8' if utf8_enabled else 'ascii'))
                            logging.info(f"Successfully listed directory {directory} for {addr[0]}:{addr[1]}")
                        elif cmd == 'RETR':
                            file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                            if os.path.exists(file_path) and os.path.isfile(file_path):
                                with open(file_path, 'rb') as file:
                                    file.seek(rest_position)
                                    while True:
                                        chunk = file.read(8192)
                                        if not chunk:
                                            break
                                        data_sock.sendall(chunk)
                                logging.info(f"File {file_path} retrieved by {addr[0]}:{addr[1]}")
                            else:
                                conn.send(b'550 File not found\r\n')
                                logging.warning(f"File not found: {file_path} for {addr[0]}:{addr[1]}")
                        elif cmd == 'STOR':
                            file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, 'wb' if rest_position == 0 else 'r+b') as file:
                                if rest_position > 0:
                                    file.seek(rest_position)
                                while True:
                                    chunk = data_sock.recv(8192)
                                    if not chunk:
                                        break
                                    file.write(chunk)
                            if is_within_working_hours(user_settings):
                                self.image_queue.put((file_path, user_settings))
                                logging.info(f"File {file_path} queued for processing")
                                conn.send(b'226 Transfer complete, file queued for processing\r\n')
                            else:
                                from image_processor import cleanup_files
                                cleanup_files(file_path, MAIN_FTP_DIRECTORY)
                                conn.send(b'226 Transfer complete (file deleted - outside working hours)\r\n')
                                logging.info(f"File {file_path} deleted - outside working hours")

                        conn.send(b'226 Transfer complete\r\n')
                    except Exception as e:
                        conn.send(b'425 Can\'t open data connection\r\n')
                        logging.error(f"Failed to establish data connection for {cmd}: {str(e)}")
                    finally:
                        if data_sock:
                            data_sock.close()
                        if pasv_sock:
                            pasv_sock.close()
                            pasv_sock = None
                        rest_position = 0
                elif cmd == 'MKD':
                    new_dir = os.path.normpath(os.path.join(current_directory, arg))
                    full_path = os.path.join(user_settings['FTP_DIRECTORY'], new_dir.lstrip('/'))
                    try:
                        os.makedirs(full_path, exist_ok=True)
                        conn.send(f'257 "{new_dir}" directory created\r\n'.encode('utf-8' if utf8_enabled else 'ascii'))
                        logging.info(f"Directory {full_path} created by {addr[0]}:{addr[1]}")
                    except Exception as e:
                        conn.send(b'550 Failed to create directory\r\n')
                        logging.error(f"Failed to create directory {full_path} for {addr[0]}:{addr[1]}: {str(e)}")
                elif cmd == 'RMD':
                    dir_path = os.path.normpath(os.path.join(current_directory, arg))
                    full_path = os.path.join(user_settings['FTP_DIRECTORY'], dir_path.lstrip('/'))
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        try:
                            os.rmdir(full_path)
                            conn.send(b'250 Directory removed\r\n')
                            logging.info(f"Directory {full_path} removed by {addr[0]}:{addr[1]}")
                        except Exception as e:
                            conn.send(b'550 Failed to remove directory\r\n')
                            logging.error(f"Failed to remove directory {full_path} for {addr[0]}:{addr[1]}: {str(e)}")
                    else:
                        conn.send(b'550 Directory not found\r\n')
                        logging.warning(f"Directory not found for removal: {full_path} for {addr[0]}:{addr[1]}")
                elif cmd == 'DELE':
                    file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            conn.send(b'250 File deleted\r\n')
                            logging.info(f"File {file_path} deleted by {addr[0]}:{addr[1]}")
                        except Exception as e:
                            conn.send(b'550 Failed to delete file\r\n')
                            logging.error(f"Failed to delete file {file_path} for {addr[0]}:{addr[1]}: {str(e)}")
                    else:
                        conn.send(b'550 File not found\r\n')
                        logging.warning(f"File not found for deletion: {file_path} for {addr[0]}:{addr[1]}")
                elif cmd == 'SIZE':
                    file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        conn.send(f'213 {size}\r\n'.encode())
                        logging.info(f"Size request for {file_path}: {size} bytes, for {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'550 File not found\r\n')
                        logging.warning(f"File not found for size request: {file_path} for {addr[0]}:{addr[1]}")
                elif cmd == 'REST':
                    try:
                        rest_position = int(arg)
                        conn.send(b'350 Restarting at specified position\r\n')
                        logging.info(f"REST position set to {rest_position} for {addr[0]}:{addr[1]}")
                    except ValueError:
                        conn.send(b'501 Invalid REST position\r\n')
                        logging.warning(f"Invalid REST position '{arg}' received from {addr[0]}:{addr[1]}")
                elif cmd == 'RNFR':
                    rename_from = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                    if os.path.exists(rename_from):
                        conn.send(b'350 Ready for RNTO\r\n')
                        logging.info(f"RNFR command received for {rename_from} from {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'550 File not found\r\n')
                        logging.warning(f"File not found for RNFR: {rename_from} for {addr[0]}:{addr[1]}")
                elif cmd == 'RNTO':
                    if rename_from:
                        rename_to = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                        try:
                            os.rename(rename_from, rename_to)
                            conn.send(b'250 Rename successful\r\n')
                            logging.info(f"File renamed from {rename_from} to {rename_to} by {addr[0]}:{addr[1]}")
                        except Exception as e:
                            conn.send(b'553 Rename failed\r\n')
                            logging.error(f"Failed to rename file from {rename_from} to {rename_to} for {addr[0]}:{addr[1]}: {str(e)}")
                        finally:
                            rename_from = None
                    else:
                        conn.send(b'503 Bad sequence of commands\r\n')
                        logging.warning(f"RNTO command received without prior RNFR from {addr[0]}:{addr[1]}")
                elif cmd == 'OPTS':
                    if arg.upper().startswith('UTF8 '):
                        utf8_setting = arg.split(' ')[1].upper()
                        if utf8_setting == 'ON':
                            utf8_enabled = True
                            conn.send(b'200 UTF8 set to on\r\n')
                            logging.info(f"UTF8 enabled for {addr[0]}:{addr[1]}")
                        elif utf8_setting == 'OFF':
                            utf8_enabled = False
                            conn.send(b'200 UTF8 set to off\r\n')
                            logging.info(f"UTF8 disabled for {addr[0]}:{addr[1]}")
                        else:
                            conn.send(b'501 Invalid UTF8 option\r\n')
                            logging.warning(f"Invalid UTF8 option '{utf8_setting}' received from {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'501 Option not supported\r\n')
                        logging.warning(f"Unsupported OPTS command '{arg}' received from {addr[0]}:{addr[1]}")
                elif cmd == 'MDTM':
                    file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), arg)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        mtime = os.path.getmtime(file_path)
                        mtimestr = time.strftime('%Y%m%d%H%M%S', time.localtime(mtime))
                        conn.send(f'213 {mtimestr}\r\n'.encode())
                        logging.info(f"MDTM request for {file_path}: {mtimestr}, for {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'550 File not found\r\n')
                        logging.warning(f"File not found for MDTM request: {file_path} for {addr[0]}:{addr[1]}")
                elif cmd == 'MFMT':
                    parts = arg.split(' ', 1)
                    if len(parts) == 2:
                        timestamp, filename = parts
                        file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), filename)
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            try:
                                mtime = time.mktime(time.strptime(timestamp, '%Y%m%d%H%M%S'))
                                os.utime(file_path, (mtime, mtime))
                                conn.send(f'213 Modify={timestamp}; {filename}\r\n'.encode())
                                logging.info(f"Modified time of {file_path} changed to {timestamp} by {addr[0]}:{addr[1]}")
                            except Exception as e:
                                conn.send(b'550 Could not modify file time\r\n')
                                logging.error(f"Failed to modify file time for {file_path} by {addr[0]}:{addr[1]}: {str(e)}")
                        else:
                            conn.send(b'550 File not found\r\n')
                            logging.warning(f"File not found for MFMT: {file_path} for {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'501 Invalid MFMT command\r\n')
                        logging.warning(f"Invalid MFMT command received from {addr[0]}:{addr[1]}")
                elif cmd == 'SITE':
                    site_cmd = arg.split(' ')[0].upper() if arg else ''
                    if site_cmd == 'CHMOD':
                        parts = arg.split(' ', 2)
                        if len(parts) == 3:
                            mode, filename = parts[1], parts[2]
                            file_path = os.path.join(user_settings['FTP_DIRECTORY'], current_directory.lstrip('/'), filename)
                            if os.path.exists(file_path):
                                try:
                                    os.chmod(file_path, int(mode, 8))
                                    conn.send(b'200 CHMOD command successful\r\n')
                                    logging.info(f"Changed permissions of {file_path} to {mode} by {addr[0]}:{addr[1]}")
                                except Exception as e:
                                    conn.send(b'550 CHMOD command failed\r\n')
                                    logging.error(f"Failed to change permissions of {file_path} by {addr[0]}:{addr[1]}: {str(e)}")
                            else:
                                conn.send(b'550 File not found\r\n')
                                logging.warning(f"File not found for CHMOD: {file_path} for {addr[0]}:{addr[1]}")
                        else:
                            conn.send(b'501 Invalid SITE CHMOD command\r\n')
                            logging.warning(f"Invalid SITE CHMOD command received from {addr[0]}:{addr[1]}")
                    else:
                        conn.send(b'504 SITE command not implemented\r\n')
                        logging.warning(f"Unimplemented SITE command '{site_cmd}' received from {addr[0]}:{addr[1]}")
                elif cmd == 'HELP':
                    help_text = [
                        '214-The following commands are recognized:',
                        ' USER PASS QUIT SYST FEAT PWD CWD CDUP TYPE',
                        ' PASV EPSV LIST MLSD NLST STOR RETR MKD RMD DELE',
                        ' SIZE REST RNFR RNTO OPTS MDTM MFMT SITE HELP NOOP',
                        '214 Help OK.'
                    ]
                    conn.send('\r\n'.join(help_text).encode() + b'\r\n')
                    logging.info(f"HELP command received from {addr[0]}:{addr[1]}")
                elif cmd == 'NOOP':
                    conn.send(b'200 NOOP ok\r\n')
                    logging.debug(f"NOOP command received from {addr[0]}:{addr[1]}")
                elif cmd == 'QUIT':
                    conn.send(b'221 Goodbye\r\n')
                    with self.session_lock:
                        if session:
                            del self.active_sessions[session.username]
                    logging.info(f"User '{current_user}' from {addr[0]}:{addr[1]} logged out")
                    break
                else:
                    conn.send(b'502 Command not implemented\r\n')
                    logging.warning(f"Unimplemented command '{cmd}' received from {addr[0]}:{addr[1]}")
            except Exception as e:
                logging.error(f"Error handling command from {addr[0]}:{addr[1]}: {str(e)}")
                conn.send(b'500 Error\r\n')
        conn.close()
        logging.info(f"Connection closed for {addr[0]}:{addr[1]}")

def create_ftp_server(host, port, image_queue):
    return FTPServer(host, port, image_queue)