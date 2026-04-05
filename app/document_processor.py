import os
import logging
from typing import List, Tuple
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        logger.info(f"📄 Parsing PDF: {os.path.basename(file_path)}")
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        logger.info(f"📖 Pages found: {num_pages}")
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        logger.info(f"✅ Extracted {len(text)} characters from PDF")
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {str(e)}")
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    text = ""
    try:
        logger.info(f"📄 Parsing DOCX: {os.path.basename(file_path)}")
        doc = DocxDocument(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        logger.info(f"✅ Extracted {len(text)} characters from DOCX")
    except Exception as e:
        logger.error(f"❌ DOCX extraction failed: {str(e)}")
        raise ValueError(f"Failed to parse DOCX: {str(e)}")
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to parse TXT: {str(e)}")


def parse_document(file_path: str) -> str:
    """Parse document based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported: PDF, DOCX, TXT")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks using recursive character splitter."""
    logger.info(f"✂️  Chunking text into size {chunk_size} with overlap {chunk_overlap}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    chunks = splitter.split_text(text)
    logger.info(f"🧩 Created {len(chunks)} chunks")
    return chunks


def process_document(file_path: str) -> Tuple[str, List[str]]:
    """
    Process document: parse and chunk.
    Returns: (full_text, chunks)
    """
    full_text = parse_document(file_path)
    if not full_text:
        raise ValueError("No text extracted from document")
    
    chunks = chunk_text(full_text)
    if not chunks:
        raise ValueError("Document produced no chunks after splitting")
    
    return full_text, chunks
