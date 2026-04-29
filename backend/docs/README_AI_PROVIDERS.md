# AI Providers - Pluggable Architecture

This document explains the new pluggable AI architecture that allows you to easily switch between different AI providers like Gemini, Groq, OpenAI Router, and others.

## Overview

The AI provider system has been refactored to support multiple AI models in a plug-and-play manner. You can now:

- Use multiple AI providers simultaneously
- Switch between providers without code changes
- Add new providers easily
- Configure different models for different use cases

## Supported Providers

### 1. Gemini (Google AI)
- **Models**: gemini-2.5-pro, gemini-1.5-pro, gemini-1.5-flash, gemini-pro
- **Setup**: Get API key from [Google AI Studio](https://aistudio.google.com/)
- **Environment Variable**: `GEMINI_API_KEY`

### 2. Groq
- **Models**: llama-3.3-70b-versatile, llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
- **Setup**: Get API key from [Groq Console](https://console.groq.com/)
- **Environment Variable**: `GROQ_API_KEY`

### 3. OpenAI Router
- **Models**: anthropic/claude-3.5-sonnet, openai/gpt-4o, openai/gpt-4o-mini, meta-llama/llama-3.1-70b-instruct
- **Setup**: Get API key from [OpenRouter](https://openrouter.ai/)
- **Environment Variable**: `OPENAI_ROUTER_API_KEY`

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Configure at least one provider
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENAI_ROUTER_API_KEY=your_openai_router_api_key_here

# Set default provider
DEFAULT_AI_PROVIDER=gemini
```

### Provider Priority

The system will initialize providers based on available API keys. The default provider is determined by:

1. `DEFAULT_AI_PROVIDER` environment variable
2. First successfully initialized provider

## API Endpoints

### Get Provider Information
```http
GET /api/ai/providers
```

Returns information about all configured providers, their models, and health status.

### Switch Default Provider
```http
POST /api/ai/providers/switch
Content-Type: application/json

{
  "provider_name": "groq"
}
```

### Generate Content
```http
POST /api/ai/generate
Content-Type: application/json

{
  "prompt": "Explain quantum computing",
  "provider": "gemini",
  "model": "gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

### Check Provider Health
```http
GET /api/ai/providers/health
```

### Test Provider
```http
GET /api/ai/test?provider=groq&model=llama-3.3-70b-versatile&prompt=Hello
```

## Usage in Code

### Using the AI Service

```python
from ai_service import ai_service

# Generate content with default provider
response = await ai_service.generate_content(
    prompt="Write a short story",
    temperature=0.8
)

# Generate content with specific provider
response = await ai_service.generate_content(
    prompt="Write a short story",
    provider_name="groq",
    model="llama-3.3-70b-versatile"
)

# Check provider health
health = await ai_service.health_check()
print(f"Provider health: {health}")
```

### Using Provider Context

```python
from ai_service import ai_service

async with ai_service.provider_context("gemini") as provider:
    response = await provider.generate_content(
        prompt="Explain AI",
        model="gemini-2.5-pro"
    )
```

## Adding New Providers

### Step 1: Create Provider Class

Create a new provider class in `ai_providers/` that inherits from `BaseAIProvider`:

```python
from .base import BaseAIProvider, AIResponse

class NewProvider(BaseAIProvider):
    @property
    def provider_name(self) -> str:
        return "new_provider"
    
    @property
    def supported_models(self) -> List[str]:
        return ["model-1", "model-2"]
    
    async def initialize(self) -> None:
        # Initialize your provider client
        pass
    
    async def generate_content(self, prompt: str, model: str = None, **kwargs) -> AIResponse:
        # Implement content generation
        pass
    
    async def health_check(self) -> bool:
        # Implement health check
        pass
```

### Step 2: Register Provider

Add your provider to the factory in `ai_providers/factory.py`:

```python
from .new_provider import NewProvider

class AIProviderFactory:
    _providers: Dict[str, Type[BaseAIProvider]] = {
        # ... existing providers
        "new_provider": NewProvider,
    }
```

### Step 3: Update Configuration

Add model configuration in `config.py`:

```python
AI_PROVIDER_MODELS = {
    # ... existing providers
    'new_provider': {
        'default': 'model-1',
        'models': ['model-1', 'model-2']
    }
}
```

### Step 4: Update Initialization

Add initialization logic in `ai_startup.py`:

```python
# Add environment variable
NEW_PROVIDER_API_KEY = os.environ.get('NEW_PROVIDER_API_KEY')

# Add initialization in initialize_ai_providers()
if NEW_PROVIDER_API_KEY:
    await ai_service.add_provider(
        name="new_provider",
        provider_type="new_provider",
        api_key=NEW_PROVIDER_API_KEY,
        is_default=(DEFAULT_AI_PROVIDER == "new_provider")
    )
```

## Migration from Legacy Code

The legacy `ceo_plan_with_llm` function still works but now uses the new architecture. For new code, use:

```python
from ai_startup import ceo_plan_with_llm_new

# New implementation with provider selection
plan = await ceo_plan_with_llm_new(
    task="Create a marketing strategy",
    session_id="session_123",
    provider_name="groq",
    model="llama-3.3-70b-versatile"
)
```

## Error Handling

The system includes comprehensive error handling:

- `ProviderInitializationError`: Provider failed to initialize
- `ModelNotSupportedError`: Requested model not available
- `ContentGenerationError`: Content generation failed
- `APIKeyError`: Invalid or missing API key
- `RateLimitError`: API rate limit exceeded

## Best Practices

1. **Always configure at least one provider** - The system needs at least one working provider
2. **Use environment variables** - Never hardcode API keys
3. **Handle errors gracefully** - Providers may fail, implement fallbacks
4. **Monitor provider health** - Use health checks to ensure reliability
5. **Choose appropriate models** - Different models have different strengths and costs

## Troubleshooting

### No Providers Available
- Check that at least one API key is configured
- Verify API keys are valid
- Check network connectivity

### Provider Initialization Failed
- Verify API key format
- Check provider service status
- Review logs for specific error messages

### Content Generation Failed
- Check if model is supported by provider
- Verify prompt length limits
- Check API quotas and rate limits

## Performance Considerations

- **Provider Selection**: Choose providers based on latency, cost, and model capabilities
- **Model Selection**: Larger models are more capable but slower and more expensive
- **Caching**: Consider implementing response caching for repeated queries
- **Rate Limiting**: Implement client-side rate limiting to avoid API limits

## Security

- Store API keys securely using environment variables
- Never commit API keys to version control
- Use HTTPS for all API communications
- Implement proper input validation and sanitization
- Monitor API usage for unusual patterns
