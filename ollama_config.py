# Configuration for Ollama integration
import requests
import json
from typing import Dict, Any, Optional

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def generate(self, model: str, prompt: str, stream: bool = False) -> Optional[Dict[str, Any]]:
        """Generate response from Ollama model"""
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.api_url}/generate",
                json=data,
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ollama API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return None
    
    def chat(self, model: str, messages: list, stream: bool = False) -> Optional[Dict[str, Any]]:
        """Chat with Ollama model"""
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.api_url}/chat",
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ollama Chat API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama Chat: {e}")
            return None

# Default configuration
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "default_model": "llama2:7b",
    "timeout": 60,
    "max_tokens": 4096
}

def test_ollama_connection():
    """Test Ollama connection and print status"""
    client = OllamaClient()
    
    print("🔍 Testing Ollama connection...")
    
    if client.is_available():
        print("✅ Ollama server is running!")
        
        models = client.list_models()
        if models:
            print(f"📦 Available models: {', '.join(models)}")
            
            # Test generation
            if "llama2:7b" in models:
                print("🧪 Testing model generation...")
                result = client.generate("llama2:7b", "Hello, how are you?")
                if result:
                    print("✅ Model generation test successful!")
                    print(f"Response: {result.get('response', 'No response')[:100]}...")
                else:
                    print("❌ Model generation test failed")
            else:
                print("⚠️ llama2:7b model not found")
        else:
            print("❌ No models available")
    else:
        print("❌ Ollama server is not running")
        print("💡 Make sure to run: ollama serve")

if __name__ == "__main__":
    test_ollama_connection()
