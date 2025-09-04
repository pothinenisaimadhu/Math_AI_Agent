import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AIGateway:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_input(self, query: str) -> Dict[str, Any]:
        """Validate input query for mathematics education focus"""
        try:
            # Check if query is mathematics-related
            if not self._is_math_related(query):
                return {
                    "valid": False,
                    "error": "This system is focused on mathematics education only. Please ask math-related questions.",
                    "sanitized_query": None
                }
            
            # Check for inappropriate content
            if self._contains_inappropriate_content(query):
                return {
                    "valid": False,
                    "error": "Please keep questions appropriate for educational purposes.",
                    "sanitized_query": None
                }
            
            # Sanitize and normalize query
            sanitized = self._sanitize_query(query)
            
            return {
                "valid": True,
                "error": None,
                "sanitized_query": sanitized
            }
            
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return {
                "valid": False,
                "error": "Unable to process query. Please try again.",
                "sanitized_query": None
            }
    
    def validate_output(self, response: str) -> Dict[str, Any]:
        """Validate output for educational appropriateness"""
        try:
            # Check for educational content markers
            if not self._is_educational_response(response):
                return {
                    "valid": False,
                    "filtered_response": "I can only provide educational mathematics content. Please ask a math question.",
                    "confidence": 0.0
                }
            
            # Filter out any inappropriate content
            filtered = self._filter_response(response)
            
            # Calculate confidence based on mathematical content
            confidence = self._calculate_confidence(filtered)
            
            return {
                "valid": True,
                "filtered_response": filtered,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Output validation error: {e}")
            return {
                "valid": False,
                "filtered_response": "Error processing response. Please try again.",
                "confidence": 0.0
            }
    
    def _is_math_related(self, query: str) -> bool:
        """Check if query is mathematics-related"""
        math_keywords = [
            # Core math terms
            'derivative', 'integral', 'equation', 'solve', 'calculate', 'function',
            'algebra', 'calculus', 'geometry', 'trigonometry', 'statistics',
            'probability', 'matrix', 'vector', 'limit', 'series', 'polynomial',
            'logarithm', 'exponential', 'sin', 'cos', 'tan', 'sqrt', 'sum',
            'product', 'factor', 'prime', 'theorem', 'proof', 'formula',
            # Word problem terms
            'machines', 'widgets', 'hours', 'minutes', 'rate', 'ratio', 'proportion',
            'speed', 'distance', 'time', 'work', 'production', 'efficiency',
            'cost', 'price', 'profit', 'percentage', 'percent', 'discount',
            # Geometry terms
            'area', 'volume', 'perimeter', 'circumference', 'radius', 'diameter',
            'triangle', 'square', 'rectangle', 'circle', 'sphere', 'cube',
            'angle', 'degrees', 'radians', 'parallel', 'perpendicular',
            'shape', 'polygon', 'vertex', 'edge', 'face', 'surface',
            # Measurement and units
            'meters', 'feet', 'inches', 'centimeters', 'kilometers', 'miles',
            'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years',
            'grams', 'kilograms', 'pounds', 'ounces', 'liters', 'gallons',
            # Problem-solving terms
            'how many', 'how much', 'how long', 'how far', 'how fast',
            'find', 'determine', 'compute', 'evaluate', 'estimate'
        ]
        
        math_symbols = ['=', '+', '-', '*', '/', '^', '∫', '∑', '∏', 'π', '∞', '√', '%']
        
        query_lower = query.lower()
        
        # Check for math keywords
        if any(keyword in query_lower for keyword in math_keywords):
            return True
        
        # Check for math symbols
        if any(symbol in query for symbol in math_symbols):
            return True
        
        # Check for number patterns (including ratios and fractions)
        if re.search(r'\d+[\+\-\*/\^]\d+', query):
            return True
        
        # Check for ratio patterns (e.g., "5 machines 5 hours")
        if re.search(r'\d+\s+\w+\s+\d+\s+\w+', query):
            return True
        
        # Check for measurement patterns
        if re.search(r'\d+\s*(meters?|feet|inches?|cm|km|miles?|seconds?|minutes?|hours?)', query_lower):
            return True
            
        return False
    
    def _contains_inappropriate_content(self, query: str) -> bool:
        """Check for inappropriate content"""
        inappropriate_patterns = [
            r'\b(hack|exploit|bypass|cheat)\b',
            r'\b(personal|private|confidential)\b',
            r'\b(violence|harm|illegal)\b'
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in inappropriate_patterns)
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize and normalize query"""
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', query.strip())
        
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>{}]', '', sanitized)
        
        return sanitized
    
    def _is_educational_response(self, response: str) -> bool:
        """Check if response contains educational content"""
        educational_markers = [
            'step', 'solution', 'answer', 'formula', 'theorem', 'proof',
            'calculate', 'solve', 'derivative', 'integral', 'equation'
        ]
        
        response_lower = response.lower()
        return any(marker in response_lower for marker in educational_markers)
    
    def _filter_response(self, response: str) -> str:
        """Filter response for educational appropriateness"""
        # Remove any non-educational content
        lines = response.split('\n')
        filtered_lines = []
        
        for line in lines:
            if self._is_educational_line(line):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines) if filtered_lines else response
    
    def _is_educational_line(self, line: str) -> bool:
        """Check if a line contains educational content"""
        # Allow mathematical expressions, explanations, and educational content
        if re.search(r'[=\+\-\*/\^∫∑∏π∞√]', line):
            return True
        if any(word in line.lower() for word in ['step', 'solution', 'because', 'therefore', 'thus']):
            return True
        return len(line.strip()) > 0
    
    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score for mathematical response"""
        confidence = 0.0
        
        # Mathematical symbols increase confidence
        math_symbols = ['=', '∫', '∑', '∏', 'π', '∞', '√', '^']
        symbol_count = sum(response.count(symbol) for symbol in math_symbols)
        confidence += min(symbol_count * 0.1, 0.3)
        
        # Step-by-step solutions increase confidence
        if 'step' in response.lower():
            confidence += 0.2
        
        # Mathematical terms increase confidence
        math_terms = ['derivative', 'integral', 'equation', 'formula', 'theorem']
        term_count = sum(response.lower().count(term) for term in math_terms)
        confidence += min(term_count * 0.1, 0.3)
        
        # Length and structure
        if len(response) > 100:
            confidence += 0.2
        
        return min(confidence, 1.0)