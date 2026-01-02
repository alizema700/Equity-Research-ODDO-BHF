# PostgreSQL Schema Proposal for Sales Intelligence Platform

## Executive Summary

This document proposes the migration of the existing SQLite database to PostgreSQL (Supabase-compatible) for the Enterprise Sales Intelligence Platform. The schema includes:

- **12 Source Tables** (read-only client data)
- **10 Materialized Views** (analytics & integration layers)
- **2 New Tables** (AI history & embeddings)
- **pgvector Extension** for semantic search

---

## 1. Extensions

```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
```

---

## 2. Enums (Type Safety)

```sql
-- Client type classification
CREATE TYPE client_type_enum AS ENUM (
    'Asset Manager',
    'Hedge Fund',
    'Family Office',
    'Insurance',
    'Pension Fund',
    'Sovereign Wealth',
    'Private Bank',
    'Other'
);

-- Geographic regions
CREATE TYPE region_enum AS ENUM (
    'DACH',
    'France',
    'Benelux',
    'Nordics',
    'UK',
    'Southern Europe',
    'Other EU',
    'Non-EU'
);

-- Trade direction
CREATE TYPE trade_side_enum AS ENUM ('Buy', 'Sell');

-- Call direction
CREATE TYPE call_direction_enum AS ENUM ('Inbound', 'Outbound');

-- Market cap buckets
CREATE TYPE market_cap_enum AS ENUM ('Micro', 'Small', 'Mid', 'Large', 'Mega');

-- Notional size buckets
CREATE TYPE notional_bucket_enum AS ENUM ('Small', 'Medium', 'Large');

-- Report types
CREATE TYPE report_type_enum AS ENUM (
    'Initiation',
    'Update',
    'Flash',
    'Sector',
    'Thematic',
    'Strategy'
);

-- Risk appetite levels
CREATE TYPE risk_appetite_enum AS ENUM ('Conservative', 'Moderate', 'Aggressive');

-- Investment styles
CREATE TYPE investment_style_enum AS ENUM ('Value', 'Growth', 'GARP', 'Income', 'Momentum');

-- Confidence levels
CREATE TYPE confidence_level_enum AS ENUM ('Low', 'Medium', 'High');

-- AI model tiers
CREATE TYPE ai_model_tier_enum AS ENUM ('FAST', 'DETAILED');

-- AI generation types
CREATE TYPE ai_generation_type_enum AS ENUM ('shortlist', 'story', 'bullets', 'summary', 'search');
```

---

## 3. Source Tables (Read-Only Core Data)

### 3.1 src_clients
```sql
CREATE TABLE src_clients (
    client_id           SERIAL PRIMARY KEY,
    client_name         VARCHAR(255),
    firm_name           VARCHAR(255) NOT NULL,
    client_type         client_type_enum,
    region              region_enum,
    primary_contact_name VARCHAR(255),
    primary_contact_role VARCHAR(100),
    email               VARCHAR(255),
    phone               VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_client_firm_contact UNIQUE (firm_name, primary_contact_name)
);

-- Indexes for search
CREATE INDEX idx_clients_firm_name ON src_clients USING gin (firm_name gin_trgm_ops);
CREATE INDEX idx_clients_contact_name ON src_clients USING gin (primary_contact_name gin_trgm_ops);
CREATE INDEX idx_clients_region ON src_clients (region);
CREATE INDEX idx_clients_type ON src_clients (client_type);
```

### 3.2 src_stocks
```sql
CREATE TABLE src_stocks (
    stock_id            SERIAL PRIMARY KEY,
    company_name        VARCHAR(255) NOT NULL,
    ticker              VARCHAR(20) NOT NULL UNIQUE,
    isin                VARCHAR(12),
    sector              VARCHAR(100),
    region              region_enum,
    market_cap_bucket   market_cap_enum,
    theme_tag           VARCHAR(100),
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_ticker_format CHECK (ticker ~ '^[A-Z0-9.]+$')
);

-- Indexes
CREATE INDEX idx_stocks_ticker ON src_stocks (ticker);
CREATE INDEX idx_stocks_sector ON src_stocks (sector);
CREATE INDEX idx_stocks_theme ON src_stocks (theme_tag);
CREATE INDEX idx_stocks_region ON src_stocks (region);
```

### 3.3 src_call_logs
```sql
CREATE TABLE src_call_logs (
    call_id             SERIAL PRIMARY KEY,
    client_id           INTEGER NOT NULL REFERENCES src_clients(client_id),
    stock_id            INTEGER REFERENCES src_stocks(stock_id),
    call_timestamp      TIMESTAMPTZ NOT NULL,
    direction           call_direction_enum,
    duration_minutes    INTEGER CHECK (duration_minutes >= 0),
    discussed_company   VARCHAR(255),
    discussed_sector    VARCHAR(100),
    related_report_id   INTEGER,
    notes_raw           TEXT,
    notes_embedding     vector(1024),  -- Mistral embedding dimension
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_calls_client ON src_call_logs (client_id);
CREATE INDEX idx_calls_timestamp ON src_call_logs (call_timestamp DESC);
CREATE INDEX idx_calls_stock ON src_call_logs (stock_id) WHERE stock_id IS NOT NULL;
CREATE INDEX idx_calls_embedding ON src_call_logs USING ivfflat (notes_embedding vector_cosine_ops) WITH (lists = 100);
```

### 3.4 src_trade_executions
```sql
CREATE TABLE src_trade_executions (
    trade_id            SERIAL PRIMARY KEY,
    client_id           INTEGER NOT NULL REFERENCES src_clients(client_id),
    stock_id            INTEGER REFERENCES src_stocks(stock_id),
    trade_timestamp     TIMESTAMPTZ NOT NULL,
    instrument_name     VARCHAR(255),
    ticker              VARCHAR(20),
    sector              VARCHAR(100),
    theme_tag           VARCHAR(100),
    side                trade_side_enum NOT NULL,
    notional_bucket     notional_bucket_enum,
    quantity            NUMERIC(18, 4),
    price               NUMERIC(18, 6),
    currency            VARCHAR(3) DEFAULT 'EUR',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trades_client ON src_trade_executions (client_id);
CREATE INDEX idx_trades_timestamp ON src_trade_executions (trade_timestamp DESC);
CREATE INDEX idx_trades_stock ON src_trade_executions (stock_id) WHERE stock_id IS NOT NULL;
CREATE INDEX idx_trades_side ON src_trade_executions (side);
```

### 3.5 src_portfolio_snapshots
```sql
CREATE TABLE src_portfolio_snapshots (
    snapshot_id         SERIAL PRIMARY KEY,
    client_id           INTEGER NOT NULL REFERENCES src_clients(client_id),
    as_of_date          DATE NOT NULL,
    source_system       VARCHAR(50),
    total_aum           NUMERIC(18, 2),
    currency            VARCHAR(3) DEFAULT 'EUR',
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_snapshot_client_date UNIQUE (client_id, as_of_date)
);

-- Indexes
CREATE INDEX idx_snapshots_client ON src_portfolio_snapshots (client_id);
CREATE INDEX idx_snapshots_date ON src_portfolio_snapshots (as_of_date DESC);
```

### 3.6 src_positions
```sql
CREATE TABLE src_positions (
    position_id         SERIAL PRIMARY KEY,
    snapshot_id         INTEGER NOT NULL REFERENCES src_portfolio_snapshots(snapshot_id),
    stock_id            INTEGER NOT NULL REFERENCES src_stocks(stock_id),
    quantity            NUMERIC(18, 4) NOT NULL,
    avg_cost            NUMERIC(18, 6),
    market_value        NUMERIC(18, 2),
    weight              NUMERIC(8, 6) CHECK (weight >= 0 AND weight <= 1),
    currency            VARCHAR(3) DEFAULT 'EUR'
);

-- Indexes
CREATE INDEX idx_positions_snapshot ON src_positions (snapshot_id);
CREATE INDEX idx_positions_stock ON src_positions (stock_id);
CREATE INDEX idx_positions_weight ON src_positions (weight DESC);
```

### 3.7 src_reports
```sql
CREATE TABLE src_reports (
    report_id           SERIAL PRIMARY KEY,
    report_code         VARCHAR(50) UNIQUE,
    stock_id            INTEGER REFERENCES src_stocks(stock_id),
    ticker              VARCHAR(20),
    company_name        VARCHAR(255),
    sector              VARCHAR(100),
    report_type         report_type_enum,
    title               VARCHAR(500) NOT NULL,
    summary_3bullets    TEXT,
    publish_timestamp   TIMESTAMPTZ NOT NULL,
    analyst_name        VARCHAR(255),
    content_embedding   vector(1024),  -- For semantic search
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reports_stock ON src_reports (stock_id) WHERE stock_id IS NOT NULL;
CREATE INDEX idx_reports_publish ON src_reports (publish_timestamp DESC);
CREATE INDEX idx_reports_type ON src_reports (report_type);
CREATE INDEX idx_reports_embedding ON src_reports USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 50);
```

### 3.8 src_readership_events
```sql
CREATE TABLE src_readership_events (
    event_id            SERIAL PRIMARY KEY,
    client_id           INTEGER NOT NULL REFERENCES src_clients(client_id),
    report_id           INTEGER NOT NULL REFERENCES src_reports(report_id),
    read_timestamp      TIMESTAMPTZ NOT NULL,
    read_duration_sec   INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_readership_client ON src_readership_events (client_id);
CREATE INDEX idx_readership_report ON src_readership_events (report_id);
CREATE INDEX idx_readership_timestamp ON src_readership_events (read_timestamp DESC);
```

### 3.9 src_stock_prices
```sql
CREATE TABLE src_stock_prices (
    price_id            SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES src_stocks(stock_id),
    price_date          DATE NOT NULL,
    open                NUMERIC(18, 6),
    high                NUMERIC(18, 6),
    low                 NUMERIC(18, 6),
    close               NUMERIC(18, 6) NOT NULL,
    volume              BIGINT,
    currency            VARCHAR(3) DEFAULT 'EUR',

    -- Constraints
    CONSTRAINT uq_price_stock_date UNIQUE (stock_id, price_date)
);

-- Indexes
CREATE INDEX idx_prices_stock_date ON src_stock_prices (stock_id, price_date DESC);
```

### 3.10 src_stock_returns
```sql
CREATE TABLE src_stock_returns (
    return_id           SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES src_stocks(stock_id),
    return_date         DATE NOT NULL,
    daily_return        NUMERIC(12, 8),

    -- Constraints
    CONSTRAINT uq_return_stock_date UNIQUE (stock_id, return_date)
);

-- Indexes
CREATE INDEX idx_returns_stock_date ON src_stock_returns (stock_id, return_date DESC);
```

### 3.11 src_stock_volatility
```sql
CREATE TABLE src_stock_volatility (
    vol_id              SERIAL PRIMARY KEY,
    stock_id            INTEGER NOT NULL REFERENCES src_stocks(stock_id),
    vol_date            DATE NOT NULL,
    vol_20d             NUMERIC(10, 6),
    vol_60d             NUMERIC(10, 6),

    -- Constraints
    CONSTRAINT uq_vol_stock_date UNIQUE (stock_id, vol_date)
);

-- Indexes
CREATE INDEX idx_volatility_stock_date ON src_stock_volatility (stock_id, vol_date DESC);
```

---

## 4. NEW: AI Generation History (Compliance)

```sql
CREATE TABLE ai_generation_history (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id           INTEGER NOT NULL REFERENCES src_clients(client_id),
    user_id             UUID,  -- Supabase Auth user ID
    session_id          UUID,

    -- Request details
    generation_type     ai_generation_type_enum NOT NULL,
    model_tier          ai_model_tier_enum NOT NULL,
    model_used          VARCHAR(100) NOT NULL,  -- e.g., 'mistral-small-latest'

    -- Prompt & Response (stored for compliance)
    prompt_hash         VARCHAR(64),  -- SHA-256 hash for deduplication
    prompt_text         TEXT NOT NULL,
    prompt_tokens       INTEGER,

    response_text       TEXT,
    response_tokens     INTEGER,

    -- Metadata
    selected_ticker     VARCHAR(20),
    shortlist_tickers   VARCHAR(20)[],  -- Array of tickers in shortlist
    instruction         TEXT,

    -- Performance
    latency_ms          INTEGER,
    success             BOOLEAN DEFAULT TRUE,
    error_message       TEXT,

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_tokens_positive CHECK (prompt_tokens >= 0 AND response_tokens >= 0)
);

-- Indexes for audit and analytics
CREATE INDEX idx_ai_history_client ON ai_generation_history (client_id);
CREATE INDEX idx_ai_history_user ON ai_generation_history (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_ai_history_created ON ai_generation_history (created_at DESC);
CREATE INDEX idx_ai_history_type ON ai_generation_history (generation_type);
CREATE INDEX idx_ai_history_model ON ai_generation_history (model_used);
CREATE INDEX idx_ai_history_prompt_hash ON ai_generation_history (prompt_hash);

-- Partitioning for large-scale (optional, for future)
-- PARTITION BY RANGE (created_at);
```

---

## 5. NEW: Embeddings Cache Table

```sql
CREATE TABLE embeddings_cache (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table        VARCHAR(50) NOT NULL,  -- e.g., 'src_call_logs', 'src_reports'
    source_id           INTEGER NOT NULL,
    content_hash        VARCHAR(64) NOT NULL,  -- SHA-256 of source text
    embedding           vector(1024) NOT NULL,
    model_used          VARCHAR(100) NOT NULL,  -- e.g., 'mistral-embed'
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_embedding_source UNIQUE (source_table, source_id)
);

-- Indexes
CREATE INDEX idx_embeddings_source ON embeddings_cache (source_table, source_id);
CREATE INDEX idx_embeddings_vector ON embeddings_cache USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 6. Materialized Views (Analytics Layer)

### 6.1 ana_readership_daysdiff
```sql
CREATE MATERIALIZED VIEW ana_readership_daysdiff AS
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
    EXTRACT(DAY FROM (e.read_timestamp - r.publish_timestamp))::INTEGER AS days_diff
FROM src_readership_events e
JOIN src_reports r ON r.report_id = e.report_id;

CREATE UNIQUE INDEX idx_mv_readership_event ON ana_readership_daysdiff (event_id);
CREATE INDEX idx_mv_readership_client ON ana_readership_daysdiff (client_id);
```

### 6.2 ana_call_position_hints
```sql
CREATE MATERIALIZED VIEW ana_call_position_hints AS
WITH base AS (
    SELECT
        cl.call_id,
        cl.client_id,
        cl.call_timestamp,
        cl.stock_id,
        s.ticker,
        LOWER(cl.notes_raw) AS txt
    FROM src_call_logs cl
    JOIN src_stocks s ON s.stock_id = cl.stock_id
    WHERE cl.notes_raw IS NOT NULL
),
scored AS (
    SELECT
        call_id,
        client_id,
        call_timestamp,
        stock_id,
        ticker,
        CASE WHEN txt ~ '(hold|already|existing|current)' THEN 1 ELSE 0 END AS hint_holding,
        CASE WHEN txt ~ '(add|increase|buy more|accumulate)' THEN 1 ELSE 0 END AS hint_add,
        CASE WHEN txt ~ '(reduce|sell|trim|exit)' THEN 1 ELSE 0 END AS hint_reduce,
        CASE WHEN txt ~ '(diversif|spread|allocation)' THEN 1 ELSE 0 END AS hint_diversification,
        CASE WHEN txt ~ '(risk|hedge|protect|downside)' THEN 1 ELSE 0 END AS hint_risk_mgmt
    FROM base
),
agg AS (
    SELECT
        client_id,
        stock_id,
        ticker,
        COUNT(*) AS mention_count,
        SUM(hint_holding) AS holding_hints,
        SUM(hint_add) AS add_hints,
        SUM(hint_reduce) AS reduce_hints,
        SUM(hint_diversification) AS diversification_hints,
        SUM(hint_risk_mgmt) AS risk_mgmt_hints,
        MAX(call_timestamp) AS last_mention_ts
    FROM scored
    GROUP BY client_id, stock_id, ticker
)
SELECT * FROM agg;

CREATE UNIQUE INDEX idx_mv_hints_client_stock ON ana_call_position_hints (client_id, stock_id);
```

### 6.3 ana_client_trade_summary
```sql
CREATE MATERIALIZED VIEW ana_client_trade_summary AS
WITH base AS (
    SELECT
        client_id,
        COUNT(*) AS trade_count,
        MAX(trade_timestamp) AS last_trade_ts,
        AVG(CASE WHEN side = 'Buy' THEN 1.0 ELSE 0.0 END) AS buy_rate,
        AVG(CASE notional_bucket
            WHEN 'Small' THEN 1
            WHEN 'Medium' THEN 3
            WHEN 'Large' THEN 7
            ELSE NULL
        END) AS size_proxy
    FROM src_trade_executions
    GROUP BY client_id
),
sector_counts AS (
    SELECT
        client_id,
        sector,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY COUNT(*) DESC) AS rn
    FROM src_trade_executions
    WHERE sector IS NOT NULL
    GROUP BY client_id, sector
),
theme_counts AS (
    SELECT
        client_id,
        theme_tag,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY COUNT(*) DESC) AS rn
    FROM src_trade_executions
    WHERE theme_tag IS NOT NULL
    GROUP BY client_id, theme_tag
),
sector_share AS (
    SELECT
        sc.client_id,
        sc.sector AS top_sector,
        sc.cnt::NUMERIC / b.trade_count AS top_sector_share
    FROM sector_counts sc
    JOIN base b ON b.client_id = sc.client_id
    WHERE sc.rn = 1
),
theme_share AS (
    SELECT
        tc.client_id,
        tc.theme_tag AS top_theme,
        tc.cnt::NUMERIC / b.trade_count AS top_theme_share
    FROM theme_counts tc
    JOIN base b ON b.client_id = tc.client_id
    WHERE tc.rn = 1
),
concentration AS (
    SELECT
        client_id,
        SUM(POWER(cnt::NUMERIC / total, 2)) AS herfindahl_concentration
    FROM (
        SELECT
            client_id,
            sector,
            COUNT(*) AS cnt,
            SUM(COUNT(*)) OVER (PARTITION BY client_id) AS total
        FROM src_trade_executions
        WHERE sector IS NOT NULL
        GROUP BY client_id, sector
    ) sub
    GROUP BY client_id
)
SELECT
    b.client_id,
    b.trade_count,
    ss.top_sector,
    ROUND(ss.top_sector_share, 4) AS top_sector_share,
    ts.top_theme,
    ROUND(ts.top_theme_share, 4) AS top_theme_share,
    ROUND(b.buy_rate, 4) AS buy_rate,
    ROUND(2 * b.buy_rate - 1, 4) AS side_bias,
    ROUND(b.size_proxy, 2) AS size_proxy,
    ROUND(c.herfindahl_concentration, 4) AS herfindahl_concentration,
    b.last_trade_ts
FROM base b
LEFT JOIN sector_share ss ON ss.client_id = b.client_id
LEFT JOIN theme_share ts ON ts.client_id = b.client_id
LEFT JOIN concentration c ON c.client_id = b.client_id;

CREATE UNIQUE INDEX idx_mv_trade_summary_client ON ana_client_trade_summary (client_id);
```

### 6.4 ana_client_call_patterns
```sql
CREATE MATERIALIZED VIEW ana_client_call_patterns AS
WITH calls AS (
    SELECT
        client_id,
        call_timestamp,
        EXTRACT(DOW FROM call_timestamp)::INTEGER AS weekday_num,
        EXTRACT(HOUR FROM call_timestamp)::INTEGER AS hour,
        duration_minutes
    FROM src_call_logs
),
weekday_counts AS (
    SELECT
        client_id,
        weekday_num,
        COUNT(*) AS n,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY COUNT(*) DESC) AS rn
    FROM calls
    GROUP BY client_id, weekday_num
),
hour_counts AS (
    SELECT
        client_id,
        hour,
        COUNT(*) AS n,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY COUNT(*) DESC) AS rn
    FROM calls
    GROUP BY client_id, hour
),
agg AS (
    SELECT
        client_id,
        COUNT(*) AS call_count,
        ROUND(AVG(duration_minutes), 1) AS avg_call_duration,
        MAX(call_timestamp) AS last_call_ts
    FROM calls
    GROUP BY client_id
)
SELECT
    a.client_id,
    a.call_count,
    a.avg_call_duration,
    w.weekday_num AS best_weekday_num,
    h.hour AS best_hour,
    CASE
        WHEN h.hour BETWEEN 8 AND 10 THEN 'Morning (8-10)'
        WHEN h.hour BETWEEN 11 AND 13 THEN 'Midday (11-13)'
        WHEN h.hour BETWEEN 14 AND 16 THEN 'Afternoon (14-16)'
        WHEN h.hour BETWEEN 17 AND 19 THEN 'Late Afternoon (17-19)'
        ELSE 'Other'
    END AS best_time_window,
    ROUND(w.n::NUMERIC / a.call_count, 3) AS timing_confidence,
    a.last_call_ts
FROM agg a
LEFT JOIN weekday_counts w ON w.client_id = a.client_id AND w.rn = 1
LEFT JOIN hour_counts h ON h.client_id = a.client_id AND h.rn = 1;

CREATE UNIQUE INDEX idx_mv_call_patterns_client ON ana_client_call_patterns (client_id);
```

### 6.5 ana_client_topic_signals
```sql
CREATE MATERIALIZED VIEW ana_client_topic_signals AS
WITH text_src AS (
    SELECT
        cl.client_id,
        cl.call_timestamp AS ts,
        LOWER(COALESCE(cl.notes_raw, '') || ' ' || COALESCE(r.title, '') || ' ' || COALESCE(r.summary_3bullets, '')) AS txt
    FROM src_call_logs cl
    LEFT JOIN src_reports r ON r.report_id = cl.related_report_id
),
tagged AS (
    SELECT
        client_id,
        ts,
        CASE
            WHEN txt ~ '(valuation|multiple|pe ratio|price.to.book)' THEN 'Valuation'
            WHEN txt ~ '(earnings|eps|profit|margin|revenue)' THEN 'Earnings'
            WHEN txt ~ '(dividend|yield|income|payout)' THEN 'Dividend'
            WHEN txt ~ '(growth|expansion|scale|market share)' THEN 'Growth'
            WHEN txt ~ '(risk|volatility|hedge|downside)' THEN 'Risk'
            WHEN txt ~ '(esg|climate|sustainability|governance)' THEN 'ESG'
            WHEN txt ~ '(macro|rates|inflation|gdp|economy)' THEN 'Macro'
            ELSE 'General'
        END AS topic
    FROM text_src
    WHERE txt IS NOT NULL AND txt != ''
),
topic_counts AS (
    SELECT
        client_id,
        topic,
        COUNT(*) AS cnt,
        MAX(ts) AS last_ts,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY COUNT(*) DESC) AS rn
    FROM tagged
    GROUP BY client_id, topic
),
totals AS (
    SELECT client_id, SUM(cnt) AS total FROM topic_counts GROUP BY client_id
)
SELECT
    tc.client_id,
    tc.topic AS top_topic,
    ROUND(tc.cnt::NUMERIC / t.total, 3) AS top_topic_share,
    tc.cnt AS top_topic_count,
    tc.last_ts AS last_signal_ts
FROM topic_counts tc
JOIN totals t ON t.client_id = tc.client_id
WHERE tc.rn = 1;

CREATE UNIQUE INDEX idx_mv_topic_signals_client ON ana_client_topic_signals (client_id);
```

### 6.6 ana_client_readership_summary
```sql
CREATE MATERIALIZED VIEW ana_client_readership_summary AS
SELECT
    client_id,
    COUNT(*) AS reads_n,
    ROUND(AVG(days_diff), 1) AS avg_days_diff,
    ROUND(SUM(CASE WHEN days_diff >= 4 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*), 3) AS late_read_ratio,
    MAX(read_timestamp) AS last_read_ts
FROM ana_readership_daysdiff
GROUP BY client_id;

CREATE UNIQUE INDEX idx_mv_readership_summary_client ON ana_client_readership_summary (client_id);
```

### 6.7 int_client_availability
```sql
CREATE MATERIALIZED VIEW int_client_availability AS
SELECT
    client_id,
    CASE best_weekday_num
        WHEN 1 THEN 'Mon'
        WHEN 2 THEN 'Tue'
        WHEN 3 THEN 'Wed'
        WHEN 4 THEN 'Thu'
        WHEN 5 THEN 'Fri'
        ELSE 'Other'
    END AS best_day,
    best_hour,
    best_time_window,
    ROUND(LN(1 + call_count) * timing_confidence, 3) AS availability_score,
    CASE
        WHEN LN(1 + call_count) * timing_confidence >= 0.200 THEN 'High'
        WHEN LN(1 + call_count) * timing_confidence >= 0.100 THEN 'Medium'
        ELSE 'Low'
    END AS availability_confidence,
    call_count,
    avg_call_duration AS avg_call_duration_min,
    NOW() AS updated_at
FROM ana_client_call_patterns;

CREATE UNIQUE INDEX idx_mv_availability_client ON int_client_availability (client_id);
```

### 6.8 int_client_portfolio_summary
```sql
CREATE MATERIALIZED VIEW int_client_portfolio_summary AS
WITH stats AS (
    SELECT
        MIN(size_proxy) AS min_size,
        MAX(size_proxy) AS max_size
    FROM ana_client_trade_summary
)
SELECT
    t.client_id,
    t.trade_count,
    t.top_sector,
    t.top_sector_share,
    t.top_theme,
    t.top_theme_share,
    t.buy_rate,
    t.side_bias,
    t.size_proxy,
    t.herfindahl_concentration AS concentration_index,
    CASE
        WHEN t.herfindahl_concentration >= 0.30 THEN 'Concentrated'
        WHEN t.herfindahl_concentration >= 0.15 THEN 'Moderate'
        ELSE 'Diversified'
    END AS concentration_flag,
    CASE
        WHEN t.side_bias >= 0.3 THEN 'Net Buyer'
        WHEN t.side_bias <= -0.3 THEN 'Net Seller'
        ELSE 'Balanced'
    END AS direction_flag,
    CASE
        WHEN t.trade_count >= 100 THEN 'Very Active'
        WHEN t.trade_count >= 50 THEN 'Active'
        WHEN t.trade_count >= 20 THEN 'Moderate'
        ELSE 'Low'
    END AS activity_flag,
    CASE
        WHEN s.max_size > s.min_size THEN
            ROUND((t.size_proxy - s.min_size) / NULLIF(s.max_size - s.min_size, 0), 3)
        ELSE 0.5
    END AS size_aggressiveness_score,
    NOW() AS updated_at
FROM ana_client_trade_summary t
CROSS JOIN stats s;

CREATE UNIQUE INDEX idx_mv_portfolio_summary_client ON int_client_portfolio_summary (client_id);
```

### 6.9 int_client_profile
```sql
CREATE MATERIALIZED VIEW int_client_profile AS
WITH ranked AS (
    SELECT
        t.client_id,
        t.trade_count,
        t.size_proxy,
        t.herfindahl_concentration,
        t.top_theme,
        c.call_count,
        c.timing_confidence,
        ts.top_topic,
        ts.top_topic_share,
        PERCENT_RANK() OVER (ORDER BY t.size_proxy) AS r_size,
        PERCENT_RANK() OVER (ORDER BY t.trade_count) AS r_activity,
        PERCENT_RANK() OVER (ORDER BY t.herfindahl_concentration) AS r_concentration
    FROM ana_client_trade_summary t
    LEFT JOIN ana_client_call_patterns c ON c.client_id = t.client_id
    LEFT JOIN ana_client_topic_signals ts ON ts.client_id = t.client_id
),
scored AS (
    SELECT
        client_id,
        trade_count,
        size_proxy,
        herfindahl_concentration,
        top_theme,
        call_count,
        timing_confidence,
        top_topic,
        top_topic_share,
        r_size,
        r_activity,
        r_concentration,
        -- Risk score: higher concentration + larger trades = higher risk
        ROUND((r_concentration * 0.4 + r_size * 0.4 + r_activity * 0.2), 3) AS risk_score
    FROM ranked
)
SELECT
    client_id,
    CASE
        WHEN r_activity >= 0.7 AND call_count >= 10 THEN 'High'
        WHEN r_activity >= 0.4 OR call_count >= 5 THEN 'Medium'
        ELSE 'Low'
    END AS engagement_level,
    CASE
        WHEN top_topic IN ('Growth', 'Earnings') AND r_size >= 0.5 THEN 'Growth'
        WHEN top_topic IN ('Dividend', 'Valuation') THEN 'Value'
        WHEN top_topic = 'ESG' THEN 'ESG-Focus'
        WHEN r_concentration < 0.3 THEN 'Diversified'
        ELSE 'GARP'
    END AS investment_style,
    risk_score,
    CASE
        WHEN risk_score >= 0.65 THEN 'Aggressive'
        WHEN risk_score >= 0.35 THEN 'Moderate'
        ELSE 'Conservative'
    END AS risk_appetite,
    top_topic AS dominant_topic,
    top_topic_share AS dominant_topic_share,
    top_theme AS dominant_theme,
    ROUND(COALESCE(timing_confidence, 0) * 0.5 + r_activity * 0.5, 3) AS profile_confidence_score,
    CASE
        WHEN COALESCE(timing_confidence, 0) * 0.5 + r_activity * 0.5 >= 0.6 THEN 'High'
        WHEN COALESCE(timing_confidence, 0) * 0.5 + r_activity * 0.5 >= 0.3 THEN 'Medium'
        ELSE 'Low'
    END AS profile_confidence_level,
    NOW() AS updated_at
FROM scored;

CREATE UNIQUE INDEX idx_mv_profile_client ON int_client_profile (client_id);
```

---

## 7. Refresh Function for Materialized Views

```sql
CREATE OR REPLACE FUNCTION refresh_all_analytics_views()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Refresh in dependency order
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_readership_daysdiff;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_call_position_hints;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_client_trade_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_client_call_patterns;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_client_topic_signals;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ana_client_readership_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY int_client_availability;
    REFRESH MATERIALIZED VIEW CONCURRENTLY int_client_portfolio_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY int_client_profile;
END;
$$;

-- Schedule via pg_cron (Supabase) or external scheduler
-- SELECT cron.schedule('refresh-analytics', '0 */4 * * *', 'SELECT refresh_all_analytics_views();');
```

---

## 8. Row Level Security (RLS) Policies

```sql
-- Enable RLS on sensitive tables
ALTER TABLE src_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_generation_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see AI history for their own generations
CREATE POLICY "Users can view own AI history"
    ON ai_generation_history
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own AI history
CREATE POLICY "Users can insert own AI history"
    ON ai_generation_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role bypass for backend operations
CREATE POLICY "Service role full access"
    ON ai_generation_history
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
```

---

## 9. Indexes Summary

| Table | Index | Purpose |
|-------|-------|---------|
| src_clients | gin_trgm (firm_name, contact_name) | Fuzzy search |
| src_call_logs | ivfflat (notes_embedding) | Semantic search |
| src_reports | ivfflat (content_embedding) | Semantic search |
| ai_generation_history | btree (client_id, created_at) | Audit queries |
| all materialized views | unique (client_id) | Fast lookups |

---

## 10. Migration Script (SQLite → PostgreSQL)

```sql
-- This will be generated as a separate file: migrate_data.sql
-- Uses pg_dump compatible format for data insertion
```

---

## Schema Diagram (Simplified)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SOURCE TABLES (READ-ONLY)                      │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│ src_clients │ src_stocks  │ src_reports │src_call_logs│src_trade_exec   │
│     (50)    │    (300)    │    (120)    │   (2,169)   │    (5,263)      │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────────┬────────┘
       │             │             │             │               │
       ▼             ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     MATERIALIZED VIEWS (ANALYTICS)                       │
├─────────────────────┬───────────────────────┬───────────────────────────┤
│ ana_call_position   │ ana_client_trade      │ ana_readership_daysdiff   │
│ ana_topic_signals   │ ana_call_patterns     │ ana_readership_summary    │
└─────────┬───────────┴───────────┬───────────┴───────────────┬───────────┘
          │                       │                           │
          ▼                       ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION VIEWS (DERIVED PROFILES)                  │
├────────────────────┬────────────────────────┬───────────────────────────┤
│ int_client_profile │ int_portfolio_summary  │ int_client_availability   │
└────────────────────┴────────────────────────┴───────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEW TABLES                                       │
├────────────────────────────────┬────────────────────────────────────────┤
│   ai_generation_history        │      embeddings_cache                   │
│   (compliance audit log)       │      (pgvector storage)                 │
└────────────────────────────────┴────────────────────────────────────────┘
```

---

## Next Steps After Approval

1. **Generate migration script** to transfer SQLite data to PostgreSQL
2. **Create Supabase project** and apply schema
3. **Set up edge functions** for materialized view refresh
4. **Configure RLS policies** for multi-tenant access

---

**Awaiting your confirmation to proceed with implementation.**
