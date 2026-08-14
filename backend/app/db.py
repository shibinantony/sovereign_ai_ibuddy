from __future__ import annotations

import json
import re
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

DEFAULT_TITLE = "New conversation"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def title_from_message(content: str, maximum: int = 58) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    compact = re.sub(r"^[#>*_`\-\s]+", "", compact)
    if not compact:
        return DEFAULT_TITLE
    if len(compact) <= maximum:
        return compact
    shortened = compact[: maximum - 1].rsplit(" ", 1)[0].rstrip(".,:;!?")
    return f"{shortened or compact[: maximum - 1]}…"


class ConversationNotFoundError(KeyError):
    pass


class ConversationStore:
    """Small SQLite repository with one connection per operation.

    sqlite3 connections are intentionally short lived. This makes the repository safe
    across FastAPI's worker threads while WAL mode keeps reads responsive during writes.
    """

    def __init__(self, database_path: Path | str):
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._schema_lock = threading.Lock()
        self.initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._schema_lock, self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_conversations_updated
                    ON conversations(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
                    ON messages(conversation_id, created_at ASC);
                """
            )

    def create_conversation(self, title: str | None = None) -> dict[str, Any]:
        conversation_id = uuid4().hex
        timestamp = utc_now()
        normalized_title = (title or "").strip() or DEFAULT_TITLE
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, normalized_title, timestamp, timestamp),
            )
        return self.get_conversation(conversation_id)

    def list_conversations(
        self, *, query: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        parameters: list[Any] = []
        where = ""
        if query and query.strip():
            where = "WHERE c.title LIKE ? ESCAPE '\\'"
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            parameters.append(f"%{escaped}%")
        parameters.append(max(1, min(limit, 500)))
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) AS message_count,
                    COALESCE((
                        SELECT content
                        FROM messages latest
                        WHERE latest.conversation_id = c.id
                        ORDER BY latest.created_at DESC, latest.rowid DESC
                        LIMIT 1
                    ), '') AS preview
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                {where}
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return [self._summary_from_row(row) for row in rows]

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            connection.execute("BEGIN")
            try:
                row = connection.execute(
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.id) AS message_count,
                        COALESCE((
                            SELECT content
                            FROM messages latest
                            WHERE latest.conversation_id = c.id
                            ORDER BY latest.created_at DESC, latest.rowid DESC
                            LIMIT 1
                        ), '') AS preview
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    WHERE c.id = ?
                    GROUP BY c.id
                    """,
                    (conversation_id,),
                ).fetchone()
                if row is None:
                    raise ConversationNotFoundError(conversation_id)
                message_rows = connection.execute(
                    """
                    SELECT id, role, content, sources_json, created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC, rowid ASC
                    """,
                    (conversation_id,),
                ).fetchall()
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        detail = self._summary_from_row(row)
        detail["messages"] = [self._message_from_row(item) for item in message_rows]
        return detail

    def rename_conversation(self, conversation_id: str, title: str) -> dict[str, Any]:
        timestamp = utc_now()
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (title.strip(), timestamp, conversation_id),
            )
            if cursor.rowcount == 0:
                raise ConversationNotFoundError(conversation_id)
        return self.get_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
            if cursor.rowcount == 0:
                raise ConversationNotFoundError(conversation_id)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Sequence[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported message role: {role}")
        message_id = uuid4().hex
        timestamp = utc_now()
        encoded_sources = json.dumps(list(sources or []), ensure_ascii=False)
        with self._connection() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                conversation = connection.execute(
                    "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
                ).fetchone()
                if conversation is None:
                    raise ConversationNotFoundError(conversation_id)
                connection.execute(
                    """
                    INSERT INTO messages (
                        id, conversation_id, role, content, sources_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        encoded_sources,
                        timestamp,
                    ),
                )
                next_title = conversation["title"]
                if role == "user" and next_title == DEFAULT_TITLE:
                    user_count = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM messages
                        WHERE conversation_id = ? AND role = 'user'
                        """,
                        (conversation_id,),
                    ).fetchone()[0]
                    if user_count == 1:
                        next_title = title_from_message(content)
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (next_title, timestamp, conversation_id),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return {
            "id": message_id,
            "role": role,
            "content": content,
            "sources": list(sources or []),
            "created_at": timestamp,
        }

    def update_assistant_message(
        self,
        conversation_id: str,
        message_id: str,
        content: str,
        sources: Sequence[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Finalize a preallocated assistant message idempotently."""
        encoded_sources = json.dumps(list(sources or []), ensure_ascii=False)
        updated_at = utc_now()
        with self._connection() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT id, role, created_at
                    FROM messages
                    WHERE id = ? AND conversation_id = ?
                    """,
                    (message_id, conversation_id),
                ).fetchone()
                if row is None:
                    raise ConversationNotFoundError(conversation_id)
                if row["role"] != "assistant":
                    raise ValueError("Only assistant messages can be finalized")
                connection.execute(
                    """
                    UPDATE messages
                    SET content = ?, sources_json = ?
                    WHERE id = ? AND conversation_id = ?
                    """,
                    (content, encoded_sources, message_id, conversation_id),
                )
                connection.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (updated_at, conversation_id),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return {
            "id": message_id,
            "role": "assistant",
            "content": content,
            "sources": list(sources or []),
            "created_at": row["created_at"],
        }

    def context_messages(self, conversation_id: str, *, limit: int) -> list[dict[str, str]]:
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if exists is None:
                raise ConversationNotFoundError(conversation_id)
            rows = connection.execute(
                """
                SELECT role, content
                FROM (
                    SELECT role, content, created_at, rowid
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT ?
                ) recent
                ORDER BY created_at ASC, rowid ASC
                """,
                (conversation_id, max(1, limit)),
            ).fetchall()
        messages = [{"role": row["role"], "content": row["content"]} for row in rows]
        # Never begin a model context with an orphaned assistant response when the
        # message window cuts through the middle of a turn.
        while messages and messages[0]["role"] != "user":
            messages.pop(0)
        return messages

    @staticmethod
    def _summary_from_row(row: sqlite3.Row) -> dict[str, Any]:
        preview = re.sub(r"\s+", " ", row["preview"] or "").strip()
        if len(preview) > 120:
            preview = f"{preview[:119].rstrip()}…"
        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": int(row["message_count"]),
            "preview": preview,
        }

    @staticmethod
    def _message_from_row(row: sqlite3.Row) -> dict[str, Any]:
        try:
            sources = json.loads(row["sources_json"] or "[]")
        except json.JSONDecodeError:
            sources = []
        return {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "sources": sources if isinstance(sources, list) else [],
            "created_at": row["created_at"],
        }
