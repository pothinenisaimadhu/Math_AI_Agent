from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, validator
import requests
import logging
import os
import time
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL        = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "math_kb")
OLLAMA_URL        = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLAMA_MODEL       = os.getenv("LLAMA_MODEL", "llama3.1:8b")

# ── Frontend HTML ─────────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_HTML = None
for _p in [
    os.path.join(_BASE, "..", "frontend", "public", "index.html"),
    os.path.join(os.getcwd(), "frontend", "public", "index.html"),
]:
    if os.path.exists(_p):
        with open(_p, "r", encoding="utf-8") as _f:
            _FRONTEND_HTML = _f.read()
        logger.info(f"Loaded frontend HTML from {_p}")
        break

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy component init ───────────────────────────────────────────────────────
_qdrant = None
_ai_gateway = None

def get_qdrant():
    global _qdrant
    if _qdrant is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant = QdrantClient(url=QDRANT_URL, timeout=5)
            _qdrant.get_collections()
        except Exception as e:
            logger.warning(f"Qdrant unavailable: {e}")
            _qdrant = None
    return _qdrant

def get_ai_gateway():
    global _ai_gateway
    if _ai_gateway is None:
        try:
            from ai_gateway import AIGateway
        except ImportError:
            from backend.ai_gateway import AIGateway
        _ai_gateway = AIGateway()
    return _ai_gateway

def ollama_available():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False

def ollama_generate(prompt: str) -> Optional[str]:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.7, "num_ctx": 2048}},
            timeout=180
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None

# ── Request models ────────────────────────────────────────────────────────────
class SolveRequest(BaseModel):
    user_id: str
    question: str
    grade: str = "intermediate"
    topic: Optional[str] = None
    score_threshold: float = 0.3

    @validator("question")
    def validate_question(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Question too short")
        if len(v) > 1000:
            raise ValueError("Question too long (max 1000 characters)")
        return v

    @validator("grade")
    def validate_grade(cls, v):
        if v not in ["elementary", "intermediate", "advanced"]:
            raise ValueError("Grade must be elementary, intermediate, or advanced")
        return v

class FeedbackRequest(BaseModel):
    user_id: str
    question: str
    answer: str
    correct: bool = True

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    if _FRONTEND_HTML:
        return HTMLResponse(content=_FRONTEND_HTML)
    return {"status": "Math AI Tutor API running", "endpoints": ["/solve", "/status"]}

@app.get("/status")
def status():
    qdrant_ok = get_qdrant() is not None
    ollama_ok = ollama_available()
    return {
        "status": "healthy",
        "components": {
            "qdrant": qdrant_ok,
            "ollama": ollama_ok,
            "ai_gateway": True,
        },
        "timestamp": time.time()
    }

@app.post("/solve")
def solve(req: SolveRequest):
    start = time.time()
    query = req.question

    gateway = get_ai_gateway()
    validation = gateway.validate_input(query)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    sanitized = validation["sanitized_query"]

    grade_instructions = {
        "elementary": "Use simple language. Explain each step clearly.",
        "intermediate": "Use standard mathematical terminology. Show detailed steps.",
        "advanced": "Use advanced mathematical concepts and notation.",
    }
    instruction = grade_instructions.get(req.grade, grade_instructions["intermediate"])

    prompt = f"""You are a math professor teaching {req.grade} level students. {instruction}

Question: {sanitized}

Provide:
1. Numbered solution steps
2. Clear final answer
3. Brief explanation of key concepts used"""

    # Try Ollama
    if ollama_available():
        response = ollama_generate(prompt)
        if response:
            out = gateway.validate_output(response)
            return {
                "source": "llm",
                "answer": out["filtered_response"],
                "confidence": out["confidence"],
                "processing_time": time.time() - start
            }

    # Fallback: try knowledge base keyword search
    qdrant = get_qdrant()
    if qdrant:
        try:
            results, _ = qdrant.scroll(collection_name=QDRANT_COLLECTION, limit=100)
            query_words = set(sanitized.lower().split())
            best, best_score = None, 0.0
            for r in results:
                content = r.payload.get("page_content", "")
                matches = sum(1 for w in query_words if w in content.lower())
                score = matches / len(query_words) if query_words else 0
                if score > best_score:
                    best, best_score = content, score
            if best and best_score > 0.3:
                out = gateway.validate_output(best)
                return {
                    "source": "knowledge_base",
                    "answer": out["filtered_response"],
                    "confidence": best_score,
                    "processing_time": time.time() - start
                }
        except Exception as e:
            logger.error(f"KB search error: {e}")

    return {
        "source": "fallback",
        "answer": "Ollama LLM is not available in this deployment. To get full AI responses, run the backend locally with Ollama running.",
        "processing_time": time.time() - start
    }

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    logger.info(f"Feedback from {req.user_id}: correct={req.correct}")
    return {"status": "logged"}
