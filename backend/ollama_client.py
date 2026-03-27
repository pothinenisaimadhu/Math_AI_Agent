import requests
from typing import Optional

class OllamaClient:
    """OpenRouter-backed LLM client (drop-in replacement for Ollama)"""

    def __init__(self, base_url: str = None):
        import os
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-nano-9b-v2:free")
        self.base_url = "https://openrouter.ai/api/v1"

    def generate(self, model: str, prompt: str, timeout: int = 60) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            print(f"OpenRouter request timed out after {timeout}s")
            return None
        except Exception as e:
            print(f"OpenRouter error: {e}")
            return None

    def is_available(self) -> bool:
        return bool(self.api_key)
