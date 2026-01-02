# Library Package - Sales Intelligence Platform

This package contains the core business logic for the Sales Intelligence Platform.

## Modules

### `database.py`
Database abstraction layer supporting both SQLite (development) and PostgreSQL (production).

**Key Components:**
- `DatabaseClient`: Abstract database client with connection pooling
- `db`: Singleton database instance
- `SemanticSearch`: pgvector-based semantic search for call notes and reports
- `log_ai_generation()`: Compliance logging for all LLM requests/responses

**Usage:**
```python
from lib.database import db, semantic_search, log_ai_generation

# Query database (works with both SQLite and PostgreSQL)
clients = db.query_all("SELECT * FROM src_clients WHERE region = :region", {"region": "DACH"})

# Semantic search (requires pgvector in PostgreSQL)
results = semantic_search.search_call_notes("valuation concerns", client_id=123)

# Log AI generation for compliance
log_ai_generation(
    client_id=123,
    generation_type="story",
    model_tier="DETAILED",
    model_used="mistral-large-latest",
    prompt_text="...",
    response_text="...",
)
```

### `summarization.py`
Call log pre-summarization and objection handling.

**Key Components:**
- `CallLogSummarizer`: Aggregates and summarizes recent call logs
- `ObjectionHandler`: Detects likely objections and suggests responses
- `call_summarizer`: Singleton summarizer instance
- `objection_handler`: Singleton objection handler instance

**Usage:**
```python
from lib.summarization import call_summarizer, objection_handler

# Summarize recent calls
summary = call_summarizer.summarize_calls(client_id=123, limit=10)
# Returns: { summary, key_topics, stocks_mentioned, objections_signals, sentiment }

# Detect likely objections
objections = objection_handler.detect_likely_objections(
    call_summary=summary,
    client_profile=profile,
    selected_stock=stock,
)

# Generate formatted objection section for prompt
objection_text = objection_handler.generate_objection_section(objections)
```

## Configuration

Set these environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_TYPE` | Database type: `sqlite` or `postgres` | `sqlite` |
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `SQLITE_PATH` | Path to SQLite database | `./data.db` |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        server.py                             │
│                    (FastAPI endpoints)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         lib/                                 │
├─────────────────────────┬───────────────────────────────────┤
│     database.py         │      summarization.py             │
│  ┌─────────────────┐    │   ┌─────────────────┐             │
│  │ DatabaseClient  │    │   │ CallLogSummarizer│            │
│  │ SemanticSearch  │    │   │ ObjectionHandler │            │
│  │ log_ai_generation│   │   └─────────────────┘             │
│  └─────────────────┘    │                                   │
└─────────────────────────┴───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite (dev) / PostgreSQL (prod)               │
│                    with pgvector extension                   │
└─────────────────────────────────────────────────────────────┘
```

## Future Integration Points

### Mistral AI
When API key is available, update `summarization.py`:
```python
from mistralai.client import MistralClient

client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
summarizer = CallLogSummarizer(llm_client=client, model="mistral-small-latest")
```

### Embeddings
When Mistral embeddings are available, update `database.py`:
```python
def _get_embedding(self, text: str) -> List[float]:
    response = self.mistral_client.embeddings(
        model="mistral-embed",
        input=[text]
    )
    return response.data[0].embedding
```
