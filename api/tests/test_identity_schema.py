from __future__ import annotations

from pathlib import Path

from api.app.database import get_connection, initialize_database


def _table_names(db_path: Path) -> set[str]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    return {row["name"] for row in rows}


def _index_names(db_path: Path) -> set[str]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    return {row["name"] for row in rows}


def _column_names(db_path: Path, table: str) -> list[str]:
    with get_connection(db_path) as connection:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in rows]


def test_initialize_creates_identity_tables(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    tables = _table_names(db_path)
    assert {"employees", "magic_link_tokens", "sessions"} <= tables


def test_employees_columns(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    columns = _column_names(db_path, "employees")
    assert columns == [
        "id",
        "name",
        "email",
        "employer",
        "created_at",
        "created_by",
        "notes",
    ]


def test_magic_link_tokens_columns_and_unique(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    columns = _column_names(db_path, "magic_link_tokens")
    assert columns == [
        "id",
        "token_hash",
        "employee_id",
        "created_at",
        "expires_at",
        "revoked_at",
        "last_used_at",
        "use_count",
    ]

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO employees (id, name, employer, created_at) VALUES ('e1', 'Jamie', 'Hendrickson', '2026-05-01T00:00:00+00:00')"
        )
        connection.execute(
            "INSERT INTO magic_link_tokens (id, token_hash, employee_id, created_at, expires_at) "
            "VALUES ('t1', 'hashA', 'e1', '2026-05-01T00:00:00+00:00', '2026-05-08T00:00:00+00:00')"
        )
        connection.commit()

        try:
            connection.execute(
                "INSERT INTO magic_link_tokens (id, token_hash, employee_id, created_at, expires_at) "
                "VALUES ('t2', 'hashA', 'e1', '2026-05-01T00:00:00+00:00', '2026-05-08T00:00:00+00:00')"
            )
            connection.commit()
        except Exception as exc:
            assert "UNIQUE" in str(exc).upper()
        else:
            raise AssertionError("expected UNIQUE constraint on token_hash")


def test_magic_link_cascade_on_employee_delete(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO employees (id, name, employer, created_at) VALUES ('e1', 'Jamie', 'Hendrickson', '2026-05-01T00:00:00+00:00')"
        )
        connection.execute(
            "INSERT INTO magic_link_tokens (id, token_hash, employee_id, created_at, expires_at) "
            "VALUES ('t1', 'hashA', 'e1', '2026-05-01T00:00:00+00:00', '2026-05-08T00:00:00+00:00')"
        )
        connection.commit()

        connection.execute("DELETE FROM employees WHERE id = 'e1'")
        connection.commit()

        remaining = connection.execute(
            "SELECT COUNT(*) AS n FROM magic_link_tokens WHERE employee_id = 'e1'"
        ).fetchone()
    assert remaining["n"] == 0


def test_sessions_columns(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    columns = _column_names(db_path, "sessions")
    assert columns == [
        "token_hash",
        "role",
        "subject_id",
        "created_at",
        "expires_at",
        "last_seen_at",
    ]


def test_identity_indexes_present(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)

    indexes = _index_names(db_path)
    assert "idx_employees_employer" in indexes
    assert "idx_magic_link_tokens_employee" in indexes
    assert "idx_sessions_expires_at" in indexes
    assert "idx_sessions_role_subject" in indexes


def test_initialize_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "hma.db"
    initialize_database(db_path)
    initialize_database(db_path)

    tables = _table_names(db_path)
    assert {"employees", "magic_link_tokens", "sessions"} <= tables


def test_initialize_migrates_draft_score_to_nullable_without_data_loss(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE assessments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                scoring_mode TEXT NOT NULL DEFAULT 'ai_assisted',
                total_score INTEGER NOT NULL DEFAULT 0,
                score_band TEXT NOT NULL DEFAULT 'High opportunity for improvement',
                consent_notice_version TEXT,
                consent_accepted_at TEXT,
                consent_scope_json TEXT,
                privacy_posture TEXT NOT NULL DEFAULT 'voluntary_ergonomic_wellness',
                retention_expires_at TEXT
            );
            CREATE TABLE draft_captures (
                id TEXT PRIMARY KEY,
                assessment_id TEXT NOT NULL,
                movement_key TEXT NOT NULL,
                side TEXT NOT NULL,
                client_capture_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                detected_faults_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                pose_trace_json TEXT,
                quality_json TEXT,
                confidence REAL NOT NULL,
                source TEXT NOT NULL,
                original_filename TEXT,
                content_type TEXT,
                file_size_bytes INTEGER NOT NULL,
                video_path TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                video_deleted_at TEXT,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
                UNIQUE (assessment_id, movement_key, side),
                UNIQUE (assessment_id, client_capture_id)
            );
            INSERT INTO assessments (id, name, created_at) VALUES ('a1', 'Legacy', '2026-01-01');
            INSERT INTO draft_captures (
                id, assessment_id, movement_key, side, client_capture_id, score,
                detected_faults_json, metrics_json, confidence, source,
                file_size_bytes, created_at, expires_at
            ) VALUES (
                'd1', 'a1', 'trunk_rotation', 'left', 'c1', 2,
                '[]', '{}', 0.5, 'fallback', 10, '2026-01-01', '2026-01-08'
            );
            """
        )

    initialize_database(db_path)

    with get_connection(db_path) as connection:
        score_column = next(
            row for row in connection.execute("PRAGMA table_info(draft_captures)")
            if row["name"] == "score"
        )
        preserved = connection.execute(
            "SELECT id, score FROM draft_captures WHERE id = 'd1'"
        ).fetchone()
        connection.execute(
            "UPDATE draft_captures SET score = NULL WHERE id = 'd1'"
        )
        connection.commit()

    assert score_column["notnull"] == 0
    assert dict(preserved) == {"id": "d1", "score": 2}
