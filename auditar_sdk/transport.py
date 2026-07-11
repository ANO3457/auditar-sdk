"""Local SQLite-backed transport for air-gapped deployments."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import List, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from auditar_sdk.exceptions import QueueFullError
from auditar_sdk.models import BatchRequest, DecisionRecord


class LocalTransport:
    """Append-only local queue backed by SQLite."""

    def __init__(self, db_path: str | Path = "auditar_queue.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_rows = 100_000
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    ts TEXT NOT NULL,
                    model_name TEXT,
                    model_version TEXT,
                    use_case TEXT,
                    body TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ts ON decisions(ts)"
            )
            conn.commit()
        finally:
            conn.close()

    def enqueue(self, decision: DecisionRecord) -> None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM decisions"
            ).fetchone()
            if row["count"] >= self.max_rows:
                raise QueueFullError(
                    f"Queue is full at {self.max_rows} records."
                )
            conn.execute(
                "INSERT INTO decisions(id, ts, model_name, model_version, use_case, body) VALUES(?, ?, ?, ?, ?, ?)",
                (
                    str(decision.decision_id),
                    decision.timestamp.isoformat(),
                    decision.model_name,
                    decision.model_version,
                    decision.use_case,
                    decision.model_dump_json(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def drain(self, batch_size: int = 1000) -> List[DecisionRecord]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, body FROM decisions ORDER BY ts LIMIT ?",
                (batch_size,),
            ).fetchall()
            decisions = []
            ids = []
            for row in rows:
                ids.append(row["id"])
                decisions.append(
                    DecisionRecord.model_validate_json(row["body"])
                )
            if ids:
                placeholders = ",".join("?" for _ in ids)
                conn.execute(
                    f"DELETE FROM decisions WHERE id IN ({placeholders})",
                    ids,
                )
                conn.commit()
            return decisions
        finally:
            conn.close()

    def pending_count(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM decisions"
            ).fetchone()
            return row["count"]
        finally:
            conn.close()
