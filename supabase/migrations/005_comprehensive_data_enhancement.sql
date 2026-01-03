-- ============================================================================
-- COMPREHENSIVE DATA ENHANCEMENT FOR SALES INTELLIGENCE
-- Migration: 005_comprehensive_data_enhancement.sql
-- ============================================================================

-- ============================================================================
-- 1. CLIENT PREFERENCES (Real preferences, not inferred)
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_client_preferences (
    preference_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id           INTEGER NOT NULL,

    -- Investment Style Preferences
    prefers_dividends   BOOLEAN DEFAULT FALSE,
    prefers_growth      BOOLEAN DEFAULT FALSE,
    prefers_value       BOOLEAN DEFAULT FALSE,
    prefers_esg         BOOLEAN DEFAULT FALSE,
    prefers_momentum    BOOLEAN DEFAULT FALSE,

    -- Risk Preferences
    max_volatility      REAL,  -- Maximum acceptable volatility (e.g., 0.30 = 30%)
    min_market_cap      TEXT,  -- 'Micro', 'Small', 'Mid', 'Large', 'Mega'
    prefers_large_cap   BOOLEAN DEFAULT FALSE,

    -- Sector Preferences
    preferred_sectors   TEXT,  -- Comma-separated list
    excluded_sectors    TEXT,  -- Comma-separated list

    -- Theme Preferences
    preferred_themes    TEXT,  -- Comma-separated: 'AI', 'ESG', 'Healthcare', etc.

    -- Geographic Preferences
    preferred_regions   TEXT,  -- 'DACH', 'France', 'UK', etc.
    home_bias           REAL DEFAULT 0.5,  -- 0-1, how much they prefer home region

    -- Liquidity Preferences
    min_avg_volume      INTEGER,  -- Minimum average daily volume

    -- Income Requirements
    min_dividend_yield  REAL,  -- Minimum dividend yield (e.g., 0.02 = 2%)

    -- Notes
    preference_notes    TEXT,
    last_updated        TEXT DEFAULT (datetime('now')),
    updated_by          TEXT,

    FOREIGN KEY (client_id) REFERENCES src_clients(client_id)
);

CREATE INDEX IF NOT EXISTS idx_client_prefs_client ON src_client_preferences(client_id);

-- ============================================================================
-- 2. STOCK FUNDAMENTALS
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_stock_fundamentals (
    fundamental_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id            INTEGER NOT NULL,
    as_of_date          TEXT NOT NULL,

    -- Valuation Metrics
    pe_ratio            REAL,
    pe_forward          REAL,
    pb_ratio            REAL,  -- Price to Book
    ps_ratio            REAL,  -- Price to Sales
    ev_ebitda           REAL,

    -- Profitability
    roe                 REAL,  -- Return on Equity
    roa                 REAL,  -- Return on Assets
    profit_margin       REAL,
    operating_margin    REAL,

    -- Growth
    revenue_growth_yoy  REAL,
    earnings_growth_yoy REAL,
    revenue_growth_3y   REAL,

    -- Dividend
    dividend_yield      REAL,
    payout_ratio        REAL,
    dividend_growth_5y  REAL,

    -- Balance Sheet
    debt_to_equity      REAL,
    current_ratio       REAL,

    -- Market Data
    market_cap          REAL,
    market_cap_bucket   TEXT,
    beta                REAL,
    avg_volume_20d      INTEGER,

    -- Quality Score (ODDO BHF proprietary)
    quality_score       REAL,  -- 0-100

    FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id),
    UNIQUE(stock_id, as_of_date)
);

CREATE INDEX IF NOT EXISTS idx_fundamentals_stock ON src_stock_fundamentals(stock_id);
CREATE INDEX IF NOT EXISTS idx_fundamentals_date ON src_stock_fundamentals(as_of_date);

-- ============================================================================
-- 3. ANALYST RATINGS (ODDO BHF Research)
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_analyst_ratings (
    rating_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id            INTEGER NOT NULL,
    analyst_name        TEXT NOT NULL,

    -- Rating
    rating              TEXT NOT NULL,  -- 'Outperform', 'Neutral', 'Underperform'
    previous_rating     TEXT,
    rating_date         TEXT NOT NULL,

    -- Price Target
    price_target        REAL,
    previous_target     REAL,
    target_currency     TEXT DEFAULT 'EUR',

    -- Upside/Downside
    current_price       REAL,
    upside_percent      REAL,  -- Calculated: (target - current) / current

    -- Conviction
    conviction_level    TEXT,  -- 'High', 'Medium', 'Low'

    -- Key Thesis
    thesis_summary      TEXT,
    key_catalysts       TEXT,
    key_risks           TEXT,

    FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
);

CREATE INDEX IF NOT EXISTS idx_ratings_stock ON src_analyst_ratings(stock_id);
CREATE INDEX IF NOT EXISTS idx_ratings_date ON src_analyst_ratings(rating_date);
CREATE INDEX IF NOT EXISTS idx_ratings_rating ON src_analyst_ratings(rating);

-- ============================================================================
-- 4. UPCOMING CATALYSTS / EVENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_stock_catalysts (
    catalyst_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id            INTEGER NOT NULL,

    -- Event Details
    event_type          TEXT NOT NULL,  -- 'Earnings', 'Dividend', 'Conference', 'AGM', 'Product Launch', 'Regulatory'
    event_date          TEXT NOT NULL,
    event_time          TEXT,  -- 'Pre-Market', 'After-Hours', 'During'

    -- Description
    event_title         TEXT,
    event_description   TEXT,

    -- Impact Assessment
    expected_impact     TEXT,  -- 'High', 'Medium', 'Low'
    sentiment           TEXT,  -- 'Positive', 'Neutral', 'Negative', 'Unknown'

    -- For Earnings
    eps_estimate        REAL,
    revenue_estimate    REAL,

    -- For Dividends
    dividend_amount     REAL,
    ex_dividend_date    TEXT,

    -- Status
    is_confirmed        BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
);

CREATE INDEX IF NOT EXISTS idx_catalysts_stock ON src_stock_catalysts(stock_id);
CREATE INDEX IF NOT EXISTS idx_catalysts_date ON src_stock_catalysts(event_date);
CREATE INDEX IF NOT EXISTS idx_catalysts_type ON src_stock_catalysts(event_type);

-- ============================================================================
-- 5. CLIENT-STOCK RELATIONSHIP HISTORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_client_stock_history (
    history_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id           INTEGER NOT NULL,
    stock_id            INTEGER NOT NULL,

    -- Interaction Summary
    total_trades        INTEGER DEFAULT 0,
    total_buys          INTEGER DEFAULT 0,
    total_sells         INTEGER DEFAULT 0,
    net_direction       INTEGER DEFAULT 0,  -- buys - sells

    -- Value
    total_notional_est  REAL,
    avg_trade_size      TEXT,  -- 'Small', 'Medium', 'Large'

    -- Timing
    first_interaction   TEXT,
    last_interaction    TEXT,

    -- Reports Read
    reports_read        INTEGER DEFAULT 0,

    -- Calls Discussed
    calls_discussed     INTEGER DEFAULT 0,

    -- Current Status
    likely_holding      BOOLEAN DEFAULT FALSE,
    interest_level      TEXT,  -- 'High', 'Medium', 'Low', 'None'

    FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
    FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id),
    UNIQUE(client_id, stock_id)
);

CREATE INDEX IF NOT EXISTS idx_client_stock_client ON src_client_stock_history(client_id);
CREATE INDEX IF NOT EXISTS idx_client_stock_stock ON src_client_stock_history(stock_id);

-- ============================================================================
-- 6. SECTOR OVERVIEW
-- ============================================================================

CREATE TABLE IF NOT EXISTS src_sector_overview (
    sector_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name         TEXT NOT NULL UNIQUE,

    -- Current View
    sector_rating       TEXT,  -- 'Overweight', 'Neutral', 'Underweight'
    sector_analyst      TEXT,
    rating_date         TEXT,

    -- Thesis
    key_themes          TEXT,
    key_risks           TEXT,

    -- Metrics
    avg_pe              REAL,
    avg_dividend_yield  REAL,
    ytd_performance     REAL,

    -- Top Picks
    top_picks           TEXT  -- Comma-separated tickers
);

-- ============================================================================
-- 7. INSERT SAMPLE DATA
-- ============================================================================

-- Sample Client Preferences
INSERT OR IGNORE INTO src_client_preferences (client_id, prefers_dividends, prefers_growth, prefers_esg, preferred_sectors, preferred_themes, min_dividend_yield, max_volatility, preference_notes) VALUES
(1, 1, 0, 1, 'Utilities,Healthcare,Consumer Staples', 'ESG,Dividends', 0.03, 0.20, 'Conservative pension fund, focus on stable income and ESG compliance'),
(2, 0, 1, 0, 'Technology,Industrials,Consumer Discretionary', 'AI,Digital,Automation', NULL, 0.40, 'Aggressive hedge fund, seeking alpha through growth stories'),
(3, 1, 1, 0, 'Financials,Energy,Materials', 'Value,Cyclicals', 0.02, 0.30, 'Balanced approach, likes quality cyclicals with dividends'),
(4, 0, 1, 1, 'Technology,Healthcare', 'AI,Biotech,ESG', NULL, 0.35, 'Growth-focused family office with ESG considerations'),
(5, 1, 0, 0, 'Real Estate,Utilities,Telecoms', 'Dividends,Infrastructure', 0.04, 0.18, 'Income-focused insurance company, strict volatility limits');

-- Sample Stock Fundamentals (for existing stocks)
INSERT OR IGNORE INTO src_stock_fundamentals (stock_id, as_of_date, pe_ratio, pe_forward, dividend_yield, roe, profit_margin, revenue_growth_yoy, beta, market_cap, market_cap_bucket, quality_score) VALUES
(1, '2026-01-03', 18.5, 16.2, 0.032, 0.15, 0.12, 0.08, 0.95, 45000000000, 'Large', 78),
(2, '2026-01-03', 25.3, 22.1, 0.018, 0.22, 0.18, 0.15, 1.15, 120000000000, 'Mega', 85),
(3, '2026-01-03', 12.8, 11.5, 0.045, 0.12, 0.08, 0.03, 0.75, 8000000000, 'Mid', 65),
(4, '2026-01-03', 32.1, 28.5, 0.008, 0.28, 0.22, 0.25, 1.35, 200000000000, 'Mega', 82),
(5, '2026-01-03', 15.2, 14.0, 0.038, 0.14, 0.10, 0.05, 0.88, 22000000000, 'Large', 72),
(6, '2026-01-03', 22.5, 19.8, 0.022, 0.18, 0.14, 0.12, 1.05, 65000000000, 'Large', 76),
(7, '2026-01-03', 28.7, 24.2, 0.012, 0.25, 0.20, 0.18, 1.25, 95000000000, 'Large', 80),
(8, '2026-01-03', 10.5, 9.8, 0.055, 0.10, 0.06, 0.02, 0.65, 5000000000, 'Mid', 58),
(9, '2026-01-03', 35.2, 30.1, 0.005, 0.32, 0.25, 0.28, 1.45, 180000000000, 'Mega', 88),
(10, '2026-01-03', 14.8, 13.2, 0.042, 0.13, 0.09, 0.04, 0.70, 12000000000, 'Mid', 68);

-- Sample Analyst Ratings
INSERT OR IGNORE INTO src_analyst_ratings (stock_id, analyst_name, rating, rating_date, price_target, current_price, upside_percent, conviction_level, thesis_summary, key_catalysts) VALUES
(1, 'Dr. Schmidt', 'Outperform', '2026-01-02', 85.00, 72.50, 0.172, 'High', 'Strong market position, improving margins, ESG leader in sector', 'Q4 earnings beat, new product launch Q1'),
(2, 'Marie Dupont', 'Outperform', '2025-12-15', 145.00, 128.30, 0.130, 'High', 'AI transformation driving growth, dominant market share', 'AI product revenue acceleration'),
(3, 'Hans Weber', 'Neutral', '2025-12-20', 42.00, 41.20, 0.019, 'Medium', 'Stable but limited upside, dividend attractive', 'Dividend increase expected'),
(4, 'Sophie Martin', 'Outperform', '2026-01-01', 420.00, 385.00, 0.091, 'High', 'Cloud growth reaccelerating, AI monetization beginning', 'Q4 cloud numbers, AI revenue disclosure'),
(5, 'Thomas Mueller', 'Neutral', '2025-12-18', 58.00, 55.80, 0.039, 'Low', 'Defensive quality, fair valuation', 'Stable performer, limited catalysts'),
(6, 'Jean-Pierre Blanc', 'Outperform', '2025-12-22', 92.00, 78.50, 0.172, 'Medium', 'Beneficiary of industrial automation trend', 'Order book growth, margin expansion'),
(7, 'Anna Lindberg', 'Outperform', '2025-12-28', 165.00, 142.00, 0.162, 'High', 'Healthcare AI platform gaining traction', 'FDA approval, partnership announcements'),
(8, 'Peter Janssen', 'Underperform', '2025-12-10', 28.00, 32.50, -0.138, 'Medium', 'Structural challenges, market share loss', 'Turnaround uncertain, cash burn concerns'),
(9, 'Claire Fontaine', 'Outperform', '2026-01-02', 520.00, 465.00, 0.118, 'High', 'Dominant position in growing market', 'Expansion into new verticals'),
(10, 'Erik Svensson', 'Neutral', '2025-12-12', 38.00, 36.20, 0.050, 'Low', 'Value trap risk, but dividend safe', 'Cost cutting progress needed');

-- Sample Upcoming Catalysts
INSERT OR IGNORE INTO src_stock_catalysts (stock_id, event_type, event_date, event_time, event_title, expected_impact, sentiment, eps_estimate, revenue_estimate) VALUES
(1, 'Earnings', '2026-01-28', 'Pre-Market', 'Q4 2025 Results', 'High', 'Positive', 1.85, 12500),
(2, 'Earnings', '2026-01-30', 'After-Hours', 'Q4 2025 Results', 'High', 'Positive', 2.45, 28000),
(4, 'Earnings', '2026-02-04', 'After-Hours', 'Q4 2025 Results', 'High', 'Positive', 5.20, 95000),
(1, 'Dividend', '2026-02-15', NULL, 'Q4 Dividend Payment', 'Low', 'Positive', NULL, NULL),
(3, 'Dividend', '2026-02-10', NULL, 'Annual Dividend', 'Medium', 'Positive', NULL, NULL),
(6, 'Conference', '2026-01-15', 'During', 'Industry Conference Presentation', 'Medium', 'Neutral', NULL, NULL),
(7, 'Product Launch', '2026-02-20', NULL, 'AI Platform 2.0 Launch', 'High', 'Positive', NULL, NULL),
(9, 'Regulatory', '2026-01-20', NULL, 'EU Regulatory Decision', 'High', 'Unknown', NULL, NULL),
(2, 'Conference', '2026-01-22', 'During', 'Tech Investor Day', 'Medium', 'Positive', NULL, NULL),
(5, 'AGM', '2026-03-15', 'During', 'Annual General Meeting', 'Low', 'Neutral', NULL, NULL);

-- Sample Sector Overview
INSERT OR IGNORE INTO src_sector_overview (sector_name, sector_rating, sector_analyst, rating_date, key_themes, key_risks, avg_pe, avg_dividend_yield, ytd_performance, top_picks) VALUES
('Technology', 'Overweight', 'Marie Dupont', '2026-01-01', 'AI adoption, cloud growth, digital transformation', 'Valuation stretch, regulatory risks, rate sensitivity', 28.5, 0.012, 0.15, 'MSFT,SAP,ASML'),
('Healthcare', 'Overweight', 'Anna Lindberg', '2026-01-01', 'Aging demographics, GLP-1 drugs, AI diagnostics', 'Pricing pressure, patent cliffs, clinical trial risks', 22.3, 0.018, 0.08, 'NVO,ROG,AZN'),
('Financials', 'Neutral', 'Hans Weber', '2026-01-01', 'Higher rates benefit, digital banking', 'Credit cycle concerns, regulation', 10.5, 0.045, 0.05, 'BNP,ING,HSBA'),
('Industrials', 'Overweight', 'Jean-Pierre Blanc', '2026-01-01', 'Automation, reshoring, infrastructure', 'China slowdown, supply chain', 18.2, 0.025, 0.10, 'SIE,ABB,AIR'),
('Energy', 'Neutral', 'Thomas Mueller', '2026-01-01', 'Energy transition, LNG demand', 'Oil price volatility, stranded assets', 8.5, 0.055, -0.02, 'SHEL,TTE,EQNR'),
('Consumer Staples', 'Underweight', 'Peter Janssen', '2026-01-01', 'Defensive, pricing power', 'Volume pressure, GLP-1 impact', 20.1, 0.032, 0.03, 'NESN,OR,UNA'),
('Utilities', 'Neutral', 'Erik Svensson', '2026-01-01', 'Renewables growth, grid investment', 'Rate sensitivity, regulatory', 15.5, 0.048, 0.02, 'ENEL,IBE,ORSTED');

-- ============================================================================
-- 8. UPDATE CLIENT-STOCK HISTORY (Aggregate from trades)
-- ============================================================================

INSERT OR REPLACE INTO src_client_stock_history (client_id, stock_id, total_trades, total_buys, total_sells, net_direction, first_interaction, last_interaction, likely_holding, interest_level)
SELECT
    t.client_id,
    t.stock_id,
    COUNT(*) as total_trades,
    SUM(CASE WHEN t.side = 'Buy' THEN 1 ELSE 0 END) as total_buys,
    SUM(CASE WHEN t.side = 'Sell' THEN 1 ELSE 0 END) as total_sells,
    SUM(CASE WHEN t.side = 'Buy' THEN 1 ELSE -1 END) as net_direction,
    MIN(t.trade_timestamp) as first_interaction,
    MAX(t.trade_timestamp) as last_interaction,
    CASE WHEN SUM(CASE WHEN t.side = 'Buy' THEN 1 ELSE -1 END) > 0 THEN 1 ELSE 0 END as likely_holding,
    CASE
        WHEN COUNT(*) >= 5 THEN 'High'
        WHEN COUNT(*) >= 2 THEN 'Medium'
        ELSE 'Low'
    END as interest_level
FROM src_trade_executions t
WHERE t.stock_id IS NOT NULL
GROUP BY t.client_id, t.stock_id;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
