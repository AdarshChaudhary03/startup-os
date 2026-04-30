# AI Startup System - Backend

A FastAPI-based backend server for the AI Startup System that orchestrates specialist agents across multiple teams (Marketing, Engineering, Sales, Product) with comprehensive logging and debugging capabilities.

## Features

- **Multi-Agent Orchestration**: CEO agent that routes tasks to 20+ specialist agents
- **Team-Based Organization**: 4 core teams with specialized agents
- **LLM Integration**: Gemini API integration for intelligent task routing
- **MongoDB Integration**: Async database operations with Motor
- **CORS Support**: Cross-origin requests for frontend integration
- **Comprehensive Logging**: Structured JSON logging for API requests and orchestration tracking
- **Orchestration Debugging**: Built-in tools to analyze and debug multi-agent vs single-agent patterns
- **Environment Configuration**: Flexible configuration via environment variables

## Prerequisites

- Python 3.8+
- MongoDB (local or remote)
- Gemini API key

## Installation

1. **Clone and navigate to the backend directory:**
   ```bash
   cd startup-os/backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   
   **On Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment Configuration

1. **Edit `.env` with your configuration:**
   ```env
   # Database Configuration
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=startup_ai_db
   
   # API Keys
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # CORS Configuration
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   
   # Server Configuration
   HOST=127.0.0.1
   PORT=8000
   DEBUG=false
   ```

2. **Get a Gemini API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Replace `your_gemini_api_key_here` with your actual API key

## Database Setup

1. **Install MongoDB:**
   - **Windows/macOS**: Download from [MongoDB Community Server](https://www.mongodb.com/try/download/community)
   - **Ubuntu/Debian**: 
     ```bash
     sudo apt-get install mongodb
     ```
   - **macOS with Homebrew**:
     ```bash
     brew install mongodb-community
     ```

2. **Start MongoDB:**
   - **Windows**: MongoDB should start automatically after installation
   - **macOS/Linux**:
     ```bash
     sudo systemctl start mongod
     # or
     brew services start mongodb-community
     ```

3. **Verify MongoDB is running:**
   ```bash
   mongosh --eval "db.runCommand('ping')"
   ```

## Running the Server

### Option 1: Enhanced Runner (Recommended)
```bash
python run_backend.py
```
This provides enhanced logging setup, environment validation, and debugging information.

### Option 2: Direct Server Start
```bash
python server.py
```

### Option 3: Using uvicorn
```bash
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

The server will start on `http://127.0.0.1:8000`

## Logging System

The backend includes a comprehensive logging system that automatically tracks all API requests and orchestration events.

### Log Files (created in `logs/` directory)
- **`app.log`** - General application logs with rotation (10MB, 5 backups)
- **`api_requests.log`** - Structured JSON logs of all API requests/responses (50MB, 10 backups)
- **`orchestration.log`** - Detailed orchestration tracking for debugging multi-agent issues (25MB, 7 backups)
- **`errors.log`** - Error-only logs (10MB, 5 backups)

### Logged Information
- **API Requests**: Method, endpoint, status code, duration, IP address, user agent, request ID
- **Orchestration Events**: Agent selection, planning mode (single/sequential/parallel), LLM vs fallback routing, execution timeline
- **Error Tracking**: Detailed error context with request IDs for tracing
- **Performance Metrics**: Response times, agent execution duration, planning time

## Debugging Orchestration Issues

### Problem: System suggesting only single agents instead of multiple agents

Use the built-in orchestration analyzer to identify patterns and debug issues:

```bash
# Analyze last 24 hours of orchestration logs
python orchestration_analyzer.py

# Analyze last 48 hours
python orchestration_analyzer.py --hours 48

# Use custom log directory
python orchestration_analyzer.py --log-dir /path/to/logs
```

### Real-time Monitoring

```bash
# Monitor live orchestration events
tail -f logs/orchestration.log

# Monitor API requests
tail -f logs/api_requests.log

# Monitor errors only
tail -f logs/errors.log
```

### Log Analysis Commands

```bash
# Count orchestration modes in last 100 requests
tail -n 100 logs/orchestration.log | grep "plan_finalized" | jq '.orchestration_mode' | sort | uniq -c

# Find LLM planning failures
grep "llm_planning_failed" logs/orchestration.log | jq '.message'

# Check agent usage distribution
grep "agent_execution_start" logs/orchestration.log | jq '.agent_id' | sort | uniq -c

# Analyze response times
grep "API Response" logs/api_requests.log | jq '.duration_ms' | awk '{sum+=$1; count++} END {print "Avg:", sum/count "ms"}'
```

## API Endpoints

Once the server is running, you can access:

- **API Root**: http://localhost:8000/api/
- **Teams Endpoint**: http://localhost:8000/api/teams
- **Orchestrate Endpoint**: http://localhost:8000/api/orchestrate
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### Request/Response Tracking
All API requests include a unique `X-Request-ID` header for tracing requests through logs.

## Testing the API

**Test the root endpoint:**
```bash
curl http://localhost:8000/api/
```

**Test the teams endpoint:**
```bash
curl http://localhost:8000/api/teams
```

**Test task orchestration:**
```bash
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a blog post about AI agents"}'
```

**Test with specific agent:**
```bash
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a blog post about AI agents", "agent_id": "content_writer"}'
```

## Project Structure

```
backend/
├── server.py                    # Main FastAPI application with logging
├── logging_config.py           # Logging configuration and utilities
├── middleware.py               # API logging and orchestration middleware
├── orchestration_analyzer.py   # Orchestration debugging tool
├── run_backend.py              # Enhanced server runner
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── README.md                   # This file
├── logs/                       # Log files directory (auto-created)
│   ├── app.log
│   ├── api_requests.log
│   ├── orchestration.log
│   └── errors.log
└── venv/                       # Virtual environment
```

## Available Teams & Agents

### Marketing Team
- Content Writer
- Social Media Publisher
- SEO Specialist
- Ad Copywriter
- Analytics Agent

### Engineering Team
- Frontend Engineer
- Backend Engineer
- DevOps Agent
- QA Agent
- Architect Agent

### Sales Team
- Lead Researcher
- Outreach Agent
- Demo Agent
- Negotiator
- CRM Agent

### Product Team
- User Researcher
- PM Agent
- Designer Agent
- Roadmap Agent
- Feedback Agent

## Environment Variables

- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name
- `GEMINI_API_KEY` - Google Gemini API key for LLM functionality
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins
- `HOST` - Server host (default: 127.0.0.1)
- `PORT` - Server port (default: 8000)
- `DEBUG` - Enable debug mode (default: false)

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError"**:
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **"Connection refused" (MongoDB)**:
   - Ensure MongoDB is running
   - Check MONGO_URL in .env file

3. **"Invalid API key" (Gemini)**:
   - Verify GEMINI_API_KEY in .env file
   - Ensure API key is valid and active

4. **CORS errors**:
   - Check CORS_ORIGINS in .env file
   - Ensure frontend URL is included

### Orchestration Debugging

#### High Single-Agent Bias (>80% single-agent requests)
1. Review LLM prompt in `CEO_SYSTEM_PROMPT`
2. Check if tasks are complex enough for multi-agent handling
3. Verify agent skill definitions aren't too narrow
4. Analyze task patterns in orchestration logs

#### High Fallback Usage (LLM planning frequently fails)
1. Check Gemini API connectivity and rate limits
2. Review JSON parsing in `_extract_json()` function
3. Monitor `llm_planning_failed` events in orchestration logs
4. Verify API key permissions and quotas

#### Performance Issues
1. Check log file sizes and rotation settings
2. Monitor API response times in `api_requests.log`
3. Analyze agent execution duration patterns
4. Review database connection pooling

### Log Analysis

Use the orchestration analyzer for comprehensive debugging:

```bash
# Get detailed analysis report
python orchestration_analyzer.py

# Check for specific patterns
grep "single_agent_bias" logs/orchestration_analysis_*.txt
```

## Development

**Install development dependencies:**
```bash
pip install pytest black isort flake8 mypy
```

**Run tests:**
```bash
pytest
```

**Format code:**
```bash
black .
isort .
```

**Lint code:**
```bash
flake8 .
mypy .
```

### Adding New Logging Events

```python
from logging_config import log_orchestration_event

log_orchestration_event(
    request_id=request_id,
    event_type="custom_event",
    message="Custom event description",
    additional_data={"key": "value"}
)
```

### Custom Log Analysis

Extend `orchestration_analyzer.py` to add custom analysis patterns for your specific debugging needs.

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests and linting
4. Test logging functionality
5. Submit a pull request

## License

This project is part of the AI Startup System.