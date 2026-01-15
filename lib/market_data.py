"""
Market Data Integration - Alpha Vantage & Finnhub
==================================================

Fetches real-time stock prices and news from external APIs.

Usage:
    from lib.market_data import MarketDataClient

    client = MarketDataClient()
    price = client.get_quote("NVDA")
    news = client.get_news("NVDA")
"""

import os
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# API Keys from environment or direct
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "79JMNVR39XHL3NX1")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d5kboapr01qjaedu9lc0d5kboapr01qjaedu9lcg")

# Rate limiting
ALPHAVANTAGE_DELAY = 12  # 5 calls/minute on free tier = 12 seconds between calls
FINNHUB_DELAY = 1  # 60 calls/minute on free tier

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")


class MarketDataClient:
    """Client for fetching market data from Alpha Vantage and Finnhub."""

    def __init__(self):
        self.av_key = ALPHAVANTAGE_API_KEY
        self.fh_key = FINNHUB_API_KEY
        self.last_av_call = 0
        self.last_fh_call = 0

    def _rate_limit_av(self):
        """Enforce Alpha Vantage rate limit."""
        elapsed = time.time() - self.last_av_call
        if elapsed < ALPHAVANTAGE_DELAY:
            time.sleep(ALPHAVANTAGE_DELAY - elapsed)
        self.last_av_call = time.time()

    def _rate_limit_fh(self):
        """Enforce Finnhub rate limit."""
        elapsed = time.time() - self.last_fh_call
        if elapsed < FINNHUB_DELAY:
            time.sleep(FINNHUB_DELAY - elapsed)
        self.last_fh_call = time.time()

    # =========================================================================
    # Alpha Vantage - Stock Prices
    # =========================================================================

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a stock.

        Args:
            symbol: Stock ticker (e.g., "NVDA", "ASML")

        Returns:
            Dict with price data or None if failed
        """
        self._rate_limit_av()

        # Map European tickers to Alpha Vantage format
        av_symbol = self._map_to_alphavantage(symbol)

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": av_symbol,
            "apikey": self.av_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return {
                    "symbol": symbol,
                    "price": float(quote.get("05. price", 0)),
                    "open": float(quote.get("02. open", 0)),
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "volume": int(quote.get("06. volume", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                    "latest_trading_day": quote.get("07. latest trading day", ""),
                }
            else:
                print(f"No quote data for {symbol}: {data}")
                return None

        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None

    def get_daily_prices(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical daily prices.

        Args:
            symbol: Stock ticker
            days: Number of days of history

        Returns:
            List of daily price records
        """
        self._rate_limit_av()

        av_symbol = self._map_to_alphavantage(symbol)

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": av_symbol,
            "outputsize": "compact",  # Last 100 data points
            "apikey": self.av_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "Time Series (Daily)" in data:
                prices = []
                time_series = data["Time Series (Daily)"]

                for date_str, values in sorted(time_series.items(), reverse=True)[:days]:
                    prices.append({
                        "date": date_str,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": int(values["5. volume"]),
                    })

                return prices
            else:
                print(f"No daily data for {symbol}: {data}")
                return []

        except Exception as e:
            print(f"Error fetching daily prices for {symbol}: {e}")
            return []

    def _map_to_alphavantage(self, symbol: str) -> str:
        """Map ticker to Alpha Vantage format."""
        # European exchanges need special handling
        mappings = {
            # German stocks (XETRA)
            "SIE.DE": "SIE.DEX",
            "DBK.DE": "DBK.DEX",
            "ALV.DE": "ALV.DEX",
            "MUV2.DE": "MUV2.DEX",
            "BAYN.DE": "BAYN.DEX",
            "VOW3.DE": "VOW3.DEX",
            "BMW.DE": "BMW.DEX",
            "MBG.DE": "MBG.DEX",
            "P911.DE": "P911.DEX",
            "ADS.DE": "ADS.DEX",
            "DTE.DE": "DTE.DEX",
            "IFNNY": "IFX.DEX",  # Infineon

            # French stocks (Euronext Paris)
            "MC.PA": "MC.PAR",
            "RMS.PA": "RMS.PAR",
            "KER.PA": "KER.PAR",
            "OR.PA": "OR.PAR",
            "BNP.PA": "BNP.PAR",
            "GLE.PA": "GLE.PAR",
            "SAN.PA": "SAN.PAR",
            "TTE.PA": "TTE.PAR",
            "AIR.PA": "AIR.PAR",
            "SU.PA": "SU.PAR",
            "DG.PA": "DG.PAR",
            "ENGI.PA": "ENGI.PAR",
            "DSY.PA": "DSY.PAR",

            # Dutch stocks (Amsterdam)
            "ASML": "ASML",
            "INGA.AS": "INGA.AMS",

            # Swiss stocks
            "ROG.SW": "ROG.SWX",
            "NESN.SW": "NESN.SWX",
            "NOVN.SW": "NOVN.SWX",

            # Italian stocks
            "ENEL.MI": "ENEL.MIL",

            # Spanish stocks
            "IBE.MC": "IBE.MCE",
        }

        return mappings.get(symbol, symbol)

    # =========================================================================
    # Finnhub - News & Company Info
    # =========================================================================

    def get_news(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent news for a stock.

        Args:
            symbol: Stock ticker
            days: Days of news to fetch

        Returns:
            List of news articles
        """
        self._rate_limit_fh()

        # Map to Finnhub symbol format
        fh_symbol = self._map_to_finnhub(symbol)

        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": fh_symbol,
            "from": from_date,
            "to": to_date,
            "token": self.fh_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if isinstance(data, list):
                news = []
                for article in data[:10]:  # Limit to 10 most recent
                    news.append({
                        "headline": article.get("headline", ""),
                        "summary": article.get("summary", ""),
                        "source": article.get("source", ""),
                        "url": article.get("url", ""),
                        "datetime": datetime.fromtimestamp(article.get("datetime", 0)).strftime("%Y-%m-%d %H:%M"),
                        "sentiment": self._classify_sentiment(article.get("headline", "")),
                    })
                return news
            else:
                print(f"Unexpected news response for {symbol}: {data}")
                return []

        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return []

    def get_earnings_calendar(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get upcoming earnings date.

        Args:
            symbol: Stock ticker

        Returns:
            Earnings info or None
        """
        self._rate_limit_fh()

        fh_symbol = self._map_to_finnhub(symbol)

        url = "https://finnhub.io/api/v1/calendar/earnings"
        params = {
            "symbol": fh_symbol,
            "token": self.fh_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "earningsCalendar" in data and data["earningsCalendar"]:
                earnings = data["earningsCalendar"][0]
                return {
                    "date": earnings.get("date", ""),
                    "eps_estimate": earnings.get("epsEstimate"),
                    "eps_actual": earnings.get("epsActual"),
                    "revenue_estimate": earnings.get("revenueEstimate"),
                    "revenue_actual": earnings.get("revenueActual"),
                    "hour": earnings.get("hour", ""),
                }
            return None

        except Exception as e:
            print(f"Error fetching earnings for {symbol}: {e}")
            return None

    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company profile information.

        Args:
            symbol: Stock ticker

        Returns:
            Company profile or None
        """
        self._rate_limit_fh()

        fh_symbol = self._map_to_finnhub(symbol)

        url = "https://finnhub.io/api/v1/stock/profile2"
        params = {
            "symbol": fh_symbol,
            "token": self.fh_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data and "name" in data:
                return {
                    "name": data.get("name", ""),
                    "ticker": data.get("ticker", ""),
                    "country": data.get("country", ""),
                    "currency": data.get("currency", ""),
                    "exchange": data.get("exchange", ""),
                    "industry": data.get("finnhubIndustry", ""),
                    "market_cap": data.get("marketCapitalization", 0) * 1_000_000,  # Convert to actual
                    "logo": data.get("logo", ""),
                    "website": data.get("weburl", ""),
                }
            return None

        except Exception as e:
            print(f"Error fetching profile for {symbol}: {e}")
            return None

    def _map_to_finnhub(self, symbol: str) -> str:
        """Map ticker to Finnhub format."""
        # Finnhub uses different formats for international stocks
        # US stocks work as-is, European stocks need exchange suffix

        # Remove existing suffixes and add Finnhub format
        base_symbol = symbol.split(".")[0]

        # Most European stocks need to be mapped to US ADRs or direct listings
        # For simplicity, we'll try the base symbol first
        return base_symbol

    def _classify_sentiment(self, headline: str) -> str:
        """Simple sentiment classification based on keywords."""
        headline_lower = headline.lower()

        positive_words = ["surge", "jump", "gain", "rise", "beat", "strong", "record", "growth", "upgrade", "outperform"]
        negative_words = ["fall", "drop", "decline", "miss", "weak", "cut", "downgrade", "concern", "risk", "loss"]

        positive_count = sum(1 for word in positive_words if word in headline_lower)
        negative_count = sum(1 for word in negative_words if word in headline_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"


def update_database_prices(symbols: List[str] = None):
    """
    Update database with real prices from Alpha Vantage.

    Args:
        symbols: List of tickers to update, or None for all
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    client = MarketDataClient()

    # Get symbols from database if not provided
    if symbols is None:
        cur = conn.execute("SELECT ticker FROM src_stocks WHERE is_active = 1")
        symbols = [row["ticker"] for row in cur.fetchall()]

    print(f"Updating prices for {len(symbols)} stocks...")

    updated = 0
    failed = 0

    for symbol in symbols:
        print(f"  Fetching {symbol}...", end=" ")

        quote = client.get_quote(symbol)

        if quote and quote["price"] > 0:
            # Get stock_id
            cur = conn.execute("SELECT stock_id FROM src_stocks WHERE ticker = ?", (symbol,))
            row = cur.fetchone()

            if row:
                stock_id = row["stock_id"]
                today = datetime.now().strftime("%Y-%m-%d")

                # Insert or update price
                conn.execute("""
                    INSERT OR REPLACE INTO src_stock_prices
                    (stock_id, price_date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (stock_id, today, quote["open"], quote["high"],
                      quote["low"], quote["price"], quote["volume"]))

                print(f"${quote['price']:.2f} ({quote['change_percent']}%)")
                updated += 1
            else:
                print("stock not found in DB")
                failed += 1
        else:
            print("failed")
            failed += 1

    conn.commit()
    conn.close()

    print(f"\nUpdated: {updated}, Failed: {failed}")
    return updated, failed


def fetch_news_for_stocks(symbols: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Fetch news for multiple stocks.

    Args:
        symbols: List of tickers, or None for top stocks

    Returns:
        Dict mapping ticker to news list
    """
    client = MarketDataClient()

    # Default to key stocks
    if symbols is None:
        symbols = ["NVDA", "ASML", "SAP", "MC.PA", "NVO", "DBK.DE"]

    all_news = {}

    for symbol in symbols:
        print(f"Fetching news for {symbol}...")
        news = client.get_news(symbol)
        if news:
            all_news[symbol] = news
            print(f"  Found {len(news)} articles")
        else:
            print(f"  No news found")

    return all_news


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "prices":
            # Update all prices
            update_database_prices()

        elif command == "quote":
            # Get single quote
            if len(sys.argv) > 2:
                symbol = sys.argv[2]
                client = MarketDataClient()
                quote = client.get_quote(symbol)
                if quote:
                    print(f"\n{symbol}: ${quote['price']:.2f}")
                    print(f"  Change: {quote['change_percent']}%")
                    print(f"  Volume: {quote['volume']:,}")
                else:
                    print(f"Failed to get quote for {symbol}")
            else:
                print("Usage: python market_data.py quote SYMBOL")

        elif command == "news":
            # Get news
            if len(sys.argv) > 2:
                symbol = sys.argv[2]
                client = MarketDataClient()
                news = client.get_news(symbol)
                if news:
                    print(f"\nNews for {symbol}:")
                    for article in news[:5]:
                        print(f"\n  [{article['sentiment']}] {article['headline']}")
                        print(f"    {article['source']} - {article['datetime']}")
                else:
                    print(f"No news found for {symbol}")
            else:
                print("Usage: python market_data.py news SYMBOL")

        else:
            print("Unknown command. Available: prices, quote, news")
    else:
        print("ODDO BHF Market Data Integration")
        print("================================")
        print("\nCommands:")
        print("  python market_data.py prices       - Update all stock prices")
        print("  python market_data.py quote SYMBOL - Get quote for symbol")
        print("  python market_data.py news SYMBOL  - Get news for symbol")
