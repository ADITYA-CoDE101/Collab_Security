from __future__ import print_function
import mysql.connector
from mysql.connector import Error, errorcode
from configparser import ConfigParser
from datetime import datetime
from dotenv import load_dotenv
import os
import sys
import time
import bcrypt
import threading

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
    #-------From Net------
    def simple_spinner(self):
        spinner_chars = ['-', '\\', '|', '/']
        for _ in range(20): # Simulate a task that takes 20 steps
            for char in spinner_chars:
                sys.stdout.write(f'\rLoading {char}')
                sys.stdout.flush()
                time.sleep(0.1)
        sys.stdout.write('\rDone!      \n') # Clear the line and add a newline
    #---------------------

    


class Configration(Utils):
    def __init__(self):
        self.directory = os.path.abspath("Config") # absolute path of the folder where we will be storing the config file.
        os.makedirs(self.directory, exist_ok=True) # checek if the folder exist then returns nothing, if do not then it automaticaly create one.
        self.config_file = "server.confg"


    def check_config(self):
        print("[ * ] Verifying the configuration file", end="")
        self.loading(1)
        file_path = os.path.join(self.directory, self.config_file)
        if os.path.isfile(file_path):
            print(": OK")
            print(f"[ + ] The configuration file '{file_path}' found.")
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
            f.write(content)
        print(": OK")



class Database(Configration, Utils):
    
    _initialized = False
    _init_lock = threading.Lock()
    
    def __init__(self):
        super().__init__()
        load_dotenv()  # Load environment variables from .env file
        
        if not Database._initialized:
            self.check_config()
            
            with Database._init_lock:
                Database._initialized = True
        # self.check_config()
        host, user, password, database_name = self.fetch_db_credentials()
        self.host = self.resolve_env(host)
        self.user = self.resolve_env(user)
        self.password = self.resolve_env(password)
        self.database = self.resolve_env(database_name)
        
    def fetch_db_credentials(self):
        # Fetching the database credentials from the config file.
        cfg = ConfigParser()
        cfg_path = os.path.join(self.directory, self.config_file)
        read_files = cfg.read(cfg_path)
        if not read_files or not cfg.has_section('mysql'):
            print(f"[ ! ] Warning: config not found at {cfg_path}; using defaults")
            return 'localhost', 'root', '', 'chat1'

        host = cfg.get('mysql', 'host', fallback='localhost').strip()
        user = cfg.get('mysql', 'user', fallback='root').strip()
        password = cfg.get('mysql', 'password', fallback='').strip()
        database_name = cfg.get('mysql', 'database', fallback='chat1').strip()
        return host, user, password, database_name
    
    def resolve_env(self, value):
        # Resolve environment variables in the config values
        return os.getenv(value, value)  # If the env var is not set, return the original value
    
    def half_connection(self, max_attempts = 3):
        # Checking and establishing the connection with MySQL.
        attempts = 0
        while attempts < max_attempts:
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
                    if attempts < max_attempts:
                        print(f"[ * ] Retrying ({attempts}/{max_attempts})...")
                        self.user = input("Username: ").strip()
                        self.password = input("Password: ").strip()
                        
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
            print(": OK")
            return True
        
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
            # may do a conedtion check
            return False
            
        try:
            cursor.execute(f"USE `{dbname}`")
            print(f"[ + ] Switching to the database: {dbname}")
        except:
            print("[ - ] Unable to switch to the database; checking the connection...")
            hcnx = getattr(cursor, 'connection', None)
            """if hcnx is None:
                raise RuntimeError("Cursor has no 'connection' attribute; pass the connection instead.")"""
            try:
                if hcnx and hcnx.is_connected():
                    return True
                # Optionally try to ping and reconnect automatically
                if hcnx:
                    hcnx.ping(reconnect=True, attempts=3, delay=1)  # mysql-connector specific
                    return hcnx.is_connected()
                return False
            except Error as e:
                # connection not alive
                return False
            
        TABLES = {
            'users': (
                "CREATE TABLE IF NOT EXISTS users ("
                "`ID` INT(11) NOT NULL AUTO_INCREMENT,"
                "`Username` VARCHAR(255) NOT NULL UNIQUE,"
                "`Password` BLOB NOT NULL,"
                "`Time_Stamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
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
        while attempts < max_attempts:
            try:
                print("[ + ] Connecting with the database",end="")
                self.loading()
                #-----------Connection Credentials---------------
                
                fcnx= mysql.connector.connect(**config)
                #------------------------------------------------
                if fcnx and fcnx.is_connected():
                    print("[ + ] Connected with the Database: OK")
                    return fcnx
                
            except Error as err:
                
            #   if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                if getattr(err, 'errno', None) == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("[ - ] Invalid username/password. Please check the config or re-enter credentials.")
                    attempts += 1
                    if attempts <= max_attempts:
                        print(f"[ * ] Retrying ({attempts}/{max_attempts})...")
                        self.user = input("Username: ").strip()
                        self.password = input("Password: ").strip()
                        config['user'] = self.user
                        config['password'] = self.password
                        continue
                    else:
                        print("[ - ] Attempt limit reached. Please update the config file and try again.")
                        return False
                elif getattr(err, 'errno', None) == errorcode.ER_BAD_DB_ERROR:
                    print(f"[ - ] Database {self.database} does not exist.")
                    hcnx = self.half_connection()
                    if not hcnx:
                        return False
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
                            return False
                else:
                    print(f"[ - ] Unexpected error: {err}")
                    return False
#---------------------------------------------------------------------------------------------

class Authentication(Database):
    def __init__(self, tls_client_sock, address):
        super().__init__()
        self.tls_client_sock = tls_client_sock
        self.address = address
        self.username = ""

    def signup(self):
        # function to signup for the users
        self.tls_client_sock.send(b"Enter Username: ")
        username = self.tls_client_sock.recv(1024).decode().strip()
        self.tls_client_sock.send(b"Enter Password: ")
        password = self.tls_client_sock.recv(1024).decode().strip()

        # Check if the username already exists
        if self.is_username_taken(username):
            self.tls_client_sock.send(b"Username already taken. Please choose another.\n")
            return
        
        # Hash the password before saving it to the database.
        # Store as utf-8 string so it can be saved into TEXT/VARCHAR columns.
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # If the username is available, insert into the database
        try:
            fcnx = self.full_connection()
            if fcnx:
                cursor = fcnx.cursor()
                try:
                    cursor.execute(
                        'INSERT INTO users (Username, Password, `Time_Stamp`) VALUES (%s, %s, %s)',
                        (username, hashed_password, current_timestamp)
                    )
                    fcnx.commit()

                    # Send confirmation message to the client
                    self.tls_client_sock.send(b"Signup successful!\n")
                    self.tls_client_sock.send(f"Hello {username}.\n".encode('utf-8'))
                    self.username = username # we will be refering the user as its username instead of there ip(address)

                    print(f"New user signed up: {username}")
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        fcnx.close()
                    except Exception:
                        pass
        except Error as e:
            print(f"Database error during signup: {e}")
            self.tls_client_sock.send(b"An error occurred while processing your signup. Please try again later.\n")



    def is_username_taken(self, username):
        """Check if the username already exists in the MySQL database."""
        try:
            fcnx = self.full_connection()
            if fcnx:
                cursor = fcnx.cursor()
                try:
                    cursor.execute('SELECT 1 FROM users WHERE Username = %s', (username,))
                    user = cursor.fetchone()
                    return user is not None
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        fcnx.close()
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
        self.tls_client_sock.send(b"Enter Username: ")
        username = self.tls_client_sock.recv(1024).decode().strip()
        self.tls_client_sock.send(b"Enter Password: ")
        password = self.tls_client_sock.recv(1024).decode().strip()

        attempts = 0
        while attempts < max_attempts:
            try:
                fcnx = self.full_connection()
                if not fcnx:
                    print(b"Database unavailable. Try later.\n")
                    return False

                cursor = fcnx.cursor()
                try:
                    cursor.execute('SELECT Password FROM users WHERE Username = %s', (username,))
                    row = cursor.fetchone()
                    if not row:
                        self.tls_client_sock.send(b"Invalid username or password.")
                        self.tls_client_sock.send(b"Username does not exist.")
                        return False

                    stored = row[0] if isinstance(row, tuple) else row.get('Password')  # may be bytes or str
                    # Normalize to bytes for bcrypt
                    if isinstance(stored, str):
                        stored_bytes = stored.encode('utf-8')
                    elif isinstance(stored, bytes):
                        stored_bytes = stored
                    else:
                        stored_bytes = str(stored).encode('utf-8')

                    if bcrypt.checkpw(password.encode('utf-8'), stored_bytes):
                        self.tls_client_sock.send(b"Signin successful!")
                        self.username = username
                        self.tls_client_sock.send(f"\nWelcome back {self.username}.".encode('utf-8'))
                        return True
                    else:
                        attempts += 1
                        self.tls_client_sock.send(b"Invalid username or password.")
                        self.tls_client_sock.send(f"[ * ] Retrying ({attempts}/{max_attempts})...".encode('utf-8'))
                        if attempts < max_attempts:
                            self.tls_client_sock.send(b"Enter Username: ")
                            username = self.tls_client_sock.recv(1024).decode().strip()
                            self.tls_client_sock.send(b"Enter Password: ")
                            password = self.tls_client_sock.recv(1024).decode().strip()
                        else:
                            self.tls_client_sock.send(b"Too many failed attempts.\n---EXITING---")
                            print(f"[8]Too many failed attempts. Connection closed with {self.address}")
                            cursor.close()
                            fcnx.close()
                            return False
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    try:
                        fcnx.close()
                    except Exception:
                        pass
            except Error as e:
                print(f"Database error during signin: {e}")
                print(b"An error occurred. Please try again later.\n")
                return False
        
# class Initialize(Configration, Database):
#     def __init__(self):
#         self.check_config()
#         self.db_check()

# c = Configration()
# c.check_config()
        
# d = Database()
# d.db_check()
    

"""full_connection(): Connection with the Database
    half_connection(): Connection without the Database"""