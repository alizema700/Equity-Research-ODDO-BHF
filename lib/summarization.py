"""
Call Log Pre-Summarization Layer

Aggregates and summarizes the last N call logs for a client before story generation.
This reduces context size and improves LLM focus.
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import database layer
from lib.database import db, log_ai_generation


class CallLogSummarizer:
    """
    Pre-summarizes call logs for a client to create condensed context.

    When Mistral API is available, uses LLM for intelligent summarization.
    Otherwise, uses rule-based extraction.
    """

    def __init__(self, llm_client=None, model: str = "mistral-small-latest"):
        """
        Initialize summarizer.

        Args:
            llm_client: LLM client instance (e.g., Mistral client)
            model: Model to use for summarization (FAST tier default)
        """
        self.llm_client = llm_client
        self.model = model

    def get_recent_calls(self, client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent call logs for a client."""
        sql = """
        SELECT
            c.call_id,
            c.call_timestamp,
            c.direction,
            c.duration_minutes,
            c.discussed_company,
            c.discussed_sector,
            c.notes_raw,
            s.ticker,
            s.company_name AS stock_company,
            s.sector AS stock_sector,
            s.theme_tag
        FROM src_call_logs c
        LEFT JOIN src_stocks s ON s.stock_id = c.stock_id
        WHERE c.client_id = :client_id
        ORDER BY c.call_timestamp DESC
        LIMIT :limit
        """

        return db.query_all(sql, {"client_id": client_id, "limit": limit})

    def summarize_calls(
        self,
        client_id: int,
        limit: int = 10,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Summarize recent calls for a client.

        Args:
            client_id: Client ID
            limit: Number of recent calls to summarize
            use_llm: Whether to use LLM for summarization (if available)

        Returns:
            Dictionary with:
            - summary: Condensed text summary
            - key_topics: List of main topics discussed
            - stocks_mentioned: List of tickers mentioned
            - objections_signals: Potential objections detected
            - sentiment: Overall sentiment (positive/neutral/negative)
            - call_count: Number of calls summarized
        """
        calls = self.get_recent_calls(client_id, limit)

        if not calls:
            return {
                "summary": "No recent call history available.",
                "key_topics": [],
                "stocks_mentioned": [],
                "objections_signals": [],
                "sentiment": "neutral",
                "call_count": 0,
            }

        # If LLM is available and enabled, use intelligent summarization
        if use_llm and self.llm_client:
            return self._llm_summarize(client_id, calls)

        # Otherwise, use rule-based extraction
        return self._rule_based_summarize(calls)

    def _rule_based_summarize(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule-based summarization without LLM.
        Extracts key signals using pattern matching.
        """
        # Aggregate data
        all_notes = []
        stocks_mentioned = set()
        sectors = set()
        topics_detected = []

        # Topic detection patterns
        topic_patterns = {
            "Valuation": ["valuation", "multiple", "pe ", "p/e", "price-to"],
            "Earnings": ["earnings", "eps", "profit", "margin", "revenue", "beat", "miss"],
            "Dividend": ["dividend", "yield", "payout", "income"],
            "Growth": ["growth", "expansion", "scale", "market share"],
            "Risk": ["risk", "volatility", "downside", "hedge", "concern"],
            "ESG": ["esg", "climate", "sustainability", "governance"],
            "Macro": ["macro", "rates", "inflation", "gdp", "economy", "fed", "ecb"],
        }

        # Objection patterns
        objection_patterns = [
            ("too expensive", "Valuation concern"),
            ("overvalued", "Valuation concern"),
            ("not interested", "General resistance"),
            ("already own", "Position overlap"),
            ("too risky", "Risk aversion"),
            ("concerned about", "Specific concern"),
            ("prefer to wait", "Timing hesitation"),
            ("need more info", "Information gap"),
            ("regulatory", "Regulatory concern"),
            ("competition", "Competitive concern"),
        ]

        objections_detected = []

        for call in calls:
            notes = (call.get("notes_raw") or "").lower()
            all_notes.append(notes)

            # Extract stocks
            if call.get("ticker"):
                stocks_mentioned.add(call["ticker"])
            if call.get("discussed_sector"):
                sectors.add(call["discussed_sector"])

            # Detect topics
            for topic, patterns in topic_patterns.items():
                if any(p in notes for p in patterns):
                    topics_detected.append(topic)

            # Detect objections
            for pattern, objection_type in objection_patterns:
                if pattern in notes:
                    objections_detected.append(objection_type)

        # Count topic frequency
        topic_counts = {}
        for topic in topics_detected:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        top_topics = sorted(topic_counts.items(), key=lambda x: -x[1])[:5]

        # Determine sentiment
        positive_words = ["positive", "bullish", "interested", "like", "good", "strong", "opportunity"]
        negative_words = ["negative", "bearish", "concerned", "worried", "weak", "risk", "problem"]

        combined_notes = " ".join(all_notes)
        pos_count = sum(1 for w in positive_words if w in combined_notes)
        neg_count = sum(1 for w in negative_words if w in combined_notes)

        if pos_count > neg_count + 2:
            sentiment = "positive"
        elif neg_count > pos_count + 2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Generate summary text
        summary_parts = []
        summary_parts.append(f"Analyzed {len(calls)} recent calls.")

        if top_topics:
            topics_str = ", ".join([t[0] for t in top_topics[:3]])
            summary_parts.append(f"Key topics: {topics_str}.")

        if stocks_mentioned:
            stocks_str = ", ".join(list(stocks_mentioned)[:5])
            summary_parts.append(f"Stocks discussed: {stocks_str}.")

        if objections_detected:
            unique_objections = list(set(objections_detected))[:3]
            summary_parts.append(f"Potential concerns: {', '.join(unique_objections)}.")

        return {
            "summary": " ".join(summary_parts),
            "key_topics": [t[0] for t in top_topics],
            "stocks_mentioned": list(stocks_mentioned),
            "objections_signals": list(set(objections_detected)),
            "sentiment": sentiment,
            "call_count": len(calls),
            "sectors_discussed": list(sectors),
        }

    def _llm_summarize(self, client_id: int, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        LLM-based intelligent summarization.
        Uses Mistral Small (FAST tier) for efficiency.
        """
        import time

        # Prepare call context
        call_texts = []
        for i, call in enumerate(calls, 1):
            date = call.get("call_timestamp", "")[:10] if call.get("call_timestamp") else "unknown"
            ticker = call.get("ticker") or call.get("discussed_company") or "N/A"
            notes = call.get("notes_raw") or "(no notes)"

            call_texts.append(f"[Call {i}] {date} - {ticker}:\n{notes[:500]}")

        calls_context = "\n\n".join(call_texts)

        prompt = f"""Analyze these {len(calls)} recent client call notes and provide a structured summary.

CALL LOGS:
{calls_context}

OUTPUT (JSON only, no markdown):
{{
    "summary": "<2-3 sentence overview of client's interests and engagement>",
    "key_topics": ["<topic1>", "<topic2>", ...],
    "stocks_mentioned": ["<TICKER1>", "<TICKER2>", ...],
    "objections_signals": ["<objection1>", "<objection2>", ...],
    "sentiment": "<positive|neutral|negative>",
    "key_quotes": ["<relevant quote 1>", "<relevant quote 2>"]
}}

Rules:
- Extract ONLY information present in the call notes
- objections_signals: concerns, hesitations, or pushback expressed by client
- key_quotes: 1-2 most insightful client statements (verbatim if possible)
- Be concise and factual
"""

        start_time = time.time()

        try:
            # Call LLM (placeholder - will be replaced with actual Mistral call)
            if hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.choices[0].message.content
            else:
                # Fallback to rule-based if LLM not properly configured
                return self._rule_based_summarize(calls)

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse JSON response
            try:
                # Try to extract JSON from response
                result_text = result_text.strip()
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]

                result = json.loads(result_text)

                # Log to compliance history
                log_ai_generation(
                    client_id=client_id,
                    generation_type="summary",
                    model_tier="FAST",
                    model_used=self.model,
                    prompt_text=prompt,
                    response_text=result_text,
                    latency_ms=latency_ms,
                    success=True,
                )

                result["call_count"] = len(calls)
                return result

            except json.JSONDecodeError:
                # Log failure and fall back to rule-based
                log_ai_generation(
                    client_id=client_id,
                    generation_type="summary",
                    model_tier="FAST",
                    model_used=self.model,
                    prompt_text=prompt,
                    response_text=result_text,
                    latency_ms=latency_ms,
                    success=False,
                    error_message="JSON parse error",
                )
                return self._rule_based_summarize(calls)

        except Exception as e:
            # Log error and fall back to rule-based
            log_ai_generation(
                client_id=client_id,
                generation_type="summary",
                model_tier="FAST",
                model_used=self.model,
                prompt_text=prompt,
                response_text=None,
                latency_ms=int((time.time() - start_time) * 1000),
                success=False,
                error_message=str(e),
            )
            return self._rule_based_summarize(calls)


# ============================================================================
# Objection Handler for Story Generation
# ============================================================================

class ObjectionHandler:
    """
    Generates potential objections and best answers based on client context.
    Used to enhance story prompts with pre-emptive objection handling.
    """

    # Common objection categories and suggested handling strategies
    OBJECTION_TEMPLATES = {
        "Valuation concern": {
            "signal_words": ["expensive", "overvalued", "high multiple", "pe ratio"],
            "response_strategy": "Focus on growth trajectory, relative value vs peers, or catalysts that justify premium.",
        },
        "Already own position": {
            "signal_words": ["already own", "have position", "existing holding"],
            "response_strategy": "Discuss portfolio weighting, recent developments that warrant adding, or timing for increase.",
        },
        "Risk aversion": {
            "signal_words": ["too risky", "volatile", "concerned about downside"],
            "response_strategy": "Highlight risk mitigation factors, dividend yield, balance sheet strength, or defensive characteristics.",
        },
        "Timing hesitation": {
            "signal_words": ["wait", "later", "not now", "timing"],
            "response_strategy": "Discuss specific catalysts, entry points, or opportunity cost of waiting.",
        },
        "Sector exposure": {
            "signal_words": ["already exposed", "overweight sector", "concentration"],
            "response_strategy": "Position as differentiated exposure, discuss correlation, or suggest as replacement.",
        },
        "Information gap": {
            "signal_words": ["need more", "don't understand", "unclear"],
            "response_strategy": "Offer to schedule deep-dive call, share research reports, or provide specific data points.",
        },
        "Macro concerns": {
            "signal_words": ["macro", "rates", "recession", "inflation"],
            "response_strategy": "Discuss company's macro resilience, hedging characteristics, or counter-cyclical attributes.",
        },
        "ESG concerns": {
            "signal_words": ["esg", "sustainability", "governance", "carbon"],
            "response_strategy": "Highlight ESG improvements, ratings trajectory, or transition story.",
        },
    }

    def detect_likely_objections(
        self,
        call_summary: Dict[str, Any],
        client_profile: Dict[str, Any],
        selected_stock: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Detect likely objections based on client history and selected stock.

        Returns list of:
        {
            "objection": "Objection text",
            "likelihood": "high|medium|low",
            "suggested_response": "How to handle"
        }
        """
        objections = []

        # From call summary signals
        for signal in call_summary.get("objections_signals", []):
            for category, template in self.OBJECTION_TEMPLATES.items():
                if category.lower() in signal.lower():
                    objections.append({
                        "objection": category,
                        "likelihood": "high",
                        "suggested_response": template["response_strategy"],
                    })
                    break

        # From client profile - risk aversion check
        risk_appetite = client_profile.get("risk_appetite", "Moderate")
        if risk_appetite == "Conservative":
            # Check if stock is high volatility
            stock_vol = selected_stock.get("vol_bucket", "unknown")
            if stock_vol in ["high", "medium"]:
                objections.append({
                    "objection": "Risk aversion - volatility mismatch",
                    "likelihood": "high" if stock_vol == "high" else "medium",
                    "suggested_response": self.OBJECTION_TEMPLATES["Risk aversion"]["response_strategy"],
                })

        # Check for sector overlap
        top_sector = call_summary.get("sectors_discussed", [])
        stock_sector = selected_stock.get("sector", "")
        if stock_sector in top_sector:
            objections.append({
                "objection": "Sector already discussed frequently - potential saturation",
                "likelihood": "medium",
                "suggested_response": "Position as best-in-class within familiar sector, or highlight differentiation.",
            })

        # Check for already mentioned stocks
        stocks_mentioned = call_summary.get("stocks_mentioned", [])
        stock_ticker = selected_stock.get("ticker", "")
        if stock_ticker in stocks_mentioned:
            objections.append({
                "objection": "Stock already discussed - client may have formed opinion",
                "likelihood": "medium",
                "suggested_response": "Reference previous discussion, address any concerns raised, highlight new developments.",
            })

        return objections

    def generate_objection_section(
        self,
        objections: List[Dict[str, str]],
    ) -> str:
        """Generate formatted objection handling section for story prompt."""
        if not objections:
            return ""

        lines = ["POTENTIAL OBJECTIONS & BEST ANSWERS:"]

        for obj in objections[:4]:  # Limit to top 4
            lines.append(f"\n• Objection ({obj['likelihood']} likelihood): {obj['objection']}")
            lines.append(f"  → Best response: {obj['suggested_response']}")

        return "\n".join(lines)


# Singleton instances
call_summarizer = CallLogSummarizer()
objection_handler = ObjectionHandler()
