"""
Stock Fundamentals Data Provider
================================

Fetches real fundamental data via yfinance to enrich synthetic reports.
Includes: Valuation, Profitability, Growth, Dividends, Analyst Ratings, Holdings.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed. Run: pip install yfinance")


# =============================================================================
# Ticker Mappings for European Stocks
# =============================================================================

# Map database tickers to Yahoo Finance tickers
TICKER_MAPPINGS = {
    # German stocks (XETRA)
    "SIE.DE": "SIE.DE",
    "DBK.DE": "DBK.DE",
    "ALV.DE": "ALV.DE",
    "MUV2.DE": "MUV2.DE",
    "BAYN.DE": "BAYN.DE",
    "ADS.DE": "ADS.DE",
    "VOW3.DE": "VOW3.DE",
    "BMW.DE": "BMW.DE",
    "MBG.DE": "MBG.DE",
    "P911.DE": "P911.DE",
    "DTE.DE": "DTE.DE",

    # French stocks (Euronext Paris)
    "MC.PA": "MC.PA",
    "RMS.PA": "RMS.PA",
    "KER.PA": "KER.PA",
    "OR.PA": "OR.PA",
    "AIR.PA": "AIR.PA",
    "SU.PA": "SU.PA",
    "BNP.PA": "BNP.PA",
    "GLE.PA": "GLE.PA",
    "SAN.PA": "SAN.PA",
    "TTE.PA": "TTE.PA",
    "DG.PA": "DG.PA",
    "ENGI.PA": "ENGI.PA",
    "DSY.PA": "DSY.PA",

    # Dutch stocks
    "ASML": "ASML",
    "INGA.AS": "INGA.AS",

    # Swiss stocks
    "NESN.SW": "NESN.SW",
    "ROG.SW": "ROG.SW",
    "NOVN.SW": "NOVN.SW",

    # Italian stocks
    "ENEL.MI": "ENEL.MI",

    # Spanish stocks
    "IBE.MC": "IBE.MC",

    # US stocks (no mapping needed)
    "NVDA": "NVDA",
    "AMD": "AMD",
    "IFNNY": "IFNNY",
    "STM": "STM",
    "SAP": "SAP",
    "ABB": "ABB",
    "NVO": "NVO",
    "AZN": "AZN",
    "SHEL": "SHEL",
}


# =============================================================================
# Cache for API responses
# =============================================================================

class FundamentalsCache:
    """Simple in-memory cache with TTL for fundamental data."""

    def __init__(self, default_ttl: int = 3600):  # 1 hour default
        self._cache: Dict[str, tuple] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, expires_at = self._cache[key]
            if time.time() < expires_at:
                return data
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        ttl = ttl or self._default_ttl
        self._cache[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        self._cache.clear()


_cache = FundamentalsCache()


# =============================================================================
# Main Functions
# =============================================================================

def get_yahoo_ticker(db_ticker: str) -> str:
    """Convert database ticker to Yahoo Finance ticker."""
    return TICKER_MAPPINGS.get(db_ticker, db_ticker)


def get_stock_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch comprehensive fundamental data for a stock.

    Returns dict with:
    - valuation: P/E, P/B, PEG, EV/EBITDA, Market Cap
    - profitability: ROE, ROA, Profit Margins, Operating Margins
    - growth: Revenue Growth, EPS Growth, Earnings Growth
    - dividends: Yield, Payout Ratio, Ex-Date
    - financial_health: Debt/Equity, Current Ratio, Quick Ratio
    - analyst: Recommendations, Price Targets, Upgrades/Downgrades
    - holdings: Institutional %, Insider %, Major Holders
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"fundamentals:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            return {"error": f"No data available for {ticker}"}

        # Build comprehensive fundamentals
        fundamentals = {
            "ticker": ticker,
            "name": info.get("shortName", info.get("longName", ticker)),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange"),
            "last_price": info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "market_cap_formatted": _format_market_cap(info.get("marketCap")),

            # Valuation Metrics
            "valuation": {
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "ev_revenue": info.get("enterpriseToRevenue"),
                "enterprise_value": info.get("enterpriseValue"),
            },

            # Profitability Metrics
            "profitability": {
                "roe": _pct(info.get("returnOnEquity")),
                "roa": _pct(info.get("returnOnAssets")),
                "gross_margin": _pct(info.get("grossMargins")),
                "operating_margin": _pct(info.get("operatingMargins")),
                "profit_margin": _pct(info.get("profitMargins")),
                "ebitda": info.get("ebitda"),
                "ebitda_formatted": _format_large_number(info.get("ebitda")),
            },

            # Growth Metrics
            "growth": {
                "revenue_growth": _pct(info.get("revenueGrowth")),
                "earnings_growth": _pct(info.get("earningsGrowth")),
                "earnings_quarterly_growth": _pct(info.get("earningsQuarterlyGrowth")),
                "revenue_per_share": info.get("revenuePerShare"),
                "trailing_eps": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
            },

            # Dividend Metrics
            "dividends": {
                "dividend_yield": _pct(info.get("dividendYield")),
                "dividend_rate": info.get("dividendRate"),
                "payout_ratio": _pct(info.get("payoutRatio")),
                "ex_dividend_date": _format_timestamp(info.get("exDividendDate")),
                "five_year_avg_yield": _pct(info.get("fiveYearAvgDividendYield", 0) / 100 if info.get("fiveYearAvgDividendYield") else None),
            },

            # Financial Health
            "financial_health": {
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "free_cash_flow": info.get("freeCashflow"),
                "operating_cash_flow": info.get("operatingCashflow"),
            },

            # Price Targets & Analyst Ratings
            "analyst": {
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
                "target_mean": info.get("targetMeanPrice"),
                "target_median": info.get("targetMedianPrice"),
                "recommendation": info.get("recommendationKey"),
                "recommendation_mean": info.get("recommendationMean"),  # 1=Strong Buy, 5=Sell
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
            },

            # Institutional & Insider Holdings
            "holdings": {
                "institutional_pct": _pct(info.get("heldPercentInstitutions")),
                "insider_pct": _pct(info.get("heldPercentInsiders")),
                "short_ratio": info.get("shortRatio"),
                "short_pct_float": _pct(info.get("shortPercentOfFloat")),
                "float_shares": info.get("floatShares"),
            },

            # 52-Week Range
            "price_range": {
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "fifty_day_avg": info.get("fiftyDayAverage"),
                "two_hundred_day_avg": info.get("twoHundredDayAverage"),
                "beta": info.get("beta"),
            },

            "fetched_at": datetime.now().isoformat(),
        }

        # Cache for 1 hour
        _cache.set(cache_key, fundamentals, ttl=3600)

        return fundamentals

    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_analyst_recommendations(ticker: str) -> Dict[str, Any]:
    """
    Get detailed analyst recommendations history.

    Returns:
    - current recommendation
    - recommendation history (last 3 months)
    - upgrades/downgrades
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"recommendations:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        # Get recommendations DataFrame
        recs = stock.recommendations
        if recs is None or recs.empty:
            return {"ticker": ticker, "recommendations": [], "summary": None}

        # Convert to list of dicts
        recs_list = []
        for idx, row in recs.tail(20).iterrows():  # Last 20 recommendations
            recs_list.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
                "firm": row.get("Firm", "Unknown"),
                "to_grade": row.get("To Grade", row.get("toGrade", "")),
                "from_grade": row.get("From Grade", row.get("fromGrade", "")),
                "action": row.get("Action", row.get("action", "")),
            })

        # Summarize
        grades = [r["to_grade"] for r in recs_list if r["to_grade"]]
        buy_count = sum(1 for g in grades if "buy" in g.lower() or "outperform" in g.lower() or "overweight" in g.lower())
        hold_count = sum(1 for g in grades if "hold" in g.lower() or "neutral" in g.lower() or "equal" in g.lower())
        sell_count = sum(1 for g in grades if "sell" in g.lower() or "underperform" in g.lower() or "underweight" in g.lower())

        result = {
            "ticker": ticker,
            "recommendations": recs_list,
            "summary": {
                "buy": buy_count,
                "hold": hold_count,
                "sell": sell_count,
                "total": len(grades),
            },
            "fetched_at": datetime.now().isoformat(),
        }

        _cache.set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        logger.error(f"Error fetching recommendations for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_institutional_holders(ticker: str) -> Dict[str, Any]:
    """Get major institutional holders."""
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"holders:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        holders_list = []

        # Institutional holders
        inst = stock.institutional_holders
        if inst is not None and not inst.empty:
            for _, row in inst.head(10).iterrows():
                holders_list.append({
                    "holder": row.get("Holder", "Unknown"),
                    "shares": row.get("Shares", 0),
                    "date_reported": str(row.get("Date Reported", "")),
                    "pct_out": row.get("% Out", 0),
                    "value": row.get("Value", 0),
                    "type": "institutional",
                })

        # Major holders summary
        major = stock.major_holders
        major_summary = {}
        if major is not None and not major.empty:
            for idx, row in major.iterrows():
                key = str(row.iloc[1]).replace(" ", "_").lower() if len(row) > 1 else f"metric_{idx}"
                major_summary[key] = row.iloc[0] if len(row) > 0 else None

        result = {
            "ticker": ticker,
            "institutional_holders": holders_list,
            "major_holders_summary": major_summary,
            "fetched_at": datetime.now().isoformat(),
        }

        _cache.set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        logger.error(f"Error fetching holders for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_earnings_history(ticker: str) -> Dict[str, Any]:
    """Get earnings history with beats/misses."""
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"earnings:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        # Quarterly earnings
        earnings_list = []
        earnings = stock.quarterly_earnings
        if earnings is not None and not earnings.empty:
            for idx, row in earnings.tail(8).iterrows():  # Last 8 quarters
                earnings_list.append({
                    "quarter": str(idx),
                    "revenue": row.get("Revenue"),
                    "earnings": row.get("Earnings"),
                })

        # Earnings dates & estimates
        calendar = stock.calendar
        next_earnings = None
        if calendar is not None:
            if isinstance(calendar, dict):
                next_earnings = calendar.get("Earnings Date")
            elif hasattr(calendar, "get"):
                next_earnings = calendar.get("Earnings Date")

        result = {
            "ticker": ticker,
            "quarterly_earnings": earnings_list,
            "next_earnings_date": str(next_earnings) if next_earnings else None,
            "fetched_at": datetime.now().isoformat(),
        }

        _cache.set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        logger.error(f"Error fetching earnings for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_fundamentals_summary(ticker: str) -> Dict[str, Any]:
    """
    Get a concise summary of key fundamentals for use in prompts.
    Returns formatted strings ready for LLM consumption.
    """
    fundamentals = get_stock_fundamentals(ticker)

    if "error" in fundamentals:
        return fundamentals

    val = fundamentals.get("valuation", {})
    prof = fundamentals.get("profitability", {})
    growth = fundamentals.get("growth", {})
    div = fundamentals.get("dividends", {})
    health = fundamentals.get("financial_health", {})
    analyst = fundamentals.get("analyst", {})
    holdings = fundamentals.get("holdings", {})

    # Build summary sections
    summary = {
        "ticker": ticker,
        "name": fundamentals.get("name"),

        "valuation_summary": _build_valuation_summary(val),
        "profitability_summary": _build_profitability_summary(prof),
        "growth_summary": _build_growth_summary(growth),
        "dividend_summary": _build_dividend_summary(div),
        "analyst_summary": _build_analyst_summary(analyst),
        "health_summary": _build_health_summary(health),

        # Key metrics for quick reference
        "key_metrics": {
            "pe": val.get("pe_trailing"),
            "roe": prof.get("roe"),
            "revenue_growth": growth.get("revenue_growth"),
            "dividend_yield": div.get("dividend_yield"),
            "debt_equity": health.get("debt_to_equity"),
            "analyst_rating": analyst.get("recommendation"),
            "price_target": analyst.get("target_mean"),
            "institutional_ownership": holdings.get("institutional_pct"),
        },

        # Full prompt-ready text block
        "prompt_block": _build_prompt_block(fundamentals),
    }

    return summary


# =============================================================================
# Helper Functions
# =============================================================================

def _pct(value) -> Optional[float]:
    """Convert decimal to percentage."""
    if value is None:
        return None
    try:
        return round(float(value) * 100, 2)
    except:
        return None


def _format_market_cap(value) -> Optional[str]:
    """Format market cap in B/M."""
    if value is None:
        return None
    try:
        if value >= 1e12:
            return f"${value/1e12:.1f}T"
        elif value >= 1e9:
            return f"${value/1e9:.1f}B"
        elif value >= 1e6:
            return f"${value/1e6:.1f}M"
        else:
            return f"${value:,.0f}"
    except:
        return None


def _format_large_number(value) -> Optional[str]:
    """Format large numbers."""
    if value is None:
        return None
    try:
        if value >= 1e9:
            return f"${value/1e9:.1f}B"
        elif value >= 1e6:
            return f"${value/1e6:.1f}M"
        else:
            return f"${value:,.0f}"
    except:
        return None


def _format_timestamp(ts) -> Optional[str]:
    """Convert Unix timestamp to date string."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except:
        return None


def _build_valuation_summary(val: Dict) -> str:
    """Build valuation summary text."""
    parts = []
    if val.get("pe_trailing"):
        parts.append(f"P/E: {val['pe_trailing']:.1f}x")
    if val.get("pe_forward"):
        parts.append(f"Fwd P/E: {val['pe_forward']:.1f}x")
    if val.get("pb_ratio"):
        parts.append(f"P/B: {val['pb_ratio']:.1f}x")
    if val.get("ev_ebitda"):
        parts.append(f"EV/EBITDA: {val['ev_ebitda']:.1f}x")
    if val.get("peg_ratio"):
        parts.append(f"PEG: {val['peg_ratio']:.2f}")
    return " | ".join(parts) if parts else "N/A"


def _build_profitability_summary(prof: Dict) -> str:
    """Build profitability summary text."""
    parts = []
    if prof.get("roe"):
        parts.append(f"ROE: {prof['roe']:.1f}%")
    if prof.get("roa"):
        parts.append(f"ROA: {prof['roa']:.1f}%")
    if prof.get("profit_margin"):
        parts.append(f"Net Margin: {prof['profit_margin']:.1f}%")
    if prof.get("operating_margin"):
        parts.append(f"Op Margin: {prof['operating_margin']:.1f}%")
    return " | ".join(parts) if parts else "N/A"


def _build_growth_summary(growth: Dict) -> str:
    """Build growth summary text."""
    parts = []
    if growth.get("revenue_growth"):
        parts.append(f"Revenue Growth: {growth['revenue_growth']:.1f}%")
    if growth.get("earnings_growth"):
        parts.append(f"Earnings Growth: {growth['earnings_growth']:.1f}%")
    if growth.get("trailing_eps"):
        parts.append(f"EPS: ${growth['trailing_eps']:.2f}")
    return " | ".join(parts) if parts else "N/A"


def _build_dividend_summary(div: Dict) -> str:
    """Build dividend summary text."""
    if not div.get("dividend_yield"):
        return "No dividend"
    parts = []
    parts.append(f"Yield: {div['dividend_yield']:.2f}%")
    if div.get("payout_ratio"):
        parts.append(f"Payout: {div['payout_ratio']:.0f}%")
    return " | ".join(parts)


def _build_analyst_summary(analyst: Dict) -> str:
    """Build analyst summary text."""
    parts = []
    if analyst.get("recommendation"):
        parts.append(f"Rating: {analyst['recommendation'].upper()}")
    if analyst.get("target_mean"):
        parts.append(f"Avg PT: ${analyst['target_mean']:.0f}")
    if analyst.get("target_high") and analyst.get("target_low"):
        parts.append(f"Range: ${analyst['target_low']:.0f}-${analyst['target_high']:.0f}")
    if analyst.get("number_of_analysts"):
        parts.append(f"({analyst['number_of_analysts']} analysts)")
    return " | ".join(parts) if parts else "N/A"


def _build_health_summary(health: Dict) -> str:
    """Build financial health summary text."""
    parts = []
    if health.get("debt_to_equity") is not None:
        parts.append(f"D/E: {health['debt_to_equity']:.1f}")
    if health.get("current_ratio"):
        parts.append(f"Current Ratio: {health['current_ratio']:.1f}")
    return " | ".join(parts) if parts else "N/A"


def _build_prompt_block(fundamentals: Dict) -> str:
    """Build full text block for LLM prompts."""
    val = fundamentals.get("valuation", {})
    prof = fundamentals.get("profitability", {})
    growth = fundamentals.get("growth", {})
    div = fundamentals.get("dividends", {})
    analyst = fundamentals.get("analyst", {})
    holdings = fundamentals.get("holdings", {})
    price_range = fundamentals.get("price_range", {})

    lines = [
        f"=== REAL-TIME FUNDAMENTALS: {fundamentals.get('name', fundamentals.get('ticker'))} ===",
        f"Market Cap: {fundamentals.get('market_cap_formatted', 'N/A')} | Sector: {fundamentals.get('sector', 'N/A')}",
        "",
        "VALUATION:",
    ]

    if val.get("pe_trailing"):
        lines.append(f"  - P/E (TTM): {val['pe_trailing']:.1f}x")
    if val.get("pe_forward"):
        lines.append(f"  - P/E (Forward): {val['pe_forward']:.1f}x")
    if val.get("pb_ratio"):
        lines.append(f"  - Price/Book: {val['pb_ratio']:.1f}x")
    if val.get("ev_ebitda"):
        lines.append(f"  - EV/EBITDA: {val['ev_ebitda']:.1f}x")
    if val.get("peg_ratio"):
        lines.append(f"  - PEG Ratio: {val['peg_ratio']:.2f}")

    lines.append("")
    lines.append("PROFITABILITY:")
    if prof.get("roe"):
        lines.append(f"  - Return on Equity: {prof['roe']:.1f}%")
    if prof.get("profit_margin"):
        lines.append(f"  - Net Profit Margin: {prof['profit_margin']:.1f}%")
    if prof.get("operating_margin"):
        lines.append(f"  - Operating Margin: {prof['operating_margin']:.1f}%")

    lines.append("")
    lines.append("GROWTH:")
    if growth.get("revenue_growth"):
        lines.append(f"  - Revenue Growth (YoY): {growth['revenue_growth']:.1f}%")
    if growth.get("earnings_growth"):
        lines.append(f"  - Earnings Growth: {growth['earnings_growth']:.1f}%")
    if growth.get("trailing_eps"):
        lines.append(f"  - EPS (TTM): ${growth['trailing_eps']:.2f}")

    if div.get("dividend_yield"):
        lines.append("")
        lines.append("DIVIDENDS:")
        lines.append(f"  - Dividend Yield: {div['dividend_yield']:.2f}%")
        if div.get("payout_ratio"):
            lines.append(f"  - Payout Ratio: {div['payout_ratio']:.0f}%")

    lines.append("")
    lines.append("ANALYST CONSENSUS:")
    if analyst.get("recommendation"):
        lines.append(f"  - Rating: {analyst['recommendation'].upper()}")
    if analyst.get("target_mean"):
        lines.append(f"  - Avg Price Target: ${analyst['target_mean']:.0f}")
    if analyst.get("target_high") and analyst.get("target_low"):
        lines.append(f"  - Target Range: ${analyst['target_low']:.0f} - ${analyst['target_high']:.0f}")
    if analyst.get("number_of_analysts"):
        lines.append(f"  - Coverage: {analyst['number_of_analysts']} analysts")

    if holdings.get("institutional_pct"):
        lines.append("")
        lines.append("OWNERSHIP:")
        lines.append(f"  - Institutional: {holdings['institutional_pct']:.1f}%")
        if holdings.get("insider_pct"):
            lines.append(f"  - Insider: {holdings['insider_pct']:.1f}%")

    if price_range.get("beta"):
        lines.append("")
        lines.append("RISK:")
        lines.append(f"  - Beta: {price_range['beta']:.2f}")
        if price_range.get("fifty_two_week_high") and price_range.get("fifty_two_week_low"):
            lines.append(f"  - 52-Week Range: ${price_range['fifty_two_week_low']:.0f} - ${price_range['fifty_two_week_high']:.0f}")

    return "\n".join(lines)


# =============================================================================
# Batch Functions for Multiple Stocks
# =============================================================================

def get_batch_fundamentals(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch fundamentals for multiple tickers.
    Returns dict mapping ticker -> fundamentals.
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_stock_fundamentals(ticker)
        time.sleep(0.1)  # Rate limiting
    return results


def get_batch_summaries(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch summaries for multiple tickers.
    Returns dict mapping ticker -> summary.
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_fundamentals_summary(ticker)
        time.sleep(0.1)  # Rate limiting
    return results


# =============================================================================
# LIVE STOCK PRICES
# =============================================================================

def get_live_price(ticker: str) -> Dict[str, Any]:
    """
    Fetch real-time/latest price data for a stock from yfinance.

    Returns:
    - current_price
    - open, high, low, close
    - volume
    - change, change_percent
    - market_state (open/closed)
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"live_price:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        # Get current quote data
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            return {"error": f"No price data for {ticker}", "ticker": ticker}

        # Get intraday data for today
        hist = stock.history(period="1d", interval="1m")

        # Calculate change
        current = info.get("regularMarketPrice", 0)
        prev_close = info.get("previousClose", info.get("regularMarketPreviousClose", 0))
        change = current - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0

        result = {
            "ticker": ticker,
            "yf_ticker": yf_ticker,
            "name": info.get("shortName", info.get("longName", ticker)),
            "current_price": current,
            "currency": info.get("currency", "USD"),
            "open": info.get("regularMarketOpen"),
            "high": info.get("regularMarketDayHigh"),
            "low": info.get("regularMarketDayLow"),
            "previous_close": prev_close,
            "volume": info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "market_cap": info.get("marketCap"),
            "market_state": info.get("marketState", "UNKNOWN"),
            "exchange": info.get("exchange"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fetched_at": datetime.now().isoformat(),
        }

        # Cache for 1 minute only (live prices)
        _cache.set(cache_key, result, ttl=60)

        return result

    except Exception as e:
        logger.error(f"Error fetching live price for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_price_history(ticker: str, period: str = "1mo") -> Dict[str, Any]:
    """
    Fetch historical price data.

    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"price_history:{ticker}:{period}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        hist = stock.history(period=period)

        if hist.empty:
            return {"error": f"No history for {ticker}", "ticker": ticker}

        # Convert to list of dicts
        history = []
        for idx, row in hist.iterrows():
            history.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2) if row["Open"] else None,
                "high": round(row["High"], 2) if row["High"] else None,
                "low": round(row["Low"], 2) if row["Low"] else None,
                "close": round(row["Close"], 2) if row["Close"] else None,
                "volume": int(row["Volume"]) if row["Volume"] else None,
            })

        result = {
            "ticker": ticker,
            "period": period,
            "history": history,
            "fetched_at": datetime.now().isoformat(),
        }

        # Cache based on period
        ttl = 300 if period in ["1d", "5d"] else 3600
        _cache.set(cache_key, result, ttl=ttl)

        return result

    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


# =============================================================================
# REAL NEWS
# =============================================================================

def get_stock_news(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fetch real news articles for a stock from yfinance.

    Returns list of news articles with:
    - title
    - publisher
    - link
    - published date
    - summary (if available)
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = f"news:{ticker}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        yf_ticker = get_yahoo_ticker(ticker)
        stock = yf.Ticker(yf_ticker)

        # Get news
        news = stock.news

        if not news:
            return {"ticker": ticker, "news": [], "message": "No news available"}

        articles = []
        for item in news[:limit]:
            # New yfinance structure: data is nested under 'content'
            content = item.get("content", item)  # Fallback to item if no content key

            # Extract title
            title = content.get("title", "")
            title_lower = title.lower() if title else ""

            # Determine sentiment based on title keywords
            sentiment = "neutral"
            if any(word in title_lower for word in ["surge", "jump", "soar", "rally", "gain", "rise", "up", "beat", "strong", "growth", "profit", "record", "boom"]):
                sentiment = "positive"
            elif any(word in title_lower for word in ["fall", "drop", "plunge", "decline", "loss", "down", "miss", "weak", "concern", "risk", "warning", "crash", "tumble"]):
                sentiment = "negative"

            # Extract publisher
            provider = content.get("provider", {})
            publisher = provider.get("displayName") if isinstance(provider, dict) else None

            # Extract link
            canonical_url = content.get("canonicalUrl", {})
            link = canonical_url.get("url") if isinstance(canonical_url, dict) else None

            # Extract published date
            pub_date_str = content.get("pubDate")
            if pub_date_str:
                try:
                    # Parse ISO format date
                    pub_date = pub_date_str.replace("Z", "").split("T")[0] + " " + pub_date_str.replace("Z", "").split("T")[1][:5]
                except:
                    pub_date = pub_date_str
            else:
                pub_date = None

            # Extract thumbnail
            thumbnail_data = content.get("thumbnail", {})
            thumbnail_url = None
            if isinstance(thumbnail_data, dict):
                resolutions = thumbnail_data.get("resolutions", [])
                if resolutions and len(resolutions) > 0:
                    thumbnail_url = resolutions[0].get("url")

            articles.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "published": pub_date,
                "type": content.get("contentType", "article"),
                "thumbnail": thumbnail_url,
                "related_tickers": item.get("relatedTickers", []),
                "sentiment": sentiment,
            })

        result = {
            "ticker": ticker,
            "news": articles,
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
        }

        # Cache for 15 minutes
        _cache.set(cache_key, result, ttl=900)

        return result

    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker, "news": []}


def get_market_news(limit: int = 20) -> Dict[str, Any]:
    """
    Fetch general market news using major index tickers.
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}

    cache_key = "market_news"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        # Use S&P 500 for general market news
        stock = yf.Ticker("^GSPC")
        news = stock.news

        if not news:
            # Fallback to AAPL news
            stock = yf.Ticker("AAPL")
            news = stock.news

        if not news:
            return {"news": [], "message": "No market news available"}

        articles = []
        for item in news[:limit]:
            title = item.get("title", "").lower()
            sentiment = "neutral"
            if any(word in title for word in ["surge", "jump", "rally", "gain", "rise", "beat", "strong"]):
                sentiment = "positive"
            elif any(word in title for word in ["fall", "drop", "plunge", "decline", "loss", "concern"]):
                sentiment = "negative"

            pub_time = item.get("providerPublishTime")
            pub_date = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M") if pub_time else None

            articles.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "published": pub_date,
                "sentiment": sentiment,
                "related_tickers": item.get("relatedTickers", []),
            })

        result = {
            "news": articles,
            "count": len(articles),
            "fetched_at": datetime.now().isoformat(),
        }

        _cache.set(cache_key, result, ttl=900)
        return result

    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        return {"error": str(e), "news": []}
