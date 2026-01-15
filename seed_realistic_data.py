"""
Realistic Seed Data for ODDO BHF Client Intelligence Platform
=============================================================

This script replaces synthetic data with realistic:
- Real European stocks (ODDO BHF coverage universe)
- Realistic institutional clients
- Call history referencing actual market events (2023/2024)
- Realistic research reports

Usage:
    python seed_realistic_data.py [--with-api]

    --with-api: Fetch real prices from Alpha Vantage (requires ALPHAVANTAGE_API_KEY)
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# =============================================================================
# REAL STOCKS - European Focus with ODDO BHF Coverage Style
# =============================================================================

REAL_STOCKS = [
    # Technology / Semiconductors - THE BIG STORY OF 2023/2024
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Mega"},
    {"ticker": "ASML", "company_name": "ASML Holding", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Mega"},
    {"ticker": "SAP", "company_name": "SAP SE", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large"},
    {"ticker": "IFNNY", "company_name": "Infineon Technologies", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large"},
    {"ticker": "STM", "company_name": "STMicroelectronics", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large"},
    {"ticker": "AMD", "company_name": "Advanced Micro Devices", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Mega"},

    # Industrials - European Champions
    {"ticker": "SIE.DE", "company_name": "Siemens AG", "sector": "Industrials", "region": "Europe", "theme_tag": "Automation", "market_cap_bucket": "Large"},
    {"ticker": "AIR.PA", "company_name": "Airbus SE", "sector": "Industrials", "region": "Europe", "theme_tag": "Aerospace", "market_cap_bucket": "Large"},
    {"ticker": "SU.PA", "company_name": "Schneider Electric", "sector": "Industrials", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large"},
    {"ticker": "ABB", "company_name": "ABB Ltd", "sector": "Industrials", "region": "Europe", "theme_tag": "Automation", "market_cap_bucket": "Large"},

    # Luxury / Consumer - French Excellence
    {"ticker": "MC.PA", "company_name": "LVMH Moët Hennessy", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Mega"},
    {"ticker": "RMS.PA", "company_name": "Hermès International", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large"},
    {"ticker": "KER.PA", "company_name": "Kering SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large"},
    {"ticker": "OR.PA", "company_name": "L'Oréal SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Consumer", "market_cap_bucket": "Large"},
    {"ticker": "ADS.DE", "company_name": "adidas AG", "sector": "Consumer", "region": "Europe", "theme_tag": "Consumer", "market_cap_bucket": "Large"},

    # Financials - European Banks
    {"ticker": "BNP.PA", "company_name": "BNP Paribas", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large"},
    {"ticker": "DBK.DE", "company_name": "Deutsche Bank AG", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large"},
    {"ticker": "INGA.AS", "company_name": "ING Groep NV", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large"},
    {"ticker": "GLE.PA", "company_name": "Société Générale", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large"},
    {"ticker": "ALV.DE", "company_name": "Allianz SE", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large"},
    {"ticker": "MUV2.DE", "company_name": "Munich Re", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large"},

    # Healthcare / Pharma
    {"ticker": "NVO", "company_name": "Novo Nordisk", "sector": "Healthcare", "region": "Europe", "theme_tag": "GLP1", "market_cap_bucket": "Mega"},
    {"ticker": "ROG.SW", "company_name": "Roche Holding", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large"},
    {"ticker": "SAN.PA", "company_name": "Sanofi SA", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large"},
    {"ticker": "BAYN.DE", "company_name": "Bayer AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large"},
    {"ticker": "AZN", "company_name": "AstraZeneca PLC", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large"},

    # Energy - Transition Play
    {"ticker": "TTE.PA", "company_name": "TotalEnergies SE", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large"},
    {"ticker": "SHEL", "company_name": "Shell PLC", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large"},
    {"ticker": "ENEL.MI", "company_name": "Enel SpA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large"},
    {"ticker": "IBE.MC", "company_name": "Iberdrola SA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large"},

    # Automotive - German Champions
    {"ticker": "VOW3.DE", "company_name": "Volkswagen AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large"},
    {"ticker": "BMW.DE", "company_name": "BMW AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large"},
    {"ticker": "MBG.DE", "company_name": "Mercedes-Benz Group", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large"},
    {"ticker": "P911.DE", "company_name": "Porsche AG", "sector": "Automotive", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large"},

    # Additional European Large Caps
    {"ticker": "NESN.SW", "company_name": "Nestlé SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Defensive", "market_cap_bucket": "Mega"},
    {"ticker": "NOVN.SW", "company_name": "Novartis AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large"},
    {"ticker": "DTE.DE", "company_name": "Deutsche Telekom", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Large"},
    {"ticker": "DG.PA", "company_name": "Vinci SA", "sector": "Industrials", "region": "Europe", "theme_tag": "Infrastructure", "market_cap_bucket": "Large"},
    {"ticker": "ENGI.PA", "company_name": "Engie SA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large"},
    {"ticker": "DSY.PA", "company_name": "Dassault Systèmes", "sector": "Technology", "region": "Europe", "theme_tag": "Software", "market_cap_bucket": "Large"},
]

# =============================================================================
# REALISTIC EUROPEAN INSTITUTIONAL CLIENTS
# =============================================================================

REAL_CLIENTS = [
    # German Institutions
    {"client_name": "Dr. Marcus Weber", "firm_name": "Union Investment", "client_type": "Asset Manager", "region": "DACH", "email": "m.weber@union-investment.de"},
    {"client_name": "Katharina Schneider", "firm_name": "DWS Group", "client_type": "Asset Manager", "region": "DACH", "email": "k.schneider@dws.com"},
    {"client_name": "Thomas Hoffmann", "firm_name": "Allianz Global Investors", "client_type": "Asset Manager", "region": "DACH", "email": "t.hoffmann@allianzgi.com"},
    {"client_name": "Stefan Richter", "firm_name": "Deka Investment", "client_type": "Asset Manager", "region": "DACH", "email": "s.richter@deka.de"},
    {"client_name": "Julia Becker", "firm_name": "MEAG Munich Ergo", "client_type": "Insurance", "region": "DACH", "email": "j.becker@meag.com"},
    {"client_name": "Michael Braun", "firm_name": "Versorgungsanstalt des Bundes", "client_type": "Pension Fund", "region": "DACH", "email": "m.braun@vbl.de"},
    {"client_name": "Andreas Krüger", "firm_name": "Berenberg Bank", "client_type": "Private Bank", "region": "DACH", "email": "a.krueger@berenberg.de"},
    {"client_name": "Christina Vogel", "firm_name": "Flossbach von Storch", "client_type": "Asset Manager", "region": "DACH", "email": "c.vogel@fvsag.com"},

    # French Institutions
    {"client_name": "Jean-Pierre Dubois", "firm_name": "Amundi Asset Management", "client_type": "Asset Manager", "region": "France", "email": "jp.dubois@amundi.com"},
    {"client_name": "Marie Laurent", "firm_name": "BNP Paribas Asset Management", "client_type": "Asset Manager", "region": "France", "email": "m.laurent@bnpparibas-am.com"},
    {"client_name": "François Martin", "firm_name": "AXA Investment Managers", "client_type": "Asset Manager", "region": "France", "email": "f.martin@axa-im.com"},
    {"client_name": "Sophie Petit", "firm_name": "Carmignac Gestion", "client_type": "Asset Manager", "region": "France", "email": "s.petit@carmignac.com"},
    {"client_name": "Nicolas Bernard", "firm_name": "La Française AM", "client_type": "Asset Manager", "region": "France", "email": "n.bernard@la-francaise.com"},
    {"client_name": "Claire Moreau", "firm_name": "ERAFP", "client_type": "Pension Fund", "region": "France", "email": "c.moreau@erafp.fr"},

    # Benelux
    {"client_name": "Pieter van der Berg", "firm_name": "APG Asset Management", "client_type": "Pension Fund", "region": "Benelux", "email": "p.vanderberg@apg.nl"},
    {"client_name": "Willem de Vries", "firm_name": "PGGM Investments", "client_type": "Pension Fund", "region": "Benelux", "email": "w.devries@pggm.nl"},
    {"client_name": "Anne-Marie Claessens", "firm_name": "KBC Asset Management", "client_type": "Asset Manager", "region": "Benelux", "email": "am.claessens@kbc.be"},

    # UK / Nordic
    {"client_name": "James Thompson", "firm_name": "Baillie Gifford", "client_type": "Asset Manager", "region": "UK", "email": "j.thompson@bailliegifford.com"},
    {"client_name": "Emma Richardson", "firm_name": "Legal & General IM", "client_type": "Asset Manager", "region": "UK", "email": "e.richardson@lgim.com"},
    {"client_name": "Erik Lindqvist", "firm_name": "Norges Bank Investment", "client_type": "Sovereign Wealth", "region": "Nordics", "email": "e.lindqvist@nbim.no"},
    {"client_name": "Anna Johansson", "firm_name": "AP Fonden", "client_type": "Pension Fund", "region": "Nordics", "email": "a.johansson@ap4.se"},

    # Hedge Funds / Family Offices
    {"client_name": "Alexander von Hohenlohe", "firm_name": "Hohenlohe Family Office", "client_type": "Family Office", "region": "DACH", "email": "a.hohenlohe@hfo.ch"},
    {"client_name": "Pierre Lefèvre", "firm_name": "Tikehau Capital", "client_type": "Hedge Fund", "region": "France", "email": "p.lefevre@tikehaucapital.com"},
    {"client_name": "Oliver Hartmann", "firm_name": "Eisler Capital", "client_type": "Hedge Fund", "region": "UK", "email": "o.hartmann@eislercapital.com"},
    {"client_name": "Sebastian Müller", "firm_name": "Quantco Capital", "client_type": "Hedge Fund", "region": "DACH", "email": "s.mueller@quantco.com"},
]

# =============================================================================
# REALISTIC MARKET EVENTS & CALL SCENARIOS (2023/2024)
# =============================================================================

MARKET_EVENTS_2023_2024 = [
    # Q1 2023 - Banking Crisis & Rate Uncertainty
    {
        "period": "2023-03",
        "event": "SVB Collapse / Banking Crisis",
        "stocks": ["DBK.DE", "BNP.PA", "INGA.AS", "GLE.PA"],
        "themes": ["Banking stress", "Credit concerns", "Rate sensitivity", "Contagion risk"],
        "sentiment": "negative",
        "call_topics": [
            "Client concerned about European bank exposure after SVB collapse",
            "Discussed contagion risk from US regional banks to European financials",
            "Client wants to reduce bank exposure, looking at alternatives",
            "Reviewing portfolio for Credit Suisse AT1 exposure"
        ]
    },
    # Q2 2023 - AI Boom Begins
    {
        "period": "2023-05",
        "event": "NVIDIA Earnings / AI Boom",
        "stocks": ["NVDA", "ASML", "AMD", "IFNNY", "STM", "SAP"],
        "themes": ["AI infrastructure", "Semiconductor demand", "Data center capex", "ChatGPT momentum"],
        "sentiment": "positive",
        "call_topics": [
            "NVIDIA guidance blowout - discussing AI infrastructure plays",
            "Client wants exposure to AI beneficiaries in Europe",
            "ASML as picks-and-shovels play for AI buildout",
            "Discussed SAP's AI integration strategy and cloud transition",
            "Client adding to semiconductor positions after NVIDIA call"
        ]
    },
    # Q3 2023 - Luxury Slowdown & China Concerns
    {
        "period": "2023-08",
        "event": "China Slowdown / Luxury Deceleration",
        "stocks": ["MC.PA", "RMS.PA", "KER.PA", "BMW.DE", "MBG.DE"],
        "themes": ["China reopening disappointment", "Luxury normalization", "Aspirational consumer weakness"],
        "sentiment": "cautious",
        "call_topics": [
            "LVMH results below expectations - China weaker than hoped",
            "Client trimming luxury exposure on China concerns",
            "Discussed Hermès resilience vs broader luxury sector",
            "German auto exposure to China EV competition"
        ]
    },
    # Q4 2023 - Rate Peak & Pharma (GLP-1)
    {
        "period": "2023-11",
        "event": "Novo Nordisk / GLP-1 Revolution",
        "stocks": ["NVO", "ROG.SW", "AZN", "BAYN.DE"],
        "themes": ["Obesity drugs", "GLP-1 market size", "Healthcare disruption", "Pharma innovation"],
        "sentiment": "positive",
        "call_topics": [
            "Novo Nordisk supply constraints - demand overwhelming",
            "Client wants GLP-1 exposure beyond Novo",
            "Discussed Roche pipeline in obesity space",
            "Bayer litigation concerns vs pharma peers"
        ]
    },
    # Q1 2024 - Rate Cut Hopes & Tech Rally
    {
        "period": "2024-01",
        "event": "Fed Pivot Expectations / Tech Rally",
        "stocks": ["NVDA", "SAP", "ASML", "DSY.PA"],
        "themes": ["Rate cut timing", "Growth stock rotation", "AI momentum continues"],
        "sentiment": "positive",
        "call_topics": [
            "Client repositioning for rate cuts - adding duration",
            "AI trade extending - NVIDIA approaching $2T market cap",
            "SAP cloud ARR acceleration impressing market",
            "Discussed European tech undervaluation vs US"
        ]
    },
    # Q2 2024 - European Elections & Geopolitics
    {
        "period": "2024-06",
        "event": "European Elections / Political Uncertainty",
        "stocks": ["BNP.PA", "GLE.PA", "TTE.PA", "ENGI.PA"],
        "themes": ["Political risk France", "European stability", "Energy policy"],
        "sentiment": "cautious",
        "call_topics": [
            "French election uncertainty weighing on banks",
            "Client concerned about European political fragmentation",
            "Energy transition policy at risk from right-wing gains",
            "Discussed defensive positioning for political volatility"
        ]
    },
    # Ongoing Themes
    {
        "period": "2024-09",
        "event": "Energy Transition & ESG",
        "stocks": ["ENEL.MI", "IBE.MC", "SU.PA", "TTE.PA", "SHEL"],
        "themes": ["Renewable investment", "Grid infrastructure", "Energy security"],
        "sentiment": "constructive",
        "call_topics": [
            "Client building renewable utilities position",
            "Schneider Electric data center power demand thesis",
            "TotalEnergies transition strategy vs pure-play renewables",
            "ESG mandate requiring energy sector review"
        ]
    },
]

# =============================================================================
# ANALYST NAMES (ODDO BHF Style)
# =============================================================================

ANALYSTS = [
    {"name": "Dr. Heinrich Müller", "sector": "Technology", "coverage": ["SAP", "ASML", "IFNNY"]},
    {"name": "Marie-Claire Dubois", "sector": "Luxury/Consumer", "coverage": ["MC.PA", "RMS.PA", "KER.PA", "OR.PA"]},
    {"name": "Hans-Peter Schmidt", "sector": "Financials", "coverage": ["DBK.DE", "BNP.PA", "ALV.DE"]},
    {"name": "Sophie Bernard", "sector": "Healthcare", "coverage": ["NVO", "ROG.SW", "SAN.PA"]},
    {"name": "Thomas Weber", "sector": "Industrials", "coverage": ["SIE.DE", "AIR.PA", "ABB"]},
    {"name": "François Martin", "sector": "Energy/Utilities", "coverage": ["TTE.PA", "ENEL.MI", "ENGI.PA"]},
    {"name": "Anna Lindberg", "sector": "Automotive", "coverage": ["VOW3.DE", "BMW.DE", "MBG.DE"]},
]


def create_database():
    """Create fresh database with realistic data."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("Creating database schema...")

    # Drop existing tables to ensure clean schema
    conn.executescript("""
        DROP TABLE IF EXISTS src_positions;
        DROP TABLE IF EXISTS src_portfolio_snapshots;
        DROP TABLE IF EXISTS src_trade_executions;
        DROP TABLE IF EXISTS src_readership_events;
        DROP TABLE IF EXISTS src_call_logs;
        DROP TABLE IF EXISTS src_reports;
        DROP TABLE IF EXISTS src_stock_prices;
        DROP TABLE IF EXISTS src_stocks;
        DROP TABLE IF EXISTS src_clients;
    """)

    # Create tables
    conn.executescript("""
        -- Core tables
        CREATE TABLE src_stocks (
            stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            ticker TEXT NOT NULL UNIQUE,
            sector TEXT,
            region TEXT,
            market_cap_bucket TEXT,
            theme_tag TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE src_clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            firm_name TEXT NOT NULL,
            client_type TEXT,
            region TEXT,
            primary_contact_name TEXT,
            primary_contact_role TEXT,
            email TEXT,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE src_call_logs (
            call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            stock_id INTEGER,
            call_timestamp TEXT NOT NULL,
            direction TEXT,
            duration_minutes INTEGER,
            discussed_company TEXT,
            discussed_sector TEXT,
            related_report_id INTEGER,
            notes_raw TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
            FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
        );

        CREATE TABLE src_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT,
            stock_id INTEGER,
            ticker TEXT,
            company_name TEXT,
            sector TEXT,
            report_type TEXT,
            title TEXT NOT NULL,
            summary_3bullets TEXT,
            publish_timestamp TEXT NOT NULL,
            analyst_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
        );

        CREATE TABLE src_readership_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            report_id INTEGER NOT NULL,
            read_timestamp TEXT NOT NULL,
            read_duration_sec INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
            FOREIGN KEY (report_id) REFERENCES src_reports(report_id)
        );

        CREATE TABLE src_trade_executions (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            stock_id INTEGER,
            trade_timestamp TEXT NOT NULL,
            instrument_name TEXT,
            ticker TEXT,
            sector TEXT,
            theme_tag TEXT,
            side TEXT NOT NULL,
            notional_bucket TEXT,
            quantity REAL,
            price REAL,
            currency TEXT DEFAULT 'EUR',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
            FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
        );

        CREATE TABLE src_portfolio_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            as_of_date TEXT NOT NULL,
            source_system TEXT,
            total_aum REAL,
            currency TEXT DEFAULT 'EUR',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
            UNIQUE(client_id, as_of_date)
        );

        CREATE TABLE src_positions (
            position_id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            avg_cost REAL,
            market_value REAL,
            weight REAL,
            currency TEXT DEFAULT 'EUR',
            FOREIGN KEY (snapshot_id) REFERENCES src_portfolio_snapshots(snapshot_id),
            FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id)
        );

        CREATE TABLE src_stock_prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER NOT NULL,
            price_date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL NOT NULL,
            volume INTEGER,
            currency TEXT DEFAULT 'EUR',
            FOREIGN KEY (stock_id) REFERENCES src_stocks(stock_id),
            UNIQUE(stock_id, price_date)
        );
    """)

    conn.commit()
    return conn


def insert_stocks(conn):
    """Insert real stocks."""
    print("Inserting real stocks...")

    # Clear existing
    conn.execute("DELETE FROM src_stocks")

    for stock in REAL_STOCKS:
        conn.execute("""
            INSERT INTO src_stocks (ticker, company_name, sector, region, market_cap_bucket, theme_tag)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (stock["ticker"], stock["company_name"], stock["sector"],
              stock["region"], stock["market_cap_bucket"], stock["theme_tag"]))

    conn.commit()
    print(f"  Inserted {len(REAL_STOCKS)} stocks")


def insert_clients(conn):
    """Insert realistic clients."""
    print("Inserting realistic clients...")

    # Clear existing
    conn.execute("DELETE FROM src_clients")

    for client in REAL_CLIENTS:
        conn.execute("""
            INSERT INTO src_clients (client_name, firm_name, client_type, region, email)
            VALUES (?, ?, ?, ?, ?)
        """, (client["client_name"], client["firm_name"], client["client_type"],
              client["region"], client["email"]))

    conn.commit()
    print(f"  Inserted {len(REAL_CLIENTS)} clients")


def get_stock_id(conn, ticker):
    """Get stock_id from ticker."""
    cur = conn.execute("SELECT stock_id FROM src_stocks WHERE ticker = ?", (ticker,))
    row = cur.fetchone()
    return row[0] if row else None


def insert_call_logs(conn):
    """Insert realistic call logs based on market events."""
    print("Inserting realistic call logs...")

    # Clear existing
    conn.execute("DELETE FROM src_call_logs")

    # Get all clients
    cur = conn.execute("SELECT client_id, client_name, firm_name, client_type FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    call_count = 0

    for event in MARKET_EVENTS_2023_2024:
        period = event["period"]
        year, month = period.split("-")

        # Generate calls for this period
        for _ in range(random.randint(15, 30)):
            client = random.choice(clients)
            ticker = random.choice(event["stocks"])
            stock_id = get_stock_id(conn, ticker)

            if not stock_id:
                continue

            # Random day in the month
            day = random.randint(1, 28)
            hour = random.randint(8, 17)
            minute = random.choice([0, 15, 30, 45])

            call_timestamp = f"{year}-{month}-{day:02d} {hour:02d}:{minute:02d}:00"

            # Get company name
            cur = conn.execute("SELECT company_name, sector FROM src_stocks WHERE stock_id = ?", (stock_id,))
            stock_info = cur.fetchone()
            company_name = stock_info[0] if stock_info else ticker
            sector = stock_info[1] if stock_info else "Unknown"

            # Create realistic note
            topic = random.choice(event["call_topics"])
            theme = random.choice(event["themes"])

            # Make notes more specific to the client type
            client_context = ""
            if client["client_type"] == "Pension Fund":
                client_context = " Client emphasizes long-term view and dividend sustainability."
            elif client["client_type"] == "Hedge Fund":
                client_context = " Client interested in short-term catalysts and entry points."
            elif client["client_type"] == "Family Office":
                client_context = " Client focused on capital preservation with selective growth."
            elif client["client_type"] == "Insurance":
                client_context = " Client needs to consider Solvency II implications."

            notes = f"{topic} Theme: {theme}.{client_context} Follow-up scheduled."

            conn.execute("""
                INSERT INTO src_call_logs
                (client_id, stock_id, call_timestamp, direction, duration_minutes,
                 discussed_company, discussed_sector, notes_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (client["client_id"], stock_id, call_timestamp,
                  random.choice(["Outbound", "Inbound"]),
                  random.randint(10, 45),
                  company_name, sector, notes))

            call_count += 1

    # Add some NVIDIA-specific calls in early 2023 (before the big move)
    nvidia_early_calls = [
        ("2023-01-15", "Discussed NVIDIA data center growth potential. AI training demand accelerating. Client skeptical of valuation but interested in the thesis."),
        ("2023-02-10", "NVIDIA gaming recovery slower than expected, but data center strength offsetting. Client considering initial position."),
        ("2023-03-20", "ChatGPT momentum creating buzz around AI infrastructure. NVIDIA as primary beneficiary. Client wants to increase exposure."),
        ("2023-04-05", "Pre-earnings positioning discussion. Consensus estimates may be too low given AI demand signals."),
        ("2023-05-25", "POST-EARNINGS: Guidance massively above expectations. Client adding aggressively. This changes everything for AI infrastructure."),
    ]

    nvidia_id = get_stock_id(conn, "NVDA")
    if nvidia_id:
        for date, note in nvidia_early_calls:
            for client in random.sample(clients, min(5, len(clients))):
                conn.execute("""
                    INSERT INTO src_call_logs
                    (client_id, stock_id, call_timestamp, direction, duration_minutes,
                     discussed_company, discussed_sector, notes_raw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (client["client_id"], nvidia_id, f"{date} {random.randint(9,16)}:00:00",
                      "Outbound", random.randint(20, 40),
                      "NVIDIA Corporation", "Technology", note))
                call_count += 1

    conn.commit()
    print(f"  Inserted {call_count} call logs")


def insert_reports(conn):
    """Insert realistic research reports."""
    print("Inserting realistic reports...")

    # Clear existing
    conn.execute("DELETE FROM src_reports")

    report_count = 0

    report_templates = [
        # NVIDIA / AI
        {"ticker": "NVDA", "type": "Update", "title": "NVIDIA: AI Demand Inflection - Raising Estimates",
         "summary": "• Data center revenue guidance 50% above consensus\n• AI training demand unprecedented\n• Maintain Outperform, PT $500 → $700"},
        {"ticker": "NVDA", "type": "Flash", "title": "NVIDIA Q2 Preview: The AI Moment",
         "summary": "• ChatGPT catalyst creating step-change in demand\n• H100 supply constraints bullish signal\n• Expect guidance to surprise significantly"},

        # ASML
        {"ticker": "ASML", "type": "Sector", "title": "European Semiconductors: AI Beneficiaries",
         "summary": "• ASML monopoly position strengthening\n• EUV demand extending beyond leading edge\n• High NA ramp on track for 2025"},
        {"ticker": "ASML", "type": "Update", "title": "ASML: Picks and Shovels for AI Gold Rush",
         "summary": "• Order book at record levels\n• China restrictions manageable\n• Raising PT to €800"},

        # Luxury
        {"ticker": "MC.PA", "type": "Update", "title": "LVMH: China Reopening Reality Check",
         "summary": "• Q3 organic growth decelerating to +9%\n• Aspirational consumer weakening\n• Selective Wines & Spirits headwinds"},
        {"ticker": "RMS.PA", "type": "Update", "title": "Hermès: Resilience in Luxury Slowdown",
         "summary": "• Leather goods momentum intact\n• Waiting lists extend further\n• Premium valuation justified"},

        # Healthcare / GLP-1
        {"ticker": "NVO", "type": "Thematic", "title": "GLP-1 Revolution: Sizing the Obesity Opportunity",
         "summary": "• TAM expanding to $100bn+ by 2030\n• Wegovy supply constraints easing 2024\n• Novo market share defensible"},

        # Banks
        {"ticker": "DBK.DE", "type": "Update", "title": "Deutsche Bank: SVB Contagion Fears Overdone",
         "summary": "• Funding profile fundamentally different\n• CET1 ratio comfortable at 13.4%\n• Attractive risk/reward at current levels"},
        {"ticker": "BNP.PA", "type": "Sector", "title": "European Banks: Rate Sensitivity Analysis",
         "summary": "• NII uplift fully flowing through\n• Credit costs normalizing not spiking\n• Sector remains undervalued vs US peers"},

        # Energy Transition
        {"ticker": "SU.PA", "type": "Update", "title": "Schneider Electric: Data Center Power Play",
         "summary": "• AI infrastructure driving power demand surge\n• Grid solutions positioning excellent\n• Raising estimates on backlog strength"},

        # Automotive
        {"ticker": "VOW3.DE", "type": "Update", "title": "Volkswagen: China EV Competition Intensifying",
         "summary": "• ID series losing ground to BYD, local players\n• Software challenges persist\n• Maintaining cautious stance"},
    ]

    # Generate reports across 2023-2024
    for template in report_templates:
        stock_id = get_stock_id(conn, template["ticker"])
        if not stock_id:
            continue

        # Get stock info
        cur = conn.execute("SELECT company_name, sector FROM src_stocks WHERE stock_id = ?", (stock_id,))
        stock_info = cur.fetchone()

        # Multiple reports per stock across time periods
        for period in ["2023-03", "2023-06", "2023-09", "2023-12", "2024-03", "2024-06", "2024-09"]:
            year, month = period.split("-")
            day = random.randint(1, 28)

            analyst = random.choice([a for a in ANALYSTS if template["ticker"] in a.get("coverage", []) or a["sector"] in str(stock_info[1])])

            report_code = f"ODDO-{template['ticker'].replace('.', '')}-{year}{month}{day:02d}"

            conn.execute("""
                INSERT INTO src_reports
                (report_code, stock_id, ticker, company_name, sector, report_type,
                 title, summary_3bullets, publish_timestamp, analyst_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_code, stock_id, template["ticker"], stock_info[0], stock_info[1],
                  template["type"], template["title"], template["summary"],
                  f"{year}-{month}-{day:02d} 07:00:00", analyst["name"]))

            report_count += 1

    conn.commit()
    print(f"  Inserted {report_count} reports")


def insert_readership_events(conn):
    """Insert realistic readership events."""
    print("Inserting readership events...")

    # Clear existing
    conn.execute("DELETE FROM src_readership_events")

    # Get clients and reports
    cur = conn.execute("SELECT client_id, client_type, region FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    cur = conn.execute("SELECT report_id, ticker, sector, publish_timestamp FROM src_reports")
    reports = [dict(row) for row in cur.fetchall()]

    event_count = 0

    for report in reports:
        # Each report read by 5-15 clients
        readers = random.sample(clients, min(random.randint(5, 15), len(clients)))

        for client in readers:
            # Read 0-3 days after publish
            publish_date = datetime.strptime(report["publish_timestamp"][:10], "%Y-%m-%d")
            read_delay = random.randint(0, 3)
            read_date = publish_date + timedelta(days=read_delay)
            read_hour = random.randint(7, 18)
            read_minute = random.randint(0, 59)

            read_timestamp = f"{read_date.strftime('%Y-%m-%d')} {read_hour:02d}:{read_minute:02d}:00"

            # Duration based on report type (longer for thematic)
            base_duration = random.randint(60, 300)

            conn.execute("""
                INSERT INTO src_readership_events (client_id, report_id, read_timestamp, read_duration_sec)
                VALUES (?, ?, ?, ?)
            """, (client["client_id"], report["report_id"], read_timestamp, base_duration))

            event_count += 1

    conn.commit()
    print(f"  Inserted {event_count} readership events")


def insert_trades(conn):
    """Insert realistic trade executions."""
    print("Inserting trade executions...")

    # Clear existing
    conn.execute("DELETE FROM src_trade_executions")

    cur = conn.execute("SELECT client_id, client_type FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    cur = conn.execute("SELECT stock_id, ticker, company_name, sector, theme_tag FROM src_stocks")
    stocks = [dict(row) for row in cur.fetchall()]

    trade_count = 0

    # Trading patterns based on market events
    for event in MARKET_EVENTS_2023_2024:
        period = event["period"]
        year, month = period.split("-")

        event_stocks = [s for s in stocks if s["ticker"] in event["stocks"]]

        for client in clients:
            # Each client trades 2-5 stocks per event period
            traded_stocks = random.sample(event_stocks, min(random.randint(2, 5), len(event_stocks)))

            for stock in traded_stocks:
                # Determine side based on sentiment
                if event["sentiment"] == "positive":
                    side = random.choices(["Buy", "Sell"], weights=[0.7, 0.3])[0]
                elif event["sentiment"] == "negative":
                    side = random.choices(["Buy", "Sell"], weights=[0.3, 0.7])[0]
                else:
                    side = random.choice(["Buy", "Sell"])

                day = random.randint(1, 28)
                hour = random.randint(9, 16)

                notional = random.choice(["Small", "Medium", "Large"])

                conn.execute("""
                    INSERT INTO src_trade_executions
                    (client_id, stock_id, trade_timestamp, instrument_name, ticker,
                     sector, theme_tag, side, notional_bucket)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (client["client_id"], stock["stock_id"],
                      f"{year}-{month}-{day:02d} {hour:02d}:00:00",
                      stock["company_name"], stock["ticker"],
                      stock["sector"], stock["theme_tag"], side, notional))

                trade_count += 1

    conn.commit()
    print(f"  Inserted {trade_count} trades")


def insert_portfolios(conn):
    """Insert portfolio snapshots and positions."""
    print("Inserting portfolio snapshots...")

    # Clear existing
    conn.execute("DELETE FROM src_positions")
    conn.execute("DELETE FROM src_portfolio_snapshots")

    cur = conn.execute("SELECT client_id, client_type FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    cur = conn.execute("SELECT stock_id, ticker, sector, theme_tag FROM src_stocks")
    stocks = [dict(row) for row in cur.fetchall()]

    snapshot_count = 0
    position_count = 0

    # Create quarterly snapshots
    for date in ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31", "2024-03-31", "2024-06-30", "2024-09-30"]:
        for client in clients:
            # AUM based on client type
            if client["client_type"] == "Sovereign Wealth":
                aum = random.uniform(50_000_000_000, 200_000_000_000)
            elif client["client_type"] == "Pension Fund":
                aum = random.uniform(10_000_000_000, 100_000_000_000)
            elif client["client_type"] == "Asset Manager":
                aum = random.uniform(5_000_000_000, 50_000_000_000)
            elif client["client_type"] == "Hedge Fund":
                aum = random.uniform(1_000_000_000, 20_000_000_000)
            else:
                aum = random.uniform(500_000_000, 5_000_000_000)

            conn.execute("""
                INSERT INTO src_portfolio_snapshots (client_id, as_of_date, total_aum)
                VALUES (?, ?, ?)
            """, (client["client_id"], date, aum))

            snapshot_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            snapshot_count += 1

            # Each client holds 10-30 positions
            positions = random.sample(stocks, min(random.randint(10, 30), len(stocks)))
            weights = [random.uniform(0.01, 0.15) for _ in positions]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]  # Normalize to 1

            for stock, weight in zip(positions, weights):
                market_value = aum * weight

                conn.execute("""
                    INSERT INTO src_positions (snapshot_id, stock_id, quantity, market_value, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (snapshot_id, stock["stock_id"],
                      market_value / random.uniform(50, 500),  # Approximate quantity
                      market_value, weight))

                position_count += 1

    conn.commit()
    print(f"  Inserted {snapshot_count} snapshots with {position_count} positions")


def insert_sample_prices(conn):
    """Insert sample stock prices (placeholder - use API for real data)."""
    print("Inserting sample stock prices...")

    # Clear existing
    conn.execute("DELETE FROM src_stock_prices")

    cur = conn.execute("SELECT stock_id, ticker FROM src_stocks")
    stocks = [dict(row) for row in cur.fetchall()]

    # Sample prices (these would come from Alpha Vantage in production)
    sample_prices = {
        "NVDA": 450.0,
        "ASML": 680.0,
        "SAP": 175.0,
        "MC.PA": 750.0,
        "NVO": 115.0,
        "SIE.DE": 165.0,
        "DBK.DE": 12.50,
        "BNP.PA": 62.0,
        "TTE.PA": 58.0,
        "ALV.DE": 245.0,
    }

    price_count = 0
    today = datetime.now()

    for stock in stocks:
        base_price = sample_prices.get(stock["ticker"], random.uniform(20, 500))

        # Generate 30 days of prices
        for i in range(30):
            date = today - timedelta(days=i)
            if date.weekday() >= 5:  # Skip weekends
                continue

            # Random daily movement
            daily_return = random.gauss(0, 0.02)
            close = base_price * (1 + daily_return * (30 - i) / 30)
            high = close * random.uniform(1.0, 1.02)
            low = close * random.uniform(0.98, 1.0)
            open_price = random.uniform(low, high)

            conn.execute("""
                INSERT OR REPLACE INTO src_stock_prices
                (stock_id, price_date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock["stock_id"], date.strftime("%Y-%m-%d"),
                  open_price, high, low, close, random.randint(1000000, 50000000)))

            price_count += 1

    conn.commit()
    print(f"  Inserted {price_count} price records")


def main():
    """Main execution."""
    print("=" * 60)
    print("ODDO BHF Client Intelligence - Realistic Data Seeding")
    print("=" * 60)
    print()

    # Backup existing database
    if os.path.exists(DB_PATH):
        backup_path = DB_PATH + ".backup"
        print(f"Backing up existing database to {backup_path}")
        import shutil
        shutil.copy(DB_PATH, backup_path)

    # Create fresh database
    conn = create_database()

    # Insert data in order
    insert_stocks(conn)
    insert_clients(conn)
    insert_reports(conn)
    insert_call_logs(conn)
    insert_readership_events(conn)
    insert_trades(conn)
    insert_portfolios(conn)
    insert_sample_prices(conn)

    conn.close()

    print()
    print("=" * 60)
    print("Data seeding complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart the server: python server.py")
    print("2. For real prices, set ALPHAVANTAGE_API_KEY and run with --with-api")
    print()


if __name__ == "__main__":
    main()
