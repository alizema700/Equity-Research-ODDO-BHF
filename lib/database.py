"""
Database Abstraction Layer

Supports both SQLite (development) and PostgreSQL/Supabase (production).
Configured via environment variables.
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager

# Environment-based configuration
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()  # "sqlite" or "postgres"
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH = os.environ.get("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "..", "data.db"))


class DatabaseClient:
    """Abstract database client supporting SQLite and PostgreSQL."""

    def __init__(self):
        self.db_type = DB_TYPE
        self._connection = None

    @contextmanager
    def get_connection(self):
        """Get a database connection (context manager)."""
        if self.db_type == "postgres":
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            import sqlite3

            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def query_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return one row."""
        params = params or {}

        with self.get_connection() as conn:
            if self.db_type == "postgres":
                cursor = conn.cursor()
                # Convert :param to %(param)s for psycopg2
                pg_sql = self._convert_params(sql)
                cursor.execute(pg_sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                cursor = conn.execute(sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None

    def query_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return all rows."""
        params = params or {}

        with self.get_connection() as conn:
            if self.db_type == "postgres":
                cursor = conn.cursor()
                pg_sql = self._convert_params(sql)
                cursor.execute(pg_sql, params)
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            else:
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(r) for r in rows]

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a statement and return affected rows."""
        params = params or {}

        with self.get_connection() as conn:
            if self.db_type == "postgres":
                cursor = conn.cursor()
                pg_sql = self._convert_params(sql)
                cursor.execute(pg_sql, params)
                return cursor.rowcount
            else:
                cursor = conn.execute(sql, params)
                return cursor.rowcount

    def _convert_params(self, sql: str) -> str:
        """Convert SQLite :param syntax to PostgreSQL %(param)s syntax."""
        import re
        return re.sub(r":(\w+)", r"%(\1)s", sql)


# Singleton instance
db = DatabaseClient()


# ============================================================================
# AI Generation History (Compliance)
# ============================================================================

def log_ai_generation(
    client_id: int,
    generation_type: str,
    model_tier: str,
    model_used: str,
    prompt_text: str,
    response_text: Optional[str] = None,
    selected_ticker: Optional[str] = None,
    shortlist_tickers: Optional[List[str]] = None,
    instruction: Optional[str] = None,
    latency_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[str]:
    """
    Log an AI generation to the compliance history table.
    Returns the generated ID or None if logging fails.
    """
    import hashlib

    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()

    if db.db_type == "postgres":
        sql = """
        INSERT INTO ai_generation_history (
            client_id, user_id, session_id, generation_type, model_tier, model_used,
            prompt_hash, prompt_text, response_text, selected_ticker, shortlist_tickers,
            instruction, latency_ms, success, error_message
        ) VALUES (
            %(client_id)s, %(user_id)s, %(session_id)s, %(generation_type)s, %(model_tier)s, %(model_used)s,
            %(prompt_hash)s, %(prompt_text)s, %(response_text)s, %(selected_ticker)s, %(shortlist_tickers)s,
            %(instruction)s, %(latency_ms)s, %(success)s, %(error_message)s
        ) RETURNING id
        """

        params = {
            "client_id": client_id,
            "user_id": user_id,
            "session_id": session_id,
            "generation_type": generation_type,
            "model_tier": model_tier,
            "model_used": model_used,
            "prompt_hash": prompt_hash,
            "prompt_text": prompt_text,
            "response_text": response_text,
            "selected_ticker": selected_ticker,
            "shortlist_tickers": shortlist_tickers,
            "instruction": instruction,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_message,
        }

        try:
            result = db.query_one(sql, params)
            return str(result["id"]) if result else None
        except Exception as e:
            print(f"Failed to log AI generation: {e}")
            return None
    else:
        # SQLite fallback - store in ana_audit_log if available
        try:
            import uuid
            request_id = str(uuid.uuid4())

            sql = """
            INSERT INTO ana_audit_log (
                request_id, user_id, client_id, action, model, prompt_masked, output_masked, latency_ms, created_at
            ) VALUES (
                :request_id, :user_id, :client_id, :action, :model, :prompt, :output, :latency_ms, :created_at
            )
            """

            db.execute(sql, {
                "request_id": request_id,
                "user_id": 0 if user_id is None else user_id,
                "client_id": client_id,
                "action": generation_type,
                "model": model_used,
                "prompt": prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text,
                "output": (response_text[:500] + "...") if response_text and len(response_text) > 500 else response_text,
                "latency_ms": latency_ms or 0,
                "created_at": datetime.now().isoformat(),
            })

            return request_id
        except Exception as e:
            print(f"Failed to log AI generation (SQLite): {e}")
            return None


# ============================================================================
# Semantic Search (pgvector)
# ============================================================================

class SemanticSearch:
    """Semantic search using pgvector embeddings."""

    def __init__(self, embedding_model: str = "placeholder"):
        """
        Initialize semantic search.

        Note: Actual embedding model (e.g., Mistral) will be injected later.
        For now, this is a placeholder that returns empty results on SQLite.
        """
        self.embedding_model = embedding_model
        self.embedding_dimension = 1024  # Mistral embedding dimension

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for text.

        TODO: Replace with actual Mistral embedding call when API key is available.
        """
        # Placeholder - returns None until Mistral is integrated
        return None

    def search_call_notes(
        self,
        query: str,
        client_id: Optional[int] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search call notes using semantic similarity.

        Args:
            query: Search query text
            client_id: Optional filter by client
            limit: Maximum results
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of matching call logs with similarity scores
        """
        if db.db_type != "postgres":
            # Fallback to keyword search on SQLite
            return self._keyword_search_calls(query, client_id, limit)

        embedding = self._get_embedding(query)
        if not embedding:
            return self._keyword_search_calls(query, client_id, limit)

        # pgvector similarity search
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        sql = """
        SELECT
            c.call_id,
            c.client_id,
            c.call_timestamp,
            c.notes_raw,
            c.discussed_company,
            c.discussed_sector,
            s.ticker,
            s.company_name,
            1 - (c.notes_embedding <=> %(embedding)s::vector) AS similarity
        FROM src_call_logs c
        LEFT JOIN src_stocks s ON s.stock_id = c.stock_id
        WHERE c.notes_embedding IS NOT NULL
          AND 1 - (c.notes_embedding <=> %(embedding)s::vector) > %(threshold)s
        """

        params = {
            "embedding": embedding_str,
            "threshold": threshold,
            "limit": limit,
        }

        if client_id:
            sql += " AND c.client_id = %(client_id)s"
            params["client_id"] = client_id

        sql += " ORDER BY c.notes_embedding <=> %(embedding)s::vector LIMIT %(limit)s"

        return db.query_all(sql, params)

    def _keyword_search_calls(
        self,
        query: str,
        client_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search for SQLite or when embeddings unavailable."""
        query_like = f"%{query.strip().lower()}%"

        if db.db_type == "postgres":
            sql = """
            SELECT
                c.call_id,
                c.client_id,
                c.call_timestamp,
                c.notes_raw,
                c.discussed_company,
                c.discussed_sector,
                s.ticker,
                s.company_name
            FROM src_call_logs c
            LEFT JOIN src_stocks s ON s.stock_id = c.stock_id
            WHERE LOWER(COALESCE(c.notes_raw, '')) LIKE %(query)s
               OR LOWER(COALESCE(c.discussed_company, '')) LIKE %(query)s
            """
        else:
            sql = """
            SELECT
                c.call_id,
                c.client_id,
                c.call_timestamp,
                c.notes_raw,
                c.discussed_company,
                c.discussed_sector,
                s.ticker,
                s.company_name
            FROM src_call_logs c
            LEFT JOIN src_stocks s ON s.stock_id = c.stock_id
            WHERE LOWER(COALESCE(c.notes_raw, '')) LIKE :query
               OR LOWER(COALESCE(c.discussed_company, '')) LIKE :query
            """

        params = {"query": query_like, "limit": limit}

        if client_id:
            if db.db_type == "postgres":
                sql += " AND c.client_id = %(client_id)s"
            else:
                sql += " AND c.client_id = :client_id"
            params["client_id"] = client_id

        sql += f" ORDER BY c.call_timestamp DESC LIMIT {limit}"

        return db.query_all(sql, params)

    def search_reports(
        self,
        query: str,
        sector: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search reports using semantic similarity."""
        if db.db_type != "postgres":
            return self._keyword_search_reports(query, sector, limit)

        embedding = self._get_embedding(query)
        if not embedding:
            return self._keyword_search_reports(query, sector, limit)

        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        sql = """
        SELECT
            r.report_id,
            r.report_code,
            r.title,
            r.ticker,
            r.company_name,
            r.sector,
            r.report_type,
            r.publish_timestamp,
            r.summary_3bullets,
            1 - (r.content_embedding <=> %(embedding)s::vector) AS similarity
        FROM src_reports r
        WHERE r.content_embedding IS NOT NULL
          AND 1 - (r.content_embedding <=> %(embedding)s::vector) > %(threshold)s
        """

        params = {
            "embedding": embedding_str,
            "threshold": threshold,
            "limit": limit,
        }

        if sector:
            sql += " AND r.sector = %(sector)s"
            params["sector"] = sector

        sql += " ORDER BY r.content_embedding <=> %(embedding)s::vector LIMIT %(limit)s"

        return db.query_all(sql, params)

    def _keyword_search_reports(
        self,
        query: str,
        sector: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search for reports."""
        query_like = f"%{query.strip().lower()}%"

        if db.db_type == "postgres":
            sql = """
            SELECT
                r.report_id,
                r.report_code,
                r.title,
                r.ticker,
                r.company_name,
                r.sector,
                r.report_type,
                r.publish_timestamp,
                r.summary_3bullets
            FROM src_reports r
            WHERE LOWER(COALESCE(r.title, '')) LIKE %(query)s
               OR LOWER(COALESCE(r.summary_3bullets, '')) LIKE %(query)s
               OR LOWER(COALESCE(r.company_name, '')) LIKE %(query)s
            """
        else:
            sql = """
            SELECT
                r.report_id,
                r.report_code,
                r.title,
                r.ticker,
                r.company_name,
                r.sector,
                r.report_type,
                r.publish_timestamp,
                r.summary_3bullets
            FROM src_reports r
            WHERE LOWER(COALESCE(r.title, '')) LIKE :query
               OR LOWER(COALESCE(r.summary_3bullets, '')) LIKE :query
               OR LOWER(COALESCE(r.company_name, '')) LIKE :query
            """

        params = {"query": query_like, "limit": limit}

        if sector:
            if db.db_type == "postgres":
                sql += " AND r.sector = %(sector)s"
            else:
                sql += " AND r.sector = :sector"
            params["sector"] = sector

        sql += f" ORDER BY r.publish_timestamp DESC LIMIT {limit}"

        return db.query_all(sql, params)


# Singleton instance
semantic_search = SemanticSearch()
