import socket
import threading
import sys
import time
import select  # need to study more about this
from protocol import (
    parse_packet,
    pkt_broadcast, pkt_disconnect, pkt_auth,
    EVT_CONNECT, EVT_AUTH_RESP, EVT_BROADCAST, EVT_SYSTEM, EVT_DISCONNECT
)

DESTINATION = "127.0.0.1"
PORT = 9898
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
                client.send(pkt_disconnect(reason))
            except Exception:
                # sending may fail if socket already broken; ignore
                pass
            terminator(client, reason, req=False)
            return

        try:
            client.send(pkt_broadcast(username="", data=mesg))
        except Exception as e:
            print("[1] Connection Lost ...", f"\n\t└─>[ ERROR ]: {e}")
            terminator(client, e, req=False)
            return
#//--------------------------------------------------------------------------// 

def receive(client):
    while not EXIT.is_set():
        try:
            response_bytes = client.recv(4096)
            if not response_bytes:
                print("[2] Connection Lost...")
                print("Connection closed by the server.")
                terminator(client, "no response", req=False)
                return

            packet = parse_packet(response_bytes)
            if packet is None:
                # Fallback to printing unparseable data
                raw = response_bytes.decode(errors="replace").strip()
                if raw == "DISCONNECTED":
                    print("disconnected from server side.")
                    terminator(client, "server requested disconnect", req=False)
                    return
                if raw:
                    print(f"\n[RAW] {raw}")
                continue

            event   = packet.get("event")
            payload = packet.get("payload", {})

            if event == EVT_CONNECT:
                print(f"\n[ SERVER ] {payload.get('message', '')}")
                if payload.get('hint'):
                    print(f"[ SERVER ] {payload.get('hint')}")

            elif event == EVT_SYSTEM:
                # This includes prompts for username/password from initialize.py
                msg = payload.get("message", "")
                print(f"\n[ SYSTEM ] {msg}")
                # Intercept auth prompts to drive local input
                if "Enter Username:" in msg or "Enter Password:" in msg:
                    val = input("> ").strip()
                    client.send(val.encode("utf-8")) # Send raw back temporarily during handshake (handled by initialize.py raw reads)
                elif "Type [ 1 ] for signUp or [ 2 ] for SignIn" in msg:
                    val = input("> ").strip()
                    client.send(val.encode("utf-8"))

            elif event == EVT_AUTH_RESP:
                status = payload.get("status")
                msg    = payload.get("message", "")
                if status == "ok":
                    print(f"\n[ AUTH ] {msg} (Username: {payload.get('username')})")
                else:
                    print(f"\n[ AUTH ERROR ] {msg}")

            elif event == EVT_BROADCAST:
                sender = payload.get("username", "Unknown")
                data   = payload.get("data", "")
                flag   = payload.get("flag", "broadcast")
                print(f"\n[{flag.upper()}] {sender} <─┘ {data}")

            elif event == EVT_DISCONNECT:
                reason = payload.get("reason", "")
                print(f"\n[ DISCONNECT ] Server requested disconnect: {reason}")
                terminator(client, "server requested disconnect", req=False)
                return

            else:
                print(f"\n[ ? ] Unhandled event '{event}': {payload}")

        except Exception as e:
            print("[3] Connection Lost ...",
                  f"\n\t└─>[ ERROR ]: {e}")
            terminator(client, str(e), req=True)                             # Termination
            return

def terminator(client, reason=None, req = False):
    if client.fileno() == -1:
        # socket already closed
        print(f"Socket already closed")
        return
    if req:
        try:
            # We now send a clean JSON disconnect packet
            client.send(pkt_disconnect(str(reason)))
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