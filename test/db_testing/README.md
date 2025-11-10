# Test folder README

This folder contains test utilities and a small harness to exercise the `signup` flow in `t2.py`.

Files
- `t2.py` - Signup and username-check logic. Uses `get_mysql_connection()` (from the project root) to connect to MySQL.
- `harness_signup.py` - A simple harness that simulates a client using `socket.socketpair()` and calls `signup()`.
- `__init__.py` - Makes the `test` folder importable as a package.

Quick start

1. Install dependencies (recommended inside a virtualenv):

```bash
pip install -r ../requirements.txt
# or directly
pip install bcrypt mysql-connector-python
```

2. Verify MySQL settings

Edit `get_mysql_connection.py` at the repository root if necessary. By default it uses:

- host: localhost
- user: root
- password: 1234
- database: chat1

3. Ensure the `users` table exists

Example SQL to create a compatible table (hashes are stored as bytes by the harness):

```sql
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password BLOB NOT NULL
);
```

If you'd rather store the bcrypt hash as a UTF-8 string (TEXT/VARCHAR), change the code in `t2.py` to decode the hashed bytes:

```py
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

4. Run the harness (it will create then delete a test user):

```bash
python3 harness_signup.py
```

Notes
- The harness uses `socket.socketpair()` to simulate a client/server socket locally; it does not open network ports.
- `harness_signup.py` loads `t2.py` by path to avoid import issues when running as a script.
- If you prefer pure unit tests that do not touch a live MySQL instance, I can convert the harness to use SQLite or provide mocked tests.

Troubleshooting
- If you see "No module named 'mysql'", install `mysql-connector-python` as shown above.
- If connection fails, confirm MySQL is running and the credentials in `get_mysql_connection.py` are correct.
