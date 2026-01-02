# Analytics Enhancement - Statistische Signifikanz verbessern

## Aktuelle Probleme

### 1. Risk Score (int_client_profile)

**Aktuell:**
```sql
risk_score = 0.40 * PERCENT_RANK(size_proxy)
           + 0.35 * PERCENT_RANK(trade_count)
           + 0.25 * PERCENT_RANK(concentration)
```

**Probleme:**
- ❌ Ignoriert **Volatilität der gehaltenen Aktien** (72.300 Datenpunkte ungenutzt!)
- ❌ Relative Ranks statt absolute Risikometriken
- ❌ Keine Gewichtung nach Positionsgröße
- ❌ Arbiträre Gewichte (0.40, 0.35, 0.25)

**Vorschlag - Portfolio-basierter VaR-Proxy:**
```sql
portfolio_risk = Σ(position_weight × stock_vol_60d)
```

---

### 2. Engagement Level

**Aktuell:**
- `call_count >= 6` → High Touch
- `call_count >= 3` → Regular

**Probleme:**
- ❌ Keine Berücksichtigung der **Call-Dauer**
- ❌ Keine **Recency** (Calls vor 1 Monat = Calls vor 1 Jahr)
- ❌ Keine **Trend-Erkennung** (steigend/fallend)

**Vorschlag - Time-Weighted Engagement:**
```sql
engagement_score = Σ(call_duration × recency_weight)
-- recency_weight = exp(-days_ago / 90)  -- 90-Tage Halbwertszeit
```

---

### 3. Trade Activity

**Aktuell:**
- Einfache Zählung aller Trades

**Probleme:**
- ❌ Keine **Momentum-Erkennung** (beschleunigt/verlangsamt)
- ❌ Keine **Saisonalität** (Quartalsende-Aktivität)
- ❌ Keine **Conviction** (Häufung in bestimmten Aktien)

**Vorschlag:**
```sql
trade_momentum = trades_last_30d / trades_prior_30d
conviction_score = MAX(stock_trade_count) / total_trades
```

---

### 4. Readership Analysis

**Aktuell:**
- `days_diff` = Tage zwischen Publikation und Lesen

**Probleme:**
- ❌ Keine **Report-Type Präferenz** (liest nur Initiation? Nur Sector?)
- ❌ Keine **Engagement-Tiefe** (wie schnell nach Publikation?)
- ❌ Keine **Coverage-Breite** (wie viele verschiedene Sektoren?)

**Vorschlag:**
```sql
read_velocity = 1 / (1 + avg_days_diff)  -- Schnelligkeit
read_breadth = COUNT(DISTINCT sector) / total_sectors  -- Breite
read_depth = reads_per_report_type  -- Präferenz
```

---

### 5. Position Hints (Call Notes)

**Aktuell:**
```sql
CASE WHEN txt LIKE '%hold%' OR txt LIKE '%already%' THEN 1 ELSE 0 END
```

**Probleme:**
- ❌ Einfaches Keyword-Matching (hohe False-Positive-Rate)
- ❌ Keine **Sentiment-Stärke** (leicht interessiert vs. sehr überzeugt)
- ❌ Keine **Negation-Erkennung** ("not interested" → false positive für "interested")

**Vorschlag:**
- Erweiterte Patterns mit Kontext
- Sentiment-Wörter zählen und gewichten
- Negation-Patterns ausschließen

---

## Ungenutzte Datenquellen

| Daten | Zeilen | Aktuell genutzt? | Potenzial |
|-------|--------|------------------|-----------|
| `src_stock_volatility` | 72.300 | ❌ NEIN | Portfolio-Risiko |
| `src_stock_returns` | 78.000 | ❌ NEIN | Momentum-Signale |
| `src_stock_prices` | 78.000 | ⚠️ Nur close | Trend-Analyse |
| `src_positions.weight` | 514 | ⚠️ Nur Anzeige | Konzentrations-Risiko |
| `src_call_logs.duration` | 2.169 | ⚠️ Nur avg | Engagement-Tiefe |

---

## Neue Metriken (Vorschlag)

### A. Portfolio Risk Score (NEU)

```sql
CREATE VIEW ana_client_portfolio_risk AS
WITH latest_snap AS (
  SELECT client_id, MAX(snapshot_id) as snap_id
  FROM src_portfolio_snapshots
  GROUP BY client_id
),
pos_vol AS (
  SELECT
    p.snapshot_id,
    ls.client_id,
    p.weight,
    v.vol_60d,
    p.weight * COALESCE(v.vol_60d, 0.25) AS weighted_vol
  FROM src_positions p
  JOIN latest_snap ls ON ls.snap_id = p.snapshot_id
  LEFT JOIN (
    SELECT stock_id, vol_60d
    FROM src_stock_volatility
    WHERE (stock_id, vol_date) IN (
      SELECT stock_id, MAX(vol_date) FROM src_stock_volatility GROUP BY stock_id
    )
  ) v ON v.stock_id = p.stock_id
)
SELECT
  client_id,
  SUM(weighted_vol) AS portfolio_volatility,  -- VaR-Proxy
  MAX(weight) AS max_position_weight,         -- Concentration
  COUNT(CASE WHEN weight > 0.10 THEN 1 END) AS large_positions,
  CASE
    WHEN SUM(weighted_vol) >= 0.25 THEN 'High'
    WHEN SUM(weighted_vol) >= 0.15 THEN 'Medium'
    ELSE 'Low'
  END AS volatility_bucket
FROM pos_vol
GROUP BY client_id;
```

### B. Engagement Momentum (NEU)

```sql
CREATE VIEW ana_client_engagement_momentum AS
WITH calls_30d AS (
  SELECT client_id, COUNT(*) as cnt, SUM(duration_minutes) as dur
  FROM src_call_logs
  WHERE julianday('now') - julianday(call_timestamp) <= 30
  GROUP BY client_id
),
calls_60d AS (
  SELECT client_id, COUNT(*) as cnt, SUM(duration_minutes) as dur
  FROM src_call_logs
  WHERE julianday('now') - julianday(call_timestamp) BETWEEN 31 AND 60
  GROUP BY client_id
),
trades_30d AS (
  SELECT client_id, COUNT(*) as cnt
  FROM src_trade_executions
  WHERE julianday('now') - julianday(trade_timestamp) <= 30
  GROUP BY client_id
),
trades_60d AS (
  SELECT client_id, COUNT(*) as cnt
  FROM src_trade_executions
  WHERE julianday('now') - julianday(trade_timestamp) BETWEEN 31 AND 60
  GROUP BY client_id
)
SELECT
  c.client_id,
  COALESCE(c30.cnt, 0) AS calls_last_30d,
  COALESCE(c60.cnt, 0) AS calls_prior_30d,
  ROUND(1.0 * COALESCE(c30.cnt, 0) / NULLIF(COALESCE(c60.cnt, 1), 0), 2) AS call_momentum,
  COALESCE(t30.cnt, 0) AS trades_last_30d,
  COALESCE(t60.cnt, 0) AS trades_prior_30d,
  ROUND(1.0 * COALESCE(t30.cnt, 0) / NULLIF(COALESCE(t60.cnt, 1), 0), 2) AS trade_momentum,
  CASE
    WHEN 1.0 * COALESCE(c30.cnt, 0) / NULLIF(COALESCE(c60.cnt, 1), 0) >= 1.5 THEN 'Increasing'
    WHEN 1.0 * COALESCE(c30.cnt, 0) / NULLIF(COALESCE(c60.cnt, 1), 0) <= 0.5 THEN 'Decreasing'
    ELSE 'Stable'
  END AS engagement_trend
FROM src_clients c
LEFT JOIN calls_30d c30 ON c30.client_id = c.client_id
LEFT JOIN calls_60d c60 ON c60.client_id = c.client_id
LEFT JOIN trades_30d t30 ON t30.client_id = c.client_id
LEFT JOIN trades_60d t60 ON t60.client_id = c.client_id;
```

### C. Conviction Score (NEU)

```sql
CREATE VIEW ana_client_conviction AS
WITH stock_focus AS (
  SELECT
    client_id,
    ticker,
    COUNT(*) AS trade_count,
    1.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY client_id) AS focus_share
  FROM src_trade_executions
  WHERE ticker IS NOT NULL
  GROUP BY client_id, ticker
),
call_focus AS (
  SELECT
    cl.client_id,
    s.ticker,
    COUNT(*) AS mention_count
  FROM src_call_logs cl
  JOIN src_stocks s ON s.stock_id = cl.stock_id
  GROUP BY cl.client_id, s.ticker
)
SELECT
  sf.client_id,
  sf.ticker AS top_conviction_stock,
  sf.focus_share AS trade_concentration,
  COALESCE(cf.mention_count, 0) AS call_mentions,
  sf.trade_count + COALESCE(cf.mention_count, 0) * 2 AS conviction_score,
  CASE
    WHEN sf.focus_share >= 0.20 THEN 'High Conviction'
    WHEN sf.focus_share >= 0.10 THEN 'Moderate Conviction'
    ELSE 'Diversified'
  END AS conviction_level
FROM stock_focus sf
LEFT JOIN call_focus cf ON cf.client_id = sf.client_id AND cf.ticker = sf.ticker
WHERE sf.focus_share = (
  SELECT MAX(focus_share) FROM stock_focus sf2 WHERE sf2.client_id = sf.client_id
);
```

### D. Readership Intelligence (NEU)

```sql
CREATE VIEW ana_client_readership_intelligence AS
WITH read_stats AS (
  SELECT
    r.client_id,
    rp.report_type,
    rp.sector,
    COUNT(*) AS read_count,
    AVG(r.days_diff) AS avg_days_diff
  FROM ana_readership_daysdiff r
  JOIN src_reports rp ON rp.report_id = r.report_id
  GROUP BY r.client_id, rp.report_type, rp.sector
),
type_pref AS (
  SELECT client_id, report_type, read_count,
    ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY read_count DESC) as rn
  FROM read_stats
  GROUP BY client_id, report_type
),
sector_pref AS (
  SELECT client_id, sector, SUM(read_count) as read_count,
    ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY SUM(read_count) DESC) as rn
  FROM read_stats
  GROUP BY client_id, sector
)
SELECT
  c.client_id,
  tp.report_type AS preferred_report_type,
  sp.sector AS preferred_sector,
  ROUND(1.0 / (1 + rs.avg_days_diff), 3) AS read_velocity,  -- Higher = faster reader
  COUNT(DISTINCT rs.sector) AS sector_breadth,
  CASE
    WHEN rs.avg_days_diff <= 2 THEN 'Fast'
    WHEN rs.avg_days_diff <= 5 THEN 'Normal'
    ELSE 'Slow'
  END AS reader_type
FROM src_clients c
LEFT JOIN read_stats rs ON rs.client_id = c.client_id
LEFT JOIN type_pref tp ON tp.client_id = c.client_id AND tp.rn = 1
LEFT JOIN sector_pref sp ON sp.client_id = c.client_id AND sp.rn = 1
GROUP BY c.client_id;
```

---

## Neuer Combined Risk Score

```sql
CREATE VIEW int_client_risk_enhanced AS
SELECT
  cp.client_id,

  -- Portfolio-based risk (from actual volatility)
  COALESCE(pr.portfolio_volatility, 0.20) AS portfolio_vol,

  -- Behavioral risk (from trading patterns)
  ps.concentration_index AS trade_concentration,

  -- Combined score (70% portfolio, 30% behavior)
  ROUND(
    0.70 * COALESCE(pr.portfolio_volatility, 0.20) / 0.30  -- normalize to 0-1
    + 0.30 * COALESCE(ps.concentration_index, 0.25),
    3
  ) AS combined_risk_score,

  -- Momentum adjustment
  CASE
    WHEN em.trade_momentum > 1.5 THEN 'Accelerating'
    WHEN em.trade_momentum < 0.5 THEN 'Decelerating'
    ELSE 'Stable'
  END AS activity_trend,

  -- Final risk bucket
  CASE
    WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.25
      OR COALESCE(ps.concentration_index, 0.25) >= 0.40 THEN 'High'
    WHEN COALESCE(pr.portfolio_volatility, 0.20) >= 0.15
      OR COALESCE(ps.concentration_index, 0.25) >= 0.25 THEN 'Medium'
    ELSE 'Low'
  END AS risk_level

FROM int_client_profile cp
LEFT JOIN ana_client_portfolio_risk pr ON pr.client_id = cp.client_id
LEFT JOIN int_client_portfolio_summary ps ON ps.client_id = cp.client_id
LEFT JOIN ana_client_engagement_momentum em ON em.client_id = cp.client_id;
```

---

## Zusammenfassung der Verbesserungen

| Metrik | Alt | Neu | Verbesserung |
|--------|-----|-----|--------------|
| Risk Score | Relative Ranks | Portfolio-Volatilität | +Signifikanz |
| Engagement | Count only | Time-weighted + Momentum | +Trend |
| Conviction | Nicht vorhanden | Trade + Call Focus | NEU |
| Readership | days_diff only | Velocity + Breadth + Preference | +Tiefe |
| Activity | Static count | 30d/60d Momentum | +Dynamik |

---

## Implementation Priority

1. **HIGH**: `ana_client_portfolio_risk` - Nutzt ungenutzte Vol-Daten
2. **HIGH**: `ana_client_engagement_momentum` - Trend-Erkennung
3. **MEDIUM**: `ana_client_conviction` - Fokus-Erkennung
4. **MEDIUM**: `ana_client_readership_intelligence` - Präferenz-Analyse
5. **LOW**: Enhanced keyword patterns - Weniger False Positives
