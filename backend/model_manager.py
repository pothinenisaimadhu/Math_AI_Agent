from typing import Dict, Any, Optional
import logging
from config import GRANITE_MODEL, LLAMA_MODEL, OLLAMA_URL

logger = logging.getLogger(__name__)

class ModelManager:
    """Manage multiple models for embeddings and LLM"""
    
    def __init__(self):
        self.embedding_models = {
            "granite": "sentence-transformers/all-MiniLM-L6-v2",
            "mpnet": "sentence-transformers/all-mpnet-base-v2", 
            "distilbert": "sentence-transformers/distilbert-base-nli-mean-tokens"
        }
        
        self.llm_models = {
            "llama3.1": "llama3.1:8b",
            "llama3.1-70b": "llama3.1:70b",
            "codellama": "codellama:7b",
            "mistral": "mistral:7b"
        }
        
        self.current_embedding = "granite"
        self.current_llm = "llama3.1"
    
    def get_embedding_model(self, model_name: Optional[str] = None) -> str:
        """Get embedding model name"""
        if model_name and model_name in self.embedding_models:
            return self.embedding_models[model_name]
        return self.embedding_models[self.current_embedding]
    
    def get_llm_model(self, model_name: Optional[str] = None) -> str:
        """Get LLM model name"""
        if model_name and model_name in self.llm_models:
            return self.llm_models[model_name]
        return self.llm_models[self.current_llm]
    
    def switch_embedding_model(self, model_name: str) -> bool:
        """Switch embedding model"""
        if model_name in self.embedding_models:
            self.current_embedding = model_name
            logger.info(f"Switched embedding model to: {model_name}")
            return True
        logger.warning(f"Unknown embedding model: {model_name}")
        return False
    
    def switch_llm_model(self, model_name: str) -> bool:
        """Switch LLM model"""
        if model_name in self.llm_models:
            self.current_llm = model_name
            logger.info(f"Switched LLM model to: {model_name}")
            return True
        logger.warning(f"Unknown LLM model: {model_name}")
        return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        return {
            "embedding_models": list(self.embedding_models.keys()),
            "llm_models": list(self.llm_models.keys()),
            "current": {
                "embedding": self.current_embedding,
                "llm": self.current_llm
            }
        }