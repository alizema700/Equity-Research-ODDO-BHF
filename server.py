import os
import json
import sqlite3
from io import BytesIO
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import anyio

from dotenv import load_dotenv

# Load .env from the project directory (same folder as this file),
# so it works even if you start uvicorn from a different working directory.
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from openai import OpenAI

# Optional PDF generation (install: pip install reportlab)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    A4 = None
    mm = None
    canvas = None


# =========================
# Config
# =========================

DB_PATH = os.environ.get("CLIENT_DB_PATH", os.path.join(BASE_DIR, "data.db"))

# SQLite-only (built-in sqlite3; no aiosqlite / SQLAlchemy)
DATABASE_URL = f"sqlite:///{DB_PATH}"

OPENAI_API_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.environ.get("OPENAI_MODEL") or "gpt-5-mini").strip()

oa = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


app = FastAPI(title="Client Storytelling Prototype (DB-only)")

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database tables and views on startup."""
    await ensure_audit_table()
    await ensure_analytics_views()


# =========================
# Root endpoint - serve frontend
# =========================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend not found</h1><p>Place index.html in frontend/</p>")


# =========================
# DB helpers (sqlite3 only)
# =========================

def _sqlite_connect() -> sqlite3.Connection:
    # One connection per query (safe/simple). `row_factory` gives dict-like rows.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _query_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    params = params or {}
    conn = _sqlite_connect()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _query_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = params or {}
    conn = _sqlite_connect()
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


async def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    # Run blocking sqlite3 in a thread so FastAPI stays responsive.
    return await anyio.to_thread.run_sync(_query_one, sql, params)


async def fetch_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    # Run blocking sqlite3 in a thread so FastAPI stays responsive.
    return await anyio.to_thread.run_sync(_query_all, sql, params)


async def table_exists(table_name: str) -> bool:
    row = await fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:t",
        {"t": table_name},
    )
    return bool(row)


def _execute_write(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid."""
    params = params or {}
    conn = _sqlite_connect()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


async def execute_write(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    return await anyio.to_thread.run_sync(_execute_write, sql, params)


# =========================
# Audit Trail: ai_generation_history table
# =========================

async def ensure_audit_table():
    """Create ai_generation_history table if it doesn't exist."""
    await execute_write("""
        CREATE TABLE IF NOT EXISTS ai_generation_history (
            generation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            generation_type TEXT NOT NULL CHECK(generation_type IN ('shortlist', 'story')),
            model_used TEXT,
            ticker TEXT,
            mode TEXT,
            instruction TEXT,
            prompt_text TEXT,
            response_text TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            created_by TEXT DEFAULT 'system'
        )
    """)
    # Index for fast client lookups
    await execute_write("""
        CREATE INDEX IF NOT EXISTS idx_gen_history_client
        ON ai_generation_history(client_id, created_at DESC)
    """)


async def ensure_analytics_views():
    """Create enhanced analytics views for SQLite."""

    # 0a. Base view: Readership with days_diff
    await execute_write("""
        CREATE VIEW IF NOT EXISTS ana_readership_daysdiff AS
        SELECT
            e.event_id,
            e.client_id,
            e.report_id,
            r.report_code,
            r.report_type,
            r.sector AS report_sector,
            r.company_name AS report_company,
            r.ticker AS report_ticker,
            r.title AS report_title,
            r.publish_timestamp,
            e.read_timestamp,
            CAST(julianday(e.read_timestamp) - julianday(r.publish_timestamp) AS INTEGER) AS days_diff
        FROM src_readership_events e
        JOIN src_reports r ON r.report_id = e.report_id
    """)

    # 0b. Base view: Client Profile
    await execute_write("""
        CREATE VIEW IF NOT EXISTS int_client_profile AS
        SELECT
            c.client_id,
            c.client_name,
            c.firm_name,
            c.client_type,
            c.region,
            COALESCE(
                CASE
                    WHEN c.client_type LIKE '%Hedge%' THEN 'Aggressive'
                    WHEN c.client_type LIKE '%Pension%' THEN 'Conservative'
                    WHEN c.client_type LIKE '%Insurance%' THEN 'Conservative'
                    ELSE 'Moderate'
                END,
                'Moderate'
            ) AS risk_appetite,
            0.5 AS risk_score,
            COALESCE(
                CASE
                    WHEN c.client_type LIKE '%Hedge%' THEN 'Active Trading'
                    WHEN c.client_type LIKE '%Quant%' THEN 'Quantitative'
                    ELSE 'Fundamental'
                END,
                'Fundamental'
            ) AS investment_style,
            NULL AS dominant_topic,
            0.5 AS activity_score
        FROM src_clients c
    """)

    # 1. Portfolio Risk View
    await execute_write("""
        CREATE VIEW IF NOT EXISTS ana_client_portfolio_risk AS
        WITH latest_snap AS (
          SELECT client_id, MAX(snapshot_id) as snap_id
          FROM src_portfolio_snapshots
          GROUP BY client_id
        ),
        pos_data AS (
          SELECT
            ls.client_id,
            p.stock_id,
            p.weight,
            p.market_value,
            COALESCE(p.weight * 0.25, 0) AS weighted_vol
          FROM src_positions p
          JOIN latest_snap ls ON ls.snap_id = p.snapshot_id
        )
        SELECT
          client_id,
          ROUND(SUM(weighted_vol), 4) AS portfolio_volatility,
          MAX(weight) AS max_position_weight,
          COUNT(*) AS total_positions,
          SUM(CASE WHEN weight > 0.10 THEN 1 ELSE 0 END) AS large_positions,
          0.25 AS avg_stock_volatility,
          0.0 AS high_vol_exposure,
          CASE
            WHEN SUM(weighted_vol) >= 0.25 THEN 'High'
            WHEN SUM(weighted_vol) >= 0.15 THEN 'Medium'
            ELSE 'Low'
          END AS volatility_risk_level,
          CASE
            WHEN MAX(weight) >= 0.20 THEN 'Concentrated'
            WHEN MAX(weight) >= 0.10 THEN 'Moderate'
            ELSE 'Diversified'
          END AS concentration_risk_level
        FROM pos_data
        GROUP BY client_id
    """)

    # 2. Engagement Momentum View
    await execute_write("""
        CREATE VIEW IF NOT EXISTS ana_client_engagement_momentum AS
        WITH calls_recent AS (
          SELECT
            client_id,
            COUNT(*) as cnt,
            SUM(duration_minutes) as total_dur,
            AVG(duration_minutes) as avg_dur
          FROM src_call_logs
          WHERE julianday('now') - julianday(call_timestamp) <= 30
          GROUP BY client_id
        ),
        calls_prior AS (
          SELECT client_id, COUNT(*) as cnt
          FROM src_call_logs
          WHERE julianday('now') - julianday(call_timestamp) BETWEEN 31 AND 60
          GROUP BY client_id
        ),
        trades_recent AS (
          SELECT
            client_id,
            COUNT(*) as cnt,
            SUM(CASE WHEN side = 'Buy' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN notional_bucket = 'Large' THEN 1 ELSE 0 END) as large_trades
          FROM src_trade_executions
          WHERE julianday('now') - julianday(trade_timestamp) <= 30
          GROUP BY client_id
        ),
        trades_prior AS (
          SELECT client_id, COUNT(*) as cnt
          FROM src_trade_executions
          WHERE julianday('now') - julianday(trade_timestamp) BETWEEN 31 AND 60
          GROUP BY client_id
        )
        SELECT
          c.client_id,
          COALESCE(cr.cnt, 0) AS calls_last_30d,
          COALESCE(cp.cnt, 0) AS calls_prior_30d,
          ROUND(COALESCE(cr.avg_dur, 0), 1) AS avg_call_duration_30d,
          ROUND(1.0 * COALESCE(cr.cnt, 0) / NULLIF(COALESCE(cp.cnt, 0), 0), 2) AS call_momentum,
          COALESCE(tr.cnt, 0) AS trades_last_30d,
          COALESCE(tp.cnt, 0) AS trades_prior_30d,
          ROUND(1.0 * COALESCE(tr.cnt, 0) / NULLIF(COALESCE(tp.cnt, 0), 0), 2) AS trade_momentum,
          CASE WHEN tr.cnt > 0 THEN ROUND(1.0 * tr.buys / tr.cnt, 2) ELSE NULL END AS recent_buy_ratio,
          COALESCE(tr.large_trades, 0) AS large_trades_30d,
          ROUND(COALESCE(cr.total_dur, 0) * 0.1 + COALESCE(tr.cnt, 0) * 2.0 + COALESCE(tr.large_trades, 0) * 5.0, 1) AS engagement_score_30d,
          CASE
            WHEN COALESCE(cr.cnt, 0) > COALESCE(cp.cnt, 0) * 1.5 OR COALESCE(tr.cnt, 0) > COALESCE(tp.cnt, 0) * 1.5 THEN 'Accelerating'
            WHEN COALESCE(cr.cnt, 0) < COALESCE(cp.cnt, 0) * 0.5 AND COALESCE(tr.cnt, 0) < COALESCE(tp.cnt, 0) * 0.5 THEN 'Cooling Off'
            WHEN COALESCE(cr.cnt, 0) = 0 AND COALESCE(tr.cnt, 0) = 0 THEN 'Dormant'
            ELSE 'Stable'
          END AS engagement_trend
        FROM src_clients c
        LEFT JOIN calls_recent cr ON cr.client_id = c.client_id
        LEFT JOIN calls_prior cp ON cp.client_id = c.client_id
        LEFT JOIN trades_recent tr ON tr.client_id = c.client_id
        LEFT JOIN trades_prior tp ON tp.client_id = c.client_id
    """)

    # 3. Conviction View (SQLite compatible - no FULL OUTER JOIN)
    await execute_write("""
        CREATE VIEW IF NOT EXISTS ana_client_conviction AS
        WITH trade_focus AS (
          SELECT
            client_id,
            ticker,
            stock_id,
            COUNT(*) AS trade_count,
            SUM(CASE WHEN side = 'Buy' THEN 1 ELSE -1 END) AS net_direction,
            1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY client_id) AS focus_share
          FROM src_trade_executions
          WHERE ticker IS NOT NULL
          GROUP BY client_id, ticker, stock_id
        ),
        ranked AS (
          SELECT *,
            ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY trade_count DESC) AS rn
          FROM trade_focus
        )
        SELECT
          client_id,
          ticker AS top_conviction_stock,
          stock_id AS top_conviction_stock_id,
          trade_count,
          0 AS call_mentions,
          net_direction,
          ROUND(focus_share, 3) AS trade_concentration,
          trade_count AS conviction_score,
          0 AS bullish_mentions,
          0 AS bearish_mentions,
          CASE
            WHEN focus_share >= 0.25 THEN 'Very High'
            WHEN focus_share >= 0.15 THEN 'High'
            WHEN focus_share >= 0.08 THEN 'Moderate'
            ELSE 'Diversified'
          END AS conviction_level,
          CASE
            WHEN net_direction > 0 THEN 'Bullish'
            WHEN net_direction < 0 THEN 'Bearish'
            ELSE 'Neutral'
          END AS sentiment_signal
        FROM ranked
        WHERE rn = 1
    """)

    # 4. Readership Intelligence View
    await execute_write("""
        CREATE VIEW IF NOT EXISTS ana_client_readership_intelligence AS
        WITH read_stats AS (
          SELECT
            r.client_id,
            COUNT(*) AS total_reads,
            AVG(r.days_diff) AS avg_days_diff,
            COUNT(DISTINCT rp.sector) AS sector_breadth,
            SUM(CASE WHEN r.days_diff <= 1 THEN 1 ELSE 0 END) AS same_day_reads,
            SUM(CASE WHEN r.days_diff >= 7 THEN 1 ELSE 0 END) AS late_reads
          FROM ana_readership_daysdiff r
          LEFT JOIN src_reports rp ON rp.report_id = r.report_id
          GROUP BY r.client_id
        )
        SELECT
          client_id,
          total_reads,
          sector_breadth,
          'Research' AS preferred_report_type,
          NULL AS preferred_sector,
          ROUND(avg_days_diff, 1) AS avg_read_delay_days,
          ROUND(1.0 / (1 + avg_days_diff), 3) AS read_velocity_score,
          ROUND(1.0 * same_day_reads / total_reads, 2) AS same_day_read_ratio,
          ROUND(1.0 * late_reads / total_reads, 2) AS late_read_ratio,
          CASE
            WHEN avg_days_diff <= 1 THEN 'Immediate'
            WHEN avg_days_diff <= 3 THEN 'Fast'
            WHEN avg_days_diff <= 7 THEN 'Normal'
            ELSE 'Slow'
          END AS reader_speed_type,
          CASE
            WHEN sector_breadth >= 8 THEN 'Generalist'
            WHEN sector_breadth >= 4 THEN 'Multi-Sector'
            ELSE 'Specialist'
          END AS reader_breadth_type,
          ROUND(total_reads * 0.3 + (1.0 / (1 + avg_days_diff)) * 50 + sector_breadth * 2, 1) AS readership_quality_score
        FROM read_stats
    """)

    # 5. Enhanced Risk View
    await execute_write("""
        CREATE VIEW IF NOT EXISTS int_client_risk_enhanced AS
        SELECT
          cp.client_id,
          cp.risk_appetite AS original_risk_appetite,
          cp.risk_score AS original_risk_score,
          COALESCE(pr.portfolio_volatility, 0.20) AS portfolio_volatility,
          pr.volatility_risk_level,
          pr.max_position_weight,
          pr.concentration_risk_level,
          em.engagement_trend,
          em.trade_momentum,
          em.call_momentum,
          em.recent_buy_ratio,
          cv.top_conviction_stock,
          cv.conviction_level,
          cv.sentiment_signal,
          ri.reader_speed_type,
          ri.reader_breadth_type,
          ri.preferred_sector AS reading_focus_sector,
          0.5 AS enhanced_risk_score,
          CASE
            WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.25 THEN 'High'
            WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.15 THEN 'Medium'
            ELSE 'Low'
          END AS enhanced_risk_level,
          CASE
            WHEN em.engagement_trend = 'Accelerating' THEN 'Hot Lead - High Activity'
            WHEN em.engagement_trend = 'Cooling Off' THEN 'Re-engage - Activity Declining'
            WHEN em.engagement_trend = 'Dormant' THEN 'Wake Up Call Needed'
            ELSE 'Normal Engagement'
          END AS action_signal
        FROM int_client_profile cp
        LEFT JOIN ana_client_portfolio_risk pr ON pr.client_id = cp.client_id
        LEFT JOIN ana_client_engagement_momentum em ON em.client_id = cp.client_id
        LEFT JOIN ana_client_conviction cv ON cv.client_id = cp.client_id
        LEFT JOIN ana_client_readership_intelligence ri ON ri.client_id = cp.client_id
    """)


async def log_generation(
    client_id: int,
    generation_type: str,
    model_used: str,
    response_text: str,
    ticker: Optional[str] = None,
    mode: Optional[str] = None,
    instruction: Optional[str] = None,
    prompt_text: Optional[str] = None,
) -> int:
    """Save a generation to the audit trail. Returns generation_id."""
    return await execute_write(
        """
        INSERT INTO ai_generation_history
        (client_id, generation_type, model_used, ticker, mode, instruction, prompt_text, response_text)
        VALUES (:client_id, :generation_type, :model_used, :ticker, :mode, :instruction, :prompt_text, :response_text)
        """,
        {
            "client_id": client_id,
            "generation_type": generation_type,
            "model_used": model_used,
            "ticker": ticker,
            "mode": mode,
            "instruction": instruction,
            "prompt_text": prompt_text,
            "response_text": response_text,
        }
    )


async def get_generation_history(client_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get generation history for a client."""
    return await fetch_all(
        """
        SELECT
            generation_id,
            client_id,
            generation_type,
            model_used,
            ticker,
            mode,
            instruction,
            response_text,
            created_at,
            created_by
        FROM ai_generation_history
        WHERE client_id = :client_id
        ORDER BY created_at DESC
        LIMIT :limit
        """,
        {"client_id": client_id, "limit": limit}
    )


# =========================
# Core data access (matches your schema)
# =========================

async def search_clients(q: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fuzzy search for clients.
    - Splits query into terms
    - Matches each term against multiple fields
    - Scores by number of matching terms and field priority
    - Returns sorted by relevance
    """
    q = q.strip().lower()
    if not q:
        return []

    # Split into terms for fuzzy matching
    terms = [t.strip() for t in q.split() if t.strip()]
    if not terms:
        return []

    # Build dynamic WHERE clause for each term
    # Each term must match at least one field (AND logic for terms)
    # Within a term, match any field (OR logic for fields)
    where_parts = []
    params = {}

    for i, term in enumerate(terms):
        term_pattern = f"%{term}%"
        params[f"t{i}"] = term_pattern
        where_parts.append(f"""
            (LOWER(COALESCE(primary_contact_name, '')) LIKE :t{i}
             OR LOWER(COALESCE(client_name, '')) LIKE :t{i}
             OR LOWER(COALESCE(firm_name, '')) LIKE :t{i}
             OR LOWER(COALESCE(region, '')) LIKE :t{i}
             OR LOWER(COALESCE(client_type, '')) LIKE :t{i})
        """)

    where_clause = " AND ".join(where_parts)

    # Score calculation for relevance ranking:
    # - Exact match in primary_contact_name: highest priority
    # - Starts with term in any field: high priority
    # - Contains term: lower priority
    score_parts = []
    for i, term in enumerate(terms):
        exact_pattern = term
        starts_pattern = f"{term}%"
        params[f"exact{i}"] = exact_pattern
        params[f"starts{i}"] = starts_pattern
        score_parts.append(f"""
            CASE WHEN LOWER(primary_contact_name) = :exact{i} THEN 100 ELSE 0 END +
            CASE WHEN LOWER(firm_name) = :exact{i} THEN 80 ELSE 0 END +
            CASE WHEN LOWER(primary_contact_name) LIKE :starts{i} THEN 50 ELSE 0 END +
            CASE WHEN LOWER(firm_name) LIKE :starts{i} THEN 40 ELSE 0 END +
            CASE WHEN LOWER(primary_contact_name) LIKE :t{i} THEN 10 ELSE 0 END +
            CASE WHEN LOWER(firm_name) LIKE :t{i} THEN 8 ELSE 0 END +
            CASE WHEN LOWER(client_name) LIKE :t{i} THEN 5 ELSE 0 END
        """)

    score_calc = " + ".join(score_parts)
    params["limit"] = limit

    sql = f"""
        SELECT
            client_id,
            client_name,
            firm_name,
            client_type,
            region,
            primary_contact_name,
            primary_contact_role,
            ({score_calc}) AS relevance_score
        FROM src_clients
        WHERE {where_clause}
        ORDER BY relevance_score DESC, firm_name, primary_contact_name
        LIMIT :limit
    """

    return await fetch_all(sql, params)

async def get_client_header(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            client_id,
            client_name,
            firm_name,
            client_type,
            region,
            primary_contact_name,
            primary_contact_role
        FROM src_clients
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    if not row:
        raise ValueError(f"Client not found for client_id={client_id}")
    return row

async def get_client_profile(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            engagement_level,
            investment_style,
            risk_score,
            risk_appetite,
            dominant_topic,
            dominant_topic_share,
            dominant_theme,
            profile_confidence_score,
            profile_confidence_level,
            updated_at
        FROM int_client_profile
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_client_portfolio_summary(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            trade_count,
            top_sector,
            top_sector_share,
            top_theme,
            top_theme_share,
            buy_rate,
            side_bias,
            size_proxy,
            concentration_index,
            concentration_flag,
            direction_flag,
            activity_flag,
            size_aggressiveness_score,
            updated_at
        FROM int_client_portfolio_summary
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_client_availability(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            best_day,
            best_hour,
            best_time_window,
            availability_score,
            availability_confidence,
            call_count,
            avg_call_duration_min,
            updated_at
        FROM int_client_availability
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_latest_portfolio_snapshot_id(client_id: int) -> Optional[int]:
    row = await fetch_one(
        """
        SELECT snapshot_id
        FROM src_portfolio_snapshots
        WHERE client_id = :client_id
        ORDER BY as_of_date DESC, created_at DESC, snapshot_id DESC
        LIMIT 1
        """,
        {"client_id": client_id},
    )
    return int(row["snapshot_id"]) if row and row.get("snapshot_id") is not None else None

async def get_top_positions(client_id: int, limit: int = 15) -> List[Dict[str, Any]]:
    snap_id = await get_latest_portfolio_snapshot_id(client_id)
    if not snap_id:
        return []

    return await fetch_all(
        """
        SELECT
            p.position_id,
            p.snapshot_id,
            p.stock_id,
            s.ticker,
            s.company_name,
            s.sector,
            s.theme_tag,
            p.quantity,
            p.avg_cost,
            p.market_value,
            p.weight,
            p.currency
        FROM src_positions p
        JOIN src_stocks s ON s.stock_id = p.stock_id
        WHERE p.snapshot_id = :snapshot_id
        ORDER BY p.weight DESC, p.market_value DESC
        LIMIT :limit
        """,
        {"snapshot_id": snap_id, "limit": limit},
    )

async def get_recent_trades(client_id: int, limit: int = 15) -> List[Dict[str, Any]]:
    return await fetch_all(
        """
        SELECT
            trade_id,
            trade_timestamp,
            instrument_name,
            ticker,
            sector,
            theme_tag,
            side,
            notional_bucket,
            stock_id
        FROM src_trade_executions
        WHERE client_id = :client_id
        ORDER BY trade_timestamp DESC, trade_id DESC
        LIMIT :limit
        """,
        {"client_id": client_id, "limit": limit},
    )

async def get_recent_calls(client_id: int, limit: int = 8) -> List[Dict[str, Any]]:
    return await fetch_all(
        """
        SELECT
            c.call_id,
            c.call_timestamp,
            c.direction,
            c.duration_minutes,
            c.discussed_company,
            c.discussed_sector,
            c.related_report_id,
            c.notes_raw,
            c.stock_id,
            s.ticker AS stock_ticker,
            s.company_name AS stock_company_name,
            s.sector AS stock_sector,
            s.theme_tag AS stock_theme_tag
        FROM src_call_logs c
        LEFT JOIN src_stocks s ON s.stock_id = c.stock_id
        WHERE c.client_id = :client_id
        ORDER BY c.call_timestamp DESC, c.call_id DESC
        LIMIT :limit
        """,
        {"client_id": client_id, "limit": limit},
    )

async def get_recent_reads_daysdiff(client_id: int, limit: int = 12) -> List[Dict[str, Any]]:
    return await fetch_all(
        """
        SELECT
            event_id,
            report_id,
            report_code,
            report_type,
            report_sector,
            report_company,
            report_ticker,
            report_title,
            publish_timestamp,
            read_timestamp,
            days_diff
        FROM ana_readership_daysdiff
        WHERE client_id = :client_id
        ORDER BY read_timestamp DESC, event_id DESC
        LIMIT :limit
        """,
        {"client_id": client_id, "limit": limit},
    )

async def get_call_position_hints(client_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    return await fetch_all(
        """
        SELECT
            stock_id,
            ticker,
            mention_count,
            holding_hints,
            add_hints,
            reduce_hints,
            diversification_hints,
            risk_mgmt_hints,
            last_mention_ts
        FROM ana_call_position_hints
        WHERE client_id = :client_id
        ORDER BY mention_count DESC, last_mention_ts DESC
        LIMIT :limit
        """,
        {"client_id": client_id, "limit": limit},
    )

async def get_topic_signals(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            top_topic,
            top_topic_share,
            top_topic_count,
            last_signal_ts
        FROM ana_client_topic_signals
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_trade_summary(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            trade_count,
            top_sector,
            top_sector_share,
            top_theme,
            top_theme_share,
            buy_rate,
            side_bias,
            size_proxy,
            herfindahl_concentration,
            last_trade_ts
        FROM ana_client_trade_summary
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_call_patterns(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            call_count,
            avg_call_duration,
            best_weekday_num,
            best_hour,
            best_time_window,
            timing_confidence,
            last_call_ts
        FROM ana_client_call_patterns
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}

async def get_readership_summary(client_id: int) -> Dict[str, Any]:
    row = await fetch_one(
        """
        SELECT
            reads_n,
            avg_days_diff,
            late_read_ratio,
            last_read_ts
        FROM ana_client_readership_summary
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


# =========================
# ENHANCED ANALYTICS (new views)
# =========================

async def get_portfolio_risk(client_id: int) -> Dict[str, Any]:
    """Get portfolio-level risk metrics based on position volatility."""
    row = await fetch_one(
        """
        SELECT
            portfolio_volatility,
            max_position_weight,
            total_positions,
            large_positions,
            avg_stock_volatility,
            high_vol_exposure,
            volatility_risk_level,
            concentration_risk_level
        FROM ana_client_portfolio_risk
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


async def get_engagement_momentum(client_id: int) -> Dict[str, Any]:
    """Get 30d vs 60d engagement momentum."""
    row = await fetch_one(
        """
        SELECT
            calls_last_30d,
            calls_prior_30d,
            call_momentum,
            trades_last_30d,
            trades_prior_30d,
            trade_momentum,
            recent_buy_ratio,
            large_trades_30d,
            engagement_score_30d,
            engagement_trend
        FROM ana_client_engagement_momentum
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


async def get_conviction(client_id: int) -> Dict[str, Any]:
    """Get client's top conviction stock and sentiment."""
    row = await fetch_one(
        """
        SELECT
            top_conviction_stock,
            top_conviction_stock_id,
            trade_count,
            call_mentions,
            net_direction,
            trade_concentration,
            conviction_score,
            conviction_level,
            sentiment_signal
        FROM ana_client_conviction
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


async def get_readership_intelligence(client_id: int) -> Dict[str, Any]:
    """Get enhanced readership metrics (velocity, breadth, preferences)."""
    row = await fetch_one(
        """
        SELECT
            total_reads,
            sector_breadth,
            preferred_report_type,
            preferred_sector,
            avg_read_delay_days,
            read_velocity_score,
            same_day_read_ratio,
            reader_speed_type,
            reader_breadth_type,
            readership_quality_score
        FROM ana_client_readership_intelligence
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


async def get_enhanced_risk(client_id: int) -> Dict[str, Any]:
    """Get enhanced risk assessment combining all signals."""
    row = await fetch_one(
        """
        SELECT
            original_risk_appetite,
            enhanced_risk_level,
            enhanced_risk_score,
            portfolio_volatility,
            volatility_risk_level,
            concentration_risk_level,
            engagement_trend,
            trade_momentum,
            top_conviction_stock,
            conviction_level,
            sentiment_signal,
            action_signal
        FROM int_client_risk_enhanced
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    return row or {}


async def get_sector_momentum() -> List[Dict[str, Any]]:
    """Get market-wide sector flow signals."""
    return await fetch_all(
        """
        SELECT
            sector,
            trades_30d,
            buy_ratio,
            momentum,
            flow_signal,
            unique_clients
        FROM ana_sector_momentum
        ORDER BY trades_30d DESC
        LIMIT 10
        """
    )


# =========================
# Stock universe + market fields (based ONLY on your tables)
# =========================

async def get_stock_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    return await fetch_one(
        """
        SELECT
            stock_id,
            company_name,
            ticker,
            sector,
            region,
            market_cap_bucket,
            theme_tag,
            created_at
        FROM src_stocks
        WHERE ticker = :ticker
        """,
        {"ticker": ticker},
    )

async def get_stock_market_fields(stock_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Returns latest close + latest vol fields for each stock_id."""
    if not stock_ids:
        return {}

    out: Dict[int, Dict[str, Any]] = {int(sid): {} for sid in stock_ids}

    # SQLite (uses IN (...))
    placeholders = ",".join([":id" + str(i) for i in range(len(stock_ids))])
    id_params = {"id" + str(i): int(stock_ids[i]) for i in range(len(stock_ids))}

    prices = await fetch_all(
        f"""
        SELECT p.stock_id, p.close, p.currency, p.price_date
        FROM src_stock_prices p
        JOIN (
            SELECT stock_id, MAX(price_date) AS max_date
            FROM src_stock_prices
            WHERE stock_id IN ({placeholders})
            GROUP BY stock_id
        ) mx
          ON mx.stock_id = p.stock_id AND mx.max_date = p.price_date
        """,
        id_params,
    )

    vols = await fetch_all(
        f"""
        SELECT v.stock_id, v.vol_20d, v.vol_60d, v.vol_date
        FROM src_stock_volatility v
        JOIN (
            SELECT stock_id, MAX(vol_date) AS max_date
            FROM src_stock_volatility
            WHERE stock_id IN ({placeholders})
            GROUP BY stock_id
        ) mx
          ON mx.stock_id = v.stock_id AND mx.max_date = v.vol_date
        """,
        id_params,
    )

    for r in prices:
        out[int(r["stock_id"])].update(
            {
                "last_close": r.get("close"),
                "price_currency": r.get("currency"),
                "price_date": r.get("price_date"),
            }
        )
    for r in vols:
        out[int(r["stock_id"])].update(
            {
                "vol_20d": r.get("vol_20d"),
                "vol_60d": r.get("vol_60d"),
                "vol_date": r.get("vol_date"),
            }
        )
    return out

def vol_bucket(vol_60d: Optional[float]) -> str:
    # Only bucket if we have a number; otherwise unknown
    if vol_60d is None:
        return "unknown"
    try:
        v = float(vol_60d)
    except Exception:
        return "unknown"
    # simple buckets (no external market assumptions)
    if v < 0.20:
        return "low"
    if v < 0.35:
        return "medium"
    return "high"


# =========================
# Build client context (DB-only)
# =========================

async def build_avoid_tickers(client_id: int) -> List[str]:
    avoid = set()

    for h in await get_top_positions(client_id, limit=15):
        if h.get("ticker"):
            avoid.add(h["ticker"])

    for t in await get_recent_trades(client_id, limit=15):
        if t.get("ticker"):
            avoid.add(t["ticker"])

    return sorted(avoid)

async def build_candidate_universe(client_id: int, max_candidates: int = 120) -> List[Dict[str, Any]]:
    """
    Build a reasonable candidate set from src_stocks using client signals:
      - hinted tickers (ana_call_position_hints)
      - read tickers (ana_readership_daysdiff.report_ticker)
      - call-linked stock_id (src_call_logs.stock_id)
      - portfolio top_sector/top_theme (int_client_portfolio_summary)
      - plus diversifiers (other sectors)
    Returns list of stock rows from src_stocks.
    """
    prof = await get_client_profile(client_id)
    psum = await get_client_portfolio_summary(client_id)

    top_sector = (psum.get("top_sector") or "").strip()
    top_theme = (psum.get("top_theme") or "").strip()
    dom_theme = (prof.get("dominant_theme") or "").strip()

    avoid = set(await build_avoid_tickers(client_id))

    hinted = await get_call_position_hints(client_id, limit=30)
    hinted_tickers = [h.get("ticker") for h in hinted if h.get("ticker")]
    hinted_tickers = [t for t in hinted_tickers if t not in avoid]

    reads = await get_recent_reads_daysdiff(client_id, limit=20)
    read_tickers = [r.get("report_ticker") for r in reads if r.get("report_ticker")]
    read_tickers = [t for t in read_tickers if t not in avoid]

    calls = await get_recent_calls(client_id, limit=12)
    call_tickers = []
    call_stock_ids = []
    for c in calls:
        if c.get("stock_ticker"):
            call_tickers.append(c["stock_ticker"])
        if c.get("stock_id"):
            call_stock_ids.append(int(c["stock_id"]))
    call_tickers = [t for t in call_tickers if t and t not in avoid]

    # 1) Direct ticker picks
    ticker_pool = []
    for t in hinted_tickers[:25] + read_tickers[:25] + call_tickers[:25]:
        if t and t not in ticker_pool:
            ticker_pool.append(t)

    stocks_by_ticker: List[Dict[str, Any]] = []
    if ticker_pool:
        placeholders = ",".join([":t" + str(i) for i in range(len(ticker_pool))])
        params = {"t" + str(i): ticker_pool[i] for i in range(len(ticker_pool))}
        stocks_by_ticker = await fetch_all(
            f"""
            SELECT
                stock_id,
                company_name,
                ticker,
                sector,
                region,
                market_cap_bucket,
                theme_tag,
                created_at
            FROM src_stocks
            WHERE ticker IN ({placeholders})
            """,
            params,
        )

    # 2) Stock IDs from calls
    stocks_by_id: List[Dict[str, Any]] = []
    if call_stock_ids:
        unique_ids = []
        for sid in call_stock_ids:
            if sid not in unique_ids:
                unique_ids.append(sid)

        placeholders = ",".join([":id" + str(i) for i in range(len(unique_ids))])
        params = {"id" + str(i): int(unique_ids[i]) for i in range(len(unique_ids))}
        stocks_by_id = await fetch_all(
            f"""
            SELECT
                stock_id,
                company_name,
                ticker,
                sector,
                region,
                market_cap_bucket,
                theme_tag,
                created_at
            FROM src_stocks
            WHERE stock_id IN ({placeholders})
            """,
            params,
        )

    # 3) Sector/theme focused
    sector_theme_stocks: List[Dict[str, Any]] = []
    conds = []
    params: List[Any] = []
    if top_sector:
        conds.append(f"sector = :p{len(params)}")
        params.append(top_sector)
    if top_theme:
        conds.append(f"theme_tag = :p{len(params)}")
        params.append(top_theme)
    if dom_theme and dom_theme != top_theme:
        conds.append(f"theme_tag = :p{len(params)}")
        params.append(dom_theme)

    if conds:
        where = " OR ".join(conds)
        sector_theme_stocks = await fetch_all(
            f"""
            SELECT
                stock_id,
                company_name,
                ticker,
                sector,
                region,
                market_cap_bucket,
                theme_tag,
                created_at
            FROM src_stocks
            WHERE ({where})
            LIMIT 120
            """,
            {f"p{i}": params[i] for i in range(len(params))},
        )

    # 4) Diversifiers: pick from other sectors
    diversifiers: List[Dict[str, Any]] = []
    if top_sector:
        diversifiers = await fetch_all(
            """
            SELECT
                stock_id,
                company_name,
                ticker,
                sector,
                region,
                market_cap_bucket,
                theme_tag,
                created_at
            FROM src_stocks
            WHERE sector != :top_sector
            LIMIT 120
            """,
            {"top_sector": top_sector},
        )
    else:
        diversifiers = await fetch_all(
            """
            SELECT
                stock_id,
                company_name,
                ticker,
                sector,
                region,
                market_cap_bucket,
                theme_tag,
                created_at
            FROM src_stocks
            LIMIT 120
            """
        )

    # merge unique by stock_id, remove avoid tickers
    merged: Dict[int, Dict[str, Any]] = {}
    for group in (stocks_by_ticker, stocks_by_id, sector_theme_stocks, diversifiers):
        for s in group:
            sid = int(s["stock_id"])
            if s.get("ticker") in avoid:
                continue
            merged[sid] = s

    # trim
    out = list(merged.values())[:max_candidates]
    return out

async def build_client_context(client_id: int) -> Dict[str, Any]:
    client = await get_client_header(client_id)
    profile = await get_client_profile(client_id)
    portfolio_summary = await get_client_portfolio_summary(client_id)
    availability = await get_client_availability(client_id)

    top_positions = await get_top_positions(client_id, limit=15)
    recent_trades = await get_recent_trades(client_id, limit=15)
    recent_calls = await get_recent_calls(client_id, limit=10)

    reads_daysdiff = await get_recent_reads_daysdiff(client_id, limit=12)
    readership_summary = await get_readership_summary(client_id)

    call_hints = await get_call_position_hints(client_id, limit=20)
    topic_signals = await get_topic_signals(client_id)
    trade_summary = await get_trade_summary(client_id)
    call_patterns = await get_call_patterns(client_id)

    avoid_tickers = await build_avoid_tickers(client_id)

    # ENHANCED ANALYTICS (new)
    portfolio_risk = await get_portfolio_risk(client_id)
    engagement_momentum = await get_engagement_momentum(client_id)
    conviction = await get_conviction(client_id)
    readership_intel = await get_readership_intelligence(client_id)
    enhanced_risk = await get_enhanced_risk(client_id)

    return {
        "client": client,
        "profile": profile,
        "portfolio_summary": portfolio_summary,
        "availability": availability,
        "signals": {
            "recent_calls": recent_calls,
            "recent_trades": recent_trades,
            "recent_reads_daysdiff": reads_daysdiff,
            "readership_summary": readership_summary,
            "call_position_hints": call_hints,
            "topic_signals": topic_signals,
            "trade_summary": trade_summary,
            "call_patterns": call_patterns,
        },
        "holdings": {"top_positions": top_positions},
        "constraints": {"avoid_tickers": avoid_tickers},
        # NEW: Enhanced analytics
        "enhanced": {
            "portfolio_risk": portfolio_risk,
            "engagement_momentum": engagement_momentum,
            "conviction": conviction,
            "readership_intelligence": readership_intel,
            "risk_assessment": enhanced_risk,
        },
    }


# =========================
# OpenAI calls
# =========================

def llm_text(prompt: str) -> str:
    """Return plain text from the LLM.

    We intentionally use Chat Completions here for maximum compatibility with
    older `openai` Python SDK versions that do not support `oa.responses.*`.
    """
    if oa is None:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or export it in your shell.")

    resp = oa.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Follow instructions precisely."},
            {"role": "user", "content": prompt},
        ],
    )

    txt = (resp.choices[0].message.content or "").strip()
    return txt

def llm_json(prompt: str) -> Dict[str, Any]:
    """
    Best-effort JSON-only response. If the model returns text around JSON,
    we try to extract the first {...} block.
    """
    txt = llm_text(prompt)
    if not txt:
        raise ValueError("LLM returned empty output.")

    # direct parse first
    try:
        return json.loads(txt)
    except Exception:
        pass

    # try to extract JSON object
    start = txt.find("{")
    end = txt.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = txt[start:end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    raise ValueError("LLM did not return valid JSON.")


# =========================
# API models
# =========================

class ShortlistRequest(BaseModel):
    client_id: int
    instruction: Optional[str] = None
    max_candidates: int = 120
    max_words: int = 320

class StoryForStockRequest(BaseModel):
    client_id: int
    selected_ticker: str = Field(..., min_length=1)
    mode: str = "FULL"  # FULL or BULLETS
    instruction: Optional[str] = None
    max_words: int = 260


# =========================
# Prompt builders (DB-only, no hallucinated fields)
# =========================

def prompt_for_shortlist(
    client_ctx: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    candidates_market: Dict[int, Dict[str, Any]],
    instruction: str,
    max_words: int,
) -> str:
    """
    We ask for strict JSON output to drive the UI cards.
    """
    avoid = client_ctx.get("constraints", {}).get("avoid_tickers", []) or []

    # Compact candidate payload
    cand_payload = []
    for s in candidates:
        sid = int(s["stock_id"])
        m = candidates_market.get(sid, {})
        cand_payload.append(
            {
                "stock_id": sid,
                "ticker": s.get("ticker"),
                "company_name": s.get("company_name"),
                "sector": s.get("sector"),
                "theme_tag": s.get("theme_tag"),
                "region": s.get("region"),
                "market_cap_bucket": s.get("market_cap_bucket"),
                "last_close": m.get("last_close"),
                "price_currency": m.get("price_currency"),
                "price_date": m.get("price_date"),
                "vol_20d": m.get("vol_20d"),
                "vol_60d": m.get("vol_60d"),
                "vol_date": m.get("vol_date"),
            }
        )

    minimal_ctx = {
        "client": client_ctx.get("client", {}),
        "profile": client_ctx.get("profile", {}),
        "portfolio_summary": client_ctx.get("portfolio_summary", {}),
        "availability": client_ctx.get("availability", {}),
        "signals": client_ctx.get("signals", {}),
        "holdings": client_ctx.get("holdings", {}),
        "constraints": client_ctx.get("constraints", {}),
        "candidates": cand_payload,
    }

    return f"""
You are an AI equity sales assistant supporting a sell-side analyst.

CRITICAL DATA RULES
- Use ONLY the JSON provided.
- Do NOT invent facts. If missing, write null / "unknown".
- You MUST select stocks ONLY from candidates[].

GOAL
Create a client-personalized shortlist of exactly 10 stocks for this client, optimized for:
- client risk_appetite + investment_style
- their dominant exposure (portfolio_summary top_sector/top_theme) and diversification
- signals: call notes (notes_raw), call_position_hints, readership_daysdiff (days_diff), recent_trades
- avoid repeating holdings/recent trades unless clearly justified (avoid_tickers is provided)

OUTPUT (STRICT JSON ONLY)
Return ONE JSON object with exactly these keys:
{{
  "shortlist": [
    {{
      "stock_id": <int>,
      "ticker": <string>,
      "company_name": <string>,
      "sector": <string>,
      "theme_tag": <string|null>,
      "last_close": <number|null>,
      "price_currency": <string|null>,
      "vol_20d": <number|null>,
      "vol_60d": <number|null>,
      "vol_bucket": <"low"|"medium"|"high"|"unknown">,
      "why_bullets": [<string>, <string>, <string>]
    }},
    ...
  ],
  "top_picks": [<ticker1>, <ticker2>],
  "notes_for_analyst": [<string>, <string>, ...]
}}

RULES
- shortlist must have EXACTLY 10 items
- why_bullets must be EXACTLY 3 bullets per stock
- top_picks must be EXACTLY 2 tickers and must be in shortlist
- vol_bucket: decide using vol_60d only if present; else "unknown"
- Do NOT output markdown. Do NOT output extra keys. JSON only.

ANALYST INSTRUCTION:
{instruction}

JSON INPUT:
{json.dumps(minimal_ctx, ensure_ascii=False)}

Max length guidance: ~{max_words} words worth of JSON strings.
""".strip()

def prompt_for_story(
    client_ctx: Dict[str, Any],
    selected_stock: Dict[str, Any],
    instruction: str,
    mode: str,
    max_words: int,
    call_summary: Optional[Dict[str, Any]] = None,
    objection_section: Optional[str] = None,
) -> str:
    mode = (mode or "FULL").upper()
    if mode not in ("FULL", "BULLETS"):
        mode = "FULL"

    # Extract client profile for risk matching logic
    profile = client_ctx.get("profile", {})
    enhanced = client_ctx.get("enhanced", {})
    risk_assessment = enhanced.get("risk_assessment", {})
    portfolio_summary = client_ctx.get("portfolio_summary", {})

    # Determine client risk profile
    client_type = client_ctx.get("client", {}).get("client_type", "")
    risk_appetite = profile.get("risk_appetite", "Moderate")
    investment_style = profile.get("investment_style", "Fundamental")

    # Build risk matching guidance
    risk_guidance = ""
    if "Hedge" in client_type or risk_appetite in ["High", "Aggressive"]:
        risk_guidance = """
RISK PROFILE MATCH: This is a HIGH-RISK client (Hedge Fund / Aggressive).
- Prioritize stocks with higher volatility and upside potential
- Emphasize alpha generation, momentum plays, and asymmetric risk/reward
- If recommending a defensive stock, explicitly justify why (portfolio balance, hedging)
"""
    elif "Pension" in client_type or "Insurance" in client_type or risk_appetite in ["Low", "Conservative"]:
        risk_guidance = """
RISK PROFILE MATCH: This is a LOW-RISK client (Pension/Insurance / Conservative).
- Prioritize stable, dividend-paying, low-volatility stocks
- Emphasize capital preservation, steady income, quality metrics
- If recommending a higher-risk stock, justify the risk-adjusted return
"""
    else:
        risk_guidance = """
RISK PROFILE MATCH: This is a MODERATE-RISK client.
- Balance growth potential with risk management
- Consider both upside opportunity and downside protection
"""

    # For story, we pass a small structured pack (no giant universe)
    pack = {
        "client": client_ctx.get("client", {}),
        "profile": client_ctx.get("profile", {}),
        "portfolio_summary": client_ctx.get("portfolio_summary", {}),
        "availability": client_ctx.get("availability", {}),
        "signals": client_ctx.get("signals", {}),
        "holdings": client_ctx.get("holdings", {}),
        "constraints": client_ctx.get("constraints", {}),
        "enhanced": client_ctx.get("enhanced", {}),
        "selected_stock": selected_stock,
    }

    # Add pre-summarized call context if available
    if call_summary:
        pack["call_summary"] = call_summary

    # Build objection section
    objection_block = ""
    if objection_section:
        objection_block = f"""
{objection_section}

IMPORTANT: Address likely objections proactively in your story. Include a dedicated section:
"POTENTIAL OBJECTIONS & BEST ANSWERS" with 2-3 anticipated client pushbacks and how to handle them.
"""

    return f"""
You are an elite equity sales storyteller at ODDO BHF. Your job is to craft compelling,
personalized investment narratives that connect research insights to client needs.

{risk_guidance}

=== STORYTELLING FRAMEWORK ===

Your story MUST follow this structure:

1. THE HOOK (Opening)
   - Start with a compelling reason why this stock matters RIGHT NOW
   - Connect to a macro theme, sector trend, or catalyst the client cares about
   - Reference their recent reading behavior or call discussions if available

2. THE INVESTMENT THESIS
   Write a persuasive narrative explaining:
   - WHY this stock will perform well (fundamental drivers, catalysts, competitive advantages)
   - Use SPECIFIC data points from ODDO BHF research when available:
     * Analyst recommendations and price targets
     * Earnings momentum and margin expansion
     * Sector tailwinds and market positioning
   - If no research data available, focus on the strategic fit with client needs

3. CLIENT-SPECIFIC FIT
   Explain why this stock is PERFECT for THIS specific client:
   - Portfolio context: How it complements their current holdings (top_sector, concentration)
   - Risk alignment: Match to their risk_appetite and investment_style
   - Historical patterns: Reference similar successful investments they've made
   - Preference signals: Use their reading patterns, call discussions, and trade history

   EXAMPLES TO INCLUDE:
   - "You've shown interest in {sector} through your recent trades in {similar_stocks}..."
   - "This aligns with the {theme} focus you mentioned in your {date} call..."
   - "Given your {buy_rate}% buy rate in {sector}, this fits your conviction style..."

4. TIMING & CATALYSTS
   - Why NOW is the right time to act
   - Upcoming events (earnings, conferences, regulatory decisions)
   - Technical or momentum considerations if relevant

5. PORTFOLIO INTEGRATION
   - Suggested position sizing based on their portfolio concentration
   - How this affects their sector/theme exposure
   - Diversification benefits or concentration risks

6. OBJECTION HANDLING (CRITICAL)
   Anticipate and address 2-3 likely pushbacks based on:
   - Their risk profile and past concerns from calls
   - Current market conditions
   - Sector-specific risks

   Format:
   "You might ask: [Objection]"
   "Here's why that's actually an opportunity: [Response]"

7. CALL TO ACTION
   - 2 specific talking points for the sales call
   - 1 smart question to gauge client interest
   - Suggested next steps

=== CRITICAL DATA RULES ===
- Use ONLY the JSON provided - do NOT invent facts
- Reference SPECIFIC evidence from the data:
  * signals.recent_calls.notes_raw - actual call content
  * signals.recent_reads_daysdiff - what they're reading (days_diff shows urgency)
  * signals.recent_trades - their trading patterns
  * signals.call_position_hints - explicit position signals
  * enhanced.engagement_momentum - are they accelerating or cooling off?
  * enhanced.conviction - their top conviction stock and sentiment
- If data is missing, acknowledge it: "Based on available data..."

=== OUTPUT FORMAT ===
Mode FULL: Complete narrative story (~{max_words} words)
Mode BULLETS: 8-10 punchy bullet points for quick call prep

{objection_block}

=== STYLE GUIDELINES ===
- Confident but not arrogant
- Data-driven with specific numbers
- Client-centric (use "you" and "your portfolio")
- Actionable and forward-looking
- No generic statements - everything must be specific to THIS client

MODE: {mode}
ANALYST INSTRUCTION: {instruction if instruction else "None - use default storytelling framework"}

=== CLIENT DATA ===
{json.dumps(pack, ensure_ascii=False, indent=2)}
""".strip()


# =========================
# PDF export (Shortlist report)
# =========================

def _require_pdf_deps() -> None:
    if canvas is None or A4 is None or mm is None:
        raise RuntimeError(
            "PDF export requires 'reportlab'. Install it with: pip install reportlab"
        )


def build_shortlist_pdf_bytes(client_ctx: Dict[str, Any], shortlist_payload: Dict[str, Any]) -> bytes:
    """Build a simple A4 PDF with client essentials + shortlist. Returns raw PDF bytes."""
    _require_pdf_deps()

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    def _line(y: float, text: str, size: int = 11) -> float:
        # Avoid crashes on None / non-string values
        safe = str(text) if text is not None else ""
        c.setFont("Helvetica", size)
        c.drawString(20 * mm, y, safe)
        return y

    def _new_page() -> float:
        c.showPage()
        c.setFont("Helvetica", 11)
        return H - 20 * mm

    y = H - 20 * mm

    client = client_ctx.get("client", {}) or {}
    profile = client_ctx.get("profile", {}) or {}
    psum = client_ctx.get("portfolio_summary", {}) or {}
    avail = client_ctx.get("availability", {}) or {}

    _line(y, "Client Storytelling – Shortlist Report", 16); y -= 10 * mm
    _line(y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"); y -= 8 * mm

    _line(y, f"Client: {client.get('client_name','')}  | Firm: {client.get('firm_name','')}"); y -= 6 * mm
    _line(y, f"Type: {client.get('client_type','')}  | Region: {client.get('region','')}"); y -= 6 * mm
    _line(y, f"Primary contact: {client.get('primary_contact_name','')} ({client.get('primary_contact_role','')})"); y -= 10 * mm

    _line(y, "Key Profile Signals", 13); y -= 7 * mm
    _line(y, f"Investment style: {profile.get('investment_style','unknown')}"); y -= 6 * mm
    _line(y, f"Risk appetite: {profile.get('risk_appetite','unknown')} | Risk score: {profile.get('risk_score','unknown')}"); y -= 6 * mm
    _line(y, f"Dominant theme: {profile.get('dominant_theme','unknown')}"); y -= 10 * mm

    _line(y, "Portfolio Summary", 13); y -= 7 * mm
    _line(y, f"Top sector: {psum.get('top_sector','unknown')} ({psum.get('top_sector_share','unknown')})"); y -= 6 * mm
    _line(y, f"Top theme: {psum.get('top_theme','unknown')} ({psum.get('top_theme_share','unknown')})"); y -= 10 * mm

    _line(y, "Availability", 13); y -= 7 * mm
    _line(y, f"Best time window: {avail.get('best_time_window','unknown')} | Score: {avail.get('availability_score','unknown')}"); y -= 10 * mm

    top_picks = shortlist_payload.get("top_picks", []) or []
    notes = shortlist_payload.get("notes_for_analyst", []) or []
    shortlist = shortlist_payload.get("shortlist", []) or []

    _line(y, f"Top picks: {', '.join([str(x) for x in top_picks]) if top_picks else '—'}", 12); y -= 10 * mm

    _line(y, "Shortlist (10)", 13); y -= 7 * mm
    for i, it in enumerate(shortlist[:10], start=1):
        if y < 30 * mm:
            y = _new_page()

        t = it.get("ticker", "—") if isinstance(it, dict) else "—"
        name = it.get("company_name", "—") if isinstance(it, dict) else "—"
        sector = it.get("sector", "—") if isinstance(it, dict) else "—"
        vb = it.get("vol_bucket", "unknown") if isinstance(it, dict) else "unknown"
        _line(y, f"{i}. {t} – {name} | {sector} | vol: {vb}", 10); y -= 5 * mm

        why = it.get("why_bullets", []) if isinstance(it, dict) else []
        if not isinstance(why, list):
            why = []
        for b in why[:3]:
            if y < 30 * mm:
                y = _new_page()
            _line(y, f"   • {str(b)}", 9); y -= 4.5 * mm
        y -= 2 * mm

    if notes:
        if y < 50 * mm:
            y = _new_page()
        _line(y, "Notes for analyst", 13); y -= 7 * mm
        for n in notes[:12]:
            if y < 30 * mm:
                y = _new_page()
            _line(y, f"• {str(n)}", 10); y -= 5 * mm

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()

# =========================
# API endpoints
# =========================

@app.get("/", response_class=HTMLResponse)
def home():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Backend is running.</h3><p>Use /api/health or /api/search?q=...</p>"

@app.get("/api/health")
async def api_health():
    try:
        for t in [
            "src_clients", "src_stocks", "src_call_logs", "src_trade_executions",
            "src_stock_prices", "src_stock_volatility",
            "src_portfolio_snapshots", "src_positions",
            "ana_readership_daysdiff", "int_client_profile", "int_client_portfolio_summary",
        ]:
            _ = await table_exists(t)

        row = await fetch_one("SELECT COUNT(*) AS n FROM src_clients")
        return {
            "ok": True,
            "clients": row["n"] if row else None,
            "database_url": DATABASE_URL,
            "db_path": DB_PATH,
            "model": OPENAI_MODEL,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "database_url": DATABASE_URL,
            "db_path": DB_PATH,
            "model": OPENAI_MODEL,
        }

@app.get("/api/env")
def api_env():
    return {
        "openai_key_present": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL,
        "db_path": DB_PATH,
        "database_url": DATABASE_URL,
        "base_dir": BASE_DIR,
        "env_path": ENV_PATH,
        "cwd": os.getcwd(),
    }

@app.get("/api/search")
async def api_search(q: str = Query(..., min_length=1), limit: int = 20):
    try:
        return {"results": await search_clients(q, limit=limit)}
    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e), "results": []})

@app.get("/api/client/{client_id}")
async def api_client(client_id: int):
    """
    DB-only client view for UI (facts + constraints + last calls/trades/reads)
    This does NOT depend on int_story_context_snapshot.
    """
    try:
        ctx = await build_client_context(client_id)
        return {
            "client": ctx.get("client", {}),
            "profile": ctx.get("profile", {}),
            "portfolio_summary": ctx.get("portfolio_summary", {}),
            "availability": ctx.get("availability", {}),
            "signals": ctx.get("signals", {}),
            "holdings": ctx.get("holdings", {}),
            "constraints": ctx.get("constraints", {}),
            # Enhanced analytics (new views)
            "enhanced": ctx.get("enhanced", {}),
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e)})

@app.post("/api/shortlist")
async def api_shortlist(req: ShortlistRequest):
    """
    Returns structured shortlist for frontend cards:
      {
        "shortlist": [...10 items...],
        "top_picks": [...2 tickers...],
        "notes_for_analyst": [...],
        "shortlist_text": "<raw json text from LLM>"
      }
    """
    try:
        if oa is None:
            raise RuntimeError("OPENAI_API_KEY is missing or not loaded. Check /api/env and ensure .env is in the project folder next to server.py.")
        ctx = await build_client_context(req.client_id)

        instruction = (req.instruction or "").strip()
        if not instruction:
            instruction = "Rank 10 stocks that fit this client; prioritize personalization + diversification; use calls/reads (days_diff) as evidence."

        candidates = await build_candidate_universe(req.client_id, max_candidates=req.max_candidates)

        if not candidates:
            raise ValueError("No candidates found in src_stocks for shortlist generation.")

        stock_ids = [int(s["stock_id"]) for s in candidates]
        market = await get_stock_market_fields(stock_ids)

        # Build prompt
        prompt = prompt_for_shortlist(
            client_ctx=ctx,
            candidates=candidates,
            candidates_market=market,
            instruction=instruction,
            max_words=req.max_words,
        )

        # LLM JSON
        data = llm_json(prompt)

        shortlist = data.get("shortlist")
        top_picks = data.get("top_picks")
        notes = data.get("notes_for_analyst")

        if not isinstance(shortlist, list) or len(shortlist) != 10:
            raise ValueError("LLM JSON invalid: shortlist must be a list of exactly 10 items.")
        if not isinstance(top_picks, list) or len(top_picks) != 2:
            raise ValueError("LLM JSON invalid: top_picks must be a list of exactly 2 tickers.")

        # Post-process: ensure vol_bucket exists and is consistent with vol_60d
        cleaned = []
        for item in shortlist:
            if not isinstance(item, dict):
                continue
            # Ensure required keys exist (don’t invent values; default to None/unknown)
            sid = item.get("stock_id")
            try:
                sid_int = int(sid) if sid is not None else None
            except Exception:
                sid_int = None

            v60 = item.get("vol_60d")
            bucket = item.get("vol_bucket")
            if bucket not in ("low", "medium", "high", "unknown"):
                bucket = vol_bucket(v60)

            why = item.get("why_bullets")
            if not isinstance(why, list):
                why = []
            # Keep exactly 3 strings
            why = [str(x) for x in why][:3]
            while len(why) < 3:
                why.append("unknown (insufficient evidence in provided signals)")

            cleaned.append(
                {
                    "stock_id": sid_int,
                    "ticker": item.get("ticker"),
                    "company_name": item.get("company_name"),
                    "sector": item.get("sector"),
                    "theme_tag": item.get("theme_tag"),
                    "last_close": item.get("last_close"),
                    "price_currency": item.get("price_currency"),
                    "vol_20d": item.get("vol_20d"),
                    "vol_60d": item.get("vol_60d"),
                    "vol_bucket": bucket,
                    "why_bullets": why,
                }
            )

        # Keep only 10
        cleaned = cleaned[:10]

        # Log to audit trail
        shortlist_text = json.dumps(data, ensure_ascii=False, indent=2)
        generation_id = await log_generation(
            client_id=req.client_id,
            generation_type="shortlist",
            model_used=OPENAI_MODEL,
            response_text=shortlist_text,
            instruction=instruction,
        )

        return {
            "client_id": req.client_id,
            "model": OPENAI_MODEL,
            "shortlist": cleaned,
            "top_picks": top_picks,
            "notes_for_analyst": notes if isinstance(notes, list) else [],
            "shortlist_text": shortlist_text,
            "generation_id": generation_id,
        }

    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e)})

@app.post("/api/story_for_stock")
async def api_story_for_stock(req: StoryForStockRequest):
    try:
        if oa is None:
            raise RuntimeError("OPENAI_API_KEY is missing or not loaded. Check /api/env and ensure .env is in the project folder next to server.py.")
        ctx = await build_client_context(req.client_id)

        instruction = (req.instruction or "").strip()
        if not instruction:
            instruction = "Make it persuasive and client-specific. Use WHAT/WWHY and cite calls/reads/trades evidence."

        ticker = req.selected_ticker.strip()
        stock = await get_stock_by_ticker(ticker)
        if not stock:
            raise ValueError(f"Ticker '{ticker}' not found in src_stocks.")

        # Enrich selected stock with latest close + latest vol
        market = await get_stock_market_fields([int(stock["stock_id"])])
        m = market.get(int(stock["stock_id"]), {})
        selected_stock = {
            **stock,
            "last_close": m.get("last_close"),
            "price_currency": m.get("price_currency"),
            "price_date": m.get("price_date"),
            "vol_20d": m.get("vol_20d"),
            "vol_60d": m.get("vol_60d"),
            "vol_bucket": vol_bucket(m.get("vol_60d")),
            "vol_date": m.get("vol_date"),
        }

        prompt = prompt_for_story(
            client_ctx=ctx,
            selected_stock=selected_stock,
            instruction=instruction,
            mode=req.mode,
            max_words=req.max_words,
        )

        story = llm_text(prompt)

        # Log to audit trail
        generation_id = await log_generation(
            client_id=req.client_id,
            generation_type="story",
            model_used=OPENAI_MODEL,
            response_text=story,
            ticker=ticker,
            mode=(req.mode or "FULL").upper(),
            instruction=instruction,
        )

        return {
            "client_id": req.client_id,
            "model": OPENAI_MODEL,
            "selected_ticker": ticker,
            "mode": (req.mode or "FULL").upper(),
            "story": story,
            "generation_id": generation_id,
        }

    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e)})


# =========================
# History endpoint (audit trail)
# =========================

@app.get("/api/history/{client_id}")
async def api_history(client_id: int, limit: int = 50):
    """Get generation history for a client (for compliance/audit)."""
    try:
        history = await get_generation_history(client_id, limit=limit)
        return {"client_id": client_id, "history": history}
    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e), "history": []})


# PDF endpoint for shortlist report
@app.post("/api/shortlist.pdf")
async def api_shortlist_pdf(req: ShortlistRequest):
    """Generate a PDF report (client essentials + shortlist) and return it as a download."""
    try:
        _require_pdf_deps()

        # Reuse the same shortlist generator to ensure the PDF matches the UI
        payload = await api_shortlist(req)
        if isinstance(payload, JSONResponse):
            return payload
        if isinstance(payload, dict) and payload.get("error"):
            return JSONResponse(status_code=200, content=payload)

        ctx = await build_client_context(req.client_id)
        pdf_bytes = build_shortlist_pdf_bytes(ctx, payload)

        filename = f"shortlist_client_{req.client_id}.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        return JSONResponse(status_code=200, content={"error": str(e)})