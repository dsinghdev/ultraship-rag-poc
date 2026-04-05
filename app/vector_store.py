import os
import faiss
import logging
import numpy as np
from typing import List, Tuple
import google.generativeai as genai
from app.config import GOOGLE_API_KEY, EMBEDDING_MODEL, TOP_K_CHUNKS

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for document chunks with Gemini embeddings."""
    
    def __init__(self):
        self.index = None
        self.chunks = []
        self._initialized = False
    
    def initialize(self, chunks: List[str]):
        """Create embeddings and build FAISS index using batch processing."""
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        self.chunks = chunks
        
        # Generate embeddings using Gemini Batch API
        embeddings_list = []
        batch_size = 50  # Process in manageable batches to respect API limits
        
        logger.info(f"🚀 Starting batch embedding for {len(chunks)} chunks...")
        
        try:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                logger.info(f"📦 Processing batch {i//batch_size + 1} ({len(batch)} chunks)")
                
                response = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch,
                    task_type="retrieval_document"
                )
                embeddings_list.extend(response['embedding'])
                
            embeddings_array = np.array(embeddings_list, dtype=np.float32)
            
            # Build FAISS index
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            self.index.add(embeddings_array)
            
            self._initialized = True
            logger.info("✅ Vector store initialization complete")
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                logger.error("🛑 Gemini API Quota Exhausted! Please wait for reset or check your API limit.")
                raise ValueError("Gemini API Rate Limit hit. Your daily quota is likely exhausted.")
            else:
                logger.error(f"❌ Embedding failed: {error_msg}")
                raise e
    
    def search(self, query: str, top_k: int = TOP_K_CHUNKS) -> List[Tuple[str, float]]:
        """
        Search for relevant chunks.
        Returns: List of (chunk_text, similarity_score)
        """
        if not self._initialized:
            raise ValueError("VectorStore not initialized")
        
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Embed query
        response = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = response['embedding']
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.index.search(query_array, min(top_k, len(self.chunks)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                # Convert inner product to similarity (0-1 range)
                similarity = float((score + 1) / 2)  # Normalize from [-1, 1] to [0, 1]
                results.append((self.chunks[idx], similarity))
        
        return results
    
    def is_initialized(self) -> bool:
        return self._initialized


# Global vector store instance
vector_store = VectorStore()
