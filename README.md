# Math AI Tutor - Agentic RAG System

**Overview**
- FastAPI backend with Qdrant vector database and Ollama LLM integration
- React frontend with chat history and query editing capabilities
- AI Gateway for mathematics education content validation
- Enhanced retrieval system with keyword matching and caching

**Architecture**
- **Backend**: FastAPI with comprehensive error handling and input validation
- **Database**: Qdrant vector database for knowledge base storage
- **LLM**: Ollama integration with configurable timeout and model options
- **Frontend**: React SPA with two-panel layout and interactive chat history
- **AI Gateway**: Input/output validation for educational mathematics content

**Environment Variables**
- `QDRANT_URL` (default: http://localhost:6333)
- `QDRANT_COLLECTION` (default: math_kb)
- `OLLAMA_URL` (default: http://localhost:11434)
- `LLAMA_MODEL` (default: llama3.1:8b)
- `OLLAMA_TIMEOUT` (default: 180 seconds)
- `FRONTEND_API_URL` (default: http://localhost:8000)
- `SERPER_API_KEY` (optional for web search)
- `MCP_STUB` (set to "true" to use stub MCP)

**Quick Start**
1. Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
2. Start Ollama: `ollama serve` and `ollama pull llama3.1:8b`
3. Install backend dependencies: `pip install -r backend/requirements.txt`
4. Seed knowledge base: `python backend/seed_qdrant.py --enhanced --data-file math_dataset.json`
5. Start backend: `uvicorn backend.main:app --reload --port 8000`
6. Open frontend: Open `frontend/public/index.html` in browser

**Features**
- **Chat History**: Left sidebar with persistent conversation history
- **Query Editing**: Edit and resend previous questions with inline editing
- **Math Recognition**: AI Gateway recognizes word problems, geometry, and mathematical expressions
- **Enhanced Retrieval**: Hybrid search with keyword matching and relevance scoring
- **Error Handling**: Comprehensive error handling with fallback responses
- **Response Caching**: LRU cache with TTL for improved performance
- **Educational Focus**: Content validation ensures mathematics education focus

**Frontend Features**
- Two-panel layout with chat history sidebar
- Click any history item to reuse the question
- Edit button on each history item for inline editing
- Real-time chat interface with user/bot message distinction
- Responsive design with clean UI

**Backend Components**
- `main.py`: FastAPI application with solve endpoint
- `ai_gateway.py`: Input/output validation for educational content
- `enhanced_retrieval.py`: Advanced retrieval with keyword matching
- `ollama_client.py`: Ollama integration with timeout handling
- `response_cache.py`: LRU cache for response optimization
- `model_manager.py`: Flexible model management system