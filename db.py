import sqlite3
from datetime import datetime

DB_FILE = 'buildmetrics.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    conn.commit()
    conn.close()

def log_project(area, floors, tier, grade, estimated_cost):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute('''
        INSERT INTO projects_log (timestamp, area, floors, tier, grade, estimated_cost)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, area, floors, tier, grade, estimated_cost))
    conn.commit()
    conn.close()

def get_projects_log():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM projects_log ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return rows
