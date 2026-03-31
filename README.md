# Collab_Security_Platform
![Python](https://img.shields.io/badge/Python-3.x-blue)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)
![Security](https://img.shields.io/badge/Security-mTLS_%2B_bcrypt-green)
![Data](https://img.shields.io/badge/Protocol-JSON-yellow)
![Architecture](https://img.shields.io/badge/Architecture-MultiThreaded-red)
![Status](https://img.shields.io/badge/Status-Actively_Developed-brightgreen)

---

## 🔐 Secure Multi-Threaded TCP Chat Platform

## 📌 Overview

This project is a **multi-threaded TCP Chat Server** built using Python.  
It implements secure authentication with MySQL integration and bcrypt password hashing.

The system is designed with a modular architecture and features a **fully TLS-enabled secure communication system** utilizing **Mutual TLS (mTLS)** for two-way authentication, alongside structured **JSON data framing** for robust data transfer.

---

## 🏗 Architecture
```text
            ┌───────────────────────┐
            │        Client         │
            │   (Threaded I/O)      │
            └──────────┬────────────┘
                       │ mTLS Tunnel (JSON)
            ┌──────────▼────────────┐
            │   Chat Server Core    │
            │   (Multi-Threaded)    │
            ├──────────┬────────────┤
            │Auth Layer│ Broadcast  │
            ├──────────┴────────────┤
            │   Database Layer      │
            │      (MySQL)          │
            └───────────────────────┘

.TCP
└── Multi-Threaded Server
    ├── Mutual TLS (mTLS) Security Layer
    ├── JSON Protocol Communication Layer
    ├── Authentication Layer (bcrypt)
    ├── Database Layer (MySQL)
    ├── Broadcast System
    └── Client Management (ACL / UACL)
```

### Core Files

- `Servers/s1.py` → Main multi-threaded server with mTLS encryption
- `Servers/initialize.py` → Database, authentication, configuration logic
- `Servers/protocol.py` → Standardized JSON packet builder and parser
- `Servers/ServTSL.py` → SSL/TLS Context generation for Server
- `Clients/c1.py` → Secure client with mTLS support
- `Clients/ClientTLS.py` → SSL/TLS Context generation for Client
- `Config/server.confg` → Server configuration file

---

# ⚙️ Technologies Used

## 🐍 Language
- Python 3.x
- MySQL

---

## 🌐 Networking & Data

| Module | Purpose |
|---------|----------|
| `socket` | TCP communication |
| `ssl` | mTLS Network Encryption |
| `threading` | Multi-client concurrency |
| `select` | Non-blocking input handling (client side) |
| `json` | Structured message framing |
| `signal` | Graceful shutdown handling |


---

## 🗄 Database

| Technology | Purpose |
|------------|----------|
| MySQL | Persistent user storage |
| `mysql.connector` | Python-MySQL interface |
| `ConfigParser` | Configuration management |

---

## 🔐 Security Stack

| Technology | Purpose |
|------------|----------|
| **mTLS** (Mutual TLS) | End-to-end encryption & client-server verification |
| **bcrypt** | Password hashing |
| Attempt limiting | Brute-force mitigation |
| Thread locks | Race condition prevention |

---

# 📚 Python Libraries Used & Purpose

### 1️⃣ socket & ssl
- Creating TCP server and wrapping with TLS
- Handshake and two-way authentication
- Encrypted sending/receiving data

### 2️⃣ json
- Standardized data packet construction
- Event routing based on JSON fields

### 3️⃣ threading
- Handling each client in separate threads
- Concurrent send/receive operations

### 4️⃣ mysql.connector
- Connecting to MySQL
- Creating database if missing
- Creating user table
- Executing parameterized queries

### 5️⃣ bcrypt
- Hashing passwords during signup
- Verifying passwords during signin

### 6️⃣ ConfigParser & dotenv
- Reading configuration files and `.env` securely
- Managing MySQL credentials and certificates path

### 7️⃣ select (Client Side)
- Non-blocking stdin monitoring
- Preventing thread blocking
- Clean shutdown handling

---

# 🔐 Security Design Philosophy

This system enforces:

1. **Encrypted Network Traffic:** All communications run over an mTLS tunnel protecting against MITM and eavesdropping.
2. **Double Identity Verification:** Server verifies the client's certificate, and the client verifies the server's certificate.
3. **No plaintext password storage:** Passwords are hashed with bcrypt.
4. **Structured Protocol:** Exclusively accepts JSON payloads to prevent injection or malformed data attacks.
5. **Parameterized SQL queries:** SQL injection resistance.
6. **Thread-safe shared resource handling:** Locks are used for shared data.
7. **Graceful socket shutdown:** Reduces descriptor leaks.

---


# 🛡 Threat Model

| Threat | Mitigation |
|--------|------------|
| Eavesdropping / MITM | **mTLS network encryption** |
| Rogue Server / Client Spoofing | **mTLS mutual certificate validation** |
| Password theft from DB | **bcrypt hashing** |
| SQL Injection | **Parameterized queries** |
| Malformed String Protocol | **JSON packet parsing & validation** |
| Thread race conditions | **Lock mechanism** |

---

# 🔁 Implemented Features

✔ **NEW:** Mutual TLS (mTLS) Authentication and End-to-End Encryption  
✔ **NEW:** JSON Protocol Data Communication and Routing Layer  
✔ Multi-threaded TCP server  
✔ SignUp / SignIn authentication  
✔ Automatic database creation  
✔ Automatic table creation  
✔ Password hashing with bcrypt  
✔ Thread-safe client lists  
✔ Broadcast messaging system  
✔ Graceful disconnect protocol (`RQST-> DISCONNECT`)  
✔ Clean server shutdown (Ctrl + C safe exit)  

---

# 🔐 Authentication Flow

1. Client initiates TCP connection.
2. **mTLS Handshake:** Server and Client verify each other's certificates.
3. Server prompts for JSON Auth Packet via `EVT_CONNECT`:
   - SignUp
   - SignIn
4. Client responds with `EVT_AUTH` JSON payload.
5. Credentials are validated against MySQL and bcrypt.
6. Client added to Authenticated Client List (ACL).
7. Server emits `EVT_AUTH_RESP` confirming login, and messaging unlocks.

---

## Future Enhancements

### _Core mechanism that may get added and the END GOAL_
  - _Collaborative pentesting platform for pentesters_
  - _Collective reports management system_
  - _AI enabled featuring_
  
### 🛡 Security Improvements
  - Rate limiting per IP
  - Logging & monitoring
  - Intrusion detection logic
  - Session tokens or Token-based authentication

### 💬 Protocol Improvements
  - Command parsing system
  - Private messaging (DM logic partially implemented using flags)
  - Chat rooms

### 📦 Feature Expansion
  - Message history storage
  - Admin roles
  - User banning system
  - Heartbeat mechanism
  - Asyncio-based implementation

---

## 🖥 Installation & Setup

### Install Dependencies
```bash
pip install mysql-connector-python bcrypt python-dotenv pyOpenSSL
``` 

### Setup MySQL
Ensure MySQL server is running.
```bash
sudo systemctl start mysql
```
Update credentials inside:
```
Config/server.confg
```

### Certificates Setup
Ensure valid TLS certificates and CA keys are placed in your `.env` configured paths for `ServTSL.py` and `ClientTLS.py`.

### Run Server
```bash
cd Servers
python s1.py
```

### Run Client
```bash
cd Clients
python c1.py
```

### 📂 Project Structure
```text
├── Servers/
│    ├── s1.py
│    ├── initialize.py
│    ├── protocol.py
│    └── ServTSL.py
├── Clients/
│    ├── c1.py
│    ├── c2.py
│    ├── protocol.py
│    └── ClientTLS.py
├── Config/
│    └── server.confg
├── .env
└── README.md
```

---
## 👨‍💻 Author

_**Aditya**_
- Cybersecurity Enthusiast
- Computer Science and Engineering student
