from typing import Dict, Optional, Tuple
import google.generativeai as genai
from app.config import (
    GOOGLE_API_KEY, 
    LLM_MODEL, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS,
    SIMILARITY_THRESHOLD,
    CONFIDENCE_THRESHOLD,
    MIN_CHUNK_AGREEMENT
)
from app.vector_store import vector_store


class QASystem:
    """RAG-based Q&A system with guardrails and confidence scoring."""
    
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt for the LLM with context and question."""
        prompt = f"""You are an AI assistant for a Transportation Management System (TMS). 
Answer the user's question based ONLY on the provided document context below.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Answer ONLY using information from the context above.
- If the context does not contain enough information to answer, say "I cannot find this information in the document."
- IF the user's question is just a greeting (e.g., "hi", "hello") or conversational small talk entirely unrelated to logistics, respond politely as a TMS AI assistant and start your entire response exactly with the tag `[CONVERSATION]`.
- Be specific and precise with numbers, dates, and names.
- Keep your answer concise.

ANSWER:"""
        return prompt
    
    def _calculate_confidence(self, similarities: list, answer: str, context: str) -> float:
        """
        Calculate confidence score based on:
        1. Retrieval similarity (average of top chunks)
        2. Answer coverage (how much the answer uses context)
        3. Chunk agreement (consistency across retrieved chunks)
        """
        # Base similarity score
        if not similarities:
            return 0.0
        
        avg_similarity = sum(similarities) / len(similarities)
        max_similarity = max(similarities)
        
        # Chunk agreement: how similar are the top chunks to each other
        chunk_agreement = 1.0 - (max_similarity - avg_similarity) if max_similarity > 0 else 0.5
        
        # Answer coverage: penalize very short or very long answers
        answer_length = len(answer.split())
        if answer_length < 5:
            coverage_score = 0.5  # Very short answer
        elif answer_length > 200:
            coverage_score = 0.6  # Potentially verbose
        else:
            coverage_score = 0.8  # Good length
        
        # Weighted confidence score
        confidence = (
            avg_similarity * 0.5 +
            chunk_agreement * 0.3 +
            coverage_score * 0.2
        )
        
        return round(min(confidence, 1.0), 3)
    
    def _apply_guardrails(self, confidence: float, max_similarity: float) -> Tuple[bool, Optional[str]]:
        """
        Apply guardrails to prevent hallucination.
        Returns: (pass, refusal_reason)
        """
        # Check overall confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            return False, "I cannot confidently answer this question based on the document."
        
        # Check retrieval similarity threshold
        if max_similarity < SIMILARITY_THRESHOLD:
            return False, "The retrieved context is not sufficiently relevant to answer this question."
        
        return True, None
    
    def ask(self, question: str) -> Dict:
        """
        Process a question with RAG.
        Returns dict with: answer, sources, confidence, guardrail_status
        """
        if not vector_store.is_initialized():
            return {
                "answer": "No document has been uploaded yet. Please upload a document first.",
                "sources": [],
                "confidence": 0.0,
                "guardrail_triggered": False,
                "guardrail_reason": None
            }
        
        # Retrieve relevant chunks
        search_results = vector_store.search(question)
        
        if not search_results:
            return {
                "answer": "I cannot find relevant information in the document.",
                "sources": [],
                "confidence": 0.0,
                "guardrail_triggered": True,
                "guardrail_reason": "No relevant context found"
            }
        
        # Build context from retrieved chunks
        context = "\n\n---\n\n".join([chunk for chunk, _ in search_results])
        similarities = [sim for _, sim in search_results]
        
        # Generate answer
        prompt = self._build_prompt(question, context)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=LLM_MAX_TOKENS
            )
        )
        
        answer = response.text.strip()
        
        # Calculate confidence
        confidence = self._calculate_confidence(similarities, answer, context)
        
        # Check for conversational bypass
        is_conversational = answer.startswith("[CONVERSATION]")
        if is_conversational:
            answer = answer.replace("[CONVERSATION]", "").strip()
            confidence = 1.0  # High confidence for knowing how to say hello
            guardrail_pass = True
            guardrail_reason = None
        else:
            # Apply guardrails normally
            guardrail_pass, guardrail_reason = self._apply_guardrails(confidence, max(similarities))
            
            if not guardrail_pass:
                answer = guardrail_reason
                confidence = max(confidence, 0.0)
        
        # Format sources
        sources = [
            {"text": chunk, "similarity": round(sim, 3)}
            for chunk, sim in search_results
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "guardrail_triggered": not guardrail_pass,
            "guardrail_reason": guardrail_reason
        }


qa_system = QASystem()
