-- ============================================================================
-- ENHANCED ANALYTICS VIEWS
-- Statistically significant metrics using previously unused data
-- ============================================================================

-- ============================================================================
-- 1. PORTFOLIO RISK (uses src_stock_volatility - previously unused!)
-- ============================================================================

-- SQLite version
CREATE VIEW IF NOT EXISTS ana_client_portfolio_risk AS
WITH latest_snap AS (
  SELECT client_id, MAX(snapshot_id) as snap_id
  FROM src_portfolio_snapshots
  GROUP BY client_id
),
latest_vol AS (
  SELECT stock_id, vol_60d, vol_20d
  FROM src_stock_volatility
  WHERE (stock_id, vol_date) IN (
    SELECT stock_id, MAX(vol_date) FROM src_stock_volatility GROUP BY stock_id
  )
),
pos_vol AS (
  SELECT
    ls.client_id,
    p.stock_id,
    p.weight,
    p.market_value,
    COALESCE(v.vol_60d, 0.25) AS vol_60d,
    COALESCE(v.vol_20d, 0.20) AS vol_20d,
    p.weight * COALESCE(v.vol_60d, 0.25) AS weighted_vol
  FROM src_positions p
  JOIN latest_snap ls ON ls.snap_id = p.snapshot_id
  LEFT JOIN latest_vol v ON v.stock_id = p.stock_id
)
SELECT
  client_id,

  -- Portfolio volatility (VaR proxy)
  ROUND(SUM(weighted_vol), 4) AS portfolio_volatility,

  -- Concentration metrics
  MAX(weight) AS max_position_weight,
  COUNT(*) AS total_positions,
  SUM(CASE WHEN weight > 0.10 THEN 1 ELSE 0 END) AS large_positions,
  SUM(CASE WHEN weight > 0.05 THEN 1 ELSE 0 END) AS medium_positions,

  -- Volatility distribution
  AVG(vol_60d) AS avg_stock_volatility,
  MAX(vol_60d) AS max_stock_volatility,
  SUM(CASE WHEN vol_60d > 0.30 THEN weight ELSE 0 END) AS high_vol_exposure,

  -- Risk buckets
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

FROM pos_vol
GROUP BY client_id;


-- ============================================================================
-- 2. ENGAGEMENT MOMENTUM (30d vs 60d comparison)
-- ============================================================================

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
  SELECT
    client_id,
    COUNT(*) as cnt,
    SUM(duration_minutes) as total_dur
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
  SELECT
    client_id,
    COUNT(*) as cnt
  FROM src_trade_executions
  WHERE julianday('now') - julianday(trade_timestamp) BETWEEN 31 AND 60
  GROUP BY client_id
)
SELECT
  c.client_id,

  -- Call metrics
  COALESCE(cr.cnt, 0) AS calls_last_30d,
  COALESCE(cp.cnt, 0) AS calls_prior_30d,
  ROUND(COALESCE(cr.avg_dur, 0), 1) AS avg_call_duration_30d,
  ROUND(
    1.0 * COALESCE(cr.cnt, 0) / NULLIF(COALESCE(cp.cnt, 0), 0),
    2
  ) AS call_momentum,

  -- Trade metrics
  COALESCE(tr.cnt, 0) AS trades_last_30d,
  COALESCE(tp.cnt, 0) AS trades_prior_30d,
  ROUND(
    1.0 * COALESCE(tr.cnt, 0) / NULLIF(COALESCE(tp.cnt, 0), 0),
    2
  ) AS trade_momentum,

  -- Directional signal (recent buys vs total)
  CASE
    WHEN tr.cnt > 0 THEN ROUND(1.0 * tr.buys / tr.cnt, 2)
    ELSE NULL
  END AS recent_buy_ratio,

  -- Size signal (large trades increasing?)
  COALESCE(tr.large_trades, 0) AS large_trades_30d,

  -- Combined engagement score
  ROUND(
    COALESCE(cr.total_dur, 0) * 0.1  -- Call time weighted
    + COALESCE(tr.cnt, 0) * 2.0      -- Trade count weighted
    + COALESCE(tr.large_trades, 0) * 5.0,  -- Large trades bonus
    1
  ) AS engagement_score_30d,

  -- Trend classification
  CASE
    WHEN COALESCE(cr.cnt, 0) > COALESCE(cp.cnt, 0) * 1.5
      OR COALESCE(tr.cnt, 0) > COALESCE(tp.cnt, 0) * 1.5 THEN 'Accelerating'
    WHEN COALESCE(cr.cnt, 0) < COALESCE(cp.cnt, 0) * 0.5
      AND COALESCE(tr.cnt, 0) < COALESCE(tp.cnt, 0) * 0.5 THEN 'Cooling Off'
    WHEN COALESCE(cr.cnt, 0) = 0 AND COALESCE(tr.cnt, 0) = 0 THEN 'Dormant'
    ELSE 'Stable'
  END AS engagement_trend

FROM src_clients c
LEFT JOIN calls_recent cr ON cr.client_id = c.client_id
LEFT JOIN calls_prior cp ON cp.client_id = c.client_id
LEFT JOIN trades_recent tr ON tr.client_id = c.client_id
LEFT JOIN trades_prior tp ON tp.client_id = c.client_id;


-- ============================================================================
-- 3. CONVICTION SCORE (Trade + Call focus on specific stocks)
-- ============================================================================

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
call_focus AS (
  SELECT
    cl.client_id,
    s.ticker,
    s.stock_id,
    COUNT(*) AS mention_count,
    SUM(CASE WHEN LOWER(cl.notes_raw) LIKE '%bullish%'
              OR LOWER(cl.notes_raw) LIKE '%positive%'
              OR LOWER(cl.notes_raw) LIKE '%upside%' THEN 1 ELSE 0 END) AS bullish_mentions,
    SUM(CASE WHEN LOWER(cl.notes_raw) LIKE '%bearish%'
              OR LOWER(cl.notes_raw) LIKE '%concern%'
              OR LOWER(cl.notes_raw) LIKE '%risk%' THEN 1 ELSE 0 END) AS bearish_mentions
  FROM src_call_logs cl
  JOIN src_stocks s ON s.stock_id = cl.stock_id
  WHERE cl.notes_raw IS NOT NULL
  GROUP BY cl.client_id, s.ticker, s.stock_id
),
combined AS (
  SELECT
    COALESCE(tf.client_id, cf.client_id) AS client_id,
    COALESCE(tf.ticker, cf.ticker) AS ticker,
    COALESCE(tf.stock_id, cf.stock_id) AS stock_id,
    COALESCE(tf.trade_count, 0) AS trade_count,
    COALESCE(tf.net_direction, 0) AS net_direction,
    COALESCE(tf.focus_share, 0) AS trade_focus_share,
    COALESCE(cf.mention_count, 0) AS call_mentions,
    COALESCE(cf.bullish_mentions, 0) AS bullish_mentions,
    COALESCE(cf.bearish_mentions, 0) AS bearish_mentions,
    -- Conviction score: trades + weighted call mentions + sentiment
    COALESCE(tf.trade_count, 0)
    + COALESCE(cf.mention_count, 0) * 2
    + COALESCE(cf.bullish_mentions, 0) * 3
    - COALESCE(cf.bearish_mentions, 0) * 2 AS conviction_score
  FROM trade_focus tf
  FULL OUTER JOIN call_focus cf
    ON cf.client_id = tf.client_id AND cf.stock_id = tf.stock_id
),
ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY conviction_score DESC) AS rn
  FROM combined
)
SELECT
  client_id,
  ticker AS top_conviction_stock,
  stock_id AS top_conviction_stock_id,
  trade_count,
  call_mentions,
  net_direction,
  ROUND(trade_focus_share, 3) AS trade_concentration,
  conviction_score,
  bullish_mentions,
  bearish_mentions,
  CASE
    WHEN trade_focus_share >= 0.25 THEN 'Very High'
    WHEN trade_focus_share >= 0.15 THEN 'High'
    WHEN trade_focus_share >= 0.08 THEN 'Moderate'
    ELSE 'Diversified'
  END AS conviction_level,
  CASE
    WHEN net_direction > 0 AND bullish_mentions > bearish_mentions THEN 'Bullish'
    WHEN net_direction < 0 AND bearish_mentions > bullish_mentions THEN 'Bearish'
    WHEN net_direction > 0 THEN 'Accumulating'
    WHEN net_direction < 0 THEN 'Reducing'
    ELSE 'Neutral'
  END AS sentiment_signal
FROM ranked
WHERE rn = 1;


-- ============================================================================
-- 4. READERSHIP INTELLIGENCE (velocity, breadth, preferences)
-- ============================================================================

CREATE VIEW IF NOT EXISTS ana_client_readership_intelligence AS
WITH read_by_type AS (
  SELECT
    r.client_id,
    rp.report_type,
    COUNT(*) AS read_count,
    AVG(r.days_diff) AS avg_days_diff
  FROM ana_readership_daysdiff r
  JOIN src_reports rp ON rp.report_id = r.report_id
  GROUP BY r.client_id, rp.report_type
),
read_by_sector AS (
  SELECT
    r.client_id,
    rp.sector,
    COUNT(*) AS read_count
  FROM ana_readership_daysdiff r
  JOIN src_reports rp ON rp.report_id = r.report_id
  WHERE rp.sector IS NOT NULL
  GROUP BY r.client_id, rp.sector
),
type_pref AS (
  SELECT client_id, report_type, read_count, avg_days_diff,
    ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY read_count DESC) as rn
  FROM read_by_type
),
sector_pref AS (
  SELECT client_id, sector, read_count,
    ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY read_count DESC) as rn
  FROM read_by_sector
),
client_totals AS (
  SELECT
    client_id,
    COUNT(*) AS total_reads,
    AVG(days_diff) AS overall_avg_days_diff,
    COUNT(DISTINCT report_sector) AS sector_breadth,
    SUM(CASE WHEN days_diff <= 1 THEN 1 ELSE 0 END) AS same_day_reads,
    SUM(CASE WHEN days_diff >= 7 THEN 1 ELSE 0 END) AS late_reads
  FROM ana_readership_daysdiff
  GROUP BY client_id
)
SELECT
  ct.client_id,
  ct.total_reads,
  ct.sector_breadth,

  -- Preferred content
  tp.report_type AS preferred_report_type,
  sp.sector AS preferred_sector,

  -- Velocity metrics
  ROUND(ct.overall_avg_days_diff, 1) AS avg_read_delay_days,
  ROUND(1.0 / (1 + ct.overall_avg_days_diff), 3) AS read_velocity_score,
  ROUND(1.0 * ct.same_day_reads / ct.total_reads, 2) AS same_day_read_ratio,
  ROUND(1.0 * ct.late_reads / ct.total_reads, 2) AS late_read_ratio,

  -- Reader classification
  CASE
    WHEN ct.overall_avg_days_diff <= 1 THEN 'Immediate'
    WHEN ct.overall_avg_days_diff <= 3 THEN 'Fast'
    WHEN ct.overall_avg_days_diff <= 7 THEN 'Normal'
    ELSE 'Slow'
  END AS reader_speed_type,

  CASE
    WHEN ct.sector_breadth >= 8 THEN 'Generalist'
    WHEN ct.sector_breadth >= 4 THEN 'Multi-Sector'
    ELSE 'Specialist'
  END AS reader_breadth_type,

  -- Engagement quality
  ROUND(
    ct.total_reads * 0.3
    + (1.0 / (1 + ct.overall_avg_days_diff)) * 50
    + ct.sector_breadth * 2,
    1
  ) AS readership_quality_score

FROM client_totals ct
LEFT JOIN type_pref tp ON tp.client_id = ct.client_id AND tp.rn = 1
LEFT JOIN sector_pref sp ON sp.client_id = ct.client_id AND sp.rn = 1;


-- ============================================================================
-- 5. ENHANCED CLIENT RISK (combines all new signals)
-- ============================================================================

CREATE VIEW IF NOT EXISTS int_client_risk_enhanced AS
SELECT
  cp.client_id,

  -- From original profile
  cp.risk_appetite AS original_risk_appetite,
  cp.risk_score AS original_risk_score,

  -- Portfolio-based risk (NEW - from actual volatility)
  COALESCE(pr.portfolio_volatility, 0.20) AS portfolio_volatility,
  pr.volatility_risk_level,
  pr.max_position_weight,
  pr.concentration_risk_level,

  -- Behavioral signals (NEW)
  em.engagement_trend,
  em.trade_momentum,
  em.call_momentum,
  em.recent_buy_ratio,

  -- Conviction (NEW)
  cv.top_conviction_stock,
  cv.conviction_level,
  cv.sentiment_signal,

  -- Readership (NEW)
  ri.reader_speed_type,
  ri.reader_breadth_type,
  ri.preferred_sector AS reading_focus_sector,

  -- ENHANCED RISK SCORE
  -- 40% portfolio vol, 30% concentration, 20% momentum, 10% conviction
  ROUND(
    0.40 * COALESCE(pr.portfolio_volatility, 0.20) / 0.30  -- normalize assuming 0.30 = high
    + 0.30 * COALESCE(ps.concentration_index, 0.25)
    + 0.20 * (CASE
        WHEN em.engagement_trend = 'Accelerating' THEN 0.8
        WHEN em.engagement_trend = 'Stable' THEN 0.5
        ELSE 0.2
      END)
    + 0.10 * (CASE cv.conviction_level
        WHEN 'Very High' THEN 0.9
        WHEN 'High' THEN 0.7
        WHEN 'Moderate' THEN 0.4
        ELSE 0.2
      END),
    3
  ) AS enhanced_risk_score,

  -- FINAL RISK LEVEL (evidence-based)
  CASE
    WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.25
      OR pr.concentration_risk_level = 'Concentrated' THEN 'High'
    WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.15
      OR ps.concentration_index >= 0.30 THEN 'Medium'
    ELSE 'Low'
  END AS enhanced_risk_level,

  -- ACTIONABLE INSIGHTS
  CASE
    WHEN em.engagement_trend = 'Accelerating' AND cv.sentiment_signal = 'Bullish'
      THEN 'Hot Lead - High Activity + Bullish'
    WHEN em.engagement_trend = 'Cooling Off'
      THEN 'Re-engage - Activity Declining'
    WHEN em.engagement_trend = 'Dormant'
      THEN 'Wake Up Call Needed'
    WHEN cv.conviction_level IN ('Very High', 'High') AND cv.sentiment_signal = 'Reducing'
      THEN 'Position Change - Watch Closely'
    ELSE 'Normal Engagement'
  END AS action_signal

FROM int_client_profile cp
LEFT JOIN ana_client_portfolio_risk pr ON pr.client_id = cp.client_id
LEFT JOIN int_client_portfolio_summary ps ON ps.client_id = cp.client_id
LEFT JOIN ana_client_engagement_momentum em ON em.client_id = cp.client_id
LEFT JOIN ana_client_conviction cv ON cv.client_id = cp.client_id
LEFT JOIN ana_client_readership_intelligence ri ON ri.client_id = cp.client_id;


-- ============================================================================
-- 6. SECTOR MOMENTUM (market-wide signals)
-- ============================================================================

CREATE VIEW IF NOT EXISTS ana_sector_momentum AS
WITH recent_trades AS (
  SELECT
    sector,
    SUM(CASE WHEN side = 'Buy' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN side = 'Sell' THEN 1 ELSE 0 END) AS sells,
    COUNT(*) AS total_trades,
    COUNT(DISTINCT client_id) AS unique_clients
  FROM src_trade_executions
  WHERE julianday('now') - julianday(trade_timestamp) <= 30
    AND sector IS NOT NULL
  GROUP BY sector
),
prior_trades AS (
  SELECT
    sector,
    COUNT(*) AS total_trades
  FROM src_trade_executions
  WHERE julianday('now') - julianday(trade_timestamp) BETWEEN 31 AND 60
    AND sector IS NOT NULL
  GROUP BY sector
)
SELECT
  rt.sector,
  rt.total_trades AS trades_30d,
  COALESCE(pt.total_trades, 0) AS trades_prior_30d,
  rt.buys,
  rt.sells,
  rt.unique_clients,
  ROUND(1.0 * rt.buys / NULLIF(rt.total_trades, 0), 2) AS buy_ratio,
  ROUND(1.0 * rt.total_trades / NULLIF(COALESCE(pt.total_trades, 0), 0), 2) AS momentum,
  CASE
    WHEN rt.buys > rt.sells * 1.5 THEN 'Strong Buy'
    WHEN rt.buys > rt.sells THEN 'Mild Buy'
    WHEN rt.sells > rt.buys * 1.5 THEN 'Strong Sell'
    WHEN rt.sells > rt.buys THEN 'Mild Sell'
    ELSE 'Balanced'
  END AS flow_signal
FROM recent_trades rt
LEFT JOIN prior_trades pt ON pt.sector = rt.sector
ORDER BY rt.total_trades DESC;
