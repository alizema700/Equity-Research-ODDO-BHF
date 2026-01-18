"""
Expanded Stock Universe for ODDO BHF Platform
==============================================
140+ European and Global stocks with detailed metadata
"""

EXPANDED_STOCKS = [
    # =========================================================================
    # TECHNOLOGY / SEMICONDUCTORS (25 stocks)
    # =========================================================================
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Mega", "volatility": "high", "dividend_yield": 0.02, "beta": 1.7},
    {"ticker": "ASML", "company_name": "ASML Holding NV", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Mega", "volatility": "high", "dividend_yield": 0.7, "beta": 1.3},
    {"ticker": "SAP", "company_name": "SAP SE", "sector": "Technology", "region": "Europe", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.5, "beta": 1.0},
    {"ticker": "IFNNY", "company_name": "Infineon Technologies AG", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.8, "beta": 1.4},
    {"ticker": "STM", "company_name": "STMicroelectronics NV", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.5, "beta": 1.5},
    {"ticker": "AMD", "company_name": "Advanced Micro Devices", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Mega", "volatility": "high", "dividend_yield": 0.0, "beta": 1.8},
    {"ticker": "DSY.PA", "company_name": "Dassault Systemes SE", "sector": "Technology", "region": "Europe", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.5, "beta": 0.9},
    {"ticker": "CAP.PA", "company_name": "Capgemini SE", "sector": "Technology", "region": "Europe", "theme_tag": "IT Services", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.8, "beta": 1.1},
    {"ticker": "ATOS.PA", "company_name": "Atos SE", "sector": "Technology", "region": "Europe", "theme_tag": "IT Services", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.6},
    {"ticker": "WOLF.PA", "company_name": "Worldline SA", "sector": "Technology", "region": "Europe", "theme_tag": "Fintech", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.3},
    {"ticker": "NEXI.MI", "company_name": "Nexi SpA", "sector": "Technology", "region": "Europe", "theme_tag": "Fintech", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.2},
    {"ticker": "TEAM", "company_name": "Atlassian Corporation", "sector": "Technology", "region": "US", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 1.4},
    {"ticker": "CRM", "company_name": "Salesforce Inc", "sector": "Technology", "region": "US", "theme_tag": "Software", "market_cap_bucket": "Mega", "volatility": "medium", "dividend_yield": 0.0, "beta": 1.2},
    {"ticker": "NOW", "company_name": "ServiceNow Inc", "sector": "Technology", "region": "US", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.0, "beta": 1.1},
    {"ticker": "INTC", "company_name": "Intel Corporation", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 1.2, "beta": 1.0},
    {"ticker": "TSM", "company_name": "Taiwan Semiconductor", "sector": "Technology", "region": "Asia", "theme_tag": "AI", "market_cap_bucket": "Mega", "volatility": "high", "dividend_yield": 1.5, "beta": 1.3},
    {"ticker": "SNPS", "company_name": "Synopsys Inc", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.0, "beta": 1.2},
    {"ticker": "CDNS", "company_name": "Cadence Design Systems", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.0, "beta": 1.1},
    {"ticker": "BE.PA", "company_name": "Bureau Veritas SA", "sector": "Technology", "region": "Europe", "theme_tag": "Quality Assurance", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 2.5, "beta": 0.8},
    {"ticker": "DDOG", "company_name": "Datadog Inc", "sector": "Technology", "region": "US", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 1.5},
    {"ticker": "NET", "company_name": "Cloudflare Inc", "sector": "Technology", "region": "US", "theme_tag": "Software", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 1.6},
    {"ticker": "PLTR", "company_name": "Palantir Technologies", "sector": "Technology", "region": "US", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 2.0},
    {"ticker": "SOF.PA", "company_name": "Soitec SA", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.5},
    {"ticker": "ASM.AS", "company_name": "ASM International NV", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.4, "beta": 1.4},
    {"ticker": "BESI.AS", "company_name": "BE Semiconductor Industries", "sector": "Technology", "region": "Europe", "theme_tag": "AI", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 1.0, "beta": 1.5},

    # =========================================================================
    # INDUSTRIALS (20 stocks)
    # =========================================================================
    {"ticker": "SIE.DE", "company_name": "Siemens AG", "sector": "Industrials", "region": "Europe", "theme_tag": "Automation", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.8, "beta": 1.1},
    {"ticker": "AIR.PA", "company_name": "Airbus SE", "sector": "Industrials", "region": "Europe", "theme_tag": "Aerospace", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.2, "beta": 1.3},
    {"ticker": "SU.PA", "company_name": "Schneider Electric SE", "sector": "Industrials", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.8, "beta": 1.0},
    {"ticker": "ABB", "company_name": "ABB Ltd", "sector": "Industrials", "region": "Europe", "theme_tag": "Automation", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.0, "beta": 1.0},
    {"ticker": "DG.PA", "company_name": "Vinci SA", "sector": "Industrials", "region": "Europe", "theme_tag": "Infrastructure", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.8},
    {"ticker": "HON", "company_name": "Honeywell International", "sector": "Industrials", "region": "US", "theme_tag": "Automation", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.0, "beta": 0.9},
    {"ticker": "CAT", "company_name": "Caterpillar Inc", "sector": "Industrials", "region": "US", "theme_tag": "Infrastructure", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.6, "beta": 1.1},
    {"ticker": "GE", "company_name": "General Electric Co", "sector": "Industrials", "region": "US", "theme_tag": "Aerospace", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.7, "beta": 1.2},
    {"ticker": "KNEBV.HE", "company_name": "Kone Oyj", "sector": "Industrials", "region": "Europe", "theme_tag": "Infrastructure", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.8, "beta": 0.7},
    {"ticker": "RAND.AS", "company_name": "Randstad NV", "sector": "Industrials", "region": "Europe", "theme_tag": "Services", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 4.5, "beta": 1.2},
    {"ticker": "SGO.PA", "company_name": "Saint-Gobain SA", "sector": "Industrials", "region": "Europe", "theme_tag": "Construction", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 3.0, "beta": 1.1},
    {"ticker": "VOLVA.ST", "company_name": "Volvo AB", "sector": "Industrials", "region": "Europe", "theme_tag": "Transportation", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.0, "beta": 1.2},
    {"ticker": "MTX.DE", "company_name": "MTU Aero Engines AG", "sector": "Industrials", "region": "Europe", "theme_tag": "Aerospace", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 1.5, "beta": 1.3},
    {"ticker": "SAF.PA", "company_name": "Safran SA", "sector": "Industrials", "region": "Europe", "theme_tag": "Aerospace", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.2, "beta": 1.2},
    {"ticker": "LR.PA", "company_name": "Legrand SA", "sector": "Industrials", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 2.2, "beta": 0.9},
    {"ticker": "ATCO-A.ST", "company_name": "Atlas Copco AB", "sector": "Industrials", "region": "Europe", "theme_tag": "Automation", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.8, "beta": 1.0},
    {"ticker": "TEP.PA", "company_name": "Teleperformance SE", "sector": "Industrials", "region": "Europe", "theme_tag": "Services", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 2.5, "beta": 1.3},
    {"ticker": "DE", "company_name": "Deere & Company", "sector": "Industrials", "region": "US", "theme_tag": "Agriculture", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.3, "beta": 1.0},
    {"ticker": "RR.L", "company_name": "Rolls-Royce Holdings", "sector": "Industrials", "region": "Europe", "theme_tag": "Aerospace", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 1.5},
    {"ticker": "BA", "company_name": "Boeing Co", "sector": "Industrials", "region": "US", "theme_tag": "Aerospace", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 0.0, "beta": 1.4},

    # =========================================================================
    # DEFENSE / AEROSPACE (10 stocks) - wichtig für Compliance-Filter
    # =========================================================================
    {"ticker": "LMT", "company_name": "Lockheed Martin Corp", "sector": "Defense", "region": "US", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.6, "beta": 0.7},
    {"ticker": "RTX", "company_name": "RTX Corporation", "sector": "Defense", "region": "US", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.4, "beta": 0.8},
    {"ticker": "NOC", "company_name": "Northrop Grumman Corp", "sector": "Defense", "region": "US", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 1.5, "beta": 0.6},
    {"ticker": "GD", "company_name": "General Dynamics Corp", "sector": "Defense", "region": "US", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.0, "beta": 0.7},
    {"ticker": "RHM.DE", "company_name": "Rheinmetall AG", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 1.5, "beta": 1.4},
    {"ticker": "HO.PA", "company_name": "Thales SA", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.0, "beta": 0.9},
    {"ticker": "BA.L", "company_name": "BAE Systems PLC", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.5, "beta": 0.7},
    {"ticker": "LDO.MI", "company_name": "Leonardo SpA", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 1.2, "beta": 1.1},
    {"ticker": "SAAB-B.ST", "company_name": "Saab AB", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 1.0, "beta": 1.0},
    {"ticker": "HAG.DE", "company_name": "Hensoldt AG", "sector": "Defense", "region": "Europe", "theme_tag": "Defense", "market_cap_bucket": "Small", "volatility": "high", "dividend_yield": 0.8, "beta": 1.3},

    # =========================================================================
    # CONSUMER / LUXURY (18 stocks)
    # =========================================================================
    {"ticker": "MC.PA", "company_name": "LVMH Moet Hennessy", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Mega", "volatility": "medium", "dividend_yield": 1.5, "beta": 1.1},
    {"ticker": "RMS.PA", "company_name": "Hermes International", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.8, "beta": 0.9},
    {"ticker": "KER.PA", "company_name": "Kering SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 2.5, "beta": 1.2},
    {"ticker": "OR.PA", "company_name": "L'Oreal SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Consumer", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 1.5, "beta": 0.8},
    {"ticker": "ADS.DE", "company_name": "adidas AG", "sector": "Consumer", "region": "Europe", "theme_tag": "Consumer", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 1.0, "beta": 1.3},
    {"ticker": "NESN.SW", "company_name": "Nestle SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Defensive", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 3.0, "beta": 0.5},
    {"ticker": "UL", "company_name": "Unilever PLC", "sector": "Consumer", "region": "Europe", "theme_tag": "Defensive", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.6},
    {"ticker": "DANOY", "company_name": "Danone SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Defensive", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.8, "beta": 0.5},
    {"ticker": "PG", "company_name": "Procter & Gamble Co", "sector": "Consumer", "region": "US", "theme_tag": "Defensive", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 2.4, "beta": 0.4},
    {"ticker": "KO", "company_name": "Coca-Cola Co", "sector": "Consumer", "region": "US", "theme_tag": "Defensive", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 3.0, "beta": 0.5},
    {"ticker": "PEP", "company_name": "PepsiCo Inc", "sector": "Consumer", "region": "US", "theme_tag": "Defensive", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 2.7, "beta": 0.5},
    {"ticker": "PUMA.DE", "company_name": "Puma SE", "sector": "Consumer", "region": "Europe", "theme_tag": "Consumer", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 1.2, "beta": 1.2},
    {"ticker": "BOSS.DE", "company_name": "Hugo Boss AG", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 3.0, "beta": 1.3},
    {"ticker": "MONC.MI", "company_name": "Moncler SpA", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.0, "beta": 1.1},
    {"ticker": "CFR.SW", "company_name": "Richemont SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.0, "beta": 1.0},
    {"ticker": "BRBY.L", "company_name": "Burberry Group PLC", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 4.0, "beta": 1.3},
    {"ticker": "EL", "company_name": "Estee Lauder Cos", "sector": "Consumer", "region": "US", "theme_tag": "Consumer", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 2.0, "beta": 1.2},
    {"ticker": "RCO.PA", "company_name": "Remy Cointreau SA", "sector": "Consumer", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 2.5, "beta": 1.2},

    # =========================================================================
    # FINANCIALS (20 stocks)
    # =========================================================================
    {"ticker": "BNP.PA", "company_name": "BNP Paribas SA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 6.5, "beta": 1.3},
    {"ticker": "DBK.DE", "company_name": "Deutsche Bank AG", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 3.0, "beta": 1.5},
    {"ticker": "INGA.AS", "company_name": "ING Groep NV", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 7.0, "beta": 1.3},
    {"ticker": "GLE.PA", "company_name": "Societe Generale SA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 8.0, "beta": 1.5},
    {"ticker": "ALV.DE", "company_name": "Allianz SE", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 4.5, "beta": 0.9},
    {"ticker": "MUV2.DE", "company_name": "Munich Re", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.8},
    {"ticker": "CS.PA", "company_name": "AXA SA", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 5.5, "beta": 0.9},
    {"ticker": "HSBA.L", "company_name": "HSBC Holdings PLC", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.0, "beta": 1.1},
    {"ticker": "UBSG.SW", "company_name": "UBS Group AG", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 4.0, "beta": 1.2},
    {"ticker": "UCG.MI", "company_name": "UniCredit SpA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 6.0, "beta": 1.4},
    {"ticker": "ISP.MI", "company_name": "Intesa Sanpaolo SpA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 7.5, "beta": 1.2},
    {"ticker": "SAN.MC", "company_name": "Banco Santander SA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 4.5, "beta": 1.3},
    {"ticker": "BBVA.MC", "company_name": "BBVA SA", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.5, "beta": 1.3},
    {"ticker": "CBK.DE", "company_name": "Commerzbank AG", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 4.0, "beta": 1.5},
    {"ticker": "LLOY.L", "company_name": "Lloyds Banking Group", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.0, "beta": 1.2},
    {"ticker": "BARC.L", "company_name": "Barclays PLC", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 4.5, "beta": 1.4},
    {"ticker": "NN.AS", "company_name": "NN Group NV", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 6.0, "beta": 0.8},
    {"ticker": "G.MI", "company_name": "Generali SpA", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 5.0, "beta": 0.9},
    {"ticker": "ZURN.SW", "company_name": "Zurich Insurance Group", "sector": "Financials", "region": "Europe", "theme_tag": "Insurance", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 5.5, "beta": 0.7},
    {"ticker": "SWEDA.ST", "company_name": "Swedbank AB", "sector": "Financials", "region": "Europe", "theme_tag": "Banking", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 7.0, "beta": 1.1},

    # =========================================================================
    # HEALTHCARE / PHARMA (18 stocks)
    # =========================================================================
    {"ticker": "NVO", "company_name": "Novo Nordisk A/S", "sector": "Healthcare", "region": "Europe", "theme_tag": "GLP1", "market_cap_bucket": "Mega", "volatility": "medium", "dividend_yield": 1.0, "beta": 0.9},
    {"ticker": "ROG.SW", "company_name": "Roche Holding AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.6},
    {"ticker": "SAN.PA", "company_name": "Sanofi SA", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.8, "beta": 0.6},
    {"ticker": "BAYN.DE", "company_name": "Bayer AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 5.0, "beta": 1.0},
    {"ticker": "AZN", "company_name": "AstraZeneca PLC", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.0, "beta": 0.6},
    {"ticker": "NOVN.SW", "company_name": "Novartis AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.5},
    {"ticker": "GSK.L", "company_name": "GSK PLC", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 4.0, "beta": 0.6},
    {"ticker": "LLY", "company_name": "Eli Lilly & Co", "sector": "Healthcare", "region": "US", "theme_tag": "GLP1", "market_cap_bucket": "Mega", "volatility": "medium", "dividend_yield": 0.7, "beta": 0.8},
    {"ticker": "MRK", "company_name": "Merck & Co Inc", "sector": "Healthcare", "region": "US", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 2.5, "beta": 0.5},
    {"ticker": "JNJ", "company_name": "Johnson & Johnson", "sector": "Healthcare", "region": "US", "theme_tag": "Pharma", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 3.0, "beta": 0.5},
    {"ticker": "PFE", "company_name": "Pfizer Inc", "sector": "Healthcare", "region": "US", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.5, "beta": 0.7},
    {"ticker": "ABBV", "company_name": "AbbVie Inc", "sector": "Healthcare", "region": "US", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.7},
    {"ticker": "UCB.BR", "company_name": "UCB SA", "sector": "Healthcare", "region": "Europe", "theme_tag": "Pharma", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 1.2, "beta": 0.8},
    {"ticker": "GILD", "company_name": "Gilead Sciences Inc", "sector": "Healthcare", "region": "US", "theme_tag": "Pharma", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.6},
    {"ticker": "SIKA.SW", "company_name": "Sika AG", "sector": "Healthcare", "region": "Europe", "theme_tag": "Specialty", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.2, "beta": 1.0},
    {"ticker": "SRG.MI", "company_name": "Snam SpA", "sector": "Healthcare", "region": "Europe", "theme_tag": "Defensive", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 6.5, "beta": 0.5},
    {"ticker": "REGN", "company_name": "Regeneron Pharmaceuticals", "sector": "Healthcare", "region": "US", "theme_tag": "Biotech", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.0, "beta": 0.8},
    {"ticker": "VRTX", "company_name": "Vertex Pharmaceuticals", "sector": "Healthcare", "region": "US", "theme_tag": "Biotech", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.0, "beta": 0.7},

    # =========================================================================
    # ENERGY / UTILITIES (15 stocks)
    # =========================================================================
    {"ticker": "TTE.PA", "company_name": "TotalEnergies SE", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.0, "beta": 1.0},
    {"ticker": "SHEL", "company_name": "Shell PLC", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 4.0, "beta": 0.9},
    {"ticker": "ENEL.MI", "company_name": "Enel SpA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 7.0, "beta": 0.9},
    {"ticker": "IBE.MC", "company_name": "Iberdrola SA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 4.5, "beta": 0.7},
    {"ticker": "ENGI.PA", "company_name": "Engie SA", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 8.0, "beta": 0.8},
    {"ticker": "RWE.DE", "company_name": "RWE AG", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.5, "beta": 1.0},
    {"ticker": "E.ON.DE", "company_name": "E.ON SE", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 4.5, "beta": 0.7},
    {"ticker": "BP.L", "company_name": "BP PLC", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 4.5, "beta": 1.0},
    {"ticker": "EQNR.OL", "company_name": "Equinor ASA", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 3.5, "beta": 1.1},
    {"ticker": "VWS.CO", "company_name": "Vestas Wind Systems", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.3},
    {"ticker": "ORSTED.CO", "company_name": "Orsted A/S", "sector": "Utilities", "region": "Europe", "theme_tag": "Renewables", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 2.0, "beta": 1.2},
    {"ticker": "XOM", "company_name": "Exxon Mobil Corp", "sector": "Energy", "region": "US", "theme_tag": "EnergyTransition", "market_cap_bucket": "Mega", "volatility": "medium", "dividend_yield": 3.5, "beta": 0.9},
    {"ticker": "CVX", "company_name": "Chevron Corp", "sector": "Energy", "region": "US", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 4.0, "beta": 0.9},
    {"ticker": "ENI.MI", "company_name": "Eni SpA", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 6.5, "beta": 1.0},
    {"ticker": "REP.MC", "company_name": "Repsol SA", "sector": "Energy", "region": "Europe", "theme_tag": "EnergyTransition", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 5.5, "beta": 1.1},

    # =========================================================================
    # AUTOMOTIVE (12 stocks)
    # =========================================================================
    {"ticker": "VOW3.DE", "company_name": "Volkswagen AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 6.0, "beta": 1.3},
    {"ticker": "BMW.DE", "company_name": "BMW AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.5, "beta": 1.2},
    {"ticker": "MBG.DE", "company_name": "Mercedes-Benz Group AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 6.5, "beta": 1.2},
    {"ticker": "P911.DE", "company_name": "Porsche AG", "sector": "Automotive", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 2.5, "beta": 1.1},
    {"ticker": "STLAM.MI", "company_name": "Stellantis NV", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 8.0, "beta": 1.4},
    {"ticker": "RNO.PA", "company_name": "Renault SA", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 3.5, "beta": 1.5},
    {"ticker": "TSLA", "company_name": "Tesla Inc", "sector": "Automotive", "region": "US", "theme_tag": "EV", "market_cap_bucket": "Mega", "volatility": "high", "dividend_yield": 0.0, "beta": 2.0},
    {"ticker": "F", "company_name": "Ford Motor Co", "sector": "Automotive", "region": "US", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 5.0, "beta": 1.4},
    {"ticker": "GM", "company_name": "General Motors Co", "sector": "Automotive", "region": "US", "theme_tag": "EV", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 1.0, "beta": 1.3},
    {"ticker": "CON.DE", "company_name": "Continental AG", "sector": "Automotive", "region": "Europe", "theme_tag": "EV", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 3.5, "beta": 1.4},
    {"ticker": "RACE.MI", "company_name": "Ferrari NV", "sector": "Automotive", "region": "Europe", "theme_tag": "Luxury", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 0.7, "beta": 1.0},
    {"ticker": "7203.T", "company_name": "Toyota Motor Corp", "sector": "Automotive", "region": "Asia", "theme_tag": "EV", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 2.5, "beta": 0.8},

    # =========================================================================
    # TELECOM / MEDIA (8 stocks)
    # =========================================================================
    {"ticker": "DTE.DE", "company_name": "Deutsche Telekom AG", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 3.5, "beta": 0.7},
    {"ticker": "TEF.MC", "company_name": "Telefonica SA", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 7.5, "beta": 0.9},
    {"ticker": "ORA.PA", "company_name": "Orange SA", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 7.0, "beta": 0.6},
    {"ticker": "VOD.L", "company_name": "Vodafone Group PLC", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 8.0, "beta": 0.8},
    {"ticker": "TELIA.ST", "company_name": "Telia Company AB", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 6.5, "beta": 0.6},
    {"ticker": "KPN.AS", "company_name": "Koninklijke KPN NV", "sector": "Telecom", "region": "Europe", "theme_tag": "Telecom", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 4.5, "beta": 0.5},
    {"ticker": "VIV.PA", "company_name": "Vivendi SE", "sector": "Media", "region": "Europe", "theme_tag": "Media", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 2.5, "beta": 0.9},
    {"ticker": "WBD", "company_name": "Warner Bros Discovery", "sector": "Media", "region": "US", "theme_tag": "Media", "market_cap_bucket": "Mid", "volatility": "high", "dividend_yield": 0.0, "beta": 1.5},

    # =========================================================================
    # MATERIALS / CHEMICALS (8 stocks)
    # =========================================================================
    {"ticker": "LIN", "company_name": "Linde PLC", "sector": "Materials", "region": "Europe", "theme_tag": "Chemicals", "market_cap_bucket": "Mega", "volatility": "low", "dividend_yield": 1.2, "beta": 0.8},
    {"ticker": "AI.PA", "company_name": "Air Liquide SA", "sector": "Materials", "region": "Europe", "theme_tag": "Chemicals", "market_cap_bucket": "Large", "volatility": "low", "dividend_yield": 1.8, "beta": 0.7},
    {"ticker": "BAS.DE", "company_name": "BASF SE", "sector": "Materials", "region": "Europe", "theme_tag": "Chemicals", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 6.5, "beta": 1.1},
    {"ticker": "SYK.DE", "company_name": "Symrise AG", "sector": "Materials", "region": "Europe", "theme_tag": "Specialty", "market_cap_bucket": "Mid", "volatility": "low", "dividend_yield": 1.0, "beta": 0.8},
    {"ticker": "DSM.AS", "company_name": "DSM-Firmenich AG", "sector": "Materials", "region": "Europe", "theme_tag": "Specialty", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 1.5, "beta": 0.9},
    {"ticker": "AKZA.AS", "company_name": "Akzo Nobel NV", "sector": "Materials", "region": "Europe", "theme_tag": "Chemicals", "market_cap_bucket": "Mid", "volatility": "medium", "dividend_yield": 3.0, "beta": 1.0},
    {"ticker": "RIO", "company_name": "Rio Tinto PLC", "sector": "Materials", "region": "Europe", "theme_tag": "Mining", "market_cap_bucket": "Large", "volatility": "medium", "dividend_yield": 5.5, "beta": 1.1},
    {"ticker": "GLEN.L", "company_name": "Glencore PLC", "sector": "Materials", "region": "Europe", "theme_tag": "Mining", "market_cap_bucket": "Large", "volatility": "high", "dividend_yield": 4.0, "beta": 1.3},
]

# Total: 174 stocks
