from __future__ import print_function
import mysql.connector
from mysql.connector import Error, errorcode
from configparser import ConfigParser
import time


class Database:
    def __init__(self):
        cfg = ConfigParser()
        cfg_path = '/home/dell/Documents/Coding/git_test/backup_files/TCP-communication-/Servers/Config/server.confg'
        read_files = cfg.read(cfg_path)
        if not read_files or not cfg.has_section('mysql'):
            # warn and use defaults
            print(f"[ ! ] Warning: config not found at {cfg_path}; using defaults")

        self.host = cfg.get('mysql', 'host', fallback='localhost').strip()
        self.user = cfg.get('mysql', 'user', fallback='root').strip()
        self.password = cfg.get('mysql', 'password', fallback='').strip()
        self.database = cfg.get('mysql', 'database', fallback='chat1').strip()
        

    def check_config(self):
        # Check if the configuration file exists.
        # We will verify the config file before providing values to the Database class.
        # (In future this function may be moved to a dedicated config.py so it can be reused.)
        pass

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
        }  
        
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


    def signup(self):
        # function to signup for the users
        pass
    def signin(self):
        # function to signin for the users
        pass
    def is_username_taken(self):
        # Check if the user name  already exist or not.
        pass
    
    def loading(self, flag = 0):
        for i in range(4):
            print(".",end=" ")
            time.sleep(0.5)
        if flag == 0:
            print(" ")

"""full_connection(): Connection with the Database
   half_connection(): Connection without the Database"""