"""Simple test to verify Groq model update"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print(f"Python path: {sys.path[0]}")
print(f"Current directory: {os.getcwd()}")

# Check if .env file exists
env_file = backend_dir / '.env'
print(f".env file exists: {env_file.exists()}")

# Try to import the modules
try:
    from src.agents.ceo.ceo_ai_task_analyzer import ceo_ai_task_analyzer
    print(f"Successfully imported ceo_ai_task_analyzer")
    print(f"Current Groq model: {ceo_ai_task_analyzer.groq_model}")
    
    # Check if the model was updated
    if ceo_ai_task_analyzer.groq_model == "llama-3.3-70b-versatile":
        print("✓ SUCCESS: Groq model has been updated to llama-3.3-70b-versatile")
    else:
        print(f"✗ ERROR: Groq model is still {ceo_ai_task_analyzer.groq_model}")
        
except ImportError as e:
    print(f"Failed to import ceo_ai_task_analyzer: {e}")
    
# Check the actual file content
try:
    analyzer_file = backend_dir / 'src' / 'agents' / 'ceo' / 'ceo_ai_task_analyzer.py'
    if analyzer_file.exists():
        with open(analyzer_file, 'r') as f:
            content = f.read()
            if 'llama-3.3-70b-versatile' in content:
                print("✓ File contains the updated model name")
            else:
                print("✗ File does not contain the updated model name")
                # Find what model is actually in the file
                for line in content.split('\n'):
                    if 'groq_model' in line and '=' in line:
                        print(f"Found line: {line.strip()}")
except Exception as e:
    print(f"Error checking file: {e}")
