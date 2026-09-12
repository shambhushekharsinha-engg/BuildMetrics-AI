import sqlite3
import json
from datetime import datetime, timedelta
from passlib.hash import bcrypt

DB_FILE = 'buildmetrics.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Legacy logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            area REAL,
            floors INTEGER,
            tier TEXT,
            grade TEXT,
            estimated_cost REAL
        )
    ''')
    
    # User authentication table with brute-force tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            failed_attempts INTEGER DEFAULT 0,
            lockout_until TEXT
        )
    ''')
    
    # Saved projects table
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            project_name TEXT,
            timestamp TEXT,
            plot_length REAL,
            plot_width REAL,
            num_floors INTEGER,
            prompt_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        pw_hash = bcrypt.hash(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, pw_hash))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, password_hash, failed_attempts, lockout_until FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return None, "Invalid credentials"
        
    uid, pw_hash, failed_attempts, lockout_until = user
    
    # Check if account is locked
    if lockout_until:
        lockout_time = datetime.fromisoformat(lockout_until)
        if datetime.now() < lockout_time:
            conn.close()
            return None, f"Account locked until {lockout_time.strftime('%H:%M:%S')}"
        else:
            # Lockout expired, reset attempts
            failed_attempts = 0
            c.execute('UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE id = ?', (uid,))
            conn.commit()
            
    # Verify password
    if bcrypt.verify(password, pw_hash):
        c.execute('UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE id = ?', (uid,))
        conn.commit()
        conn.close()
        return uid, "Success"
    else:
        # Brute force protection: increment failed attempts
        failed_attempts += 1
        if failed_attempts >= 5:
            lockout = (datetime.now() + timedelta(minutes=15)).isoformat()
            c.execute('UPDATE users SET failed_attempts = ?, lockout_until = ? WHERE id = ?', (failed_attempts, lockout, uid))
            conn.commit()
            conn.close()
            return None, "Account locked due to 5 failed attempts (15 min lockout)."
        else:
            c.execute('UPDATE users SET failed_attempts = ? WHERE id = ?', (failed_attempts, uid))
            conn.commit()
            conn.close()
            return None, f"Invalid credentials. {5 - failed_attempts} attempts remaining."

def save_project(user_id, project_name, plot_length, plot_width, num_floors, prompt_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute('''
        INSERT INTO saved_projects (user_id, project_name, timestamp, plot_length, plot_width, num_floors, prompt_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, project_name, timestamp, plot_length, plot_width, num_floors, json.dumps(prompt_data)))
    conn.commit()
    conn.close()

def load_user_projects(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, project_name, timestamp, plot_length, plot_width, num_floors, prompt_data FROM saved_projects WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    projects = []
    for r in rows:
        projects.append({
            "id": r[0], "name": r[1], "time": r[2], "l": r[3], "w": r[4], "floors": r[5], "data": json.loads(r[6])
        })
    return projects
