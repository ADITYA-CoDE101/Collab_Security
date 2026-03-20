import socket
import threading
import sys
import time
import select
import ssl
from ClientTLS import ClientTLSConfig   # ← mTLS helper
from protocol import (
    parse_packet,
    pkt_broadcast, pkt_disconnect, pkt_auth,
    EVT_CONNECT, EVT_AUTH_RESP, EVT_BROADCAST, EVT_SYSTEM, EVT_DISCONNECT
)

DESTINATION = "localhost"
PORT = 9898
EXIT     = threading.Event()
AUTH_DONE = threading.Event()   # set once auth succeeds → unblocks send()

# Use a mutable container so the receiver thread can update it without
# needing a 'global' statement, which plays poorly with threading.
_state = {"username": ""}


#//--------------------------------------------------------------------------//
def _do_auth(client):
    """
    Prompt the user for credentials and send a single pkt_auth() JSON packet.
    Called from the receive() thread right after the server's EVT_CONNECT welcome.

    The server's authentication() reads exactly ONE auth packet then waits for
    nothing more, so we must send everything in one shot.

    AUTH_DONE is NOT set here — it is set by receive() when EVT_AUTH_RESP ok
    arrives, which guarantees the send() thread only starts after the server
    has confirmed the session.
    """
    print("\n[ AUTH ] Choose action:")
    print("         [1] Sign Up   [2] Sign In")
    while True:
        choice = input("> ").strip()
        if choice in ("1", "2"):
            break
        print("         Please enter 1 or 2.")

    action = "signup" if choice == "1" else "signin"

    username = input("Username: ").strip()
    password = input("Password: ").strip()

    try:
        client.send(pkt_auth(action=action, username=username, password=password))
    except Exception as e:
        print(f"[ AUTH ] Failed to send auth packet: {e}")


#//--------------------------------------------------------------------------//
def send(client):
    """
    Chat message loop.  Blocks on AUTH_DONE so it never touches stdin while
    _do_auth() (running in the receiver thread) is collecting credentials.
    """
    # Wait until authentication is confirmed before reading any user input.
    AUTH_DONE.wait()

    # To print the ">" prompt after authentication, to indecate the input field.
    sys.stdout.write("> ")      # it writes the prompts to the terminal.
    sys.stdout.flush()          # ??? need to study it

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
            continue

        try:
            mesg = sys.stdin.readline()
            if not mesg:        # EOF on stdin
                continue
            mesg = mesg.rstrip("\n")
            
            # Catch empty or spaces-only input, move UP and refresh the prompt
            if mesg.strip() == "":
                sys.stdout.write("\033[1A\r\033[K> ")
                sys.stdout.flush()
                continue
                
            print(f"Log: {mesg}") # 

            # To print the ">" prompt after authentication, to indecate the input field.
            sys.stdout.write("> ")      # it writes the prompts to the terminal.
            sys.stdout.flush()          # ??? need to study it

        except Exception as e:
            print("[1] Input read error:", e)
            terminator(client, e, req=False)
            return

        if mesg in ("--exit", "-q"):
            print("----EXIT----")
            reason = "Client requested EXIT."
            try:
                client.send(pkt_disconnect(reason))
            except Exception:
                pass
            terminator(client, reason, req=False)
            return

        try:
            client.send(pkt_broadcast(username=_state["username"], data=mesg))
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
                # ── Drive the auth handshake from this thread only ──
                # The send() thread is blocked on AUTH_DONE so there is
                # no stdin race.
                _do_auth(client)

            elif event == EVT_SYSTEM:
                msg = payload.get("message", "")
                print(f"\n[ SYSTEM ] {msg}")

            elif event == EVT_AUTH_RESP:
                status = payload.get("status")
                msg    = payload.get("message", "")
                if status == "ok":
                    _state["username"] = payload.get("username", "")
                    print(f"\n[ AUTH  ✓ ] {msg} (logged in as: {_state['username']})")
                    AUTH_DONE.set()     # ← unblock send() — chat is now open
                else:
                    print(f"\n[ AUTH ERROR ] {msg}")
                    # Auth failed → close down cleanly
                    terminator(client, "auth failed", req=False)
                    return

            elif event == EVT_BROADCAST:
                sender = payload.get("username", "Unknown")
                data   = payload.get("data", "")
                if(data == ""):
                    continue
                flag   = payload.get("flag", "broadcast")

#              #———————————————————————————————————————————————————————————
                # To fix [ bug ]
                """
                    ┌──(BROADCAST_ALL@u1)
                    └─> s
                    >    [ bug ]
                    ┌──(BROADCAST_ALL@u1)
                    └─> ds
                    > 
                """
                # as we see every time the we get the responce we get the new line.
                # But if i left the ">" input field empty and another responce came in the ">" input field remains there.
                # to fix this we used "\r\033[K" to clear the line.

                sys.stdout.write("\r\033[K")
                sys.stdout.flush()
               #———————————————————————————————————————————————————————————
               # removed the \n at the start of the print(f"┌──...) statement because erasing the old line means we don't need to jump to a new line anymore!
                print(f"┌──({flag.upper()}@{sender})\n└─> {data}")
                
                
                # To print the ">" prompt after authentication, to indecate the input field.
                sys.stdout.write("> ")      # it writes the prompts to the terminal.
                sys.stdout.flush()          # ??? need to study it
                # As we receive the responce from the Client(throug server ) the "\n" newline automaticlay prompt us to the next line.
                # Due to this reason we left with the blank input field without ">" prompt.
                # to fix this we add these two lines here as well so as we get to the next line we get the ">" prompt.
                """
                ┌──(dell㉿kali)-[~]
                └─$ 
                """

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
            terminator(client, str(e), req=True)
            return


def terminator(client, reason=None, req=False):
    if client.fileno() == -1:
        print("Socket already closed")
        return
    if req:
        try:
            client.send(pkt_disconnect(str(reason)))
        except Exception as e:
            print(f"[ ERROR ]: while terminating[1]: {e}")

    time.sleep(0.5)

    EXIT.set()
    AUTH_DONE.set()   # unblock send() if it is still waiting, so the thread exits

    try:
        client.shutdown(socket.SHUT_RDWR)
    except Exception as e:
        print(f"Error shutting down socket: {e}")

    try:
        client.close()
    except Exception as e:
        print(f"Error closing socket: {e}")

    print("Exiting.....")
    return


def main():
    raw_client = None
    client = None

    # --- mTLS context ---
    tls = ClientTLSConfig(
        cafile          = "",      # CA that signed the server cert
        client_certfile = "",      # OUR certificate (identity)
        client_keyfile  = "",      # OUR private key
        server_hostname = DESTINATION,
    )
    context = tls.create_context()

    try:
        #---------Raw socket ----------#
        raw_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_client.connect((DESTINATION, PORT))

        #---------TLS handshake ---------#
        client = context.wrap_socket(raw_client, server_hostname=DESTINATION)
        print(f"Connected to server at {DESTINATION}:{PORT} with TLS.")
        print("[+] TLS connection established")
        print("TLS Version:", client.version())
        print("Cipher:", client.cipher())

        #--------Start communication threads ---------#
        sender_thread   = threading.Thread(target=send,    args=(client,), daemon=True)
        receiver_thread = threading.Thread(target=receive, args=(client,), daemon=True)

        sender_thread.start()
        receiver_thread.start()

        EXIT.wait()
        sender_thread.join()
        receiver_thread.join()

    except KeyboardInterrupt:
        print("Interrupted. Closing client.")
        EXIT.set()
        AUTH_DONE.set()
        if client is not None:
            try:
                terminator(client, req=True)
            except Exception as e:
                print(f"Error while terminating client: {e}")
        sys.exit()


if __name__ == "__main__":
    main()