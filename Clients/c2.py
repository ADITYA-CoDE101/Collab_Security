import socket
import threading
import sys
import time
import select  # need to study more about this

DESTINATION = "127.0.0.1"
PORT = 9898
DISCONNECT_REQUEST = "RQST-> DISCONNECT"
EXIT = threading.Event()

#//--------------------------------------------------------------------------//
def send(client):
    # poll stdin with a short timeout so we can observe EXIT
    while not EXIT.is_set():
        # if socket closed, stop
        try:
            if client.fileno() == -1:
                print("Socket already closed")
                return
        except Exception:
            terminator(client, "fileno error", req=False)
            return

        # wait up to 0.5s for user input
        ready, _, _ = select.select([sys.stdin], [], [], 0.5)
        if not ready:
            # no input this cycle, check EXIT again
            continue

        # read line (non-blocking because select told us it's ready)
        try:
            mesg = sys.stdin.readline()
            if not mesg:
                # EOF on stdin
                continue
            mesg = mesg.rstrip("\n")
        except Exception as e:
            print("[1] Input read error:", e)
            terminator(client, e, req=False)
            return

        if mesg in ("--exit", "-q"):
            print("----EXIT----")
            reason = "Client requested EXIT."
            # send the request explicitly then clean up (terminator does cleanup)
            try:
                client.send(f"{DISCONNECT_REQUEST}: {reason}".encode())
            except Exception:
                # sending may fail if socket already broken; ignore
                pass
            terminator(client, reason, req=False)
            return

        try:
            client.send(mesg.encode())
        except Exception as e:
            print("[1] Connection Lost ...", f"\n\t└─>[ ERROR ]: {e}")
            terminator(client, e, req=False)
            return
#//--------------------------------------------------------------------------// 

def receive(client):
    while not EXIT.is_set():
        try:
            response_bytes = client.recv(4092)
            if not response_bytes:
                print("[2] Connection Lost...")
                print("Connection closed by the server.")
                terminator(client, "no response", req=False)
                return

            response = response_bytes.decode(errors="replace")
            msg = response.strip()

            # handle server-initiated disconnects or requests
            if msg == "DISCONNECTED":
                print("disconnected from server side.")
                terminator(client, "server requested disconnect", req=False)
                return

            print(f"\n\t\t\t\t\t\t{response} <─┘")
        except Exception as e:
            print("[3] Connection Lost ...",
                  f"\n\t└─>[ ERROR ]: {e}")
            terminator(client, e, req=True)                             # Termination
            return

def terminator(client, reason=None, req = False):
    if client.fileno() == -1:
        # socket already closed
        print(f"Socket already closed")
        return
    if req:
        try:
            client.send(f"{DISCONNECT_REQUEST}: {reason}".encode())    # >[2]
        except Exception as e:
            print(f"[ ERROR ]: while terminating[1]: {e}")

    time.sleep(0.5)

    EXIT.set()
    
    try:        
        client.shutdown(socket.SHUT_RDWR)  # Gracefully shutdown the socket
    except Exception as e:
        print(f"Error shutting down socket: {e}")
    
    try:
        client.close()  # Ensure the socket is properly closed
    except Exception as e:
        print(f"Error closing socket: {e}")

    print("Exiting.....")
    return
   
    
    
def main():
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((DESTINATION, PORT))

        sender_thread = threading.Thread(target=send, args=(client,))
        receiver_thread = threading.Thread(target=receive, args=(client,))

        sender_thread.start()
        receiver_thread.start()

    
        EXIT.wait()
        sender_thread.join()
        receiver_thread.join()
        # if not sender_thread.is_alive() and not receiver_thread.is_alive(): # Here it stats that both threads needs to be alive for both of them to run.
            
    except KeyboardInterrupt:
        print("Interrupted. Closing client.")
        terminator(client,req=True)
        sys.exit()
        
        
    


if __name__ == "__main__":
    main()


# we will use RQST> keyword for the request for the server

# [ ERROR ]: