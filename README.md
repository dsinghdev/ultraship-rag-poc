# 🚢 Ultra Doc-Intelligence

AI-powered logistics document analysis and Q&A system built with RAG (Retrieval-Augmented Generation) technology.

## 📋 Overview

Ultra Doc-Intelligence is a POC AI system that allows users to upload logistics documents (PDF, DOCX, TXT) and interact with them using natural language questions. The system retrieves relevant content, answers grounded questions, applies guardrails, and returns confidence scores — simulating an AI assistant inside a Transportation Management System (TMS).

## ✨ Features

- **Document Upload & Processing**: Support for PDF, DOCX, and TXT files
- **Intelligent Chunking**: Recursive character text splitting for optimal context preservation
- **Vector Indexing**: FAISS-based semantic search with OpenAI embeddings
- **RAG-based Q&A**: Context-grounded answers with source citations
- **Guardrails**: Hallucination prevention with confidence-based refusal
- **Confidence Scoring**: Multi-factor confidence calculation (similarity, chunk agreement, coverage)
- **Structured Extraction**: Automatic extraction of shipment data fields to JSON
- **Streamlit UI**: User-friendly interface for document interaction
- **REST API**: FastAPI backend with `/upload`, `/ask`, and `/extract` endpoints
- **Docker Support**: Containerized deployment with docker-compose

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI (8510)                      │
│  - Document Upload                                           │
│  - Question Interface                                        │
│  - Results Display (answers, sources, confidence)            │
│  - Structured Data Extraction View                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (8000)                     │
│                                                              │
│  POST /upload    → Parse, chunk, embed, index document      │
│  POST /ask       → Retrieve context → Generate answer       │
│  POST /extract   → Extract structured shipment data         │
│  GET  /health    → Health check                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────┐           ┌─────────────────┐
│  Document     │           │  Vector Store   │
│  Processor    │           │  (FAISS)        │
│               │           │                 │
│  - PDF        │           │  - Embeddings   │
│  - DOCX       │           │  - Index        │
│  - TXT        │           │  - Search       │
└───────────────┘           └─────────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐           ┌─────────────────┐
│  Q&A System   │           │  Structured     │
│  (RAG)        │           │  Extractor      │
│               │           │                 │
│  - Retrieval  │           │  - LLM-based    │
│  - Guardrails │           │  - JSON output  │
│  - Confidence │           │  - Null filling │
└───────────────┘           └─────────────────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
              ┌────────────────┐
              │   OpenAI API   │
              │                │
              │  - Embeddings  │
              │  - GPT-4o-mini │
              └────────────────┘
```

## 🔧 Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Streamlit
- **Vector Database**: FAISS (CPU)
- **Embeddings**: Google Gemini embedding-001
- **LLM**: Google Gemini 2.5 Flash
- **Document Processing**: PyPDF2, python-docx
- **Containerization**: Docker & docker-compose

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker & docker-compose (for containerized deployment)
- Google Gemini API key (free from Google AI Studio)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ultraship_ai
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   chmod +x run_local.sh
   ./run_local.sh
   ```

   Or manually:
   ```bash
   # Terminal 1: Start API
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2: Start Streamlit
   streamlit run app/streamlit_app.py --server.port=8510
   ```

5. **Access the application**
   - Streamlit UI: http://localhost:8510
   - FastAPI Docs: http://localhost:8000/docs
   - API Health: http://localhost:8000/health

### Docker Deployment

1. **Set environment variable**
   ```bash
   export GOOGLE_API_KEY=your_gemini_api_key_here
   ```

2. **Build and run**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Streamlit UI: http://localhost:8510
   - FastAPI API: http://localhost:8000
   - FastAPI Docs: http://localhost:8000/docs

### ☁️ Cloud Deployment (Production)

Because this system uses a separate FastAPI backend and Streamlit frontend, the best way to deploy it is using a service that supports Docker Compose (like Render or AWS).

**Deploying to Render (Recommended Free Tier)**:
1. Create a free account on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Create a **New Web Service** and select "Docker" as the environment.
4. Render will automatically read the `Dockerfile` and build both the API and Streamlit UI in the same container if you slightly modify the Dockerfile to start both processes (or link two services).
5. Add your `GOOGLE_API_KEY` to the Render Environment Variables.

**Deploying ONLY Streamlit (Streamlit Community Cloud)**:
1. If you push this to Streamlit Community Cloud, it will *only* run the UI.
2. The UI will fail to connect to the backend unless you host the FastAPI backend separately (e.g., on Render) and update the `API_BASE_URL` in your Streamlit secrets.

## 🧠 AI/ML Strategy

### Chunking Strategy

**Method**: Recursive Character Text Splitter

- **Chunk Size**: 500 characters
- **Chunk Overlap**: 50 characters (10%)
- **Separators** (in order of priority): `["\n\n", "\n", ". ", " ", ""]`

**Rationale**:
- Preserves semantic meaning by splitting at natural boundaries
- Overlap ensures context isn't lost at chunk boundaries
- Smaller chunks improve retrieval precision for specific details
- Ideal for logistics documents with structured data fields

### Retrieval Method

**Vector Search**: FAISS IndexFlatIP (Inner Product) with Gemini embeddings

1. **Embedding Model**: `models/embedding-001` (768 dimensions)
2. **Normalization**: L2 normalization for cosine similarity
3. **Top-K**: 3 most relevant chunks retrieved
4. **Similarity Metric**: Cosine similarity (normalized inner product)

**Process**:
- Query is embedded with the same model
- FAISS searches for most similar chunk vectors
- Top-K chunks returned with similarity scores
- Chunks form context for LLM generation

### Guardrails Approach

**Multi-Layer Hallucination Prevention**:

1. **Confidence Threshold** (0.6):
   - If overall confidence < 60%, refuse to answer
   - Prevents low-certainty responses

2. **Similarity Threshold** (0.65):
   - If max chunk similarity < 65%, refuse to answer
   - Ensures retrieved context is relevant

3. **Context-Only Generation**:
   - Prompt explicitly instructs: "Answer ONLY using information from the context"
   - LLM instructed to say "I cannot find this information" when context is insufficient

4. **Explicit Refusal Messages**:
   - "I cannot confidently answer this question based on the document."
   - "The retrieved context is not sufficiently relevant to answer this question."
   - "No relevant context found in the document."

### Confidence Scoring Method

**Weighted Multi-Factor Scoring**:

```
confidence = (similarity × 0.5) + (chunk_agreement × 0.3) + (coverage × 0.2)
```

**Components**:

1. **Retrieval Similarity (50%)**:
   - Average cosine similarity of top-K chunks
   - Primary indicator of context relevance

2. **Chunk Agreement (30%)**:
   - Consistency across retrieved chunks
   - Calculated as: `1.0 - (max_similarity - avg_similarity)`
   - High agreement = chunks tell consistent story

3. **Answer Coverage (20%)**:
   - Penalizes too short (<5 words) or too long (>200 words) answers
   - Optimal range: 5-200 words → 0.8 score
   - Ensures substantive but concise answers

**Score Range**: 0.0 - 1.0 (normalized)

### LLM Reasoning & Grounding
The system uses **Gemini 2.5 Flash** for its superior reasoning capabilities in logistics contexts. The model is specifically instructed via system prompts to:
1.  **Acknowledge missing data**: Say "Information not found" instead of guessing.
2.  **Cross-reference chunks**: Compare retrieved snippets to ensure they aren't contradictory.
3.  **Strict Grounding**: Only use the provided context; any external knowledge is discarded.

## 🔌 API Endpoints

### POST /upload
Upload and process a logistics document.

**Request**:
- Content-Type: `multipart/form-data`
- Body: `file` (PDF, DOCX, or TXT)

**Response**:
```json
{
  "status": "success",
  "message": "Document uploaded and processed successfully",
  "filename": "rate_confirmation.pdf",
  "chunks_created": 15,
  "document_size_chars": 7500
}
```

### POST /ask
Ask a question about the uploaded document.

**Request**:
```json
{
  "question": "What is the carrier rate?"
}
```

**Response**:
```json
{
  "status": "success",
  "question": "What is the carrier rate?",
  "answer": "The carrier rate is $2,500.00 USD.",
  "confidence": 0.87,
  "sources": [
    {
      "text": "Rate: $2,500.00 USD for this shipment...",
      "similarity": 0.92
    }
  ],
  "guardrail_triggered": false,
  "guardrail_reason": null
}
```

### POST /extract
Extract structured shipment data from the uploaded document.

**Response**:
```json
{
  "status": "success",
  "filename": "bol_12345.pdf",
  "extracted_data": {
    "shipment_id": "SHP-12345",
    "shipper": "ABC Manufacturing Inc.",
    "consignee": "XYZ Distribution Center",
    "pickup_datetime": "2026-04-10 08:00",
    "delivery_datetime": "2026-04-12 17:00",
    "equipment_type": "Dry Van",
    "mode": "FTL",
    "rate": 2500.00,
    "currency": "USD",
    "weight": 35000,
    "carrier_name": "Fast Freight LLC"
  }
}
```

### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "document_loaded": true
}
```

## 🧪 Testing

### Sample Documents
Test with logistics documents such as:
- Rate Confirmations
- Bills of Lading (BOL)
- Shipment Instructions
- Invoices
- Proof of Delivery

### Example Questions
- "What is the carrier rate?"
- "When is pickup scheduled?"
- "Who is the consignee?"
- "What is the equipment type?"
- "What is the total weight?"
- "Who is the carrier?"

## ⚠️ Failure Cases & Limitations

### Known Failure Cases

1. **Scanned PDFs / Images**:
   - OCR not implemented
   - Will return empty or minimal text
   - **Mitigation**: Use text-based PDFs only

2. **Complex Table Layouts**:
   - Table structure may be lost during extraction
   - Relationships between cells might be unclear
   - **Mitigation**: Simple text-based parsing works best

3. **Multi-Page Documents**:
   - Chunking may split related information
   - Cross-page context might be lost
   - **Mitigation**: Chunk overlap helps but not perfect

4. **Very Low Confidence Answers**:
   - Guardrails will refuse to answer
   - May frustrate users seeking any response
   - **Mitigation**: Clear messaging about why answer was refused

5. **Missing Fields in Extraction**:
   - LLM may not find all fields in poorly structured documents
   - Returns `null` for missing fields (by design)
   - **Mitigation**: Clear indication of missing data

6. **API Rate Limits**:
   - OpenAI API has rate limits
   - High volume may cause throttling
   - **Mitigation**: Implement retry logic (not yet added)

### Current Limitations

- Single document support (no multi-document comparison)
- No document persistence (re-upload after restart)
- No user authentication
- English language only
- Requires Google Gemini API key (free tier available)

## 🚀 Improvement Ideas

### Short-Term Improvements

1. **OCR Support**:
   - Add Tesseract or cloud OCR for scanned documents
   - Enable image-based PDF processing

2. **Document Persistence**:
   - Save vector indexes to disk
   - Maintain document history
   - Support document switching

3. **Better Table Handling**:
   - Table-aware chunking
   - Structural relationship preservation
   - Markdown table conversion

4. **Caching**:
   - Cache frequent questions/answers
   - Reduce API calls
   - Improve response time

5. **Retry Logic**:
   - Exponential backoff for API failures
   - Graceful degradation

### Medium-Term Improvements

6. **Multi-Document Support**:
   - Upload multiple documents
   - Cross-document queries
   - Document comparison

6. **Local LLM Support**:
   - Ollama integration
   - HuggingFace models
   - Remove cloud API dependency

8. **Advanced Chunking**:
   - Semantic chunking (sentence transformers)
   - Hierarchical chunking
   - Adaptive chunk size based on document type

9. **Better Confidence Metrics**:
   - Answer consistency across multiple LLM calls
   - Entailment checking (NLI models)
   - Source factuality verification

10. **User Feedback Loop**:
    - Rate answer quality
    - Flag incorrect answers
    - Improve system over time

### Long-Term Vision

11. **TMS Integration**:
    - Connect to actual TMS systems
    - Real-time shipment tracking
    - Automated data entry

12. **Multi-Modal Support**:
    - Handle images, diagrams
    - Extract visual information
    - Signature detection

13. **Workflow Automation**:
    - Trigger actions from extracted data
    - Integration with logistics APIs
    - Automated exception handling

## 📁 Project Structure

```
ultraship_ai/
├── app/
│   ├── __init__.py
│   ├── config.py                  # Configuration settings
│   ├── document_processor.py      # PDF/DOCX/TXT parsing & chunking
│   ├── vector_store.py            # FAISS vector database
│   ├── qa_system.py               # RAG Q&A with guardrails
│   ├── structured_extractor.py    # Shipment data extraction
│   ├── main.py                    # FastAPI application
│   └── streamlit_app.py           # Streamlit UI
├── uploads/                       # Uploaded documents (auto-created)
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Multi-container orchestration
├── .dockerignore                  # Docker exclusions
├── .env.example                   # Environment template
├── run_local.sh                   # Local development script
└── README.md                      # This file
```

## 🔐 Security Considerations

- **API Key Management**: Use environment variables, never commit `.env`
- **File Upload Validation**: Extension whitelisting, size limits (can be added)
- **Temporary Storage**: Uploads stored locally (consider cleanup for production)
- **CORS**: Configured for development (restrict for production)

## 📄 License

This is a proof-of-concept project for evaluation purposes.

## 👤 Author

Built for Ultra Ship AI Engineer Skill Test

---

**Note**: Clarity and correctness were prioritized over framework complexity, as per evaluation guidelines.
