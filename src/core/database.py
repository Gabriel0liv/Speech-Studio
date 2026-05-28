import os
import sqlite3
from pathlib import Path
from datetime import datetime

def get_database_path() -> Path:
    """Get the absolute path to the local SQLite database file."""
    # Project root is 3 levels up from this file (src/core/database.py -> src/core -> src -> root)
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    os.makedirs(data_dir, exist_ok=True)
    return data_dir / "speech_studio.db"

def get_connection() -> sqlite3.Connection:
    """Establish and configure a connection to the SQLite database."""
    db_path = get_database_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Configure WAL journal mode and busy timeout for high-concurrency safety
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
    except sqlite3.Error:
        pass
        
    return conn

def apply_migrations(conn: sqlite3.Connection):
    """Apply versioned migrations to the database schema."""
    cursor = conn.cursor()
    
    # Ensure migrations table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()
    
    # Check current migration version
    cursor.execute("SELECT MAX(version) FROM schema_migrations")
    row = cursor.fetchone()
    current_version = row[0] if row and row[0] is not None else 0
    
    # Migration 1: Schema creation
    if current_version < 1:
        print("[*] Aplicando migracao de banco de dados versao 1...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                input_kind TEXT,
                input_path TEXT,
                input_name TEXT,
                text_snippet TEXT,
                output_dir TEXT,
                primary_output_path TEXT,
                output_format TEXT,
                engine TEXT,
                model TEXT,
                voice TEXT,
                language TEXT,
                device TEXT,
                duration_seconds REAL,
                error_message TEXT,
                metadata_json TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tts_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                engine TEXT NOT NULL,
                voice TEXT,
                output_format TEXT DEFAULT "wav",
                speed REAL,
                preview_chars INTEGER DEFAULT 300,
                chunk_chars INTEGER DEFAULT 400,
                language TEXT,
                metadata_json TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speaker_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                mapping_json TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Record migration
        cursor.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (1, datetime.now().isoformat())
        )
        conn.commit()
        
        # Seed initial data (default settings and presets)
        seed_initial_data(conn)

def seed_initial_data(conn: sqlite3.Connection):
    """Seed initial app settings and defaults."""
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    # Default app settings
    default_settings = [
        ("history_enabled", "true"),
        ("save_full_text_history", "false")
    ]
    for key, val in default_settings:
        cursor.execute(
            "INSERT OR IGNORE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, val, now_str)
        )
        
    # Default TTS presets
    default_presets = [
        ("Narradora Kokoro Dora (Padrao)", "kokoro", "pt_br_dora", "wav", 1.0, 300, 400, "pt-br", "{}", 1),
        ("Narrador Kokoro Alex", "kokoro", "pt_br_alex", "wav", 1.0, 300, 400, "pt-br", "{}", 0),
        ("Piper Voz Lula", "piper", "pt_br_lula", "wav", 1.0, 300, 400, "pt-br", "{}", 0),
        ("Piper Voz Faber (Narrador)", "piper", "pt_br_faber", "wav", 1.0, 300, 400, "pt-br", "{}", 0)
    ]
    for name, engine, voice, fmt, speed, preview, chunk, lang, meta, is_def in default_presets:
        cursor.execute("""
            INSERT OR IGNORE INTO tts_presets (
                name, engine, voice, output_format, speed, preview_chars, chunk_chars, language, metadata_json, is_default, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, engine, voice, fmt, speed, preview, chunk, lang, meta, is_def, now_str, now_str))
        
    conn.commit()

def initialize_database():
    """Main entrypoint to initialize data folder, DB connection, and run migrations."""
    conn = get_connection()
    try:
        apply_migrations(conn)
    finally:
        conn.close()
