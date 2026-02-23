import socket
import threading

def handle_client(conn, addr):
    print(f"[+] Client {addr} connected")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            print(f"[{addr}] {message}")
            
            # Echo response back
            response = f"Server received: {message}"
            conn.send(response.encode('utf-8'))
    except Exception as e:
        print(f"[-] Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Client {addr} disconnected")

def main():
    """
    Start a TCP server that listens for incoming client connections on port 5000.
    The server accepts multiple concurrent connections by spawning a new daemon thread
    for each client. Each thread runs the handle_client function to process that client's
    requests independently.
    The server binds to all available network interfaces (0.0.0.0) and can queue up to 5
    pending connections. The socket is set to reuse the address to allow quick restarts
    without TIME_WAIT delays.
    Gracefully shuts down when interrupted (Ctrl+C) and ensures the server socket is
    properly closed in all cases.
    Raises:
        KeyboardInterrupt: Caught internally to trigger graceful shutdown.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5000))
    server.listen(5)
    print("[*] Server listening on port 5000...")
    
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server")
    finally:
        server.close()

if __name__ == "__main__":
    main()
