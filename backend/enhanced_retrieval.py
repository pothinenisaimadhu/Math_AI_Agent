import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
import hashlib
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class EnhancedRetrieval:
    def __init__(self, qdrant_client: QdrantClient, collection: str):
        self.qdrant_client = qdrant_client
        self.collection = collection
        self.cache = {}
        
    def _cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key for query"""
        key_data = f"{query}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @lru_cache(maxsize=100)
    def cached_search(self, query_hash: str, query_vector: tuple, **kwargs) -> List[Dict]:
        """Cached vector search"""
        return self._vector_search(list(query_vector), **kwargs)
    
    def _vector_search(self, query_vector: List[float], **kwargs) -> List[Dict]:
        """Core vector search with enhanced parameters"""
        search_params = {
            "collection_name": self.collection,
            "query_vector": query_vector,
            "limit": kwargs.get("top_k", 5),
            "score_threshold": kwargs.get("score_threshold", 0.3)
        }
        
        # Add metadata filters
        if kwargs.get("topic"):
            search_params["query_filter"] = Filter(
                must=[FieldCondition(key="topic", match=MatchValue(value=kwargs["topic"]))]
            )
        
        if kwargs.get("grade_level"):
            grade_filter = Filter(
                must=[FieldCondition(key="grade_level", match=MatchValue(value=kwargs["grade_level"]))]
            )
            if "query_filter" in search_params:
                search_params["query_filter"].must.append(grade_filter.must[0])
            else:
                search_params["query_filter"] = grade_filter
        
        try:
            results = self.qdrant_client.search(**search_params)
            return self._format_results_with_metadata(results)
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def _format_results_with_metadata(self, results) -> List[Dict]:
        """Format results with rich metadata"""
        formatted = []
        for result in results:
            doc = {
                "content": result.payload.get("page_content", ""),
                "score": result.score,
                "metadata": {
                    "source_id": result.payload.get("source_id"),
                    "topic": result.payload.get("topic"),
                    "grade_level": result.payload.get("grade_level"),
                    "educational_notes": result.payload.get("educational_notes")
                }
            }
            formatted.append(doc)
        return formatted
    
    def hybrid_search(self, query: str, query_vector: List[float], **kwargs) -> List[Dict]:
        """Hybrid search combining vector and keyword matching"""
        # Vector search
        vector_results = self._vector_search(query_vector, **kwargs)
        
        # Keyword search (simple implementation)
        keyword_results = self._keyword_search(query, **kwargs)
        
        # Combine and rerank
        combined = self._merge_and_rerank(vector_results, keyword_results, query)
        
        logger.info(f"Hybrid search: {len(vector_results)} vector + {len(keyword_results)} keyword = {len(combined)} combined")
        return combined
    
    def _keyword_search(self, query: str, **kwargs) -> List[Dict]:
        """Enhanced keyword search with better matching"""
        try:
            # Scroll through all documents for keyword matching
            results, _ = self.qdrant_client.scroll(
                collection_name=self.collection,
                limit=100  # Adjust based on collection size
            )
            
            keyword_matches = []
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            for result in results:
                content = result.payload.get("page_content", "")
                content_lower = content.lower()
                
                # Calculate different types of matches
                exact_match = query_lower in content_lower
                word_matches = sum(1 for word in query_words if word in content_lower)
                
                # Look for mathematical expressions
                math_expr_match = self._extract_math_expression(query_lower, content_lower)
                
                # Calculate composite score
                score = 0.0
                if exact_match:
                    score += 1.0  # Highest score for exact matches
                elif math_expr_match:
                    score += 0.8  # High score for math expression matches
                elif word_matches > 0:
                    score += (word_matches / len(query_words)) * 0.6  # Partial word matches
                
                # Only include results with meaningful scores
                if score > 0.3:
                    doc = {
                        "content": content,
                        "score": score,
                        "metadata": {
                            "source_id": result.payload.get("source_id"),
                            "topic": result.payload.get("topic"),
                            "grade_level": result.payload.get("grade_level"),
                            "educational_notes": result.payload.get("educational_notes")
                        }
                    }
                    keyword_matches.append(doc)
            
            return sorted(keyword_matches, key=lambda x: x["score"], reverse=True)[:kwargs.get("top_k", 5)]
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    def _extract_math_expression(self, query: str, content: str) -> bool:
        """Check if mathematical expressions match"""
        import re
        
        # Extract mathematical expressions from both query and content
        math_pattern = r'[fx]\([^)]+\)\s*=\s*[^\s]+'
        
        query_math = re.findall(math_pattern, query)
        content_math = re.findall(math_pattern, content)
        
        if query_math and content_math:
            # Normalize expressions for comparison
            query_expr = ''.join(query_math).replace(' ', '')
            content_expr = ''.join(content_math).replace(' ', '')
            
            # Check if query expression is contained in content expression
            return query_expr in content_expr
        
        return False
    
    def _merge_and_rerank(self, vector_results: List[Dict], keyword_results: List[Dict], query: str) -> List[Dict]:
        """Merge and rerank results using simple scoring"""
        # Create a combined list with weighted scores
        combined = {}
        
        # Add vector results with higher weight
        for doc in vector_results:
            doc_id = doc["metadata"]["source_id"]
            combined[doc_id] = doc.copy()
            combined[doc_id]["final_score"] = doc["score"] * 0.7  # Vector weight
        
        # Add keyword results
        for doc in keyword_results:
            doc_id = doc["metadata"]["source_id"]
            if doc_id in combined:
                # Boost existing documents
                combined[doc_id]["final_score"] += doc["score"] * 0.3  # Keyword weight
            else:
                combined[doc_id] = doc.copy()
                combined[doc_id]["final_score"] = doc["score"] * 0.3
        
        # Sort by final score and return top results
        sorted_results = sorted(combined.values(), key=lambda x: x["final_score"], reverse=True)
        return sorted_results[:5]  # Return top 5
    
    async def async_search(self, query: str, query_vector: List[float], **kwargs) -> List[Dict]:
        """Async wrapper for search operations"""
        loop = asyncio.get_event_loop()
        
        if kwargs.get("use_hybrid", False):
            return await loop.run_in_executor(None, self.hybrid_search, query, query_vector, **kwargs)
        else:
            return await loop.run_in_executor(None, self._vector_search, query_vector, **kwargs)