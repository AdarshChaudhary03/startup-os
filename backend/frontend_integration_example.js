/**
 * Frontend Integration Example for Separate Agent Endpoints
 * 
 * This example shows how the frontend should integrate with the new
 * separate agent endpoints architecture for real-time progress tracking.
 */

class AgentOrchestrator {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.currentExecution = null;
    }

    /**
     * Execute a task with real-time progress tracking
     * @param {string} task - The task to execute
     * @param {function} onProgress - Progress callback function
     * @param {function} onStepComplete - Step completion callback
     * @param {function} onError - Error callback
     * @returns {Promise<Object>} Final execution result
     */
    async executeTask(task, onProgress, onStepComplete, onError) {
        try {
            // Step 1: Get orchestration plan
            onProgress && onProgress({
                stage: 'planning',
                message: 'Getting orchestration plan...',
                progress: 0
            });

            const plan = await this.getOrchestrationPlan(task);
            
            if (!plan || !plan.steps || plan.steps.length === 0) {
                throw new Error('No orchestration plan received');
            }

            onProgress && onProgress({
                stage: 'planning_complete',
                message: `Plan ready: ${plan.steps.length} agents in ${plan.mode} mode`,
                progress: 10,
                plan: plan
            });

            // Step 2: Execute each agent in the plan
            const results = [];
            const totalSteps = plan.steps.length;

            for (let i = 0; i < plan.steps.length; i++) {
                const step = plan.steps[i];
                const stepProgress = 10 + ((i / totalSteps) * 80); // 10-90% for execution

                onProgress && onProgress({
                    stage: 'executing',
                    message: `Executing ${step.agent_name}...`,
                    progress: stepProgress,
                    currentStep: i + 1,
                    totalSteps: totalSteps,
                    currentAgent: step.agent_name
                });

                try {
                    const stepResult = await this.executeAgentStep(step);
                    results.push(stepResult);

                    onStepComplete && onStepComplete({
                        stepIndex: i,
                        step: step,
                        result: stepResult,
                        progress: stepProgress + (80 / totalSteps)
                    });

                    // For sequential mode, pass output to next step
                    if (plan.mode === 'sequential' && i < plan.steps.length - 1) {
                        plan.steps[i + 1].context = stepResult.output;
                    }

                } catch (stepError) {
                    onError && onError({
                        stage: 'step_execution',
                        stepIndex: i,
                        step: step,
                        error: stepError.message
                    });
                    throw stepError;
                }
            }

            // Step 3: Completion
            onProgress && onProgress({
                stage: 'complete',
                message: 'All agents completed successfully',
                progress: 100
            });

            return {
                success: true,
                plan: plan,
                results: results,
                primaryOutput: results[0]?.output || '',
                totalDuration: results.reduce((sum, r) => sum + (r.duration_ms || 0), 0)
            };

        } catch (error) {
            onError && onError({
                stage: 'execution_failed',
                error: error.message
            });
            throw error;
        }
    }

    /**
     * Get orchestration plan from CEO agent
     * @param {string} task - The task to plan
     * @returns {Promise<Object>} Orchestration plan
     */
    async getOrchestrationPlan(task) {
        const response = await fetch(`${this.baseUrl}/api/orchestrate/plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Planning failed: ${response.status} ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Execute a single agent step
     * @param {Object} step - The orchestration step
     * @returns {Promise<Object>} Agent execution result
     */
    async executeAgentStep(step) {
        const requestBody = {
            task: step.instruction
        };

        // Add context if available (for sequential execution)
        if (step.context) {
            requestBody.context = step.context;
        }

        const response = await fetch(`${this.baseUrl}${step.endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Agent ${step.agent_name} failed: ${response.status} ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Get list of available agents
     * @returns {Promise<Object>} List of agents with endpoints
     */
    async getAvailableAgents() {
        const response = await fetch(`${this.baseUrl}/api/agents/list`);
        
        if (!response.ok) {
            throw new Error(`Failed to get agents list: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Execute a specific agent directly
     * @param {string} agentId - The agent ID
     * @param {string} task - The task to execute
     * @returns {Promise<Object>} Agent execution result
     */
    async executeSpecificAgent(agentId, task) {
        const endpoint = `/api/agents/${agentId.replace('_', '-')}`;
        
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Agent execution failed: ${response.status} ${errorText}`);
        }

        return await response.json();
    }
}

// Usage Example
class TaskExecutionUI {
    constructor() {
        this.orchestrator = new AgentOrchestrator();
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Example: Handle task submission
        document.getElementById('execute-task-btn')?.addEventListener('click', () => {
            const task = document.getElementById('task-input')?.value;
            if (task) {
                this.executeTaskWithUI(task);
            }
        });
    }

    async executeTaskWithUI(task) {
        const progressBar = document.getElementById('progress-bar');
        const statusText = document.getElementById('status-text');
        const stepsContainer = document.getElementById('steps-container');
        const resultsContainer = document.getElementById('results-container');

        // Clear previous results
        if (stepsContainer) stepsContainer.innerHTML = '';
        if (resultsContainer) resultsContainer.innerHTML = '';

        try {
            const result = await this.orchestrator.executeTask(
                task,
                // Progress callback
                (progress) => {
                    if (progressBar) {
                        progressBar.style.width = `${progress.progress}%`;
                    }
                    if (statusText) {
                        statusText.textContent = progress.message;
                    }
                    console.log('Progress:', progress);
                },
                // Step completion callback
                (stepResult) => {
                    this.addStepToUI(stepResult, stepsContainer);
                    console.log('Step completed:', stepResult);
                },
                // Error callback
                (error) => {
                    console.error('Execution error:', error);
                    if (statusText) {
                        statusText.textContent = `Error: ${error.error}`;
                        statusText.style.color = 'red';
                    }
                }
            );

            // Display final results
            this.displayFinalResults(result, resultsContainer);

        } catch (error) {
            console.error('Task execution failed:', error);
            if (statusText) {
                statusText.textContent = `Failed: ${error.message}`;
                statusText.style.color = 'red';
            }
        }
    }

    addStepToUI(stepResult, container) {
        if (!container) return;

        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-result';
        stepDiv.innerHTML = `
            <div class="step-header">
                <h4>${stepResult.step.agent_name}</h4>
                <span class="step-status ${stepResult.result.success ? 'success' : 'error'}">
                    ${stepResult.result.success ? '✅' : '❌'}
                </span>
            </div>
            <div class="step-details">
                <p><strong>Task:</strong> ${stepResult.step.instruction}</p>
                <p><strong>Output:</strong> ${stepResult.result.output}</p>
                <p><strong>Duration:</strong> ${stepResult.result.duration_ms}ms</p>
            </div>
        `;
        container.appendChild(stepDiv);
    }

    displayFinalResults(result, container) {
        if (!container) return;

        container.innerHTML = `
            <div class="final-results">
                <h3>Execution Complete</h3>
                <p><strong>Mode:</strong> ${result.plan.mode}</p>
                <p><strong>Total Duration:</strong> ${result.totalDuration}ms</p>
                <p><strong>Agents Used:</strong> ${result.results.length}</p>
                <div class="primary-output">
                    <h4>Primary Output:</h4>
                    <p>${result.primaryOutput}</p>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TaskExecutionUI();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AgentOrchestrator, TaskExecutionUI };
}
