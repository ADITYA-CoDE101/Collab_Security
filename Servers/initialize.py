from __future__ import print_function
import mysql.connector
from mysql.connector import Error, errorcode
from configparser import ConfigParser
from datetime import datetime
import os
import time
import bcrypt


class Utils:
    # Utilities

    #-------Loading-------
    def loading(self, flag = 0):
        for i in range(4):
            print(".",end=" ")
            time.sleep(0.5)
        if flag == 0:
            print(" ")
    #---------------------


class Configration(Utils):
    def __init__(self):
        self.directory = file_path = os.path.abspath("Config")
        self.config_file = "server.confg"


    def check_config(self):
        print("[ * ] Vrifieng the configrations file",end="")
        self.loading(1)
        file_path = os.path.join(self.directory, self.config_file)
        if os.path.isfile(file_path):
            print(": OK")
            print(f"[ + ] The configer file '{file_path}' Found.")
        else:
            print(": NO")
            print(f"[ - ] The configer file '{file_path}' does not exist or is not a file.")
            self.create_config()
    
    def create_config(self):
        print("[ + ] Creating Configration file", end=' ')
        content = '''# Chat server configuration
# Save as /home/dell/Documents/Coding/git_test/backup_files/TCP-communication-/Servers/chat.confg

[server]
# Address and port to listen on
bind_address = 0.0.0.0
port = 12345
protocol = tcp

[mysql]
host = localhost
user = dell
password = 1234 
database = chat1

# Text shown to clients after connect
welcome_message = Welcome to the Chat Server!
motd = Be respectful. No spam.

# Maximum simultaneous connected clients
max_clients = 100

[logging]
level = info       # debug, info, warn, error
file = /var/log/chat_server.log
rotate = daily
max_size_mb = 50

[security]
enable_tls = false
tls_cert = /etc/ssl/certs/chat_server.crt
tls_key = /etc/ssl/private/chat_server.key

# Authentication options
require_auth = false
auth_method = password  # password, token, oauth
# If require_auth = true, provide a user store or hook in your server implementation

# IP/CIDR entries allowed to connect (comma separated), use * for all
allowed_clients = *

[limits]
max_message_length = 2048
max_join_rate_per_minute = 60   # connections per minute from same IP
connection_timeout_seconds = 300
heartbeat_interval_seconds = 60

[storage]
message_history_enabled = true
history_retention_days = 30
storage_path = /var/lib/chat_server/messages.db

[users]
# Example admin entry (store real hashed passwords in production)
admin_user = admin
admin_pass_hash = 

# End of configuration'''
        file_path = os.path.join(self.directory, self.config_file)
        with open(file_path, "w") as f:
            f.writelines(content)
        print(": OK")



class Database(Configration, Utils):
    def __init__(self):
        self.check_config()
        cfg = ConfigParser()
        cfg_path = os.path.join(self.directory, self.config_file)
        read_files = cfg.read(cfg_path)
        if not read_files or not cfg.has_section('mysql'):
            # warn and use defaults
            print(f"[ ! ] Warning: config not found at {cfg_path}; using defaults")

        self.host = cfg.get('mysql', 'host', fallback='localhost').strip()
        self.user = cfg.get('mysql', 'user', fallback='root').strip()
        self.password = cfg.get('mysql', 'password', fallback='').strip()
        self.database = cfg.get('mysql', 'database', fallback='chat1').strip()
        

    def half_connection(self, max_attempts = 3):
        # Checking and establishing the connection with MySQL.
        attempts = 0
        while attempts <= max_attempts:
            try:
                print("[ * ] Connecting with the database",end=" ")
                self.loading()

                #-----------Connection Credentials---------------
                hcnx= mysql.connector.connect(
                    host = self.host,
                    user = self.user,
                    password = self.password
                )
                #------------------------------------------------

                if hcnx and hcnx.is_connected():
                    print(": OK")
                    print("[ + ] Connected with the Database: OK")
                    return hcnx
            except Error as err:
                attempts += 1
                # if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                if getattr(err, 'errno', None) == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("[ - ] Invalid username/password. Please check the config or re-enter credentials.")
                    if attempts <= max_attempts:
                        print(f"[ * ] Retrying ({attempts}/{max_attempts})...")
                        self.user = input("Username: ").strip()
                        self.password = input("Password: ").strip()
                        continue
                    else:
                        print("[ - ] Attempt limit reached. Please update the config file and try again.")
                        return False
                else:
                    print(f"[ - ] Unexpected error while connecting: {err}")
                    return False
        # if we exit loop
        return False
    
    def db_check(self):
        # Check whether the database exists and connect to the MySQL server

        # --------------Checking the Connection-------------------------------
        hcnx = self.half_connection()
        if not hcnx:
            return False
        # --------------------------------------------------------------------

        cursor = hcnx.cursor()
        try:
            print("[ * ] Checking database existence", end=" ")
            self.loading(flag=1)
            cursor.execute(f"USE `{self.database}`")
            # print(": OK")
            # return True
        
        except Error as err:
            if getattr(err, 'errno', None) == errorcode.ER_BAD_DB_ERROR:
                print(f"\n[ - ] Database {self.database} does not exist. Attempting to create it...")
                if self.create_db(cursor):
                    cursor.close()
                    hcnx.close()
                    print("[ + ] Database {} created successfully.".format(self.database), end="")
                else:
                    print("[ ! ] Database can't be created!!")
                    return False
            else:
                print(f"[ - ] Unknown error occurred: {err}")
                return False
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                hcnx.close()
            except Exception:
                pass
        print(": OK")
        return True
    
    def create_db(self, cursor):
        dbname = str(self.database)
        try:
            cursor.execute(
                f"CREATE DATABASE {dbname} DEFAULT CHARACTER SET 'utf8'")
        except Error as err:
            print(f"Failed creating database: {err}")
            return False
            
        try:
            cursor.execute(f"USE `{dbname}`")
            print(f"[ + ] Switching to the database: {dbname}")
        except:
            print("[ - ] Unable to switch to the database; checking the connection...")
            conn = getattr(cursor, 'connection', None)
            """if conn is None:
                raise RuntimeError("Cursor has no 'connection' attribute; pass the connection instead.")"""
            try:
                if conn.is_connected():
                    return True
                # Optionally try to ping and reconnect automatically
                conn.ping(reconnect=True, attempts=3, delay=1)  # mysql-connector specific
                return conn.is_connected()
            except Error as e:
                # connection not alive
                return False
            
        TABLES = {
            'users': (
                "CREATE TABLE IF NOT EXISTS users ("
                "`ID` INT(11) NOT NULL AUTO_INCREMENT,"
                "`Username` VARCHAR(255) NOT NULL UNIQUE,"
                "`Password` BLOB NOT NULL,"
                "`Time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                " PRIMARY KEY (`ID`)"
                ") ENGINE=InnoDB"
            )
        }  # will add another table to store ip's of the users for security measures we will add in the future
        
        for table_name ,table_description in TABLES.items():
            try:
                print("Creating table {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except Error as err:
                if getattr(err, 'errno', None) == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
                    return False
            else:
                print("OK")

        return True

#---------------------------------------------------------------------------------------------
    def full_connection(self, max_attempts = 3):
        # Initialize the connection with the database
        # Check whether the database exists and connect to the MySQL server
        config  = {
                    'host': self.host,
                    'user': self.user,
                    'password': self.password,
                    'database': self.database
                }
        attempts = 0
        while attempts <= max_attempts:
            try:
                print("[ * ] Connecting with the database",end=" ")
                self.loading()
                #-----------Connection Credentials---------------
                
                fcnx= mysql.connector.connect(**config)
                #------------------------------------------------
                if fcnx and fcnx.is_connected():
                    print("[ + ] Connected with the Database: OK")
                    return fcnx
                
            except Error as err:
                attempts += 1
            #   if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                if getattr(err, 'errno', None) == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("[ - ] Invalid username/password. Please check the config or re-enter credentials.")
                    if attempts <= max_attempts:
                        print(f"[ * ] Retrying ({attempts}/{max_attempts})...")
                        self.user = input("Username: ").strip()
                        self.password = input("Password: ").strip()
                        config['user'] = self.user
                        config['password'] = self.password
                        continue
                    else:
                        print("[ - ] Attempt limit reached. Please update the config file and try again.")
                        return None
                elif getattr(err, 'errno', None) == errorcode.ER_BAD_DB_ERROR:
                    print(f"[ - ] Database {self.database} does not exist.")
                    hcnx = self.half_connection()
                    if not hcnx:
                        return None
                    cursor = hcnx.cursor()
                    if self.create_db(cursor): # It may break
                        try:
                            cursor.close()
                            hcnx.close()
                        except Exception:
                            pass
                        print(f"[ + ] Database {str(self.database)} created successfully: OK")
                        try:
                            fcnx = mysql.connector.connect( **config )
                            if fcnx and fcnx.is_connected():
                                return fcnx
                        except Error:
                            return None
                else:
                    print(f"[ - ] Unexpected error: {err}")
                    return None
#---------------------------------------------------------------------------------------------

class Authentication(Database):
    def __init__(self, client_sock, address):
        super().__init__()
        self.client_sock = client_sock
        self.address = address
        self.username = ""

    def signup(self):
        # function to signup for the users
        self.client_sock.send(b"Enter Username: ")
        username = self.client_sock.recv(1024).decode().strip()
        self.client_sock.send(b"Enter Password: ")
        password = self.lient_sock.recv(1024).decode().strip()

        # Check if the username already exists
        if self.is_username_taken(username):
            print("Username already taken. Please choose another.\n")
            return
        
        # Hash the password before saving it to the database.
        # Store as utf-8 string so it can be saved into TEXT/VARCHAR columns.
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        current_timestamp = datetime.now()

        # If the username is available, insert into the database
        try:
            conn = self.full_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        'INSERT INTO users (username, password, `Time[ YYYY-MM-DD HH:MM:SS ]`) VALUES (%s, %s, %s)',
                        (username, hashed_password, current_timestamp)
                    )
                    conn.commit()

                    # Send confirmation message to the client
                    self.client_sock.send(b"Signup successful!\n")
                    self.client_sock.send(f"Hello {username}.\n".encode('utf-8'))
                    self.username = username # we will be refering the user as its username instead of there ip(address)

                    print(f"New user signed up: {username}")
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Error as e:
            print(f"Database error during signup: {e}")
            print(b"An error occurred while processing your signup. Please try again later.\n")


    def is_username_taken(self, username):
        """Check if the username already exists in the MySQL database."""
        try:
            conn = self.full_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
                    user = cursor.fetchone()
                    return user is not None
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Error as e:
            print(f"Database error while checking username: {e}")
            return False
        
    def signin(self, max_attempts = 3):
        """
        Simple signin flow over a socket.
        Returns True on success, False on failure.
        """
        self.client_sock.send(b"Enter Username: ")
        username = self.client_sock.recv(1024).decode().strip()
        self.client_sock.send(b"Enter Password: ")
        password = self.client_sock.recv(1024).decode().strip()

        attempts = 0
        while attempts <= max_attempts;
            try:
                conn = self.full_connection()
                if not conn:
                    print(b"Database unavailable. Try later.\n")
                    return False

                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
                    row = cursor.fetchone()
                    if not row:
                        self.client_sock.send(b"Invalid username or password.\n")
                        return False

                    stored = row[0]  # may be bytes or str
                    # Normalize to bytes for bcrypt
                    if isinstance(stored, str):
                        stored_bytes = stored.encode('utf-8')
                    else:
                        stored_bytes = stored

                    if bcrypt.checkpw(password.encode('utf-8'), stored_bytes):
                        self.client_sock.send(b"Signin successful!\n")
                        self.username = username
                        self.client_sock.send(f"Welcome back {self.username}.")
                        return True
                    else:
                        attempts=+1
                        self.client_sock.send(b"Invalid username or password.\n")
                        self.client_sock.send(f"[ * ] Retrying ({attempts}/{max_attempts})...".encode('utf-8'))
                        if attempts <= max_attempts:
                            self.client_sock.send(b"Enter Username: ")
                            username = self.client_sock.recv(1024).decode().strip()
                            self.client_sock.send(b"Enter Password: ")
                            password = self.client_sock.recv(1024).decode().strip()
                        else:
                            self.client_sock.send(b"Too mant failded attemps.\n ---EXITING---")
                            print(f"[8]Too many failed attempts. Connection closed with {self.address}")
                            cursor.close()
                            conn.close()
                            return False
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        conn.close()
                    except Exception:
                        pass
            except Error as e:
                print(f"Database error during signin: {e}")
                print(b"An error occurred. Please try again later.\n")
                return False
        

        
        
        

    """full_connection(): Connection with the Database
    half_connection(): Connection without the Database"""