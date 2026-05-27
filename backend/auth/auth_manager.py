"""
Authentication manager for VerifAI — Security hardened.
Save to: backend/auth/auth_manager.py
"""
import sqlite3
import bcrypt
import secrets
import re
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

# ── FIX 3: Password validation ─────────────────────────────────────────
def validate_password(password: str) -> Optional[str]:
    """
    Returns an error message if invalid, None if valid.
    Requirements: 8+ chars, 1 uppercase, 1 special character.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\+=/\\]", password):
        return "Password must contain at least one special character."
    return None

def register_user(name: str, email: str, password: str) -> Dict:
    init_db()
    email = email.lower().strip()

    if not name or len(name.strip()) < 2:
        return {"success": False, "error": "Name must be at least 2 characters."}
    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email address."}

    # FIX 3: use the shared validator
    pw_error = validate_password(password)
    if pw_error:
        return {"success": False, "error": pw_error}

    hashed = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

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
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "No account found with this email."}

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        conn.close()
        return {"success": False, "error": "Incorrect password."}

    token   = secrets.token_urlsafe(32)
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
        "token":   token,
        "user": {
            "id":    user["id"],
            "name":  user["name"],
            "email": user["email"],
        }
    }

def validate_session(token: str) -> Optional[Dict]:
    if not token:
        return None
    init_db()
    conn = get_db()
    row = conn.execute("""
        SELECT u.id, u.name, u.email, s.expires_at
        FROM sessions s JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,)).fetchone()

    if not row:
        conn.close()
        return None

    if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None

    conn.execute(
        "DELETE FROM sessions WHERE user_id = ? AND expires_at < ?",
        (row["id"], datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"id": row["id"], "name": row["name"], "email": row["email"]}

def logout_session(token: str):
    if not token:
        return
    init_db()
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

# ── FIX 2: Reset password by email ────────────────────────────────────
def reset_password(email: str, new_password: str) -> Dict:
    """Reset a user's password given their email."""
    init_db()
    email = email.lower().strip()

    pw_error = validate_password(new_password)
    if pw_error:
        return {"success": False, "error": pw_error}

    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "No account found with this email."}

    hashed = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (hashed, user["id"])
    )
    # Invalidate all existing sessions so old sessions can't be reused
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Password reset successfully. Please sign in."}
