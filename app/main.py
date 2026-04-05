import os
import uuid
import shutil
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import UPLOAD_DIR
from app.document_processor import process_document
from app.vector_store import vector_store
from app.qa_system import qa_system
from app.structured_extractor import structured_extractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Logistics AI Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track current document state
current_document = {
    "file_path": None,
    "full_text": None,
    "filename": None
}


class QuestionRequest(BaseModel):
    question: str


class ExtractRequest(BaseModel):
    pass


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a logistics document (PDF, DOCX, TXT).
    Creates vector index for RAG-based Q&A.
    """
    logger.info(f"📁 Received upload request for: {file.filename}")
    
    # Validate file extension
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        logger.warning(f"❌ Unsupported file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: PDF, DOCX, TXT"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Save uploaded file
        logger.info(f"💾 Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        logger.info(f"⚙️  Processing document: {file.filename}")
        full_text, chunks = process_document(str(file_path))
        
        # Build vector index
        logger.info(f"🧠 Building vector index for {len(chunks)} chunks")
        vector_store.initialize(chunks)
        
        # Update current document
        current_document["file_path"] = str(file_path)
        current_document["full_text"] = full_text
        current_document["filename"] = file.filename
        
        logger.info(f"✅ Successfully processed: {file.filename} ({len(full_text)} chars)")
        
        return {
            "status": "success",
            "message": f"Document '{file.filename}' uploaded and processed successfully",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "document_size_chars": len(full_text)
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing upload: {str(e)}", exc_info=True)
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the uploaded document.
    Returns answer with sources and confidence score.
    """
    if not current_document["full_text"]:
        logger.warning("❓ Question received but no document uploaded")
        raise HTTPException(
            status_code=400,
            detail="No document uploaded. Please upload a document first."
        )
    
    logger.info(f"❓ Question: {request.question}")
    
    try:
        result = qa_system.ask(request.question)
        logger.info(f"💡 Answer generated (Confidence: {result['confidence']:.2f})")
        return {
            "status": "success",
            "question": request.question,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "sources": result["sources"],
            "guardrail_triggered": result["guardrail_triggered"],
            "guardrail_reason": result["guardrail_reason"]
        }
    except Exception as e:
        logger.error(f"❌ Error in /ask: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract")
async def extract_structured_data():
    """
    Extract structured shipment data from uploaded document.
    Returns JSON with shipment fields (null if missing).
    """
    if not current_document["full_text"]:
        logger.warning("🔍 Extraction requested but no document uploaded")
        raise HTTPException(
            status_code=400,
            detail="No document uploaded. Please upload a document first."
        )
    
    logger.info(f"🔍 Extracting structured data from: {current_document['filename']}")
    
    try:
        extracted_data = structured_extractor.extract(current_document["full_text"])
        
        if "error" in extracted_data:
            logger.warning(f"⚠️ Extraction error: {extracted_data['error']}")
            logger.warning(f"📄 Raw Output that failed: {extracted_data.get('raw_output')}")
            return {
                "status": "error",
                "message": extracted_data["error"],
                "raw_output": extracted_data.get("raw_output")
            }
        
        logger.info("✅ Data extraction successful")
        return {
            "status": "success",
            "filename": current_document["filename"],
            "extracted_data": extracted_data
        }
    except Exception as e:
        logger.error(f"❌ Error in /extract: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/document/text")
async def get_document_text():
    """Retrieve full text of the currently loaded document."""
    if not current_document["full_text"]:
        raise HTTPException(
            status_code=400,
            detail="No document uploaded"
        )
    
    return {
        "status": "success",
        "filename": current_document["filename"],
        "full_text": current_document["full_text"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "document_loaded": current_document["full_text"] is not None,
        "filename": current_document["filename"]
    }
