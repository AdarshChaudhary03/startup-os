
# Backend API Endpoints Test Report

Generated at: 2026-05-01T11:52:11.977922

## Summary
- Total Endpoints Tested: 13
- Successful Tests: 3
- Failed Tests: 10
- Success Rate: 23.1%

## Detailed Results

### Successful Endpoints
- **GET /api/teams**
  - Status Code: 200
  - Response Time: 0.004s

- **GET /api/ceo/chat/sessions**
  - Status Code: 200
  - Response Time: 0.003s

- **POST /api/ceo/simplified/process**
  - Status Code: 200
  - Response Time: 3.100s

### Failed Endpoints
- **GET /health**
  - Error: HTTP 307: 

- **GET /api/agents**
  - Error: HTTP 404: {"detail":"Not Found"}

- **GET /api/agents/status**
  - Error: HTTP 404: {"detail":"Not Found"}

- **POST /api/ceo/chat/start**
  - Error: HTTP 500: {"error":{"code":"HTTP_500","message":"'CEOConversationFlow' object has no attribute 'get_initial_questions'","timestamp":"2026-05-01T06:22:08.824111","path":"/api/ceo/chat/start"}}

- **POST /api/ceo/requirements/gather**
  - Error: HTTP 404: {"detail":"Not Found"}

- **POST /api/orchestrate**
  - Error: HTTP 422: {"detail":[{"type":"missing","loc":["body","task"],"msg":"Field required","input":{"directive":"Test orchestration"},"url":"https://errors.pydantic.dev/2.12/v/missing"}]}

- **GET /api/orchestration/status**
  - Error: HTTP 404: {"detail":"Not Found"}

- **POST /api/ceo/orchestrate**
  - Error: HTTP 422: {"detail":[{"type":"missing","loc":["body","task"],"msg":"Field required","input":{"directive":"Test CEO orchestration"},"url":"https://errors.pydantic.dev/2.12/v/missing"}]}

- **POST /api/agents/content_writer_v2/execute**
  - Error: HTTP 404: {"detail":"Not Found"}

- **POST /api/agents/social_media_publisher/execute**
  - Error: HTTP 404: {"detail":"Not Found"}

## Recommendations
1. Investigate and fix the failed endpoints listed above
2. Check server logs for detailed error information
3. Ensure all required services and dependencies are running
4. Verify API authentication and authorization if applicable
