import sqlite3
from typing import Optional, Dict, Any, List
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Files table (catalog, ratings, tags, labels, hashes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_metadata (
            filepath TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            mtime REAL NOT NULL,
            width INTEGER,
            height INTEGER,
            format TEXT,
            rating INTEGER DEFAULT 0,
            color_label TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            comment TEXT DEFAULT '',
            dhash TEXT,
            sha256 TEXT,
            is_corrupt INTEGER DEFAULT 0,
            last_indexed REAL DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # Collections / Favorites
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at REAL DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_items (
            collection_id INTEGER,
            filepath TEXT,
            added_at REAL DEFAULT (strftime('%s', 'now')),
            PRIMARY KEY (collection_id, filepath),
            FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_folders (
            folder_path TEXT PRIMARY KEY,
            added_at REAL DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    conn.commit()
    conn.close()

def get_file_record(filepath: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_metadata WHERE filepath = ?", (filepath,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_file_record(filepath: str, fields: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    keys = list(fields.keys())
    values = [fields[k] for k in keys]
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    
    cursor.execute(f"""
        INSERT INTO file_metadata (filepath, filename, filesize, mtime, {', '.join(keys)})
        VALUES (?, '', 0, 0, {', '.join(['?'] * len(keys))})
        ON CONFLICT(filepath) DO UPDATE SET {set_clause}
    """, [filepath] + values + values)
    
    conn.commit()
    conn.close()

def get_favorites() -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT folder_path FROM favorite_folders ORDER BY added_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_favorite(folder_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO favorite_folders (folder_path) VALUES (?)", (folder_path,))
    conn.commit()
    conn.close()

def remove_favorite(folder_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorite_folders WHERE folder_path = ?", (folder_path,))
    conn.commit()
    conn.close()
