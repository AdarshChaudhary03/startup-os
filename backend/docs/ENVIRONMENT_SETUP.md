# Content Writer v2 - Environment Setup Guide

## 🔧 Prerequisites

### Required Environment Variables

```bash
# AI Provider Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
OPENAI_API_KEY=sk_your_openai_api_key_here  # Optional, for OpenAI Router

# Content Writer v2 Configuration
CONTENT_WRITER_PROVIDER=groq
CONTENT_WRITER_MODEL=llama-3.1-70b-versatile
CONTENT_WRITER_TEMPERATURE=0.7

# Brand Configuration (Optional)
BRAND_NAME="Your Brand Name"
BRAND_VOICE="Professional yet approachable, friendly and helpful"
TARGET_AUDIENCE="Tech-savvy millennials and professionals"

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_ORCHESTRATION_LOGGING=true
```

### Create .env File

```bash
# Navigate to backend directory
cd startup-os/backend

# Create .env file
cat > .env << 'EOF'
# AI Provider Settings
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
CONTENT_WRITER_PROVIDER=groq
CONTENT_WRITER_MODEL=llama-3.1-70b-versatile
CONTENT_WRITER_TEMPERATURE=0.7

# Brand Settings
BRAND_NAME="Startup OS"
BRAND_VOICE="Innovative, professional, and user-focused"
TARGET_AUDIENCE="Entrepreneurs, developers, and business professionals"

# Logging
LOG_LEVEL=INFO
ENABLE_ORCHESTRATION_LOGGING=true
EOF
```

## 📦 Dependencies

### Python Dependencies

Add to `requirements.txt`:

```txt
# Existing dependencies...

# Content Writer v2 Dependencies
groq>=0.4.0
openai>=1.0.0
aiohttp>=3.8.0
pydantic>=2.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_`)

### 2. Configure Environment

```bash
# Set Groq API key
export GROQ_API_KEY="gsk_your_actual_key_here"

# Verify it's set
echo $GROQ_API_KEY
```

### 3. Test Configuration

```python
# Test script: test_setup.py
import asyncio
import os
from content_writer_v2.main_agent import ContentWriterMainAgent
from content_writer_v2.config import DEFAULT_CONFIG

async def test_setup():
    print("Testing Content Writer v2 setup...")
    
    # Check environment variables
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        print("❌ GROQ_API_KEY not set")
        return
    
    if not groq_key.startswith('gsk_'):
        print("❌ Invalid GROQ_API_KEY format")
        return
    
    print("✅ GROQ_API_KEY configured")
    
    try:
        # Initialize main agent
        agent = ContentWriterMainAgent(DEFAULT_CONFIG)
        await agent.initialize()
        print("✅ Content Writer v2 Main Agent initialized")
        
        # Test content generation
        result = await agent.generate_content(
            task="Write a short Instagram caption about coffee",
            request_id="test_setup"
        )
        
        print("✅ Content generation test successful")
        print(f"Generated content preview: {result['content'][:100]}...")
        print(f"Category used: {result.get('category_used', 'unknown')}")
        print(f"Sub-agent used: {result.get('sub_agent_used', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return
    
    print("\n🎉 Content Writer v2 setup complete and working!")

if __name__ == "__main__":
    asyncio.run(test_setup())
```

Run the test:

```bash
python test_setup.py
```

## 🔍 Verification Steps

### 1. Check File Structure

```bash
# Verify Content Writer v2 files exist
ls -la content_writer_v2/
# Should show: __init__.py, main_agent.py, factory.py, config.py, sub_agents/, README.md

ls -la content_writer_v2/sub_agents/
# Should show: __init__.py, base.py, social_media.py, blog.py, script.py, marketing.py, technical.py
```

### 2. Test Imports

```python
# Test all imports
python -c "
from content_writer_v2.main_agent import ContentWriterMainAgent
from content_writer_v2.config import DEFAULT_CONFIG
from content_writer_v2.factory import ContentAgentFactory
from content_writer_v2.sub_agents import SocialMediaAgent, BlogAgent
print('✅ All imports successful')
"
```

### 3. Test AI Provider

```python
# Test Groq provider
python -c "
import asyncio
from ai_providers.groq_provider import GroqProvider

async def test():
    provider = GroqProvider()
    health = await provider.health_check()
    print(f'Groq provider health: {health}')

asyncio.run(test())
"
```

### 4. Test Server Integration

```bash
# Start the server
python server.py

# In another terminal, test the API
curl --location 'http://localhost:8000/api/orchestrate' \
--header 'Content-Type: application/json' \
--data '{
    "task": "Write an Instagram caption for a beautiful sunset"
}'
```

## 🐛 Common Issues & Solutions

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'content_writer_v2'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd startup-os/backend

# Check Python path
python -c "import sys; print(sys.path)"

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: API Key Errors

**Error**: `AIProviderError: Failed to initialize groq provider`

**Solutions**:
```bash
# Check API key is set
echo $GROQ_API_KEY

# Check API key format (should start with 'gsk_')
echo $GROQ_API_KEY | head -c 10

# Test API key manually
curl -H "Authorization: Bearer $GROQ_API_KEY" \
     "https://api.groq.com/openai/v1/models"
```

### Issue 3: Configuration Issues

**Error**: Configuration not loading properly

**Solution**:
```python
# Test configuration loading
from content_writer_v2.config import DEFAULT_CONFIG
print(f"Provider: {DEFAULT_CONFIG.ai_provider.provider}")
print(f"Model: {DEFAULT_CONFIG.ai_provider.model}")
print(f"Brand: {DEFAULT_CONFIG.brand_name}")
```

### Issue 4: Logging Issues

**Error**: No logs appearing

**Solution**:
```bash
# Create logs directory
mkdir -p logs

# Check logging configuration
python -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('content_writer_v2')
logger.info('Test log message')
"
```

## 🔧 Advanced Configuration

### Custom AI Provider Settings

```python
# Custom configuration
from content_writer_v2.config import ContentWriterV2Config, AIProviderConfig

custom_config = ContentWriterV2Config(
    ai_provider=AIProviderConfig(
        provider="groq",
        model="llama-3.1-70b-versatile",
        temperature=0.8,  # Higher creativity
        max_tokens=3000   # Longer content
    ),
    brand_name="My Custom Brand",
    brand_voice="Casual and friendly"
)

agent = ContentWriterMainAgent(custom_config)
```

### Platform-Specific Configuration

```python
# Instagram-optimized configuration
from content_writer_v2.config import INSTAGRAM_CONFIG

instagram_agent = ContentWriterMainAgent(INSTAGRAM_CONFIG)

# LinkedIn-optimized configuration
from content_writer_v2.config import LINKEDIN_CONFIG

linkedin_agent = ContentWriterMainAgent(LINKEDIN_CONFIG)
```

### Environment-Based Configuration

```bash
# Development environment
export CONTENT_WRITER_TEMPERATURE=0.9
export CONTENT_WRITER_MODEL=llama-3.1-8b-instant

# Production environment
export CONTENT_WRITER_TEMPERATURE=0.7
export CONTENT_WRITER_MODEL=llama-3.1-70b-versatile
```

## 📊 Monitoring & Observability

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
export ENABLE_ORCHESTRATION_LOGGING=true
```

### Monitor Performance

```python
# Performance monitoring script
import time
import asyncio
from content_writer_v2.main_agent import ContentWriterMainAgent
from content_writer_v2.config import DEFAULT_CONFIG

async def performance_test():
    agent = ContentWriterMainAgent(DEFAULT_CONFIG)
    await agent.initialize()
    
    tasks = [
        "Write an Instagram caption about coffee",
        "Write a blog post about AI",
        "Create a reel script about fitness"
    ]
    
    for task in tasks:
        start_time = time.time()
        result = await agent.generate_content(task=task, request_id=f"perf_test_{time.time()}")
        end_time = time.time()
        
        print(f"Task: {task[:30]}...")
        print(f"Duration: {end_time - start_time:.2f}s")
        print(f"Content length: {len(result['content'])} chars")
        print(f"Sub-agent: {result.get('sub_agent_used', 'unknown')}")
        print("---")

asyncio.run(performance_test())
```

## ✅ Production Readiness Checklist

- [ ] ✅ GROQ_API_KEY configured and valid
- [ ] ✅ All dependencies installed
- [ ] ✅ Content Writer v2 files in place
- [ ] ✅ Import tests passing
- [ ] ✅ AI provider health check passing
- [ ] ✅ Orchestrate API returning real content
- [ ] ✅ Logging configured and working
- [ ] ✅ Error handling tested
- [ ] ✅ Performance benchmarks met
- [ ] ✅ Environment variables documented
- [ ] ✅ Backup API keys available
- [ ] ✅ Monitoring and alerting configured

---

**Environment Setup Complete** ✅  
**Ready for Development** 🚀  
**Production Ready** 🎉