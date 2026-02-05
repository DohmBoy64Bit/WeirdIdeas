import requests
import json
from config import Config

class OllamaClient:
    def __init__(self, base_url=None, model=None, app=None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.model = model or Config.OLLAMA_MODEL
        self.app = app # Store for config access if needed

    def generate(self, prompt, system_prompt=None, options=None):
        """
        Generate text completion using Ollama.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if options:
            payload["options"] = options

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return None

    def check_health(self):
        """
        Check if Ollama service is reachable.
        """
        try:
            response = requests.get(self.base_url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
