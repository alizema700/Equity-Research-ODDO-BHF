#!/usr/bin/env python3
"""
SQLite to PostgreSQL Data Migration Script
Exports data from SQLite and generates PostgreSQL-compatible INSERT statements.

Usage:
    python migrate_data.py --sqlite-path ../data.db --output 002_seed_data.sql

Or import directly to Supabase:
    python migrate_data.py --sqlite-path ../data.db --supabase-url $SUPABASE_URL --supabase-key $SUPABASE_SERVICE_KEY
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from typing import Any, Dict, List, Optional

# Optional: Direct Supabase import
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


# Table migration order (respects foreign key dependencies)
MIGRATION_ORDER = [
    "src_clients",
    "src_stocks",
    "src_reports",
    "src_call_logs",
    "src_trade_executions",
    "src_portfolio_snapshots",
    "src_positions",
    "src_readership_events",
    "src_stock_prices",
    "src_stock_returns",
    "src_stock_volatility",
    "int_story_context_snapshot",
]

# Column mappings (SQLite -> PostgreSQL)
# Format: { "table": { "sqlite_col": "pg_col" or None to skip } }
COLUMN_MAPPINGS = {
    "src_clients": {
        "client_id": "client_id",
        "client_name": "client_name",
        "firm_name": "firm_name",
        "client_type": "client_type",
        "region": "region",
        "primary_contact_name": "primary_contact_name",
        "primary_contact_role": "primary_contact_role",
        "created_at": "created_at",
        "updated_at": "updated_at",
    },
    "src_stocks": {
        "stock_id": "stock_id",
        "company_name": "company_name",
        "ticker": "ticker",
        "sector": "sector",
        "region": "region",
        "market_cap_bucket": "market_cap_bucket",
        "theme_tag": "theme_tag",
        "created_at": "created_at",
    },
    "src_call_logs": {
        "call_id": "call_id",
        "client_id": "client_id",
        "call_timestamp": "call_timestamp",
        "direction": "direction",
        "duration_minutes": "duration_minutes",
        "discussed_company": "discussed_company",
        "discussed_sector": "discussed_sector",
        "related_report_id": "related_report_id",
        "notes_raw": "notes_raw",
        "stock_id": "stock_id",
    },
    "src_trade_executions": {
        "trade_id": "trade_id",
        "client_id": "client_id",
        "trade_timestamp": "trade_timestamp",
        "instrument_name": "instrument_name",
        "ticker": "ticker",
        "sector": "sector",
        "theme_tag": "theme_tag",
        "side": "side",
        "notional_bucket": "notional_bucket",
        "stock_id": "stock_id",
    },
    "src_portfolio_snapshots": {
        "snapshot_id": "snapshot_id",
        "client_id": "client_id",
        "as_of_date": "as_of_date",
        "source_system": "source_system",
        "created_at": "created_at",
    },
    "src_positions": {
        "position_id": "position_id",
        "snapshot_id": "snapshot_id",
        "stock_id": "stock_id",
        "quantity": "quantity",
        "avg_cost": "avg_cost",
        "market_value": "market_value",
        "weight": "weight",
        "currency": "currency",
    },
    "src_reports": {
        "report_id": "report_id",
        "report_code": "report_code",
        "publish_timestamp": "publish_timestamp",
        "report_type": "report_type",
        "sector": "sector",
        "company_name": "company_name",
        "ticker": "ticker",
        "title": "title",
        "summary_3bullets": "summary_3bullets",
        "stock_id": "stock_id",
    },
    "src_readership_events": {
        "event_id": "event_id",
        "client_id": "client_id",
        "report_id": "report_id",
        "read_timestamp": "read_timestamp",
    },
    "src_stock_prices": {
        "price_id": "price_id",
        "stock_id": "stock_id",
        "price_date": "price_date",
        "close": "close",
        "currency": "currency",
    },
    "src_stock_returns": {
        "return_id": "return_id",
        "stock_id": "stock_id",
        "return_date": "return_date",
        "daily_return": "daily_return",
    },
    "src_stock_volatility": {
        "vol_id": "vol_id",
        "stock_id": "stock_id",
        "vol_date": "vol_date",
        "vol_20d": "vol_20d",
        "vol_60d": "vol_60d",
    },
    "int_story_context_snapshot": {
        "snapshot_id": "snapshot_id",
        "client_id": "client_id",
        "created_at": "created_at",
        "trigger_type": "trigger_type",
        "trigger_ref_id": "trigger_ref_id",
        "context_json": "context_json",
    },
}


def escape_sql_string(value: Any) -> str:
    """Escape a value for PostgreSQL SQL insertion."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape single quotes by doubling them
        escaped = value.replace("'", "''")
        # Handle newlines and special characters
        escaped = escaped.replace("\n", "\\n").replace("\r", "\\r")
        return f"'{escaped}'"
    if isinstance(value, dict):
        # JSON/JSONB
        json_str = json.dumps(value).replace("'", "''")
        return f"'{json_str}'::jsonb"
    return f"'{str(value)}'"


def get_sqlite_data(conn: sqlite3.Connection, table: str) -> tuple:
    """Fetch all data from a SQLite table."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        if not rows:
            return [], []

        columns = rows[0].keys()
        data = [dict(row) for row in rows]
        return list(columns), data
    except Exception as e:
        print(f"Warning: Could not read table {table}: {e}")
        return [], []


def generate_insert_sql(
    table: str,
    columns: List[str],
    data: List[Dict[str, Any]],
    batch_size: int = 100
) -> str:
    """Generate PostgreSQL INSERT statements."""
    if not data:
        return f"-- No data for {table}\n"

    # Get column mapping
    mapping = COLUMN_MAPPINGS.get(table, {})

    # Filter and map columns
    pg_columns = []
    sqlite_columns = []
    for col in columns:
        pg_col = mapping.get(col, col)  # Default to same name
        if pg_col is not None:
            pg_columns.append(pg_col)
            sqlite_columns.append(col)

    if not pg_columns:
        return f"-- No mappable columns for {table}\n"

    sql_parts = [f"\n-- {table} ({len(data)} rows)\n"]

    # Process in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]

        values_list = []
        for row in batch:
            values = []
            for sqlite_col in sqlite_columns:
                val = row.get(sqlite_col)
                values.append(escape_sql_string(val))
            values_list.append(f"({', '.join(values)})")

        col_names = ", ".join(pg_columns)
        sql_parts.append(
            f"INSERT INTO {table} ({col_names}) VALUES\n" +
            ",\n".join(values_list) +
            "\nON CONFLICT DO NOTHING;\n"
        )

    return "\n".join(sql_parts)


def reset_sequences_sql(tables: List[str]) -> str:
    """Generate SQL to reset sequences after data import."""
    sql_parts = ["\n-- Reset sequences to max ID + 1\n"]

    sequence_map = {
        "src_clients": ("client_id", "src_clients_client_id_seq"),
        "src_stocks": ("stock_id", "src_stocks_stock_id_seq"),
        "src_call_logs": ("call_id", "src_call_logs_call_id_seq"),
        "src_trade_executions": ("trade_id", "src_trade_executions_trade_id_seq"),
        "src_portfolio_snapshots": ("snapshot_id", "src_portfolio_snapshots_snapshot_id_seq"),
        "src_positions": ("position_id", "src_positions_position_id_seq"),
        "src_reports": ("report_id", "src_reports_report_id_seq"),
        "src_readership_events": ("event_id", "src_readership_events_event_id_seq"),
        "src_stock_prices": ("price_id", "src_stock_prices_price_id_seq"),
        "src_stock_returns": ("return_id", "src_stock_returns_return_id_seq"),
        "src_stock_volatility": ("vol_id", "src_stock_volatility_vol_id_seq"),
        "int_story_context_snapshot": ("snapshot_id", "int_story_context_snapshot_snapshot_id_seq"),
    }

    for table in tables:
        if table in sequence_map:
            id_col, seq_name = sequence_map[table]
            sql_parts.append(
                f"SELECT setval('{seq_name}', COALESCE((SELECT MAX({id_col}) FROM {table}), 0) + 1, false);\n"
            )

    return "".join(sql_parts)


def migrate_to_sql_file(sqlite_path: str, output_path: str):
    """Export SQLite data to a PostgreSQL SQL file."""
    print(f"Reading from: {sqlite_path}")
    print(f"Writing to: {output_path}")

    conn = sqlite3.connect(sqlite_path)

    sql_parts = [
        "-- ============================================================================\n",
        "-- SALES INTELLIGENCE PLATFORM - Data Migration\n",
        f"-- Generated: {datetime.now().isoformat()}\n",
        "-- Source: SQLite database\n",
        "-- ============================================================================\n\n",
        "BEGIN;\n\n",
    ]

    migrated_tables = []

    for table in MIGRATION_ORDER:
        columns, data = get_sqlite_data(conn, table)

        if data:
            print(f"  {table}: {len(data)} rows")
            sql_parts.append(generate_insert_sql(table, columns, data))
            migrated_tables.append(table)
        else:
            print(f"  {table}: (empty or not found)")

    # Reset sequences
    sql_parts.append(reset_sequences_sql(migrated_tables))

    # Refresh materialized views
    sql_parts.append("\n-- Refresh materialized views\n")
    sql_parts.append("SELECT refresh_all_analytics_views();\n")

    sql_parts.append("\nCOMMIT;\n")

    conn.close()

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(sql_parts))

    print(f"\nMigration SQL written to: {output_path}")
    print(f"Total tables migrated: {len(migrated_tables)}")


def migrate_to_supabase(sqlite_path: str, supabase_url: str, supabase_key: str):
    """Directly import data to Supabase."""
    if not HAS_SUPABASE:
        print("Error: supabase-py is not installed. Run: pip install supabase")
        sys.exit(1)

    print(f"Reading from: {sqlite_path}")
    print(f"Importing to: {supabase_url}")

    supabase: Client = create_client(supabase_url, supabase_key)
    conn = sqlite3.connect(sqlite_path)

    for table in MIGRATION_ORDER:
        columns, data = get_sqlite_data(conn, table)

        if not data:
            print(f"  {table}: (empty or not found)")
            continue

        # Map columns
        mapping = COLUMN_MAPPINGS.get(table, {})
        mapped_data = []

        for row in data:
            mapped_row = {}
            for sqlite_col, val in row.items():
                pg_col = mapping.get(sqlite_col, sqlite_col)
                if pg_col is not None:
                    mapped_row[pg_col] = val
            mapped_data.append(mapped_row)

        # Insert in batches
        batch_size = 500
        for i in range(0, len(mapped_data), batch_size):
            batch = mapped_data[i:i + batch_size]
            try:
                supabase.table(table).upsert(batch).execute()
            except Exception as e:
                print(f"  Error inserting into {table}: {e}")
                continue

        print(f"  {table}: {len(data)} rows imported")

    conn.close()
    print("\nDirect import complete!")


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default=os.path.join(os.path.dirname(__file__), "..", "data.db"),
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "002_seed_data.sql"),
        help="Output SQL file path"
    )
    parser.add_argument(
        "--supabase-url",
        help="Supabase project URL (for direct import)"
    )
    parser.add_argument(
        "--supabase-key",
        help="Supabase service role key (for direct import)"
    )

    args = parser.parse_args()

    # Resolve paths
    sqlite_path = os.path.abspath(args.sqlite_path)

    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite database not found at {sqlite_path}")
        sys.exit(1)

    if args.supabase_url and args.supabase_key:
        migrate_to_supabase(sqlite_path, args.supabase_url, args.supabase_key)
    else:
        output_path = os.path.abspath(args.output)
        migrate_to_sql_file(sqlite_path, output_path)


if __name__ == "__main__":
    main()
