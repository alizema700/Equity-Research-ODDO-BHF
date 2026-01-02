"""
Sales Intelligence Platform - Library Package

Contains:
- database: Database abstraction layer (SQLite/PostgreSQL)
- summarization: Call log summarization and objection handling
"""

from lib.database import db, semantic_search, log_ai_generation, SemanticSearch
from lib.summarization import call_summarizer, objection_handler, CallLogSummarizer, ObjectionHandler

__all__ = [
    "db",
    "semantic_search",
    "log_ai_generation",
    "SemanticSearch",
    "call_summarizer",
    "objection_handler",
    "CallLogSummarizer",
    "ObjectionHandler",
]
