import socket
import sys

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", 5000))
        print("[+] Connected to server")
        
        while True:
            message = input("You: ")
            if message.lower() == "quit":
                break
                
            client.send(message.encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            print(f"Server: {response}\n")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        client.close()
        print("[-] Disconnected")

if __name__ == "__main__":
    main()
