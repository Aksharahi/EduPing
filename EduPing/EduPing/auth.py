"""
User authentication and database management module for EduPing
Handles user registration, login, and WhatsApp number management
"""

import sqlite3
import bcrypt
import os
from datetime import datetime
from pathlib import Path


# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def init_database():
    """Initialize the users database with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hash_value: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))


def user_exists(email: str) -> bool:
    """Check if user already exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def register_user(email: str, password: str, whatsapp_number: str, full_name: str = "") -> dict:
    """
    Register a new user
    
    Args:
        email: User email (must be unique)
        password: User password (will be hashed)
        whatsapp_number: WhatsApp number with country code (e.g., 919876543210)
        full_name: User's full name (optional)
    
    Returns:
        dict with 'success' and 'message' keys
    """
    if user_exists(email):
        return {"success": False, "message": "Email already registered"}
    
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    
    if not whatsapp_number or not whatsapp_number.isdigit():
        return {"success": False, "message": "WhatsApp number must contain only digits"}
    
    password_hash = hash_password(password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, whatsapp_number, full_name)
            VALUES (?, ?, ?, ?)
        """, (email, password_hash, whatsapp_number, full_name))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "User registered successfully"}
    except Exception as e:
        return {"success": False, "message": f"Registration failed: {str(e)}"}


def login_user(email: str, password: str) -> dict:
    """
    Authenticate user credentials
    
    Args:
        email: User email
        password: User password (will be verified against hash)
    
    Returns:
        dict with 'success', 'message', and 'user_data' keys
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, whatsapp_number FROM users WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {"success": False, "message": "Invalid email or password"}
        
        # Get password hash for verification
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        hash_row = cursor.fetchone()
        conn.close()
        
        if not verify_password(password, hash_row[0]):
            return {"success": False, "message": "Invalid email or password"}
        
        user_data = {
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "whatsapp_number": user[3]
        }
        
        return {"success": True, "message": "Login successful", "user_data": user_data}
    except Exception as e:
        return {"success": False, "message": f"Login failed: {str(e)}"}


def get_user_by_email(email: str) -> dict:
    """Get user data by email"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, whatsapp_number FROM users WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
        
        return {
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "whatsapp_number": user[3]
        }
    except Exception as e:
        return None


def update_whatsapp_number(email: str, whatsapp_number: str) -> dict:
    """Update user's WhatsApp number"""
    if not whatsapp_number or not whatsapp_number.isdigit():
        return {"success": False, "message": "WhatsApp number must contain only digits"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET whatsapp_number = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE email = ?
        """, (whatsapp_number, email))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "WhatsApp number updated successfully"}
    except Exception as e:
        return {"success": False, "message": f"Update failed: {str(e)}"}


def get_all_users() -> list:
    """Get all registered users (for admin purposes)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, whatsapp_number, created_at FROM users
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": u[0],
                "email": u[1],
                "full_name": u[2],
                "whatsapp_number": u[3],
                "created_at": u[4]
            }
            for u in users
        ]
    except Exception as e:
        return []


# Initialize database on module import
if not os.path.exists(DB_PATH):
    init_database()
