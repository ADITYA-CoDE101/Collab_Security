import os
import sys
import time
import signal
import socket
import threading
from initialize import Utils, Authentication, Database
from dotenv import load_dotenv
import json
import OpenSSL
import ssl
from ServTSL import TLSConfig
from protocol import (
    EVT_CONNECT, EVT_AUTH, EVT_AUTH_RESP, EVT_BROADCAST, EVT_DISCONNECT, EVT_SYSTEM,
    FLAG_BROADCAST_ALL, FLAG_DM, FLAG_BROADCAST_AI,
    parse_packet, build_packet,
    pkt_connect, pkt_system, pkt_broadcast, pkt_disconnect,
)


load_dotenv()  # Load environment variables from .env file

IP   = os.getenv("HOST", "localhost")   # Default to localhost if not set
PORT = int(os.getenv("PORT", 5000))     # Default to 5000 if not set
UACL = []                               # Unauthenticated Client List
ACL  = []                               # Authenticated Client List  { sock: username }
CLIENTS = []                            # All Clients List
CLIENTS_LOCK = threading.Lock()

# map: tls_sock → username  (set after successful auth)
CLIENT_USERNAMES: dict = {}

utls = Utils()


# ─────────────────────────────────────────────────────────────────────────────
def broadcast(packet_bytes: bytes, sender_sock):
    """Send a pre-built JSON packet to every authenticated client except the sender."""
    with CLIENTS_LOCK:
        for A_client in ACL:           # A_client → Authenticated client
            if A_client != sender_sock:
                try:
                    A_client.send(packet_bytes)
                except Exception as e:
                    print(f"[BROADCAST] Error sending to client: {e}")
                    terminator(A_client, client_sock_addrs=None)
                    continue


# ─────────────────────────────────────────────────────────────────────────────
def handle_client(tls_client_sock, client_address):
    if not authentication(tls_client_sock, client_address):
        print(f"Authentication failed for {client_address}, closing thread.")
        return  # stop thread cleanly

    username = CLIENT_USERNAMES.get(tls_client_sock, str(client_address))

    while True:
        try:
            data = tls_client_sock.recv(4096)
            if not data:
                break

            # ── Try to parse as JSON packet ──
            packet = parse_packet(data)

            if packet is None:
                # Non-JSON data (legacy / malformed) – fall back to raw text
                raw = data.decode(errors="ignore").strip()
                print(f"[RAW] from {client_address}: {raw}")
                # Wrap it as a broadcast for backward compatibility
                packet = {
                    "event"  : EVT_BROADCAST,
                    "payload": {
                        "flag"    : FLAG_BROADCAST_ALL,
                        "username": username,
                        "to"      : "broadcast",
                        "data"    : raw,
                    },
                }

            event   = packet.get("event")
            payload = packet.get("payload", {})

            # ── Route on event type ──────────────────────────────────────────
            if event == EVT_DISCONNECT:
                reason = payload.get("reason", "")
                print(f"[DISCONNECT] {client_address} ({username}): {reason}")
                terminator(tls_client_sock, client_address, cmd=False)
                break

            elif event == EVT_BROADCAST:
                flag = payload.get("flag", FLAG_BROADCAST_ALL)
                msg  = payload.get("data", "")
                if(msg == ""):
                    continue
                print(f"[{flag.upper()}] {username}: {msg}")

                # Re-stamp with server-side username in case client faked it
                out_packet = pkt_broadcast(
                    username = username,
                    data     = msg,
                    role     = payload.get("role", "member"),
                    to       = payload.get("to", "broadcast"),
                    flag     = flag,
                )

                if flag == FLAG_BROADCAST_ALL:
                    broadcast(out_packet, tls_client_sock)
                elif flag == FLAG_DM:
                    target_user = payload.get("to", "")
                    _send_dm(out_packet, target_user, tls_client_sock)
                # FLAG_BROADCAST_AI handled in the future when AI client exists

            else:
                # Unknown event – log and ignore
                print(f"[ PROTOCOL ] Unknown event '{event}' from {client_address}")

        except Exception as e:
            print(f"[ERROR] Handling client {client_address}: {e}")
            break

    # ── Thread exit → ensure cleanup ────────────────────────────────────────
    if (tls_client_sock in CLIENTS) and (tls_client_sock in ACL):
        try:
            terminator(tls_client_sock, client_address)
        except Exception:
            print("Thread still alive after client closed.")
    return


# ─────────────────────────────────────────────────────────────────────────────
def _send_dm(packet_bytes: bytes, target_username: str, sender_sock):
    """Send a DM packet to a specific authenticated user by username."""
    with CLIENTS_LOCK:
        for sock, uname in CLIENT_USERNAMES.items():
            if uname == target_username and sock != sender_sock and sock in ACL:
                try:
                    sock.send(packet_bytes)
                except Exception as e:
                    print(f"[DM] Error sending to {target_username}: {e}")
                return
    print(f"[DM] Target user '{target_username}' not found or not authenticated.")


# ─────────────────────────────────────────────────────────────────────────────
def terminator(tls_client_sock, client_sock_addrs, cmd=True):
    if tls_client_sock.fileno() == -1:
        print(f"Socket already closed for {client_sock_addrs}")
        return

    if cmd:
        try:
            tls_client_sock.send(pkt_disconnect("Server closed this connection."))
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"[3] Error sending disconnect packet to {tls_client_sock}: {e}")

    with CLIENTS_LOCK:
        if tls_client_sock in ACL:
            ACL.remove(tls_client_sock)
        if tls_client_sock in CLIENTS:
            CLIENTS.remove(tls_client_sock)
        CLIENT_USERNAMES.pop(tls_client_sock, None)

    if cmd:
        try:
            time.sleep(0.1)
            tls_client_sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print(f"[4] Error shutting down socket {client_sock_addrs}: {e}")

        if tls_client_sock.fileno() != -1: # if the socket is not closed yet , then we close it manually.
            try:
                tls_client_sock.close()
            except Exception as e:
                print(f"[5] Error closing socket {client_sock_addrs}: {e}")

    print(f"[6] Connection closed: {client_sock_addrs}")


# ─────────────────────────────────────────────────────────────────────────────
def authentication(tls_client_sock, client_address) -> bool:
    """Drive the signup/signin flow using JSON packets. Returns True on success."""
    auth = Authentication(tls_client_sock, client_address)

    # Send welcome + hint about what to do
    tls_client_sock.send(pkt_connect("Welcome to the Chat!"))

    # Receive the client's auth packet
    try:
        raw = tls_client_sock.recv(4096)
        packet = parse_packet(raw)
    except Exception as e:
        print(f"[AUTH] Receive error from {client_address}: {e}")
        terminator(tls_client_sock, client_address)
        return False

    if packet is None or packet.get("event") != EVT_AUTH:
        tls_client_sock.send(pkt_system("Expected an 'authentication' packet.", status="error"))
        terminator(tls_client_sock, client_address)
        return False

    payload = packet.get("payload", {})
    action  = payload.get("action", "")    # AUTH_SIGNUP or AUTH_SIGNIN

    if action == "signup":
        success = auth.signup(payload)
        if not success:
            terminator(tls_client_sock, client_address)
            return False
        # After signup, proceed directly to signin
        success = auth.signin(payload)

    elif action == "signin":
        success = auth.signin(payload)

    else:
        tls_client_sock.send(pkt_system("Unknown action. Use 'signup' or 'signin'.", status="error"))
        terminator(tls_client_sock, client_address)
        return False

    if not success:
        terminator(tls_client_sock, client_address)
        return False

    # Mark as authenticated
    with CLIENTS_LOCK:
        ACL.append(tls_client_sock)
        CLIENTS.append(tls_client_sock)
        if tls_client_sock in UACL:
            UACL.remove(tls_client_sock)
        CLIENT_USERNAMES[tls_client_sock] = auth.username

    return True


# ─────────────────────────────────────────────────────────────────────────────
def initialize():
    db = Database()
    if not db.db_check():
        print("[ ! ] Database initialization failed!")
        sys.exit(1)


def main():
    initialize()
    global server
    #-----------------------------------
    def signal_handler(sig, frame):
        print('\n[ * ] Shutting down gracefully...')
        server.close()
        sys.exit(0)
    #-------------------------------------
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C handler
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    server.listen()
    print("[ * ] Server listening...")
    utls.loading()
    utls.simple_spinner()

    # Paths loaded from .env via TLSConfig (SSL_CERT_PATH, SSL_KEY_PATH, SSL_CA_PATH)
    tls_cfg = TLSConfig(
        certfile  = "",
        keyfile   = "",
        cafile    = "",
        raw_socket= server
    )
    ssl_ctx = tls_cfg.create_context()

    while True:
        try:
            client, address = server.accept()
            print(f"[ + ]    Accepted connection from {address}")
            print("[ + ]    Proceeding with the TLS Tunneling", end="")
            utls.loading()
            print("\n")

            tls_client = ssl_ctx.wrap_socket(client, server_side=True)
            with CLIENTS_LOCK:
                UACL.append(tls_client)
            threading.Thread(target=handle_client, args=(tls_client, address)).start()

        except Exception as e:
            print(e)
            try:
                terminator(tls_client, address)
            except Exception:
                pass
            break

    server.close()


if __name__ == '__main__':
    main()


#######<------SFH------->####### --> start form here again
# ??? --> need to test and recheck

# >[number]   --> we do next or later.

""" /-------------------------------------------------------------------------------------------------/ """
# 1. will use the sql instead of the file handling to access and minupulate the credential data
""" /-------------------------------------------------------------------------------------------------/ """
# use
#       sudo lsof -i :<PORT NUMBER>
# to resolve the issue : OSError: [Errno 98] Address already in use
