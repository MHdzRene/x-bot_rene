
import io
import os
from pathlib import Path

# Function to load environment variables from .env file
def load_env_from_file():
    """Loads environment variables from a .env file using io"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        with io.open(env_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment variables loaded from .env")
    else:
        print("⚠️ .env file not found")

# Get API keys from environment variables securely
def get_api_credentials():
    """Gets API credentials securely from environment variables"""
    credentials = {
        'API_KEY': os.getenv('API_KEY'),
        'API_SECRET': os.getenv('API_SECRET'), 
        'BEARER_TOKEN': os.getenv('BEARER_TOKEN'),
        'ACCESS_TOKEN': os.getenv('ACCESS_TOKEN'),
        'ACCESS_TOKEN_SECRET': os.getenv('ACCESS_TOKEN_SECRET')
    }
    
    # Check that all credentials are available
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        print(f"❌ Missing the following credentials: {', '.join(missing)}")
        return None
    
    print("🔐 Credentials loaded securely")
    return credentials