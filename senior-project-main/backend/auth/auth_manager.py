"""
Authentication manager for VerifAI.
Uses SQLite + bcrypt for secure user management.
Save to: backend/auth/auth_manager.py
"""
import sqlite3
import bcrypt
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/users.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            last_login  TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT    PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            created_at  TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def register_user(name: str, email: str, password: str) -> Dict:
    init_db()
    email = email.lower().strip()

    # Validate
    if not name or len(name.strip()) < 2:
        return {"success": False, "error": "Name must be at least 2 characters."}
    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email address."}
    if len(password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters."}

    # Hash password
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name.strip(), email, hashed, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Account created for {name}."}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "An account with this email already exists."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(email: str, password: str) -> Dict:
    init_db()
    email = email.lower().strip()

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "No account found with this email."}

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        conn.close()
        return {"success": False, "error": "Incorrect password."}

    # Create session token (30 days)
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user["id"], datetime.utcnow().isoformat(), expires)
    )
    conn.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), user["id"])
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": {
            "id":    user["id"],
            "name":  user["name"],
            "email": user["email"],
        }
    }

def validate_session(token: str) -> Optional[Dict]:
    """Validate a session token and return user info if valid"""
    if not token:
        return None
    init_db()
    conn = get_db()
    row = conn.execute("""
        SELECT u.id, u.name, u.email, s.expires_at
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,)).fetchone()
    conn.close()

    if not row:
        return None
    if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        return None  # Expired

    return {"id": row["id"], "name": row["name"], "email": row["email"]}

def logout_session(token: str):
    """Invalidate a session token"""
    if not token:
        return
    init_db()
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
