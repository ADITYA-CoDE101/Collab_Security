import bcrypt
from mysql.connector import Error
import bcrypt
import mysql.connector
from datetime import datetime
from configparser import ConfigParser



print("MySQL Connector module is imported.")
def get_mysql_connection():
    print("Attempting to connect to MySQL database...")
    try:
        cfg = ConfigParser()
        cfg .read('/home/dell/Documents/Coding/git_test/backup_files/TCP-communication-/test/test_config/chat.confg')
        conn = mysql.connector.connect(
            host = cfg.get('msql', 'host', fallback='localhost'),
            user = cfg.get('mysql', 'user', fallback='root'),
            password = cfg.get('mysql', 'password', fallback=''),
            database=cfg.get('mysql', 'database', fallback='chat1')
        )
        ''' host="localhost",       # Hostname of your MySQL server
            user="dell",   # Your MySQL username
            password="1234",  # Your MySQL password
            database="chat1"     # Your database name'''
        print("Connection to MySQL database was successful.")
        if conn.is_connected():
            print("MySQL connection is active.")
            return conn
    except Error as e:
        print("Failed to connect to MySQL database.")
        print(f"Error: {e}")
        return None
    
def signup():
    print("Enter Username: ")
    username = input("userame")
    print(b"Enter Password: ")
    password = input("password")

    # Check if the username already exists
    if is_username_taken(username):
        print("Username already taken. Please choose another.\n")
        return
    
    # Hash the password before saving it to the database.
    # Store as utf-8 string so it can be saved into TEXT/VARCHAR columns.
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    current_timestamp = datetime.now()

    # If the username is available, insert into the database
    try:
        conn = get_mysql_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO users (username, password, `Time_Stamp`) VALUES (%s, %s, %s)',
                    (username, hashed_password, current_timestamp)
                )
                conn.commit()

                # Send confirmation message to the client
                print("Signup successful!\n")
                print(f"Hello {username}, you are now registered.\n".encode('utf-8'))

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


def is_username_taken(username):
    """Check if the username already exists in the MySQL database."""
    try:
        conn = get_mysql_connection()
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
    
def signin():
    """
    Simple signin flow over a socket.
    Returns True on success, False on failure.
    """
    print(b"Enter Username: ")
    username = input()

    print(b"Enter Password: ")
    password = input()

    try:
        conn = get_mysql_connection()
        if not conn:
            print(b"Database unavailable. Try later.\n")
            return False

        cursor = conn.cursor()
        try:
            cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
            row = cursor.fetchone()
            if not row:
                print(b"Invalid username or password.\n")
                return False

            stored = row[0]  # may be bytes or str
            # Normalize to bytes for bcrypt
            if isinstance(stored, str):
                stored_bytes = stored.encode('utf-8')
            else:
                stored_bytes = stored

            if bcrypt.checkpw(password.encode('utf-8'), stored_bytes):
                print(b"Signin successful!\n")
                return True
            else:
                print(b"Invalid username or password.\n")
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
    

signup()
signin()

