
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from qdrant_client import QdrantClient, models
from config import QDRANT_URL, QDRANT_COLLECTION, GRANITE_MODEL, OLLAMA_URL, LLAMA_MODEL
from mcp import MCPClient
from ollama_client import OllamaClient
from ai_gateway import AIGateway
from enhanced_retrieval import EnhancedRetrieval
from model_manager import ModelManager
from response_cache import ResponseCache
import requests
import logging
import asyncio
from typing import Optional, Dict, Any
import time
from functools import lru_cache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components with error handling
qdrant_client = None
search_client = None
ollama_client = None
ai_gateway = None
enhanced_retrieval = None
model_manager = None
response_cache = None

# Cache for repeated queries
@lru_cache(maxsize=100)
def cached_search(query: str) -> str:
    """Cache search results for repeated queries"""
    return str(time.time())  # Simple cache key

def initialize_components():
    """Initialize all components with proper error handling"""
    global qdrant_client, search_client, ollama_client, ai_gateway, enhanced_retrieval, model_manager, response_cache
    
    try:
        # Initialize Qdrant with connection test
        qdrant_client = QdrantClient(url=QDRANT_URL)
        # Test connection
        qdrant_client.get_collections()
        logging.info("✅ Qdrant connected successfully")
    except Exception as e:
        logging.error(f"❌ Qdrant connection failed: {e}")
        qdrant_client = None
    
    try:
        # Initialize MCP client
        search_client = MCPClient()
        logging.info("✅ MCP client initialized")
    except Exception as e:
        logging.error(f"❌ MCP client initialization failed: {e}")
        search_client = None
    
    try:
        # Initialize Ollama with availability check
        ollama_client = OllamaClient(base_url=OLLAMA_URL)
        if ollama_client.is_available():
            logging.info("✅ Ollama connected successfully")
        else:
            logging.warning("⚠️ Ollama not available")
    except Exception as e:
        logging.error(f"❌ Ollama initialization failed: {e}")
        ollama_client = None
    
    try:
        # Initialize AI Gateway
        ai_gateway = AIGateway()
        logging.info("✅ AI Gateway initialized")
    except Exception as e:
        logging.error(f"❌ AI Gateway initialization failed: {e}")
        ai_gateway = None
    
    try:
        # Initialize Enhanced Retrieval
        if qdrant_client:
            enhanced_retrieval = EnhancedRetrieval(qdrant_client, QDRANT_COLLECTION)
            logging.info("✅ Enhanced Retrieval initialized")
    except Exception as e:
        logging.error(f"❌ Enhanced Retrieval initialization failed: {e}")
        enhanced_retrieval = None
    
    try:
        # Initialize Model Manager
        model_manager = ModelManager()
        logging.info("✅ Model Manager initialized")
    except Exception as e:
        logging.error(f"❌ Model Manager initialization failed: {e}")
        model_manager = None
    
    try:
        # Initialize Response Cache
        response_cache = ResponseCache(max_size=500, ttl=1800)  # 30 min TTL
        logging.info("✅ Response Cache initialized")
    except Exception as e:
        logging.error(f"❌ Response Cache initialization failed: {e}")
        response_cache = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize components on startup
initialize_components()

class SolveRequest(BaseModel):
    user_id: str
    question: str
    grade: str = "intermediate"
    topic: Optional[str] = None
    use_hybrid_search: bool = False
    score_threshold: float = 0.3
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Question too short')
        if len(v.strip()) > 1000:
            raise ValueError('Question too long (max 1000 characters)')
        return v.strip()
    
    @validator('grade')
    def validate_grade(cls, v):
        allowed_grades = ['elementary', 'intermediate', 'advanced']
        if v not in allowed_grades:
            raise ValueError(f'Grade must be one of: {allowed_grades}')
        return v
    
    @validator('score_threshold')
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score threshold must be between 0.0 and 1.0')
        return v

class FeedbackRequest(BaseModel):
    user_id: str
    question: str
    answer: str
    correct: bool = True
    
    @validator('question', 'answer')
    def validate_text_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

@app.get("/status")
def status():
    """Health check endpoint with component status"""
    component_status = {
        "qdrant": qdrant_client is not None,
        "ollama": ollama_client is not None and ollama_client.is_available() if ollama_client else False,
        "mcp": search_client is not None,
        "ai_gateway": ai_gateway is not None,
        "enhanced_retrieval": enhanced_retrieval is not None,
        "model_manager": model_manager is not None,
        "response_cache": response_cache is not None
    }
    
    cache_stats = response_cache.stats() if response_cache else {}
    model_info = model_manager.list_models() if model_manager else {}
    
    overall_status = "healthy" if any(component_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "components": component_status,
        "cache_stats": cache_stats,
        "models": model_info,
        "timestamp": time.time()
    }

@app.post("/solve")
def solve(req: SolveRequest):
    """Solve mathematical problems with comprehensive error handling"""
    start_time = time.time()
    query = req.question
    
    # Log the request
    logging.info(f"Received question: {query[:100]}..." if len(query) > 100 else f"Received question: {query}")
    
    # Check if AI Gateway is available
    if not ai_gateway:
        raise HTTPException(status_code=503, detail="AI Gateway not available")
    
    # AI Gateway: Input Validation
    try:
        input_validation = ai_gateway.validate_input(query)
        if not input_validation["valid"]:
            logging.warning(f"Input validation failed: {input_validation['error']}")
            raise HTTPException(status_code=400, detail=input_validation["error"])
        
        sanitized_query = input_validation["sanitized_query"]
        logging.info(f"Input validated and sanitized")
    except Exception as e:
        logging.error(f"Input validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid input")
    
    try:
        # 1. Knowledge Base Lookup (if Qdrant available)
        if qdrant_client and enhanced_retrieval:
            try:
                # Check if collection exists
                collections = qdrant_client.get_collections()
                if any(c.name == QDRANT_COLLECTION for c in collections.collections):
                    logging.info("Searching knowledge base...")
                    
                    # Simple text-based search in Qdrant
                    kb_results = enhanced_retrieval._keyword_search(
                        sanitized_query,
                        top_k=3,
                        score_threshold=req.score_threshold
                    )
                    
                    if kb_results and kb_results[0]["score"] > req.score_threshold:
                        logging.info(f"Found KB match with score: {kb_results[0]['score']}")
                        
                        # Get KB content and send to LLM for processing
                        best_match = kb_results[0]
                        kb_content = best_match["content"]
                        metadata = best_match["metadata"]
                        
                        # Create prompt with KB context
                        prompt = f"""You are a math professor. Use the following knowledge base content to answer the specific question.

Knowledge Base Content:
{kb_content}

Specific Question: {sanitized_query}

Provide a step-by-step solution tailored to this specific question. If the KB content doesn't exactly match, adapt the solution method to the current question."""
                        
                        logging.info("Sending KB content to LLM for processing...")
                        
                        # Process with LLM
                        if ollama_client and ollama_client.is_available():
                            response = ollama_client.generate(LLAMA_MODEL, prompt)
                            if response:
                                # AI Gateway: Output Validation
                                output_validation = ai_gateway.validate_output(response)
                                
                                processing_time = time.time() - start_time
                                logging.info(f"KB+LLM request completed in {processing_time:.2f}s")
                                
                                return {
                                    "source": "knowledge_base+llm",
                                    "answer": f"**Based on Knowledge Base:**\n\n{output_validation['filtered_response']}\n\n**Source:** {metadata.get('source_id', 'Unknown')}",
                                    "score": best_match["score"],
                                    "confidence": output_validation["confidence"],
                                    "processing_time": processing_time,
                                    "metadata": metadata
                                }
                        
                        # Fallback to raw KB content if LLM fails
                        kb_response = f"**From Knowledge Base:**\n\n{kb_content}\n\n**Source:** {metadata.get('source_id', 'Unknown')}"
                        output_validation = ai_gateway.validate_output(kb_response)
                        
                        processing_time = time.time() - start_time
                        return {
                            "source": "knowledge_base",
                            "answer": output_validation["filtered_response"],
                            "score": best_match["score"],
                            "confidence": output_validation["confidence"],
                            "processing_time": processing_time,
                            "metadata": metadata
                        }
                    else:
                        logging.info("No good KB matches found, continuing to web search")
                else:
                    logging.warning(f"Collection {QDRANT_COLLECTION} not found")
            except Exception as e:
                logging.error(f"Knowledge base search error: {e}")

        # 2. Web Search + LLM Processing
        web_results = None
        if search_client:
            try:
                logging.info(f"Searching web for: {sanitized_query}")
                web_results = search_client.search(sanitized_query)
                
                if web_results and web_results.get("results"):
                    logging.info(f"Found {len(web_results['results'])} web results")
                    
                    # Format context properly
                    formatted_context = format_search_context(web_results["results"])
                    web_summary = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('snippet', '')[:100]}..." for r in web_results["results"]])
                    
                    logging.info(f"Search results formatted, forwarding to LLM")
                    
                    # Try LLM processing
                    if ollama_client and ollama_client.is_available():
                        prompt = create_educational_prompt(sanitized_query, formatted_context, req.grade)
                        
                        try:
                            response = ollama_client.generate(LLAMA_MODEL, prompt)
                            if response:
                                logging.info(f"LLM response received ({len(response)} chars)")
                                
                                # AI Gateway: Output Validation
                                output_validation = ai_gateway.validate_output(response)
                                
                                processing_time = time.time() - start_time
                                logging.info(f"Request completed in {processing_time:.2f}s")
                                
                                return {
                                    "source": "web+llm",
                                    "answer": f"**Search Found:**\n{web_summary}\n\n**Analysis:**\n{output_validation['filtered_response']}",
                                    "web_sources": len(web_results["results"]),
                                    "confidence": output_validation["confidence"],
                                    "processing_time": processing_time
                                }
                        except Exception as e:
                            logging.error(f"LLM processing error: {e}")
                else:
                    logging.info("No web results found")
            except Exception as e:
                logging.error(f"Web search error: {e}")

        # 3. Fallback → Direct LLM
        if ollama_client and ollama_client.is_available():
            try:
                logging.info("Using direct LLM fallback")
                prompt = create_educational_prompt(sanitized_query, "", req.grade)
                
                response = ollama_client.generate(LLAMA_MODEL, prompt)
                if response:
                    logging.info(f"Fallback LLM response received ({len(response)} chars)")
                    
                    # AI Gateway: Output Validation
                    output_validation = ai_gateway.validate_output(response)
                    
                    processing_time = time.time() - start_time
                    logging.info(f"Fallback request completed in {processing_time:.2f}s")
                    
                    return {
                        "source": "llm",
                        "answer": output_validation["filtered_response"],
                        "confidence": output_validation["confidence"],
                        "processing_time": processing_time
                    }
            except Exception as e:
                logging.error(f"Fallback LLM error: {e}")
        
        # 4. Final fallback
        processing_time = time.time() - start_time
        logging.warning(f"All processing methods failed, returning fallback message")
        
        return {
            "source": "fallback",
            "answer": "I'm currently unable to process your question. Please ensure Ollama is running with the llama3.1:8b model, or try again later.",
            "processing_time": processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logging.error(f"Unexpected error in solve: {e}")
        return {
            "source": "error", 
            "answer": "I can only help with mathematics education. Please ask a math question.",
            "processing_time": processing_time
        }

def format_search_context(results: list) -> str:
    """Format search results into readable context"""
    if not results:
        return ""
    
    formatted = []
    for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
        title = result.get('title', 'Unknown Source')
        content = result.get('content', result.get('snippet', ''))
        if content:
            formatted.append(f"Source {i} ({title}):\n{content[:500]}..." if len(content) > 500 else f"Source {i} ({title}):\n{content}")
    
    return "\n\n".join(formatted)

def create_educational_prompt(question: str, context: str, grade_level: str) -> str:
    """Create educational prompt based on grade level"""
    grade_instructions = {
        "elementary": "Use simple language and basic concepts. Explain each step clearly.",
        "intermediate": "Use standard mathematical terminology. Show detailed steps.",
        "advanced": "Use advanced mathematical concepts and notation as appropriate."
    }
    
    instruction = grade_instructions.get(grade_level, grade_instructions["intermediate"])
    
    if context:
        return f"""You are a math professor teaching {grade_level} level students. {instruction}

Based on the following information, provide a clear step-by-step solution:

Reference Material:
{context}

Question: {question}

Provide:
1. Numbered solution steps
2. Clear final answer
3. Brief explanation of key concepts used"""
    else:
        return f"""You are a math professor teaching {grade_level} level students. {instruction}

Question: {question}

Provide:
1. Numbered solution steps
2. Clear final answer
3. Brief explanation of key concepts used"""

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    """Handle user feedback with proper error handling"""
    logging.info(f"Received feedback from user {req.user_id}: correct={req.correct}")
    
    try:
        if req.correct:
            # For now, just log positive feedback (embeddings disabled)
            logging.info(f"Positive feedback logged for question: {req.question[:50]}...")
            return {"status": "logged", "message": "Positive feedback logged"}
        else:
            logging.info(f"Negative feedback logged for question: {req.question[:50]}...")
            return {"status": "logged", "message": "Negative feedback logged"}
    except Exception as e:
        logging.error(f"Feedback processing error: {e}")
        return {"status": "error", "message": "Failed to process feedback"}

@app.post("/models/switch")
def switch_model(model_type: str, model_name: str):
    """Switch embedding or LLM model"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    if model_type == "embedding":
        success = model_manager.switch_embedding_model(model_name)
    elif model_type == "llm":
        success = model_manager.switch_llm_model(model_name)
    else:
        raise HTTPException(status_code=400, detail="Model type must be 'embedding' or 'llm'")
    
    if success:
        return {"status": "success", "message": f"Switched {model_type} model to {model_name}"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown {model_type} model: {model_name}")

@app.get("/models")
def list_models():
    """List available models"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not available")
    
    return model_manager.list_models()

@app.post("/cache/clear")
def clear_cache():
    """Clear response cache"""
    if not response_cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    response_cache.clear()
    return {"status": "success", "message": "Cache cleared"}

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    if not response_cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    return response_cache.stats()
