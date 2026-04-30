# AI Startup System - Backend

A production-ready FastAPI backend system for AI-powered startup operations including content writing, social media publishing, and CEO orchestration.

## Project Structure

```
backend/
├── src/                    # Main source code
│   ├── agents/            # AI agent modules
│   │   ├── contentWriter/
│   │   ├── content_writer_v2/
│   │   ├── social_media_publisher/
│   │   └── ceo_*.py       # CEO agent files
│   ├── routes/            # API route handlers
│   ├── services/          # Business logic services
│   └── core/              # Core infrastructure
│       ├── ai_providers/  # AI provider integrations
│       └── config.py      # Configuration
├── tests/                 # Test files
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── assets/                # Static assets
├── server.py              # Main application entry point
├── run_backend.py         # Backend runner
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

## Features

- **AI Agents**: Content writing, social media publishing, CEO orchestration
- **Multiple AI Providers**: Gemini, Groq, OpenAI Router support
- **RESTful API**: FastAPI-based with automatic documentation
- **State Management**: Agent state persistence and management
- **Social Media Integration**: Instagram, Facebook, LinkedIn, Twitter
- **Production Ready**: Comprehensive logging, error handling, CORS

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Server**
   ```bash
   python server.py
   # or
   python run_backend.py
   ```

4. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB connection string | Yes |
| `DB_NAME` | Database name | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Optional |
| `GROQ_API_KEY` | Groq API key | Optional |
| `OPENAI_ROUTER_API_KEY` | OpenAI Router API key | Optional |
| `DEFAULT_AI_PROVIDER` | Default AI provider (gemini/groq/openai_router) | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No |

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Agent Operations
- `POST /agents/{agent_type}` - Execute agent operations
- `GET /agents/{agent_id}/state` - Get agent state
- `POST /agents/{agent_id}/state` - Update agent state

### CEO Operations
- `POST /ceo/orchestrate` - CEO orchestration
- `POST /ceo/requirements` - Requirements gathering
- `POST /ceo/chat` - CEO chat interface

### Content Writing
- `POST /content/write` - Generate content
- `POST /content/v2/write` - Content Writer V2

### Social Media
- `POST /social/publish` - Publish to social media
- `POST /social/instagram` - Instagram specific publishing

## Testing

Run tests using:
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_specific.py

# Run with coverage
python -m pytest tests/ --cov=src
```

## Development

### Code Style
- Use Black for code formatting
- Use isort for import sorting
- Use flake8 for linting
- Use mypy for type checking

### Adding New Agents
1. Create agent module in `src/agents/`
2. Implement agent interface
3. Add routes in `src/routes/`
4. Update configuration
5. Add tests

## Production Deployment

1. **Environment Setup**
   - Set production environment variables
   - Configure MongoDB connection
   - Set up AI provider API keys

2. **Security**
   - Configure CORS origins
   - Set up authentication if needed
   - Enable HTTPS

3. **Monitoring**
   - Configure logging level
   - Set up health checks
   - Monitor API performance

4. **Scaling**
   - Use process managers (PM2, Supervisor)
   - Configure load balancing
   - Set up database clustering

## License

MIT License - see LICENSE file for details.
