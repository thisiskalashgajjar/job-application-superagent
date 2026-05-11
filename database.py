#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database.py
Created and coded by Kalash Tejendra Gajjar.
Copyrights to Kalash Tejendra Gajjar

"""

import sqlite3
from datetime import datetime

DB = "applications.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS applications(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     job_title TEXT,
                     company TEXT,
                     url TEXT,
                     resume TEXT,
                     cover_letter TEXT,
                     status TEXT DEFAULT 'Applied',
                     applied_at TEXT
                     )
                 """)
    conn.commit()
    conn.close()
    
def log_application(job_title, company, url, resume, cover_letter, applied_at):
    conn = sqlite3.connect(DB)
    values = (job_title, company, url, resume, cover_letter, applied_at)
    conn.execute(
        "INSERT INTO applications (job_title, company, url, resume, cover_letter, applied_at) VALUES (?, ?, ?, ?, ?, ?)",
        values
    )
    conn.commit()
    conn.close()

def update_status(app_id, new_status):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
    conn.commit()
    conn.close()

def get_all_applications():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM applications ORDER BY applied_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]