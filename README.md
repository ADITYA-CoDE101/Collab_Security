# Collab_Security_Platform-
![Python](https://img.shields.io/badge/Python-3.x-blue)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)
![Security](https://img.shields.io/badge/Security-bcrypt-green)
![Architecture](https://img.shields.io/badge/Architecture-MultiThreaded-red)
![Status](https://img.shields.io/badge/Status-Actively_Developed-brightgreen)

---

## 🔐 Secure Multi-Threaded TCP Chat Server

## 📌 Overview

This project is a **multi-threaded TCP Chat Server** built using Python.  
It implements secure authentication with MySQL integration and bcrypt password hashing.

The system is designed with modular architecture so it can be extended into a **fully TLS-enabled secure communication system** in future versions.

---

## 🏗 Architecture
```
            ┌─────────────────────┐
            │        Client        │
            │  (Threaded I/O)      │
            └──────────┬──────────┘
                       │ TCP
            ┌──────────▼──────────┐
            │   Chat Server Core   │
            │  (Multi-Threaded)    │
            ├──────────┬──────────┤
            │ Auth Layer│Broadcast │
            ├──────────┴──────────┤
            │  Database Layer      │
            │   (MySQL)            │
            └─────────────────────┘

.TCP
└── Multi-Threaded Server
├── Authentication Layer
├── Database Layer (MySQL)
├── Broadcast System
└── Client Management (ACL / UACL)

```


### Core Files

- `server.py` → Main multi-threaded server
- `client.py` → Client-side communication logic
- `initialize.py` → Database, authentication, configuration logic
- `Config/server.confg` → Server configuration file

---

# ⚙️ Technologies Used

## 🐍 Language
- Python 3.x
- Mysql

---

## 🌐 Networking

| Module | Purpose |
|---------|----------|
| `socket` | TCP communication |
| `threading` | Multi-client concurrency |
| `select` | Non-blocking input handling (client side) |
| `signal` | Graceful shutdown handling |


---

## 🗄 Database

| Technology | Purpose |
|------------|----------|
| MySQL | Persistent user storage |
| `mysql.connector` | Python-MySQL interface |
| `ConfigParser` | Configuration management |

---

## 🔐 Security

| Technology | Purpose |
|------------|----------|
| `bcrypt` | Password hashing |
| Login attempt limit | Brute-force mitigation |
| Hashed password storage | No plaintext credentials |

---

## 🔐 Security Stack

| Technology | Purpose |
|------------|----------|
| bcrypt | Password hashing |
| Attempt limiting | Brute-force mitigation |
| Thread locks | Race condition prevention |

---

# 📚 Python Libraries Used & Purpose

### 1️⃣ socket
- Creating TCP server
- Accepting connections
- Sending/receiving data
- Graceful shutdown

### 2️⃣ threading
- Handling each client in separate threads
- Concurrent send/receive operations

### 3️⃣ mysql.connector
- Connecting to MySQL
- Creating database if missing
- Creating user table
- Executing parameterized queries

### 4️⃣ bcrypt
- Hashing passwords during signup
- Verifying passwords during signin

### 5️⃣ ConfigParser
- Reading configuration file
- Managing MySQL credentials and server settings

### 6️⃣ datetime
- Storing user registration timestamps

### 7️⃣ select (Client Side)
- Non-blocking stdin monitoring
- Preventing thread blocking
- Clean shutdown handling

---

# 🔐 Security Design Philosophy

This system enforces:

1. No plaintext password storage
2. Parameterized SQL queries (SQL injection resistance)
3. Thread-safe shared resource handling
4. Graceful socket shutdown (reduces descriptor leaks)
5. Separation of concerns:
   - Networking layer
   - Authentication layer
   - Database layer

---


# 🛡 Threat Model (Current Version)

| Threat | Mitigation |
|--------|------------|
| Password theft from DB | bcrypt hashing |
| SQL Injection | Parameterized queries |
| Thread race conditions | Lock mechanism |
| Broken connections | Graceful termination handling |

---

# ⚠️ Current Security Limitation

Traffic is currently transmitted over raw TCP.

This means:
- Credentials are encrypted in database
- BUT network traffic is not yet encrypted

---

# 🔁 Implemented Features



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

1. Client connects
2. Server prompts for:
   - SignUp (1)
   - SignIn (2)
3. Credentials are validated against MySQL
4. Password verified using bcrypt
5. Client added to Authenticated Client List (ACL)
6. Messaging enabled

---

# 🧠 Client Management System

| List | Description |
|------|-------------|
| `UACL` | Unauthenticated Clients |
| `ACL` | Authenticated Clients |
| `CLIENTS` | All connected clients |

Thread safety is maintained using:

```python
CLIENTS_LOCK = threading.Lock()
```
--- 

## Future Enhancements

### _Core mechanism that may get added and the END GOAL_
  - _Collabrotive pentesting platform for pentesters_
  - _Collective reports managment system_
  - _AI enabled featuring_
  
### 🔒 TLS / SSL Integration

  - Wrap socket using Python ssl module
  - Certificate-based encryption
  - Secure handshake before authentication
  - Protection against MITM attacks

### 🛡 Security Improvements

  - Rate limiting per IP
  - Logging & monitoring
  - Intrusion detection logic
  - Session tokens

### Token-based authentication
  
  - 💬 Protocol Improvements
  - Structured JSON message framing
  - ommand parsing system
  - Private messaging
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
```
pip install mysql-connector-python bcrypt
``` 

### Setup MySQL
Ensure MySQL server is running.
```
sudo systemctl start mysql
```
Update credentials inside:
```
Config/server.confg
```

### Run Server
```
python server.py
```

### 4️⃣ Run Client
```
python client.py
```

### 📂 Project Structure
```
├── server.py
├── client.py
├── initialize.py
├── Config/
│    └── server.confg
```

---
##👨‍💻 Author

_**Aditya**_
- Cybersecurity Enthusiast
- Computer science and Engineering student
