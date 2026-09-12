import sqlite3
import json
import hashlib
from datetime import datetime

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
    
    # User authentication table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

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
