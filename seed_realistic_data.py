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
import json
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
        DROP TABLE IF EXISTS src_client_events;
        DROP TABLE IF EXISTS src_client_compliance;
        DROP TABLE IF EXISTS src_client_contact_prefs;
        DROP TABLE IF EXISTS src_client_email_activity;
        DROP TABLE IF EXISTS src_client_meetings;
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

        -- CRM Data: Meetings & Events
        CREATE TABLE src_client_meetings (
            meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            meeting_date TEXT NOT NULL,
            meeting_type TEXT NOT NULL,  -- 'in_person', 'video_call', 'roadshow', 'conference', 'dinner'
            location TEXT,
            duration_minutes INTEGER,
            attendees TEXT,  -- JSON array of names
            topics_discussed TEXT,  -- JSON array of topics
            outcome TEXT,  -- 'positive', 'neutral', 'follow_up_needed'
            notes TEXT,
            organizer TEXT,  -- ODDO employee name
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id)
        );

        -- CRM Data: Email Activity Summary
        CREATE TABLE src_client_email_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            month TEXT NOT NULL,  -- '2024-01' format
            emails_sent INTEGER DEFAULT 0,
            emails_received INTEGER DEFAULT 0,
            avg_response_time_hours REAL,  -- Average time to respond
            emails_opened INTEGER DEFAULT 0,
            links_clicked INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id),
            UNIQUE(client_id, month)
        );

        -- CRM Data: Contact Preferences
        CREATE TABLE src_client_contact_prefs (
            pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,
            preferred_channel TEXT DEFAULT 'phone',  -- 'phone', 'email', 'video', 'in_person'
            preferred_time TEXT,  -- 'morning', 'afternoon', 'evening'
            preferred_days TEXT,  -- JSON array: ['Monday', 'Tuesday']
            preferred_frequency TEXT DEFAULT 'weekly',  -- 'daily', 'weekly', 'bi-weekly', 'monthly'
            language TEXT DEFAULT 'English',
            timezone TEXT DEFAULT 'CET',
            do_not_contact_until TEXT,  -- Date if temporarily unavailable
            notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id)
        );

        -- Compliance/KYC Data
        CREATE TABLE src_client_compliance (
            compliance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,

            -- KYC Status
            kyc_status TEXT DEFAULT 'approved',  -- 'pending', 'approved', 'expired', 'review_needed'
            kyc_expiry_date TEXT,
            kyc_last_review TEXT,
            kyc_risk_rating TEXT DEFAULT 'standard',  -- 'low', 'standard', 'enhanced'

            -- Investor Classification (MiFID II)
            investor_type TEXT DEFAULT 'professional',  -- 'retail', 'professional', 'eligible_counterparty'
            mifid_category TEXT,

            -- Investment Mandate
            mandate_type TEXT,  -- 'discretionary', 'advisory', 'execution_only'
            aum_declared REAL,  -- AUM in EUR (if disclosed)
            aum_currency TEXT DEFAULT 'EUR',

            -- Restrictions
            allowed_instruments TEXT,  -- JSON: ['equities', 'bonds', 'derivatives']
            restricted_sectors TEXT,  -- JSON: ['defense', 'tobacco']
            restricted_countries TEXT,  -- JSON: ['Russia', 'Iran']
            max_single_position_pct REAL,  -- Max % in single position
            leverage_allowed INTEGER DEFAULT 0,  -- Boolean
            derivatives_allowed INTEGER DEFAULT 1,  -- Boolean
            short_selling_allowed INTEGER DEFAULT 0,  -- Boolean

            -- ESG Requirements
            esg_mandate INTEGER DEFAULT 0,  -- Boolean: must follow ESG
            esg_min_score REAL,  -- Minimum ESG score required
            sfdr_classification TEXT,  -- 'article_6', 'article_8', 'article_9'
            exclusion_list TEXT,  -- JSON: specific exclusions

            -- Regulatory
            reporting_requirements TEXT,  -- JSON: required reports
            tax_status TEXT,
            domicile_country TEXT,

            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id)
        );

        -- CRM: Conference/Event Attendance
        CREATE TABLE src_client_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            event_type TEXT,  -- 'conference', 'webinar', 'roadshow', 'company_visit'
            event_date TEXT NOT NULL,
            location TEXT,
            attended INTEGER DEFAULT 1,  -- Boolean
            registered INTEGER DEFAULT 1,  -- Boolean
            sessions_attended TEXT,  -- JSON array
            feedback_score INTEGER,  -- 1-5 rating
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES src_clients(client_id)
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


# =============================================================================
# CRM DATA: Meetings, Email Activity, Contact Preferences
# =============================================================================

ODDO_EMPLOYEES = [
    "Marc Lefèvre", "Sophie Dubois", "Thomas Müller", "Anna Schmidt",
    "Pierre Martin", "Claire Bernard", "Hans Weber", "Marie Laurent"
]

MEETING_TYPES = ["in_person", "video_call", "roadshow", "conference", "dinner"]
MEETING_LOCATIONS = [
    "ODDO BHF Paris HQ", "ODDO BHF Frankfurt", "Client Office",
    "Le Bristol Paris", "Savoy London", "Four Seasons Munich",
    "Virtual (Teams)", "Virtual (Zoom)", "Davos WEF", "Monaco Investor Day"
]

MEETING_TOPICS = [
    "Portfolio Review", "Market Outlook", "Sector Deep-Dive",
    "New IPO Discussion", "Risk Assessment", "ESG Strategy",
    "Q4 Earnings Preview", "Rate Environment", "China Exposure",
    "Tech Sector Rotation", "Energy Transition", "AI Investment Thesis"
]

ODDO_EVENTS = [
    {"name": "ODDO BHF Forum Frankfurt", "type": "conference", "location": "Frankfurt"},
    {"name": "ODDO BHF CEO Conference Paris", "type": "conference", "location": "Paris"},
    {"name": "European Small & Mid Cap Conference", "type": "conference", "location": "Lyon"},
    {"name": "German Investment Seminar", "type": "conference", "location": "Munich"},
    {"name": "ODDO BHF Sustainability Day", "type": "conference", "location": "Paris"},
    {"name": "Automotive Sector Roadshow", "type": "roadshow", "location": "Stuttgart"},
    {"name": "Tech Sector Webinar", "type": "webinar", "location": "Virtual"},
    {"name": "Luxury Goods Company Visit", "type": "company_visit", "location": "Paris"},
    {"name": "Healthcare Innovation Day", "type": "webinar", "location": "Virtual"},
    {"name": "Banking Sector Update", "type": "webinar", "location": "Virtual"},
]


def insert_client_meetings(conn):
    """Insert realistic meeting history."""
    print("Inserting client meetings...")

    conn.execute("DELETE FROM src_client_meetings")

    cur = conn.execute("SELECT client_id, client_name, firm_name, region FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    meeting_count = 0
    today = datetime.now()

    for client in clients:
        # Each client has 5-15 meetings over the past 2 years
        num_meetings = random.randint(5, 15)

        for _ in range(num_meetings):
            # Random date in past 2 years
            days_ago = random.randint(1, 730)
            meeting_date = today - timedelta(days=days_ago)

            meeting_type = random.choice(MEETING_TYPES)
            location = random.choice(MEETING_LOCATIONS)

            # Adjust location based on type
            if meeting_type == "video_call":
                location = random.choice(["Virtual (Teams)", "Virtual (Zoom)"])
            elif meeting_type == "dinner":
                location = random.choice(["Le Bristol Paris", "Savoy London", "Four Seasons Munich"])

            duration = random.choice([30, 45, 60, 90, 120]) if meeting_type != "dinner" else random.randint(90, 180)

            topics = random.sample(MEETING_TOPICS, random.randint(2, 4))
            outcome = random.choices(
                ["positive", "neutral", "follow_up_needed"],
                weights=[0.5, 0.35, 0.15]
            )[0]

            organizer = random.choice(ODDO_EMPLOYEES)

            conn.execute("""
                INSERT INTO src_client_meetings
                (client_id, meeting_date, meeting_type, location, duration_minutes,
                 attendees, topics_discussed, outcome, organizer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client["client_id"],
                meeting_date.strftime("%Y-%m-%d %H:%M"),
                meeting_type,
                location,
                duration,
                json.dumps([client["client_name"], organizer]),
                json.dumps(topics),
                outcome,
                organizer
            ))
            meeting_count += 1

    conn.commit()
    print(f"  Inserted {meeting_count} meetings")


def insert_email_activity(conn):
    """Insert email activity summaries by month."""
    print("Inserting email activity...")

    conn.execute("DELETE FROM src_client_email_activity")

    cur = conn.execute("SELECT client_id, client_type FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    activity_count = 0

    # Generate 18 months of email activity
    for month_offset in range(18):
        month_date = datetime.now() - timedelta(days=month_offset * 30)
        month_str = month_date.strftime("%Y-%m")

        for client in clients:
            # Activity level based on client type
            if client["client_type"] in ["Hedge Fund", "Asset Manager"]:
                base_sent = random.randint(15, 40)
                base_received = random.randint(10, 30)
            elif client["client_type"] in ["Pension Fund", "Sovereign Wealth"]:
                base_sent = random.randint(5, 15)
                base_received = random.randint(3, 10)
            else:
                base_sent = random.randint(8, 25)
                base_received = random.randint(5, 15)

            # Add some randomness
            emails_sent = max(1, base_sent + random.randint(-5, 5))
            emails_received = max(1, base_received + random.randint(-3, 3))
            emails_opened = int(emails_sent * random.uniform(0.6, 0.95))
            links_clicked = int(emails_opened * random.uniform(0.1, 0.4))

            # Response time (hours) - faster for active clients
            avg_response = random.uniform(2, 48) if client["client_type"] == "Hedge Fund" else random.uniform(4, 72)

            conn.execute("""
                INSERT INTO src_client_email_activity
                (client_id, month, emails_sent, emails_received, avg_response_time_hours,
                 emails_opened, links_clicked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                client["client_id"],
                month_str,
                emails_sent,
                emails_received,
                round(avg_response, 1),
                emails_opened,
                links_clicked
            ))
            activity_count += 1

    conn.commit()
    print(f"  Inserted {activity_count} email activity records")


def insert_contact_preferences(conn):
    """Insert contact preferences for each client."""
    print("Inserting contact preferences...")

    conn.execute("DELETE FROM src_client_contact_prefs")

    cur = conn.execute("SELECT client_id, client_type, region FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    for client in clients:
        # Preferences based on client type
        if client["client_type"] == "Hedge Fund":
            channel = random.choice(["phone", "phone", "email"])
            frequency = random.choice(["daily", "weekly"])
            time = "morning"
        elif client["client_type"] in ["Pension Fund", "Insurance"]:
            channel = random.choice(["email", "video", "in_person"])
            frequency = random.choice(["weekly", "bi-weekly", "monthly"])
            time = random.choice(["morning", "afternoon"])
        else:
            channel = random.choice(["phone", "email", "video"])
            frequency = random.choice(["weekly", "bi-weekly"])
            time = random.choice(["morning", "afternoon"])

        # Language based on region
        if client["region"] in ["DACH"]:
            language = random.choice(["German", "English"])
        elif client["region"] in ["France"]:
            language = random.choice(["French", "English"])
        else:
            language = "English"

        # Preferred days
        days = random.sample(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], random.randint(3, 5))

        conn.execute("""
            INSERT INTO src_client_contact_prefs
            (client_id, preferred_channel, preferred_time, preferred_days,
             preferred_frequency, language, timezone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client["client_id"],
            channel,
            time,
            json.dumps(days),
            frequency,
            language,
            "CET" if client["region"] in ["DACH", "France", "Benelux"] else "GMT"
        ))

    conn.commit()
    print(f"  Inserted {len(clients)} contact preferences")


def insert_client_events(conn):
    """Insert event attendance history."""
    print("Inserting event attendance...")

    conn.execute("DELETE FROM src_client_events")

    cur = conn.execute("SELECT client_id, client_type, region FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    event_count = 0
    today = datetime.now()

    for client in clients:
        # Each client attends 2-8 events over 2 years
        num_events = random.randint(2, 8)
        attended_events = random.sample(ODDO_EVENTS, min(num_events, len(ODDO_EVENTS)))

        for event in attended_events:
            # Random date in past 2 years
            days_ago = random.randint(1, 730)
            event_date = today - timedelta(days=days_ago)

            # Some registered but didn't attend
            registered = 1
            attended = 1 if random.random() > 0.15 else 0

            feedback = random.randint(3, 5) if attended else None

            conn.execute("""
                INSERT INTO src_client_events
                (client_id, event_name, event_type, event_date, location,
                 registered, attended, feedback_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client["client_id"],
                event["name"],
                event["type"],
                event_date.strftime("%Y-%m-%d"),
                event["location"],
                registered,
                attended,
                feedback
            ))
            event_count += 1

    conn.commit()
    print(f"  Inserted {event_count} event attendance records")


# =============================================================================
# COMPLIANCE / KYC DATA
# =============================================================================

def insert_compliance_data(conn):
    """Insert compliance and KYC data for each client."""
    print("Inserting compliance/KYC data...")

    conn.execute("DELETE FROM src_client_compliance")

    cur = conn.execute("SELECT client_id, client_type, region FROM src_clients")
    clients = [dict(row) for row in cur.fetchall()]

    for client in clients:
        # KYC status - most are approved
        kyc_status = random.choices(
            ["approved", "approved", "approved", "review_needed", "pending"],
            weights=[0.7, 0.15, 0.05, 0.07, 0.03]
        )[0]

        # KYC expiry - within next 2 years
        kyc_expiry = datetime.now() + timedelta(days=random.randint(30, 730))
        kyc_last_review = datetime.now() - timedelta(days=random.randint(30, 365))

        # Risk rating based on client type
        if client["client_type"] == "Hedge Fund":
            kyc_risk = random.choice(["standard", "enhanced"])
        elif client["client_type"] in ["Pension Fund", "Insurance", "Sovereign Wealth"]:
            kyc_risk = "low"
        else:
            kyc_risk = random.choice(["low", "standard"])

        # Investor type (MiFID II)
        if client["client_type"] in ["Pension Fund", "Insurance", "Sovereign Wealth", "Asset Manager"]:
            investor_type = "professional"
        elif client["client_type"] == "Hedge Fund":
            investor_type = random.choice(["professional", "eligible_counterparty"])
        else:
            investor_type = random.choice(["professional", "retail"])

        # Mandate type
        mandate_type = random.choice(["discretionary", "advisory", "execution_only"])

        # AUM (if disclosed)
        if client["client_type"] == "Sovereign Wealth":
            aum = random.uniform(50_000_000_000, 500_000_000_000)
        elif client["client_type"] == "Pension Fund":
            aum = random.uniform(10_000_000_000, 100_000_000_000)
        elif client["client_type"] == "Asset Manager":
            aum = random.uniform(5_000_000_000, 80_000_000_000)
        elif client["client_type"] == "Hedge Fund":
            aum = random.uniform(500_000_000, 20_000_000_000)
        else:
            aum = random.uniform(100_000_000, 5_000_000_000)

        # Allowed instruments
        if client["client_type"] == "Pension Fund":
            allowed = ["equities", "bonds", "etf"]
        elif client["client_type"] == "Hedge Fund":
            allowed = ["equities", "bonds", "derivatives", "etf", "fx", "commodities"]
        else:
            allowed = random.sample(["equities", "bonds", "derivatives", "etf"], random.randint(2, 4))

        # Restricted sectors (some have ESG restrictions)
        restricted_sectors = []
        if random.random() > 0.6:
            restricted_sectors = random.sample(["defense", "tobacco", "gambling", "fossil_fuels", "nuclear"], random.randint(1, 3))

        # Restricted countries
        restricted_countries = ["Russia", "North Korea", "Iran"]
        if random.random() > 0.7:
            restricted_countries.append("China")

        # ESG mandate
        has_esg = random.random() > 0.4
        esg_min_score = random.uniform(50, 70) if has_esg else None
        sfdr = random.choice(["article_6", "article_8", "article_9"]) if has_esg else "article_6"

        # Trading permissions
        derivatives_allowed = 1 if client["client_type"] == "Hedge Fund" else random.choice([0, 1])
        short_selling = 1 if client["client_type"] == "Hedge Fund" else 0
        leverage = 1 if client["client_type"] == "Hedge Fund" else 0
        max_position = random.choice([5, 10, 15, 20]) if client["client_type"] != "Hedge Fund" else None

        # Domicile
        domicile_map = {
            "DACH": random.choice(["Germany", "Austria", "Switzerland"]),
            "France": "France",
            "Benelux": random.choice(["Netherlands", "Belgium", "Luxembourg"]),
            "UK": "United Kingdom",
            "Nordics": random.choice(["Norway", "Sweden", "Denmark", "Finland"])
        }
        domicile = domicile_map.get(client["region"], "Luxembourg")

        conn.execute("""
            INSERT INTO src_client_compliance
            (client_id, kyc_status, kyc_expiry_date, kyc_last_review, kyc_risk_rating,
             investor_type, mandate_type, aum_declared, allowed_instruments,
             restricted_sectors, restricted_countries, max_single_position_pct,
             leverage_allowed, derivatives_allowed, short_selling_allowed,
             esg_mandate, esg_min_score, sfdr_classification, domicile_country)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client["client_id"],
            kyc_status,
            kyc_expiry.strftime("%Y-%m-%d"),
            kyc_last_review.strftime("%Y-%m-%d"),
            kyc_risk,
            investor_type,
            mandate_type,
            aum,
            json.dumps(allowed),
            json.dumps(restricted_sectors),
            json.dumps(restricted_countries),
            max_position,
            leverage,
            derivatives_allowed,
            short_selling,
            1 if has_esg else 0,
            esg_min_score,
            sfdr,
            domicile
        ))

    conn.commit()
    print(f"  Inserted {len(clients)} compliance records")


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

    # CRM & Compliance data
    insert_client_meetings(conn)
    insert_email_activity(conn)
    insert_contact_preferences(conn)
    insert_client_events(conn)
    insert_compliance_data(conn)

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
