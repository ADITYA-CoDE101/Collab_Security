import mysql.connector
from mysql.connector import Error
print("MySQL Connector module is imported.")
def get_mysql_connection():
    print("Attempting to connect to MySQL database...")
    try:
        conn = mysql.connector.connect(
            host="localhost",       # Hostname of your MySQL server
            user="root",   # Your MySQL username
            password="1234",  # Your MySQL password
            database="chat1"     # Your database name
        )
        print("Connection to MySQL database was successful.")
        if conn.is_connected():
            print("MySQL connection is active.")
            return conn
    except Error as e:
        print("Failed to connect to MySQL database.")
        print(f"Error: {e}")
        return None