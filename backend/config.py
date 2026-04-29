import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database Configuration
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# AI Provider Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
OPENAI_ROUTER_API_KEY = os.environ.get('OPENAI_ROUTER_API_KEY')

# AI Service Configuration
DEFAULT_AI_PROVIDER = os.environ.get('DEFAULT_AI_PROVIDER', 'gemini')
AI_PROVIDER_TIMEOUT = int(os.environ.get('AI_PROVIDER_TIMEOUT', '30'))

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Deprecated: Legacy Gemini client (kept for backward compatibility)
# Will be removed in future versions - use ai_service instead
gemini_client = None
if GEMINI_API_KEY:
    import google.genai as genai
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# CORS Configuration
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Application Configuration
APP_TITLE = "AI Startup System"
API_PREFIX = "/api"

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Health Check Configuration
EXCLUDE_PATHS = ['/health', '/metrics', '/favicon.ico']

# AI Provider Models Configuration
AI_PROVIDER_MODELS = {
    'gemini': {
        'default': 'gemini-2.5-pro',
        'models': ['gemini-2.5-pro', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
    },
    'groq': {
        'default': 'llama-3.3-70b-versatile',
        'models': ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768']
    },
    'openai_router': {
        'default': 'anthropic/claude-3.5-sonnet',
        'models': ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'openai/gpt-4o-mini', 'meta-llama/llama-3.1-70b-instruct']
    }
}