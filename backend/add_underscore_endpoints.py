"""Script to add underscore format endpoints for all agents"""

import re

# Define the mapping of hyphenated endpoints to underscore format
endpoint_mappings = [
    ("social-media-publisher", "social_media_publisher", "social_publisher"),
    ("seo-specialist", "seo_specialist", "seo_specialist"),
    ("ad-copywriter", "ad_copywriter", "ad_copywriter"),
    ("analytics-agent", "analytics_agent", "analytics_agent"),
    ("frontend-engineer", "frontend_engineer", "frontend_engineer"),
    ("backend-engineer", "backend_engineer", "backend_engineer"),
    ("devops-agent", "devops_agent", "devops_agent"),
    ("qa-agent", "qa_agent", "qa_agent"),
    ("architect-agent", "architect_agent", "architect_agent"),
    ("lead-researcher", "lead_researcher", "lead_researcher"),
    ("outreach-agent", "outreach_agent", "outreach_agent"),
    ("demo-agent", "demo_agent", "demo_agent"),
    ("negotiator-agent", "negotiator_agent", "negotiator_agent"),
    ("crm-agent", "crm_agent", "crm_agent"),
    ("user-researcher", "user_researcher", "user_researcher"),
    ("pm-agent", "pm_agent", "pm_agent"),
    ("designer-agent", "designer_agent", "designer_agent"),
    ("roadmap-agent", "roadmap_agent", "roadmap_agent"),
    ("feedback-agent", "feedback_agent", "feedback_agent")
]

# Generate the additional endpoints code
additional_endpoints = []

for hyphen_endpoint, underscore_endpoint, agent_id in endpoint_mappings:
    if hyphen_endpoint != underscore_endpoint:
        # Generate function name from underscore endpoint
        func_name = f"execute_{underscore_endpoint}_underscore"
        
        endpoint_code = f'''@agent_router.post("/{underscore_endpoint}", response_model=AgentExecutionResponse)
async def {func_name}(req: AgentExecutionRequest, request: Request):
    """Execute {agent_id.replace('_', ' ').title()} Agent (underscore format)."""
    return await execute_agent("{agent_id}", req, request)
'''
        additional_endpoints.append(endpoint_code)

# Print the code to be added
print("# Additional underscore format endpoints to add after the existing endpoints:\n")
for endpoint in additional_endpoints:
    print(endpoint)

print("\n# Total additional endpoints:", len(additional_endpoints))