import requests
import json
from typing import Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def generate(self, model: str, prompt: str, timeout: int = 180) -> Optional[str]:
        """Generate text using Ollama API"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 2048
                }
            }
            
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "").strip()
            
        except requests.exceptions.Timeout:
            print(f"Ollama request timed out after {timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ollama API request failed: {e}")
            return None
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False