@echo off
REM Script to run the agent execution tests on Windows

echo Running Agent Execution Tests...
echo ================================

REM Navigate to frontend directory
cd /d "%~dp0"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Run the specific test file
echo.
echo Running test_agent_execution.js...
call npm test -- src/__tests__/test_agent_execution.js --verbose

REM Check test results
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ All tests passed successfully!
    echo.
    echo The TypeError fix has been validated:
    echo - executeAgent function now correctly accesses the store
    echo - Session management works properly
    echo - Agent execution flow is functioning
    echo - Content Writer to Social Publisher integration is working
) else (
    echo.
    echo ❌ Some tests failed. Please review the output above.
    exit /b 1
)

echo.
echo ================================
echo Test execution complete.
