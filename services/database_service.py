import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "lectures.db"


def _get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            audio_blob BLOB,
            duration REAL,
            transcript TEXT,
            summary TEXT,
            notes TEXT,
            flashcards TEXT,
            quiz TEXT,
            topic TEXT,
            keywords TEXT,
            word_count INTEGER,
            processing_time REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_lecture(title, audio_blob, duration, transcript, summary, notes,
                 flashcards, quiz, topic, keywords, word_count, processing_time):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lectures
        (title, audio_blob, duration, transcript, summary, notes, flashcards, quiz,
         topic, keywords, word_count, processing_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        sqlite3.Binary(audio_blob),
        duration,
        transcript,
        summary,
        notes,
        json.dumps(flashcards),
        json.dumps(quiz),
        topic,
        json.dumps(keywords),
        word_count,
        processing_time,
        datetime.now().isoformat()
    ))
    lecture_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lecture_id


def get_all_lectures():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, duration, topic, keywords, word_count, processing_time, created_at
        FROM lectures ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    lectures = []
    for row in rows:
        data = dict(row)
        if data.get("keywords"):
            try:
                data["keywords"] = json.loads(data["keywords"])
            except Exception:
                data["keywords"] = []
        lectures.append(data)
    return lectures


def get_lecture_by_id(lecture_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    for field in ("flashcards", "quiz", "keywords"):
        if data.get(field):
            try:
                data[field] = json.loads(data[field])
            except Exception:
                data[field] = []
        else:
            data[field] = []
    return data


def delete_lecture(lecture_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total_lectures,
            SUM(duration) as total_duration,
            SUM(word_count) as total_words
        FROM lectures
    """)
    row = cursor.fetchone()
    stats = dict(row) if row else {"total_lectures": 0, "total_duration": 0, "total_words": 0}

    cursor.execute("SELECT flashcards FROM lectures WHERE flashcards IS NOT NULL")
    total_flashcards = 0
    for (fc_json,) in cursor.fetchall():
        try:
            total_flashcards += len(json.loads(fc_json))
        except Exception:
            pass

    cursor.execute("SELECT quiz FROM lectures WHERE quiz IS NOT NULL")
    total_quiz = 0
    for (quiz_json,) in cursor.fetchall():
        try:
            total_quiz += len(json.loads(quiz_json))
        except Exception:
            pass

    conn.close()
    stats["total_flashcards"] = total_flashcards
    stats["total_quiz_questions"] = total_quiz
    return stats
