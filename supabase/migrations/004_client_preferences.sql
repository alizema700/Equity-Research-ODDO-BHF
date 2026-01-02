-- ============================================================================
-- CLIENT PREFERENCES & MULTI-FACTOR PROFILING
-- Migration: 004_client_preferences.sql
-- ============================================================================

-- ============================================================================
-- 1. CLIENT PREFERENCES TABLE
-- Stores explicit and inferred client investment preferences
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_client_preferences (
    preference_id       SERIAL PRIMARY KEY,
    client_id           INTEGER REFERENCES src_clients(client_id),

    -- Income Preferences
    dividend_preference VARCHAR(20) DEFAULT 'Neutral',  -- 'High Yield', 'Growth', 'Neutral'
    min_dividend_yield  DECIMAL(5,2),                    -- e.g., 3.5 = 3.5% minimum

    -- ESG Preferences
    esg_mandate         BOOLEAN DEFAULT FALSE,
    esg_exclusions      TEXT[],                          -- Array of excluded sectors/themes
    carbon_sensitivity  VARCHAR(20) DEFAULT 'Medium',   -- 'Low', 'Medium', 'High'

    -- Sector Preferences
    preferred_sectors   TEXT[],                          -- e.g., ['Tech', 'Healthcare']
    excluded_sectors    TEXT[],                          -- e.g., ['Tobacco', 'Gambling']

    -- Theme Preferences
    preferred_themes    TEXT[],                          -- e.g., ['AI', 'EnergyTransition']

    -- Geographic Preferences
    home_bias           DECIMAL(5,2) DEFAULT 0.30,       -- % allocation to home region
    preferred_regions   TEXT[],                          -- e.g., ['Europe', 'US']
    excluded_countries  TEXT[],                          -- e.g., ['Russia', 'China']

    -- Risk Preferences (explicit)
    max_position_size   DECIMAL(5,2) DEFAULT 0.10,       -- Max single position weight
    max_sector_weight   DECIMAL(5,2) DEFAULT 0.30,       -- Max sector concentration
    volatility_limit    DECIMAL(5,2),                    -- Max acceptable vol
    drawdown_tolerance  DECIMAL(5,2),                    -- Max drawdown tolerance

    -- Liquidity Preferences
    min_market_cap      VARCHAR(20) DEFAULT 'Mid',      -- 'Micro', 'Small', 'Mid', 'Large'
    min_daily_volume    DECIMAL(15,2),                   -- Minimum avg daily volume

    -- Time Horizon
    investment_horizon  VARCHAR(20) DEFAULT 'Medium',   -- 'Short', 'Medium', 'Long'
    turnover_preference VARCHAR(20) DEFAULT 'Medium',   -- 'Low', 'Medium', 'High'

    -- Special Mandates
    benchmark_index     VARCHAR(100),                    -- e.g., 'STOXX 600', 'DAX'
    tracking_error_max  DECIMAL(5,2),                    -- For benchmark-relative

    -- Metadata
    preference_source   VARCHAR(50) DEFAULT 'inferred', -- 'explicit', 'inferred', 'default'
    confidence_score    DECIMAL(3,2) DEFAULT 0.5,        -- 0-1 confidence in preferences
    last_confirmed      TIMESTAMPTZ,                     -- When client confirmed preferences
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(client_id)
);

CREATE INDEX idx_pref_client ON src_client_preferences(client_id);
CREATE INDEX idx_pref_dividend ON src_client_preferences(dividend_preference);
CREATE INDEX idx_pref_esg ON src_client_preferences(esg_mandate);


-- ============================================================================
-- 2. MULTI-FACTOR RISK PROFILE VIEW
-- Combines multiple signals for comprehensive risk classification
-- ============================================================================

-- SQLite-compatible version (for local development)
CREATE VIEW IF NOT EXISTS int_client_risk_profile_multifactor AS
WITH
-- Factor 1: Investor Type Base Risk
investor_type_risk AS (
    SELECT
        client_id,
        client_type,
        CASE client_type
            WHEN 'HedgeFund' THEN 0.85
            WHEN 'Hedge Fund' THEN 0.85
            WHEN 'FamilyOffice' THEN 0.65
            WHEN 'Family Office' THEN 0.65
            WHEN 'AssetManager' THEN 0.55
            WHEN 'Asset Manager' THEN 0.55
            WHEN 'PrivateBank' THEN 0.50
            WHEN 'Private Bank' THEN 0.50
            WHEN 'SovereignWealth' THEN 0.45
            WHEN 'Sovereign Wealth' THEN 0.45
            WHEN 'Insurance' THEN 0.35
            WHEN 'PensionFund' THEN 0.30
            WHEN 'Pension Fund' THEN 0.30
            ELSE 0.50
        END AS type_risk_score,
        CASE
            WHEN client_type IN ('HedgeFund', 'Hedge Fund') THEN 'Aggressive'
            WHEN client_type IN ('PensionFund', 'Pension Fund', 'Insurance') THEN 'Conservative'
            ELSE 'Moderate'
        END AS type_risk_category
    FROM src_clients
),

-- Factor 2: Trading Behavior Risk
trading_behavior AS (
    SELECT
        client_id,
        COUNT(*) AS trade_count,
        AVG(CASE WHEN notional_bucket = 'Large' THEN 1.0 ELSE 0.0 END) AS large_trade_ratio,
        AVG(CASE WHEN side = 'Buy' THEN 1.0 ELSE 0.0 END) AS buy_ratio,
        -- High turnover = higher risk tolerance
        CASE
            WHEN COUNT(*) > 50 THEN 0.75
            WHEN COUNT(*) > 20 THEN 0.55
            WHEN COUNT(*) > 5 THEN 0.40
            ELSE 0.25
        END AS turnover_risk_score
    FROM src_trade_executions
    WHERE trade_timestamp >= date('now', '-180 days')
    GROUP BY client_id
),

-- Factor 3: Sector Concentration Risk
sector_concentration AS (
    SELECT
        te.client_id,
        MAX(sector_pct) AS max_sector_concentration,
        COUNT(DISTINCT sector) AS sector_diversification,
        CASE
            WHEN MAX(sector_pct) > 0.40 THEN 0.70  -- Concentrated = risk tolerant
            WHEN MAX(sector_pct) > 0.25 THEN 0.50
            ELSE 0.35
        END AS concentration_risk_score
    FROM (
        SELECT
            client_id,
            sector,
            1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY client_id) AS sector_pct
        FROM src_trade_executions
        WHERE sector IS NOT NULL
        GROUP BY client_id, sector
    ) te
    GROUP BY te.client_id
),

-- Factor 4: Position Volatility (from current holdings)
position_volatility AS (
    SELECT
        ps.client_id,
        AVG(p.weight) AS avg_position_weight,
        MAX(p.weight) AS max_position_weight,
        CASE
            WHEN MAX(p.weight) > 0.15 THEN 0.70  -- Large positions = risk tolerant
            WHEN MAX(p.weight) > 0.08 THEN 0.50
            ELSE 0.35
        END AS position_risk_score
    FROM src_positions p
    JOIN src_portfolio_snapshots ps ON ps.snapshot_id = p.snapshot_id
    WHERE ps.snapshot_id IN (
        SELECT MAX(snapshot_id) FROM src_portfolio_snapshots GROUP BY client_id
    )
    GROUP BY ps.client_id
),

-- Factor 5: Call Sentiment Analysis
call_sentiment AS (
    SELECT
        client_id,
        COUNT(*) AS total_calls,
        SUM(CASE
            WHEN LOWER(notes_raw) LIKE '%aggressive%'
              OR LOWER(notes_raw) LIKE '%high conviction%'
              OR LOWER(notes_raw) LIKE '%upside%'
              OR LOWER(notes_raw) LIKE '%momentum%' THEN 1 ELSE 0
        END) AS aggressive_mentions,
        SUM(CASE
            WHEN LOWER(notes_raw) LIKE '%conservative%'
              OR LOWER(notes_raw) LIKE '%defensive%'
              OR LOWER(notes_raw) LIKE '%dividend%'
              OR LOWER(notes_raw) LIKE '%stability%' THEN 1 ELSE 0
        END) AS conservative_mentions
    FROM src_call_logs
    WHERE notes_raw IS NOT NULL
    GROUP BY client_id
),

-- Factor 6: Reading Preferences (fast readers on volatile topics = risk tolerant)
reading_behavior AS (
    SELECT
        rd.client_id,
        AVG(rd.days_diff) AS avg_read_delay,
        COUNT(*) AS total_reads,
        SUM(CASE WHEN r.sector IN ('Tech', 'Biotech', 'Crypto') THEN 1 ELSE 0 END) AS high_vol_sector_reads,
        CASE
            WHEN AVG(rd.days_diff) < 1 THEN 0.65  -- Fast readers = more engaged
            WHEN AVG(rd.days_diff) < 3 THEN 0.50
            ELSE 0.35
        END AS reading_risk_score
    FROM ana_readership_daysdiff rd
    LEFT JOIN src_reports r ON r.report_id = rd.report_id
    GROUP BY rd.client_id
)

-- Final Combined Score
SELECT
    c.client_id,
    c.client_name,
    c.firm_name,
    c.client_type,

    -- Individual Factor Scores
    COALESCE(itr.type_risk_score, 0.50) AS investor_type_factor,
    COALESCE(tb.turnover_risk_score, 0.40) AS trading_behavior_factor,
    COALESCE(sc.concentration_risk_score, 0.40) AS concentration_factor,
    COALESCE(pv.position_risk_score, 0.40) AS position_size_factor,
    COALESCE(rb.reading_risk_score, 0.40) AS engagement_factor,

    -- Weights for each factor
    -- Investor Type: 30%, Trading: 25%, Concentration: 15%, Position Size: 15%, Engagement: 15%
    ROUND(
        0.30 * COALESCE(itr.type_risk_score, 0.50) +
        0.25 * COALESCE(tb.turnover_risk_score, 0.40) +
        0.15 * COALESCE(sc.concentration_risk_score, 0.40) +
        0.15 * COALESCE(pv.position_risk_score, 0.40) +
        0.15 * COALESCE(rb.reading_risk_score, 0.40),
        3
    ) AS composite_risk_score,

    -- Final Risk Category
    CASE
        WHEN (0.30 * COALESCE(itr.type_risk_score, 0.50) +
              0.25 * COALESCE(tb.turnover_risk_score, 0.40) +
              0.15 * COALESCE(sc.concentration_risk_score, 0.40) +
              0.15 * COALESCE(pv.position_risk_score, 0.40) +
              0.15 * COALESCE(rb.reading_risk_score, 0.40)) >= 0.65 THEN 'Aggressive'
        WHEN (0.30 * COALESCE(itr.type_risk_score, 0.50) +
              0.25 * COALESCE(tb.turnover_risk_score, 0.40) +
              0.15 * COALESCE(sc.concentration_risk_score, 0.40) +
              0.15 * COALESCE(pv.position_risk_score, 0.40) +
              0.15 * COALESCE(rb.reading_risk_score, 0.40)) >= 0.45 THEN 'Moderate'
        ELSE 'Conservative'
    END AS risk_category,

    -- Confidence based on data availability
    CASE
        WHEN tb.trade_count > 20 AND pv.avg_position_weight IS NOT NULL THEN 'High'
        WHEN tb.trade_count > 5 OR pv.avg_position_weight IS NOT NULL THEN 'Medium'
        ELSE 'Low'
    END AS profile_confidence,

    -- Behavioral Signals
    itr.type_risk_category AS investor_type_signal,
    COALESCE(tb.trade_count, 0) AS trade_activity,
    COALESCE(tb.buy_ratio, 0.5) AS buy_tendency,
    COALESCE(sc.sector_diversification, 0) AS sector_breadth,
    COALESCE(pv.max_position_weight, 0) AS max_position_pct,

    -- Sentiment from Calls
    CASE
        WHEN COALESCE(cs.aggressive_mentions, 0) > COALESCE(cs.conservative_mentions, 0) * 2 THEN 'Aggressive'
        WHEN COALESCE(cs.conservative_mentions, 0) > COALESCE(cs.aggressive_mentions, 0) * 2 THEN 'Conservative'
        ELSE 'Balanced'
    END AS call_sentiment_signal

FROM src_clients c
LEFT JOIN investor_type_risk itr ON itr.client_id = c.client_id
LEFT JOIN trading_behavior tb ON tb.client_id = c.client_id
LEFT JOIN sector_concentration sc ON sc.client_id = c.client_id
LEFT JOIN position_volatility pv ON pv.client_id = c.client_id
LEFT JOIN call_sentiment cs ON cs.client_id = c.client_id
LEFT JOIN reading_behavior rb ON rb.client_id = c.client_id;


-- ============================================================================
-- 3. INVESTMENT STYLE CLASSIFICATION
-- Determines Value/Growth/Income/etc. from behavior
-- ============================================================================

CREATE VIEW IF NOT EXISTS int_client_investment_style AS
WITH
trade_analysis AS (
    SELECT
        client_id,
        -- Theme preferences from trades
        SUM(CASE WHEN theme_tag = 'AI' THEN 1 ELSE 0 END) AS ai_trades,
        SUM(CASE WHEN theme_tag = 'EnergyTransition' THEN 1 ELSE 0 END) AS energy_trans_trades,
        SUM(CASE WHEN theme_tag = 'ESG' THEN 1 ELSE 0 END) AS esg_trades,
        SUM(CASE WHEN theme_tag IN ('Automation', 'Infra') THEN 1 ELSE 0 END) AS infra_trades,
        COUNT(*) AS total_trades,
        -- Sector preferences
        SUM(CASE WHEN sector = 'Tech' THEN 1 ELSE 0 END) AS tech_trades,
        SUM(CASE WHEN sector = 'Healthcare' THEN 1 ELSE 0 END) AS healthcare_trades,
        SUM(CASE WHEN sector = 'Financials' THEN 1 ELSE 0 END) AS financials_trades,
        SUM(CASE WHEN sector = 'Energy' THEN 1 ELSE 0 END) AS energy_trades,
        SUM(CASE WHEN sector = 'Cons' THEN 1 ELSE 0 END) AS consumer_trades
    FROM src_trade_executions
    GROUP BY client_id
),

reading_analysis AS (
    SELECT
        rd.client_id,
        SUM(CASE WHEN r.report_type = 'Earnings' THEN 1 ELSE 0 END) AS earnings_reads,
        SUM(CASE WHEN r.report_type IN ('Initiation', 'Update') THEN 1 ELSE 0 END) AS research_reads,
        SUM(CASE WHEN r.report_type IN ('StrategyNote', 'SectorNote') THEN 1 ELSE 0 END) AS strategy_reads,
        COUNT(*) AS total_reads
    FROM ana_readership_daysdiff rd
    LEFT JOIN src_reports r ON r.report_id = rd.report_id
    GROUP BY rd.client_id
)

SELECT
    c.client_id,

    -- Primary Style Classification
    CASE
        WHEN COALESCE(ta.esg_trades, 0) > COALESCE(ta.total_trades, 1) * 0.3 THEN 'ESG-Focus'
        WHEN COALESCE(ta.tech_trades, 0) + COALESCE(ta.ai_trades, 0) > COALESCE(ta.total_trades, 1) * 0.4 THEN 'Growth'
        WHEN COALESCE(ta.financials_trades, 0) + COALESCE(ta.energy_trades, 0) > COALESCE(ta.total_trades, 1) * 0.4 THEN 'Value'
        WHEN COALESCE(ra.earnings_reads, 0) > COALESCE(ra.total_reads, 1) * 0.5 THEN 'Momentum'
        ELSE 'Diversified'
    END AS primary_style,

    -- Secondary Style
    CASE
        WHEN COALESCE(ta.energy_trans_trades, 0) > 5 THEN 'Thematic (Energy Transition)'
        WHEN COALESCE(ta.ai_trades, 0) > 5 THEN 'Thematic (AI)'
        WHEN COALESCE(ta.infra_trades, 0) > 5 THEN 'Thematic (Infrastructure)'
        ELSE NULL
    END AS secondary_style,

    -- Top Sector Preference
    CASE
        WHEN COALESCE(ta.tech_trades, 0) >= COALESCE(ta.healthcare_trades, 0)
         AND COALESCE(ta.tech_trades, 0) >= COALESCE(ta.financials_trades, 0) THEN 'Tech'
        WHEN COALESCE(ta.healthcare_trades, 0) >= COALESCE(ta.financials_trades, 0) THEN 'Healthcare'
        ELSE 'Financials'
    END AS top_sector_preference,

    -- Theme Affinity
    CASE
        WHEN COALESCE(ta.ai_trades, 0) > 3 THEN 'AI'
        WHEN COALESCE(ta.energy_trans_trades, 0) > 3 THEN 'EnergyTransition'
        WHEN COALESCE(ta.esg_trades, 0) > 3 THEN 'ESG'
        ELSE NULL
    END AS theme_affinity,

    -- Reading Focus
    CASE
        WHEN COALESCE(ra.strategy_reads, 0) > COALESCE(ra.earnings_reads, 0) THEN 'Macro/Strategy'
        WHEN COALESCE(ra.earnings_reads, 0) > COALESCE(ra.research_reads, 0) THEN 'Earnings/Momentum'
        ELSE 'Fundamental Research'
    END AS reading_focus,

    -- Activity Level
    CASE
        WHEN COALESCE(ta.total_trades, 0) > 50 THEN 'Very Active'
        WHEN COALESCE(ta.total_trades, 0) > 20 THEN 'Active'
        WHEN COALESCE(ta.total_trades, 0) > 5 THEN 'Moderate'
        ELSE 'Low Activity'
    END AS activity_level

FROM src_clients c
LEFT JOIN trade_analysis ta ON ta.client_id = c.client_id
LEFT JOIN reading_analysis ra ON ra.client_id = c.client_id;
