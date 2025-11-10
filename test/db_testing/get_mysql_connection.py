import mysql.connector
from mysql.connector import Error

def get_mysql_connection():
    """Return a MySQL connection or None on failure."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="chat1"
        )
        if conn and conn.is_connected():
            return conn
    except Error as e:
        print(f"Failed to connect to MySQL database: {e}")
        conn.close()
    return None
