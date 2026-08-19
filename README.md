# AI-Based Knowledge Retrieval Platform with Query Resolution System

An AI-powered Retrieval-Augmented Generation (RAG) platform that enables users to upload knowledge-base documents and query them using natural language.

> **Detailed Documentation:** See **`PROJECT_GUIDE.md`** for the complete architecture, workflow diagrams, backend/frontend design, API documentation, and implementation details.

## Features

- 📄 Upload PDF, DOCX, TXT, and CSV documents
- 🔍 Semantic document retrieval using ChromaDB and Sentence Transformers
- 🧠 Query Understanding Agent for normalization, entity/keyword extraction and query classification
- 🔎 Hybrid retrieval with semantic search and optional exact-term matching
- 📊 Query-aware relevance ranking and low-confidence filtering
- 🤖 Response Generation Agent for grounded answers
- 📚 Source attribution and retrieval-aware confidence scoring
- 🔗 LangGraph orchestration of Query Understanding → Retrieval → Response Generation
- 💬 React-based conversational interface
- 🗂️ Document management (view and delete indexed documents)
- 📈 Background document processing with upload status tracking

## Technology Stack

### Frontend

- React 19
- Vite
- JavaScript
- Vanilla CSS

### Backend

- Python 3
- FastAPI
- Uvicorn
- Pydantic

### AI & Agent Layer

- LangChain
- LangGraph
- langchain-groq
- Groq LLM
- Sentence Transformers (`all-MiniLM-L6-v2`)
- ChromaDB
- Retrieval-Augmented Generation (RAG)

### Document Processing

- pypdf
- python-docx
- pandas
- LangChain text splitters

### API & File Handling

- python-multipart

## Project Structure

The project contains a single authoritative backend at the repository root. Do not place or maintain a second backend copy inside `frontend/`.

```text
AI-Based Knowledge Retrieval Platform with Query Resolution System/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   └── llm.py
│   │   ├── models/
│   │   ├── rag/
│   │   ├── services/
│   │   ├── agents/
│   │   │   ├── query_understanding/
│   │   │   ├── retrieval/
│   │   │   └── response_generation/
│   │   ├── orchestration/
│   │   │   ├── query_router.py
│   │   │   └── workflow.py
│   │   └── main.py
│   ├── chroma_db/
│   ├── metadata/
│   ├── uploads/
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── PROJECT_GUIDE.md
└── README.md
```

## Milestone 2 Architecture

```text
User Query
    ↓
Query Understanding Agent
    ↓
Query Router
    ↓
Retrieval Agent
    ├── Semantic Search
    ├── Optional Exact Search
    ├── Query-aware Reranking
    └── Low-confidence Filtering
    ↓
Response Generation Agent
    ├── Grounded Answer
    ├── Source Citations
    └── Confidence
    ↓
FastAPI JSON Response
    ↓
React Frontend
    └── Context Inspector
```

The integrated frontend uses `response.answer`, `response.sources`, `response.confidence`, and `retrieval.results` from the `/query` response. `chunk_id` is the canonical identifier used to map response citations to the exact retrieved chunk displayed in the Context Inspector.

The LangGraph orchestration layer currently lives in:

```text
backend/app/orchestration/
├── query_router.py
└── workflow.py
```

## Installation & Setup

### Backend

```bash
# Create virtual environment
python -m venv .venv
```

Windows:

```cmd
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=<your-key>
GROQ_MODEL=<configured-model>
```

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

### Frontend

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Do not place `GROQ_API_KEY` or other backend secrets in the frontend environment.

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Usage

1. Start the FastAPI backend.
2. Start the React frontend.
3. Upload one or more supported documents.
4. Wait for document processing to complete.
5. Ask questions through the chat interface.
6. The backend runs the Milestone 2 agent workflow.
7. View the generated answer, source information and confidence in the response.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/documents` | List indexed documents |
| POST | `/upload` | Upload a document |
| GET | `/upload/status/{job_id}` | Check upload status |
| POST | `/query` | Run the Milestone 2 query workflow |
| DELETE | `/documents/{document_id}` | Delete an indexed document |

### `/query` request

```json
{
  "query": "What does the Retrieval Agent do?",
  "k": 3
}
```

### `/query` response

The response contains:

```text
success
query
query_understanding
route
route_reason
retrieval
response
```

The `response` section contains the grounded answer, cited sources and confidence indicator.

Each retrieval result uses a canonical `chunk_id`. Response citations preserve the same `chunk_id`, allowing the frontend to open the exact retrieved chunk in the Context Inspector.

## Supported File Types

- PDF
- DOCX
- TXT
- CSV

## Milestone 2 Validation

The current Milestone 2 implementation has been validated with:

- identifier/entity queries such as `What is the email of Name_1?`
- unsupported queries where the knowledge base does not contain the requested information
- generic PDF queries such as `What does the Retrieval Agent do?`
- semantic-only queries with `exact_terms = []`
- end-to-end LangGraph execution from Query Understanding through Response Generation
- grounded responses with source citations and confidence
- FastAPI `/query` integration with the React frontend
- `chunk_id` consistency between retrieval results and response sources
- Context Inspector source-to-chunk mapping

## Security

Do not commit `backend/.env` or real API keys to Git. Keep secrets in local environment variables or an appropriate secret manager.

## Documentation

For complete technical documentation, architecture diagrams, implementation details, API flow, RAG pipeline, Milestone 2 workflow, and development guidelines, refer to:

- **PROJECT_GUIDE.md**
