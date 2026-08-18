# Drug Information Q&A Chatbot

A RAG-based chatbot backend with a Next.js web UI that answers questions about a
drug using its official FDA prescribing information PDF. Every answer is
grounded in the retrieved source text, cites the exact page it came from, and
refuses to answer when retrieval confidence is low or the question is out of
scope for the ingested documents.

## Architecture

```
backend/   FastAPI + pdfplumber + sentence-transformers + Chroma + Ollama
frontend/  Next.js (App Router) + React + Tailwind CSS + TypeScript
```

### Indexing pipeline (offline, per uploaded document)
1. PDF corpus -> drug label PDFs (uploaded via the UI or `fetch_sample_pdfs.py`)
2. Parse -> text extracted per page with `pdfplumber`; scanned pages are skipped
3. Chunk + embed -> semantic chunks (doc name, page, section metadata) embedded
   with `sentence-transformers` (`BAAI/bge-small-en-v1.5`)
4. Vector store -> Chroma persistent collection in `backend/data/vector_store`

### Query pipeline (online, per user turn)
1. User question (+ chat history)
2. Retrieval -> dense cosine search against Chroma
3. Guardrail -> confidence gate: below `CONFIDENCE_THRESHOLD` or out of scope -> refuse
4. Public lookup (auto) -> if the guardrail refuses, the drug name in the
   question is searched on the openFDA API and the matching DailyMed label PDF
   is downloaded into `backend/data/pdfs/`, ingested, and retrieval is retried
5. LLM answer -> grounded generation via local Ollama with strict system prompt

So you can ask about any marketed drug by name, even one that was never
uploaded: the system recognizes the drug keyword, fetches its official label
from the public FDA data, and answers from it. If no drug can be found (or the
fetched label still does not support the question), it refuses rather than
guessing.

## Prerequisites

- Python 3.11
- Node.js 18+
- [Ollama](https://ollama.com) with the chat model pulled, e.g.:
  ```
  ollama pull llama3.1
  ```

## Backend setup

```bash
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # adjust values if needed
uvicorn app.main:app --reload --port 8000
```

The embedding model downloads from Hugging Face on first use. Health check:
`http://localhost:8000/health`.

### Get sample FDA label PDFs (optional)

```bash
cd backend
.venv\Scripts\python.exe -m scripts.fetch_sample_pdfs --out data/pdfs
```

Downloads DailyMed PDFs for a few brands (defaults: eliquis, atorvastatin,
amoxicillin) via the openFDA API. Eliquis carries a boxed warning, so the
guardrail logic gets exercised.

## Frontend setup

```bash
cd frontend
npm install
copy .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if needed
npm run dev
```

Open `http://localhost:3000`, start a chat session, upload a PDF, and ask
questions.

## API endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST   | `/api/v1/uploadDocument` | Upload a PDF and index it |
| POST   | `/api/v1/createSession` | Create a chat session |
| POST   | `/api/v1/queryChat` | Ask a question; returns answer + citations |
| GET    | `/api/v1/sessionHistory/{sessionId}` | Chat history for a session |
| GET    | `/health` | Health check |

## Manual MVP test

With the backend running:

```bash
cd backend
.venv\Scripts\python.exe -m scripts.test_mvp --pdf data/pdfs/eliquis.pdf
```

The script uploads the PDF, asks several questions (including an out-of-scope
one), and reports whether every answer has citations and at least one refusal
triggered.

## Key constants

Defined in `backend/app/config.py` (overridable via `.env`):

- `MAX_CHUNK_TOKENS` (512)
- `CHUNK_OVERLAP` (50)
- `TOP_K_RESULTS` (5)
- `CONFIDENCE_THRESHOLD` (0.7)
- `MAX_HISTORY_TURNS` (10)

## Conventions

- Functions use camelCase, classes/services use PascalCase, constants use
  SCREAMING_SNAKE_CASE, variables use camelCase, module filenames stay
  snake_case. No emojis in code, comments, or commits.

## Out of scope (MVP)

Multi-document corpus merging, hybrid (BM25 + dense) search, production vector
DB/auth, and frontend polish beyond the current UI.
