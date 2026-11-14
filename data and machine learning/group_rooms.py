"""Shared SQLite storage for Movie Night rooms (one shared server required)."""
import os
import secrets
import sqlite3
from pathlib import Path

DB = Path(os.environ.get('MOVIE_NIGHT_DB_PATH', str(Path(__file__).resolve().parent / 'movie_rooms.sqlite3')))
MAX_CSV_BYTES = 25 * 1024 * 1024
MAX_MEMBERS = 12


def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB), timeout=20)
    db.execute('PRAGMA busy_timeout=20000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS rooms (code TEXT PRIMARY KEY, host_key TEXT NOT NULL)')
    db.execute("""CREATE TABLE IF NOT EXISTS uploads (
        code TEXT NOT NULL, name TEXT NOT NULL, csv BLOB NOT NULL,
        PRIMARY KEY (code, name), FOREIGN KEY(code) REFERENCES rooms(code))""")
    return db


def create_room():
    with connection() as db:
        for _ in range(10):
            code = secrets.token_hex(3).upper()
            key = secrets.token_urlsafe(18)
            try:
                db.execute('INSERT INTO rooms VALUES (?, ?)', (code, key))
                return code, key
            except sqlite3.IntegrityError:
                pass
    raise RuntimeError('Could not create a unique room code.')


def exists(code):
    with connection() as db:
        return db.execute('SELECT 1 FROM rooms WHERE code=?', (code,)).fetchone() is not None


def is_host(code, key):
    with connection() as db:
        return db.execute('SELECT 1 FROM rooms WHERE code=? AND host_key=?', (code, key)).fetchone() is not None


def members(code):
    with connection() as db:
        return [row[0] for row in db.execute('SELECT name FROM uploads WHERE code=? ORDER BY name', (code,))]


def upload(code, name, csv):
    if len(csv) > MAX_CSV_BYTES:
        raise ValueError('CSV is too large (25 MB limit).')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM rooms WHERE code=?', (code,)).fetchone():
            raise ValueError('Group code does not exist.')
        count = db.execute('SELECT COUNT(*) FROM uploads WHERE code=?', (code,)).fetchone()[0]
        current = db.execute('SELECT 1 FROM uploads WHERE code=? AND name=?', (code, name)).fetchone()
        if count >= MAX_MEMBERS and not current:
            raise ValueError('This group is full (12 members).')
        db.execute('INSERT OR REPLACE INTO uploads (code, name, csv) VALUES (?, ?, ?)', (code, name, csv))


def get_uploads(code):
    with connection() as db:
        return dict(db.execute('SELECT name, csv FROM uploads WHERE code=? ORDER BY name', (code,)))


def delete_room(code, key):
    if not is_host(code, key):
        raise ValueError('Invalid host key.')
    with connection() as db:
        db.execute('DELETE FROM uploads WHERE code=?', (code,))
        db.execute('DELETE FROM rooms WHERE code=? AND host_key=?', (code, key))
