import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Document processing
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Embeddings (Gemini)
EMBEDDING_MODEL = "models/gemini-embedding-001"

# LLM (Gemini)
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 500

# Retrieval
TOP_K_CHUNKS = 3
SIMILARITY_THRESHOLD = 0.65

# Guardrails
CONFIDENCE_THRESHOLD = 0.6
MIN_CHUNK_AGREEMENT = 0.5

# Google Gemini API Key (set via environment variable)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
