
import os
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "math_kb")

GRANITE_API_KEY = os.getenv("GRANITE_API_KEY", "")
GRANITE_MODEL = os.getenv("GRANITE_MODEL", "ibm/granite-embedding-30b-instruct")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
MCP_STUB = os.getenv("MCP_STUB", "true").lower() in ("1","true","yes")

FRONTEND_API_URL = os.getenv("FRONTEND_API_URL", "http://localhost:8000")
