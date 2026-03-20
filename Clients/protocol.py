"""
protocol.py  –  JSON Wire Protocol for the TCP  Project
============================================================
Single source of truth for building and parsing JSON packets shared by
both the server (s1.py, initialize.py) and all clients (c1.py, c2.py).

Packet shape
------------
Every packet sent over the socket looks like:

    {
        "event"  : "<event_name>",
        "payload": { ... }
    }

Event constants (EVT_*)
-----------------------
Use these instead of hardcoded strings so typos trigger a NameError, not
a silent protocol mismatch.

Flag constants (FLAG_*)
-----------------------
Put inside payload["flag"] to guide server-side routing.
"""

import json
from datetime import datetime, timezone


# ─── Event names ────────────────────────────────────────────────────────────

# Server → Client  :  initial handshake / welcome
EVT_CONNECT    = "connect"

# Client → Server  :  login or signup credentials
EVT_AUTH       = "authentication"

# Server → Client  :  result of an auth attempt
EVT_AUTH_RESP  = "auth_response"

# Both directions  :  a chat message
EVT_BROADCAST  = "broadcast"

# Both directions  :  clean connection teardown request
EVT_DISCONNECT = "disconnect"

# Server → Client  :  informational / prompt / error notice
EVT_SYSTEM     = "system"


# ─── Routing Flags (go inside payload["flag"]) ──────────────────────────────

FLAG_BROADCAST_ALL = "broadcast_all"   # send to every authenticated client
FLAG_DM            = "dm"              # direct message to a specific user
FLAG_BROADCAST_AI  = "broadcast_ai"   # send only to AI bot client
FLAG_SYSTEM        = "system"          # server-internal / system traffic


# ─── Auth sub-types (payload["action"]) ─────────────────────────────────────

AUTH_SIGNUP = "signup"
AUTH_SIGNIN = "signin"


# ─── Helpers ────────────────────────────────────────────────────────────────

def _timestamp() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%d %m %Y  %H:%M:%S UTC")


def build_packet(event: str, payload: dict) -> bytes:
    """
    Serialise an event + payload dict into UTF-8 JSON bytes ready to
    send over a socket.

    Usage
    -----
    sock.send(build_packet(EVT_BROADCAST, {
        "flag"     : FLAG_BROADCAST_ALL,
        "username" : "alice",
        "to"       : "broadcast",
        "data"     : "Hello everyone!",
        "timestamp": _timestamp(),
    }))
    """
    packet = {
        "event"  : event,
        "payload": payload,
    }
    return json.dumps(packet).encode("utf-8")


def parse_packet(data: bytes) -> dict | None:
    """
    Deserialise raw bytes from a socket into a packet dict.

    Returns None (and prints a warning) if the bytes are not valid JSON or
    don't match the expected ``{"event": ..., "payload": ...}`` shape.

    Usage
    -----
    packet = parse_packet(sock.recv(4096))
    if packet is None:
        return          # bad / non-JSON data – ignore or disconnect
    event   = packet["event"]
    payload = packet["payload"]
    """
    if not data:
        return None
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        print(f"[ PROTOCOL ] JSON decode error: {exc}")
        return None

    if not isinstance(obj, dict):
        print("[ PROTOCOL ] Packet is not a JSON object")
        return None
    if "event" not in obj or "payload" not in obj:
        print("[ PROTOCOL ] Missing 'event' or 'payload' key in packet")
        return None
    return obj


# ─── Convenience packet builders ────────────────────────────────────────────
# These cover every event type so neither the server nor the client needs to
# remember the exact field names.

def pkt_connect(welcome_msg: str = "Welcome to the Chat!") -> bytes:
    """Server → Client  :  initial welcome handshake."""
    return build_packet(EVT_CONNECT, {
        "flag"   : FLAG_SYSTEM,
        "message": welcome_msg,
        "hint"   : "Send an 'authentication' packet to sign up or sign in.",
    })


def pkt_system(message: str, status: str = "info") -> bytes:
    """Server → Client  :  generic system notice / prompt."""
    return build_packet(EVT_SYSTEM, {
        "flag"     : FLAG_SYSTEM,
        "status"   : status,          # "info" | "error" | "prompt"
        "message"  : message,
        "timestamp": _timestamp(),
    })


def pkt_auth(action: str, username: str, password: str, role: str = "member") -> bytes:
    """
    Client → Server  :  authentication packet.

    action   : AUTH_SIGNUP or AUTH_SIGNIN
    password : should be sent as plain text here; the server hashes it
               with bcrypt before touching the database.
    """
    return build_packet(EVT_AUTH, {
        "action"   : action,
        "role"     : role,
        "username" : username,
        "password" : password,
        "timestamp": _timestamp(),
    })


def pkt_auth_response(status: str, message: str, username: str = "") -> bytes:
    """Server → Client  :  result of a signup / signin attempt."""
    return build_packet(EVT_AUTH_RESP, {
        "flag"     : FLAG_SYSTEM,
        "status"   : status,          # "ok" | "error"
        "message"  : message,
        "username" : username,
        "timestamp": _timestamp(),
    })


def pkt_broadcast(username: str, data: str,
                  role: str = "member",
                  to: str = "broadcast",
                  flag: str = FLAG_BROADCAST_ALL) -> bytes:
    """Both directions  :  a chat message."""
    return build_packet(EVT_BROADCAST, {
        "flag"     : flag,
        "role"     : role,
        "username" : username,
        "to"       : to,
        "data"     : data,
        "timestamp": _timestamp(),
    })


def pkt_disconnect(reason: str = "") -> bytes:
    """Both directions  :  clean teardown request or acknowledgement."""
    return build_packet(EVT_DISCONNECT, {
        "flag"     : FLAG_SYSTEM,
        "reason"   : reason,
        "timestamp": _timestamp(),
    })
