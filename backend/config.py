import os
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "math_kb")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

GRANITE_MODEL = os.getenv("GRANITE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# OpenRouter replaces Ollama
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-nano-9b-v2:free")

# Keep these for backward compat (used in model_manager)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
MCP_STUB = os.getenv("MCP_STUB", "true").lower() in ("1", "true", "yes")

FRONTEND_API_URL = os.getenv("FRONTEND_API_URL", "http://localhost:8000")
