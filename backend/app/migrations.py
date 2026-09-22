"""Small SQLite schema migration helpers.

This project intentionally avoids a full migration framework to keep local setup
simple. The function below only applies backwards-compatible fixes needed when a
user already has an older `algo_study.db` file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy.engine import make_url

from .config import BACKEND_DIR, DATABASE_URL


DATABASE_PATH = BACKEND_DIR / "algo_study.db"


USER_SCOPED_TABLES = {
    "progress": "problem_id",
    "problem_notes": "problem_id",
    "submissions": "problem_id",
    "review_logs": "problem_id",
    "ai_hints": "problem_id",
}

UNIQUE_USER_PROBLEM_TABLES = ("progress", "problem_notes")


MIGRATION_MARKER = "2026-05-18-v4-hardening"


def _record_migration(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        "INSERT OR IGNORE INTO schema_migrations(name) VALUES (?)",
        (MIGRATION_MARKER,),
    )


def _sqlite_path_from_database_url() -> Path | None:
    """Return the SQLite file path used by SQLAlchemy, or None for non-file DBs."""
    try:
        url = make_url(DATABASE_URL)
    except Exception:
        return DATABASE_PATH

    if url.drivername.split("+")[0] != "sqlite":
        return None

    database = url.database
    if not database or database == ":memory:":
        return None
    return Path(database)


def _table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def _first_user_id(cursor: sqlite3.Cursor) -> int:
    if not _table_exists(cursor, "users"):
        return 1
    cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    return int(row[0]) if row else 1


def _table_sql(cursor: sqlite3.Cursor, table_name: str) -> str:
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    row = cursor.fetchone()
    return row[0] or "" if row else ""


def _has_legacy_problem_unique(sql: str) -> bool:
    normalized = " ".join(sql.replace("\n", " ").split()).lower()
    return "unique (problem_id)" in normalized or "unique(problem_id)" in normalized


def _rebuild_progress_without_legacy_unique(cursor: sqlite3.Cursor, default_user_id: int) -> None:
    sql = _table_sql(cursor, "progress")
    if not _has_legacy_problem_unique(sql):
        return

    cursor.execute("ALTER TABLE progress RENAME TO progress_old")
    cursor.execute(
        """
        CREATE TABLE progress (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            status VARCHAR,
            attempts INTEGER,
            solved_count INTEGER,
            first_solved_at DATETIME,
            last_attempt_at DATETIME,
            last_review_at DATETIME,
            next_review_at DATETIME,
            mastery_level INTEGER,
            confidence INTEGER,
            is_favorite BOOLEAN,
            is_archived BOOLEAN,
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(problem_id) REFERENCES problems (id)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO progress (
            id, user_id, problem_id, status, attempts, solved_count,
            first_solved_at, last_attempt_at, last_review_at, next_review_at,
            mastery_level, confidence, is_favorite, is_archived
        )
        SELECT
            id,
            COALESCE(user_id, ?),
            problem_id,
            COALESCE(status, 'Not Started'),
            COALESCE(attempts, 0),
            COALESCE(solved_count, 0),
            first_solved_at,
            last_attempt_at,
            last_review_at,
            next_review_at,
            COALESCE(mastery_level, 0),
            COALESCE(confidence, 0),
            COALESCE(is_favorite, 0),
            COALESCE(is_archived, 0)
        FROM progress_old
        """,
        (default_user_id,),
    )
    cursor.execute("DROP TABLE progress_old")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_progress_user_id ON progress(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_progress_problem_id ON progress(problem_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_progress_status ON progress(status)")


def _rebuild_problem_notes_without_legacy_unique(cursor: sqlite3.Cursor, default_user_id: int) -> None:
    sql = _table_sql(cursor, "problem_notes")
    if not _has_legacy_problem_unique(sql):
        return

    cursor.execute("ALTER TABLE problem_notes RENAME TO problem_notes_old")
    cursor.execute(
        """
        CREATE TABLE problem_notes (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            idea TEXT,
            key_points TEXT,
            complexity TEXT,
            pitfalls TEXT,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(problem_id) REFERENCES problems (id)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO problem_notes (
            id, user_id, problem_id, idea, key_points, complexity,
            pitfalls, summary, created_at, updated_at
        )
        SELECT
            id,
            COALESCE(user_id, ?),
            problem_id,
            COALESCE(idea, ''),
            COALESCE(key_points, ''),
            COALESCE(complexity, ''),
            COALESCE(pitfalls, ''),
            COALESCE(summary, ''),
            created_at,
            updated_at
        FROM problem_notes_old
        """,
        (default_user_id,),
    )
    cursor.execute("DROP TABLE problem_notes_old")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_problem_notes_user_id ON problem_notes(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_problem_notes_problem_id ON problem_notes(problem_id)")


def _deduplicate_user_problem_rows(cursor: sqlite3.Cursor, table_name: str) -> None:
    if not _table_exists(cursor, table_name):
        return
    if not (_column_exists(cursor, table_name, "user_id") and _column_exists(cursor, table_name, "problem_id")):
        return
    cursor.execute(
        f"""
        DELETE FROM {table_name}
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM {table_name}
            GROUP BY user_id, problem_id
        )
        """
    )


def migrate_sqlite_database(db_path: Path | None = None) -> None:
    """Apply safe migrations for old local SQLite files.

    SQLAlchemy's `create_all()` creates missing tables but does not alter already
    existing tables. Older AlgoStudy databases were single-user and therefore
    lack `user_id` on user-scoped tables. Without this migration, authenticated
    routes fail with `no such column: <table>.user_id`.
    """

    if db_path is None:
        db_path = _sqlite_path_from_database_url()
    if db_path is None or not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        default_user_id = _first_user_id(cursor)
        _rebuild_progress_without_legacy_unique(cursor, default_user_id)
        _rebuild_problem_notes_without_legacy_unique(cursor, default_user_id)

        for table_name in USER_SCOPED_TABLES:
            if not _table_exists(cursor, table_name):
                continue

            if not _column_exists(cursor, table_name, "user_id"):
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER")
                cursor.execute(
                    f"UPDATE {table_name} SET user_id = ? WHERE user_id IS NULL",
                    (default_user_id,),
                )

            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS ix_{table_name}_user_id ON {table_name}(user_id)"
            )

        if _table_exists(cursor, "progress"):
            cursor.execute("UPDATE progress SET status = 'Not Started' WHERE status IS NULL")
            cursor.execute("UPDATE progress SET attempts = 0 WHERE attempts IS NULL")
            cursor.execute("UPDATE progress SET solved_count = 0 WHERE solved_count IS NULL")
            cursor.execute("UPDATE progress SET mastery_level = 0 WHERE mastery_level IS NULL")
            cursor.execute("UPDATE progress SET confidence = 0 WHERE confidence IS NULL")
            cursor.execute("UPDATE progress SET is_favorite = 0 WHERE is_favorite IS NULL")
            cursor.execute("UPDATE progress SET is_archived = 0 WHERE is_archived IS NULL")

        for table_name in UNIQUE_USER_PROBLEM_TABLES:
            _deduplicate_user_problem_rows(cursor, table_name)
            if _table_exists(cursor, table_name):
                cursor.execute(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{table_name}_user_problem "
                    f"ON {table_name}(user_id, problem_id)"
                )

        if _table_exists(cursor, "templates"):
            if not _column_exists(cursor, "templates", "owner_user_id"):
                cursor.execute("ALTER TABLE templates ADD COLUMN owner_user_id INTEGER")
            if not _column_exists(cursor, "templates", "is_system"):
                cursor.execute("ALTER TABLE templates ADD COLUMN is_system BOOLEAN")
                cursor.execute("UPDATE templates SET is_system = 1 WHERE is_system IS NULL")
            else:
                cursor.execute("UPDATE templates SET is_system = 1 WHERE is_system IS NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_templates_owner_user_id ON templates(owner_user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_templates_is_system ON templates(is_system)")

        _record_migration(cursor)
        conn.commit()


if __name__ == "__main__":
    migrate_sqlite_database()
    print("SQLite migrations applied.")
