import socket
import threading
import time
import os
import importlib.util

# Load t2.py directly by path to avoid package import issues when running the script
here = os.path.dirname(__file__)
t2_path = os.path.join(here, 't2.py')
spec = importlib.util.spec_from_file_location('t2_module', t2_path)
t2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t2)
signup = t2.signup
is_username_taken = t2.is_username_taken

from test.db_testing.get_mysql_connection import get_mysql_connection


def client_sim(sock, username, password):
    """Simulates a client: read prompts and send responses."""
    # receive "Enter Username: "
    data = sock.recv(1024)
    # send username
    sock.sendall(username.encode() + b"\n")
    data = sock.recv(1024)  # Enter Password:
    sock.sendall(password.encode() + b"\n")
    # read confirmation (if any)
    try:
        sock.settimeout(2.0)
        resp = sock.recv(1024)
        if resp:
            print('Client got:', resp.decode(errors='ignore'))
    except socket.timeout:
        pass


def run_harness():
    # create a connected pair of sockets
    s1, s2 = socket.socketpair()

    username = f"test_user_{int(time.time())}"
    password = "P@ssw0rd"

    # server side: call signup in a thread (it expects a socket-like object)
    server_thread = threading.Thread(target=signup, args=(s1,))
    server_thread.start()

    # client simulation
    client_sim(s2, username, password)

    server_thread.join(timeout=5)

    # Verify the user exists, then cleanup
    conn = get_mysql_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute('SELECT username FROM users WHERE username = %s', (username,))
            found = cur.fetchone()
            print('DB found user:', bool(found))
            cur.execute('DELETE FROM users WHERE username = %s', (username,))
            conn.commit()
        finally:
            cur.close()
            conn.close()


if __name__ == '__main__':
    run_harness()
