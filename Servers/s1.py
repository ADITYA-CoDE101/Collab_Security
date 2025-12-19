import sys
import time
import signal
import socket
import threading
from initialize import Utils, Authentication, Database


IP = "0.0.0.0"
PORT = 9898
UACL = [] #  Unauthenticated Client List
ACL = [] #   Authenticated Client List
CLIENTS = [] # All Clients List
CLIENTS_LOCK = threading.Lock()

utls = Utils()


def broadcast(message, sender_sock):
    with CLIENTS_LOCK:
        for A_client in ACL:  # Aclient --> Authenticated client
            if A_client != sender_sock:
                try:
                    A_client.send(message)
                except Exception as e:                      # except (BrokenPipeError, ConnectionResetError) as e:
                    print(f"[1]Connection Closed due to an Exeption: {e}")
                    terminator(A_client, client_sock_addrs=None)                                      # Termination
                    # return
                    continue
                



def handle_client(client_sock, client_address):
    if not authentication(client_sock, client_address):
        print(f"Authentication failed for {client_address}, closing thread.")
        return  # stop thread cleanly                    # We have remove the context manger (with) since we do not want redundent termination
    while True:                                         # and context manger closes automaticlly at the end of the block
        try:
            data = client_sock.recv(1024)
            if not data:
                break

            terminate_msg = data.decode(errors="ignore") #If a client sends binary (or malformed UTF-8), server will crash.
            if terminate_msg.startswith("RQST-> DISCONNECT"):
                print(f"{terminate_msg}")
                terminator(client_sock, client_address, cmd=False)
                break
            
            print(f"Received from {client_address}: {data.decode()}")
            broadcast(data, client_sock)
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
            break

                                         # Termination
    
    if (client_sock in CLIENTS) and (client_sock in ACL):
        try:
            terminator(client_sock, client_address)      
        except Exception as e:
            print(f"thread is still alive! , even the client is closed.")  
    return

    # ------------------------------

def terminator(client_sock, client_sock_addrs, cmd=True):
    if client_sock.fileno() == -1:
        # socket already closed
        print(f"Socket already closed for {client_sock_addrs}")
        return
    
    if cmd:
        try:
            client_sock.send(b"DISCONNECTED")  # if socket is closed, this can raise an error
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"[3]Error sending DISCONNECTED message to {client_sock}: {e}")
            
    with CLIENTS_LOCK:        
        if client_sock in ACL:                  # Since client will not be in the ACL and CLIENTS list befor Authentication
            ACL.remove(client_sock)                 # So we need condition, if client exist in these list then remove otherwise just close the client as is.
        if client_sock in CLIENTS:
            CLIENTS.remove(client_sock)

    if cmd:
        try:
            time.sleep(0.1)
            client_sock.shutdown(socket.SHUT_RDWR)  # Gracefully shutdown the socket
        except Exception as e:
            print(f"[4]Error shutting down socket {client_sock_addrs}: {e}")

        if client_sock.fileno() != -1:
            try:
                client_sock.close()  # Ensure the socket is properly closed
            except Exception as e:
                print(f"[5]Error closing socket {client_sock_addrs}: {e}")
    print(f"[6]Connection closed: {client_sock_addrs}")


def authentication(client_sock, client_address):
    auth = Authentication(client_sock, client_address)
    client_sock.send(b"\t\tWelcome! To the Chat`!`\nDo SignUp/SingIn")
    client_sock.send(b"Type [ 1 ] for signUp or [ 2 ] for SignIn")
    opt = client_sock.recv(1024).decode()
    if opt == "1":
        auth.signup()
        if not auth.signin():             # Exit              [ if statment works if the  given condition is TRUE or NOT FALSE ]
            terminator(client_sock, client_address)              # Termination
            return False
            
        else:
            with CLIENTS_LOCK:
                ACL.append(client_sock)             # Authenticated
                CLIENTS.append(client_sock)
                UACL.remove(client_sock)
                return True
        
    elif opt == "2":
        if not auth.signin():             # if signin -> Trur then the if body will not execut .  # Exit
            print("invalid credential")
            terminator(client_sock, client_address)              # Termination
            return False
            
        else:
            with CLIENTS_LOCK:
                ACL.append(client_sock)             # Authenticated
                CLIENTS.append(client_sock)
                UACL.remove(client_sock)
                return True
    else:
        client_sock.send(b"[7]Invalid option. Connection closed.\n")
        terminator(client_sock, client_address)                  # Termination
        return False
    

        
def initialize():
    db = Database()
    if not db.db_check():
        print("[ ! ] The credentials for the database are invalide!")
        sys.exit(0)

def main():
    initialize()
    global server
    client = None
    address = None
    #-----------------------------------
    def signal_handler(sig, frame):
        print('\n[ * ] Shutting down gracefully...')
        server.close()
        sys.exit(0)
    #-------------------------------------
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C handler
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    server.listen()
    print("[ * ] Server listening...")
    utls.loading()
    utls.simple_spinner()
    
    while True:
        try:
            client, address = server.accept()
            with CLIENTS_LOCK:
                UACL.append(client)    # add to unauthenticated clients list
            print(f"[+] Accepted connection from {address}")
            threading.Thread(target=handle_client, args=(client, address)).start()
            
        except Exception as e:
            print(e)
            try:
                terminator(client, address)
            except Exception:
                pass
            break
            
    server.close()
    
if __name__ == '__main__':
    main()


#######<------SFH------->####### --> start form here agian 
# ??? --> need to test and recheck

# >[number]   --> we do next or later.

""" /-------------------------------------------------------------------------------------------------/ """
# 1. will use the sql instead of the file handling to access and minupulate the credential data
""" /-------------------------------------------------------------------------------------------------/ """
# use 
#       sudo lsof -i  :<PORT NUMBER>
# to resolve the issue : OSError: [Errno 98] Address already in use
