# Frontend Integration Guide for Separated Orchestration

## Overview
This guide shows how to integrate the new separated orchestration workflow in your frontend application for real-time agent execution tracking.

## Key Changes

### Before (Legacy)
```javascript
// Single request that executes all agents
const response = await fetch('/api/orchestrate', {
  method: 'POST',
  body: JSON.stringify({ task: 'Write an Instagram caption' })
});
const result = await response.json();
// User waits for entire process to complete
```

### After (Separated)
```javascript
// 1. Get execution plan
const planResponse = await fetch('/api/orchestrate', {
  method: 'POST',
  body: JSON.stringify({ task: 'Write an Instagram caption' })
});
const plan = await planResponse.json();

// 2. Execute agents individually with real-time updates
for (const step of plan.steps) {
  updateUI(`Executing ${step.agent_name}...`);
  
  const agentResponse = await fetch(step.endpoint, {
    method: 'POST',
    body: JSON.stringify({ task: step.instruction })
  });
  const result = await agentResponse.json();
  
  updateUI(`${step.agent_name} completed: ${result.output}`);
}
```

## Complete Implementation Example

### React Component Example
```jsx
import React, { useState, useCallback } from 'react';

const OrchestrationComponent = () => {
  const [task, setTask] = useState('');
  const [plan, setPlan] = useState(null);
  const [results, setResults] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState(null);

  const executeOrchestration = useCallback(async () => {
    if (!task.trim()) return;
    
    setIsExecuting(true);
    setError(null);
    setResults([]);
    setCurrentStep(0);
    
    try {
      // Step 1: Get orchestration plan
      const planResponse = await fetch('/api/orchestrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
      });
      
      if (!planResponse.ok) {
        throw new Error(`Planning failed: ${planResponse.statusText}`);
      }
      
      const orchestrationPlan = await planResponse.json();
      setPlan(orchestrationPlan);
      
      // Step 2: Execute each agent individually
      const agentResults = [];
      
      for (let i = 0; i < orchestrationPlan.steps.length; i++) {
        const step = orchestrationPlan.steps[i];
        setCurrentStep(i + 1);
        
        try {
          const agentResponse = await fetch(step.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              task: step.instruction,
              context: agentResults.length > 0 ? JSON.stringify(agentResults) : null,
              metadata: {
                orchestration_request_id: orchestrationPlan.request_id,
                step_number: i + 1,
                total_steps: orchestrationPlan.steps.length
              }
            })
          });
          
          const agentResult = await agentResponse.json();
          agentResults.push(agentResult);
          setResults([...agentResults]);
          
        } catch (agentError) {
          console.error(`Agent ${step.agent_name} failed:`, agentError);
          agentResults.push({
            agent_id: step.agent_id,
            agent_name: step.agent_name,
            success: false,
            error: agentError.message,
            output: `Execution failed: ${agentError.message}`
          });
          setResults([...agentResults]);
        }
      }
      
    } catch (error) {
      console.error('Orchestration failed:', error);
      setError(error.message);
    } finally {
      setIsExecuting(false);
      setCurrentStep(0);
    }
  }, [task]);

  return (
    <div className="orchestration-component">
      <div className="task-input">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Enter your task here..."
          rows={3}
          disabled={isExecuting}
        />
        <button 
          onClick={executeOrchestration}
          disabled={isExecuting || !task.trim()}
        >
          {isExecuting ? 'Executing...' : 'Execute Task'}
        </button>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {plan && (
        <div className="orchestration-plan">
          <h3>Execution Plan</h3>
          <p><strong>Mode:</strong> {plan.mode}</p>
          <p><strong>Rationale:</strong> {plan.rationale}</p>
          <p><strong>Total Steps:</strong> {plan.total_steps}</p>
          
          <div className="steps">
            {plan.steps.map((step, index) => (
              <div 
                key={step.agent_id}
                className={`step ${
                  index + 1 < currentStep ? 'completed' : 
                  index + 1 === currentStep ? 'active' : 'pending'
                }`}
              >
                <div className="step-header">
                  <span className="step-number">{index + 1}</span>
                  <span className="agent-name">{step.agent_name}</span>
                  <span className="team-name">({step.team_name})</span>
                </div>
                <div className="step-instruction">{step.instruction}</div>
                
                {results[index] && (
                  <div className="step-result">
                    <div className={`status ${results[index].success ? 'success' : 'error'}`}>
                      {results[index].success ? '✅ Completed' : '❌ Failed'}
                    </div>
                    <div className="output">{results[index].output}</div>
                    {results[index].duration_ms && (
                      <div className="duration">Duration: {results[index].duration_ms}ms</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OrchestrationComponent;
```

### CSS Styles
```css
.orchestration-component {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.task-input {
  margin-bottom: 20px;
}

.task-input textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
}

.task-input button {
  margin-top: 10px;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.task-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.orchestration-plan {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 20px;
}

.steps {
  margin-top: 20px;
}

.step {
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.step.pending {
  opacity: 0.6;
}

.step.active {
  border-color: #007bff;
  background: #f8f9fa;
}

.step.completed {
  border-color: #28a745;
  background: #d4edda;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.step-number {
  background: #007bff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.step.completed .step-number {
  background: #28a745;
}

.agent-name {
  font-weight: bold;
}

.team-name {
  color: #666;
  font-size: 0.9em;
}

.step-instruction {
  font-style: italic;
  color: #666;
  margin-bottom: 10px;
}

.step-result {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  border-left: 4px solid #ddd;
}

.step-result .status.success {
  color: #28a745;
  font-weight: bold;
}

.step-result .status.error {
  color: #dc3545;
  font-weight: bold;
}

.step-result .output {
  margin: 10px 0;
  white-space: pre-wrap;
}

.step-result .duration {
  font-size: 0.8em;
  color: #666;
}
```

## Advanced Features

### Parallel Execution
```javascript
// For parallel mode, execute agents concurrently
if (plan.mode === 'parallel') {
  const agentPromises = plan.steps.map(async (step, index) => {
    setCurrentStep(index + 1);
    
    const response = await fetch(step.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task: step.instruction })
    });
    
    return await response.json();
  });
  
  const agentResults = await Promise.allSettled(agentPromises);
  setResults(agentResults.map(result => 
    result.status === 'fulfilled' ? result.value : { error: result.reason }
  ));
}
```

### Error Recovery
```javascript
const retryFailedAgent = async (stepIndex) => {
  const step = plan.steps[stepIndex];
  
  try {
    const response = await fetch(step.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task: step.instruction })
    });
    
    const result = await response.json();
    
    // Update results array
    const newResults = [...results];
    newResults[stepIndex] = result;
    setResults(newResults);
    
  } catch (error) {
    console.error('Retry failed:', error);
  }
};
```

### Progress Tracking
```javascript
const calculateProgress = () => {
  if (!plan || !results) return 0;
  return Math.round((results.length / plan.total_steps) * 100);
};

// In component render
<div className="progress-bar">
  <div 
    className="progress-fill" 
    style={{ width: `${calculateProgress()}%` }}
  />
</div>
```

## Benefits Summary

1. **Real-time Updates**: Users see progress as each agent completes
2. **Better Error Handling**: Individual agent failures don't stop the entire process
3. **Retry Capability**: Failed agents can be retried without restarting
4. **Parallel Execution**: Agents can run concurrently when plan allows
5. **Improved UX**: Better user experience with live feedback
6. **Scalability**: Individual agents can be scaled independently

## Migration Checklist

- [ ] Update API calls to use `/api/orchestrate` for planning
- [ ] Implement individual agent execution loop
- [ ] Add real-time progress tracking UI
- [ ] Implement error handling for individual agents
- [ ] Add retry functionality for failed agents
- [ ] Update loading states and user feedback
- [ ] Test with different orchestration modes (single, sequential, parallel)
- [ ] Add fallback to legacy endpoint if needed