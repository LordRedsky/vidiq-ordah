"""
core/db.py
==========
SQLite database engine, schema, dan helper functions.
Menggunakan SQLite3 bawaan Python (tanpa ORM eksternal, lebih ringan untuk Streamlit).
"""

import sqlite3
import os
import json
from datetime import datetime

# Pastikan folder data/ ada
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "app.db")


def get_connection() -> sqlite3.Connection:
    """Membuka koneksi ke SQLite. Row factory agar hasil berupa dict."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Inisialisasi semua tabel jika belum ada."""
    conn = get_connection()
    cur = conn.cursor()

    # Tabel: profil DNA Creator
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dna_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pdf_path TEXT,
            character_image_path TEXT,
            dna_text TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Tabel: jobs (satu job = satu video YouTube)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dna_profile_id INTEGER,
            topic TEXT NOT NULL,
            visual_style TEXT DEFAULT 'Photorealistic',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (dna_profile_id) REFERENCES dna_profiles(id)
        )
    """)

    # Tabel: title_candidates (7 judul per job)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS title_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Tabel: scripts (naskah per job)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            title_id INTEGER,
            content TEXT,
            char_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (title_id) REFERENCES title_candidates(id)
        )
    """)

    # Tabel: scenes (45 scene per job)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            scene_number INTEGER NOT NULL,
            narasi TEXT,
            visual_prompt TEXT,
            image_path TEXT,
            video_path TEXT,
            audio_path TEXT,
            image_status TEXT DEFAULT 'pending',
            video_status TEXT DEFAULT 'pending',
            audio_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── DNA Profiles ────────────────────────────────────────────────────────────

def create_dna_profile(name: str, pdf_path: str = None, character_image_path: str = None, dna_text: str = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO dna_profiles (name, pdf_path, character_image_path, dna_text) VALUES (?,?,?,?)",
        (name, pdf_path, character_image_path, dna_text)
    )
    conn.commit()
    profile_id = cur.lastrowid
    conn.close()
    return profile_id


def get_all_dna_profiles() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM dna_profiles ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dna_profile(profile_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM dna_profiles WHERE id = ?", (profile_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_dna_profile(profile_id: int, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [profile_id]
    conn = get_connection()
    conn.execute(f"UPDATE dna_profiles SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


# ─── Jobs ────────────────────────────────────────────────────────────────────

def create_job(topic: str, dna_profile_id: int, visual_style: str = "Photorealistic") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO jobs (topic, dna_profile_id, visual_style) VALUES (?,?,?)",
        (topic, dna_profile_id, visual_style)
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def get_all_jobs() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT j.*, d.name as dna_name
        FROM jobs j
        LEFT JOIN dna_profiles d ON j.dna_profile_id = d.id
        ORDER BY j.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("""
        SELECT j.*, d.name as dna_name, d.dna_text, d.character_image_path
        FROM jobs j
        LEFT JOIN dna_profiles d ON j.dna_profile_id = d.id
        WHERE j.id = ?
    """, (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Title Candidates ─────────────────────────────────────────────────────────

def save_title_candidates(job_id: int, titles: list[dict]):
    """Simpan 7 judul ke database. Hapus dulu yang lama."""
    conn = get_connection()
    conn.execute("DELETE FROM title_candidates WHERE job_id = ?", (job_id,))
    conn.executemany(
        "INSERT INTO title_candidates (job_id, title, reason, status) VALUES (?,?,?,?)",
        [(job_id, t['title'], t.get('reason', ''), 'Pending') for t in titles]
    )
    conn.commit()
    conn.close()


def get_title_candidates(job_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM title_candidates WHERE job_id = ? ORDER BY id",
        (job_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def select_title(title_id: int, job_id: int):
    """Ubah status judul yang dipilih menjadi 'Terseleksi'."""
    conn = get_connection()
    # Reset semua judul job ini ke Pending dulu
    conn.execute(
        "UPDATE title_candidates SET status = 'Pending' WHERE job_id = ? AND status = 'Terseleksi'",
        (job_id,)
    )
    conn.execute(
        "UPDATE title_candidates SET status = 'Terseleksi' WHERE id = ?",
        (title_id,)
    )
    conn.commit()
    conn.close()


def get_selected_title(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM title_candidates WHERE job_id = ? AND status = 'Terseleksi' LIMIT 1",
        (job_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Scripts ─────────────────────────────────────────────────────────────────

def save_script(job_id: int, title_id: int, content: str):
    char_count = len(content)
    conn = get_connection()
    conn.execute("""
        INSERT INTO scripts (job_id, title_id, content, char_count, status)
        VALUES (?,?,?,?,'draft')
        ON CONFLICT(job_id) DO UPDATE SET
            title_id = excluded.title_id,
            content = excluded.content,
            char_count = excluded.char_count,
            status = 'draft'
    """, (job_id, title_id, content, char_count))
    conn.commit()
    conn.close()


def get_script(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM scripts WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_script_content(job_id: int, content: str, status: str = 'saved'):
    conn = get_connection()
    conn.execute(
        "UPDATE scripts SET content = ?, char_count = ?, status = ? WHERE job_id = ?",
        (content, len(content), status, job_id)
    )
    conn.commit()
    conn.close()


# ─── Scenes ──────────────────────────────────────────────────────────────────

def save_scenes(job_id: int, scenes: list[dict]):
    """Simpan 45 scene. Hapus dulu scene lama untuk job ini."""
    conn = get_connection()
    conn.execute("DELETE FROM scenes WHERE job_id = ?", (job_id,))
    conn.executemany("""
        INSERT INTO scenes (job_id, scene_number, narasi, visual_prompt)
        VALUES (?,?,?,?)
    """, [(job_id, s['scene_number'], s['narasi'], s['visual_prompt']) for s in scenes])
    conn.commit()
    conn.close()


def get_scenes(job_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM scenes WHERE job_id = ? ORDER BY scene_number",
        (job_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_scene(scene_id: int, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [scene_id]
    conn = get_connection()
    conn.execute(f"UPDATE scenes SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_scenes_summary(job_id: int) -> dict:
    """Ringkasan status generate scene untuk progress bar."""
    conn = get_connection()
    rows = conn.execute("SELECT audio_status, image_status, video_status FROM scenes WHERE job_id = ?", (job_id,)).fetchall()
    conn.close()
    total = len(rows)
    audio_done = sum(1 for r in rows if r['audio_status'] == 'done')
    image_done = sum(1 for r in rows if r['image_status'] == 'done')
    video_done = sum(1 for r in rows if r['video_status'] == 'done')
    return {
        "total": total,
        "audio_done": audio_done,
        "image_done": image_done,
        "video_done": video_done,
    }
