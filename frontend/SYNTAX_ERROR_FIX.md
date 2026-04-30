# Syntax Error Fix in apiLogger.js

## Issue
SyntaxError at line 95 in apiLogger.js: Unexpected token

## Root Cause
Missing closing brace in the try-catch block for JSON parsing. The catch block was missing its closing brace, causing a syntax error.

## Fix Applied
```javascript
// Before (incorrect):
try {
  responseData = await responseClone.json();
} catch (e) {
// Response might not be JSON
responseData = await responseClone.text();
}

// After (fixed):
try {
  responseData = await responseClone.json();
} catch (e) {
  // Response might not be JSON
  responseData = await responseClone.text();
}
}
```

## Impact
- Fixed the syntax error that was preventing the frontend from building
- Restored proper error handling for non-JSON responses
- API logging functionality now works correctly

## Testing
1. Restart the frontend development server
2. The build error should be resolved
3. API logging should work properly for both JSON and non-JSON responses