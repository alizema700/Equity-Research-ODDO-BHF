# Client Storytelling Prototype (SQLite + Snapshot + Local LLM)

This is a runnable prototype:
- Search a client
- Load a precomputed INT story context snapshot from SQLite
- Generate a tailored narrative (call-prep story) via a local LLM

## 1) Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Start a local LLM (free)
### Option A (recommended): Ollama
1) Install Ollama
2) Pull a model:
```bash
ollama pull llama3.1:8b
```
3) Make sure it's running (Ollama exposes an API at http://localhost:11434)

### Option B: LM Studio
1) Download LM Studio
2) Load a model
3) Start the REST server (OpenAI compatible). Default port is often 1234.

## 3) Run the web app
```bash
uvicorn server:app --reload --port 8000
```
Open:
http://localhost:8000

## 4) Configuration (optional)
By default the app uses Ollama.

- Use LM Studio instead:
```bash
set USE_LMSTUDIO=1
set LMSTUDIO_BASE=http://localhost:1234/v1
set LMSTUDIO_MODEL=<your model name>
```

- Choose a different Ollama model:
```bash
set OLLAMA_MODEL=qwen2.5:7b
```

## 5) Notes
- The SQLite file is included as `data.db` inside the project folder.
- Stock references use `stock_id` as the key across tables; tickers/names are attributes.
