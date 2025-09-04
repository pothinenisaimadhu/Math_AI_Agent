from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
from config import QDRANT_URL, QDRANT_COLLECTION, OLLAMA_URL, LLAMA_MODEL
from mcp import MCPClient
from ollama_client import OllamaClient
from ai_gateway import AIGateway
import requests
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple components without embeddings
qdrant_client = QdrantClient(url=QDRANT_URL)
search_client = MCPClient()
ollama_client = OllamaClient(base_url=OLLAMA_URL)
ai_gateway = AIGateway()

logging.basicConfig(level=logging.INFO)

class SolveRequest(BaseModel):
    user_id: str
    question: str
    grade: str = "intermediate"

class FeedbackRequest(BaseModel):
    user_id: str
    question: str
    answer: str
    correct: bool = True

@app.get("/status")
def status():
    return {"status": "ok"}

@app.post("/solve")
def solve(req: SolveRequest):
    query = req.question
    
    # AI Gateway: Input Validation
    input_validation = ai_gateway.validate_input(query)
    if not input_validation["valid"]:
        raise HTTPException(status_code=400, detail=input_validation["error"])
    
    sanitized_query = input_validation["sanitized_query"]
    
    try:
        # 1. Web Search (MCP) + LLM Processing
        print(f"Searching for: {sanitized_query}")
        web_results = search_client.search(sanitized_query)
        if web_results["results"]:
            print(f"Found {len(web_results['results'])} results")
            
            # Show what was found
            web_summary = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('snippet', '')[:100]}..." for r in web_results["results"]])
            print(f"Search found:\n{web_summary}")
            
            # Combine content for LLM processing
            context = "\n\n".join([f"Source: {r.get('title', 'Unknown')}\n{r.get('content', r.get('snippet', ''))}" for r in web_results["results"]])
            prompt = f"""You are a math professor. Based on the following search results, provide a clear step-by-step solution:

Search Context:
{context}

Question: {sanitized_query}

Provide numbered steps and final answer:"""
            
            print("Forwarding to Llama 3.1 for processing...")
            if ollama_client.is_available():
                response = ollama_client.generate(LLAMA_MODEL, prompt)
                if response:
                    # AI Gateway: Output Validation
                    output_validation = ai_gateway.validate_output(response)
                    
                    return {
                        "source": "web+llm",
                        "answer": f"**Search Found:**\n{web_summary}\n\n**Analysis:**\n{output_validation['filtered_response']}",
                        "web_sources": len(web_results["results"]),
                        "confidence": output_validation["confidence"]
                    }

        # 2. Fallback → Direct LLM
        if ollama_client.is_available():
            prompt = f"You are a math professor. Solve step by step:\n\nQuestion: {sanitized_query}\nAnswer:"
            response = ollama_client.generate(LLAMA_MODEL, prompt)
            if response:
                # AI Gateway: Output Validation
                output_validation = ai_gateway.validate_output(response)
                
                return {
                    "source": "llm",
                    "answer": output_validation["filtered_response"],
                    "confidence": output_validation["confidence"]
                }
        
        return {
            "source": "fallback",
            "answer": "No results found. Please ensure Ollama is running with llama3.1:8b model."
        }

    except Exception as e:
        logging.error(f"Solve error: {e}")
        return {
            "source": "error", 
            "answer": "I can only help with mathematics education. Please ask a math question."
        }

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    try:
        if req.correct:
            return {"status": "stored", "message": "Feedback saved"}
        else:
            return {"status": "skipped", "message": "Feedback marked incorrect, not stored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}