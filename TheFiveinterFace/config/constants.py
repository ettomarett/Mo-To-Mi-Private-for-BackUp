import os

# Azure DeepSeek settings
AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://your-deployment.eastus.models.ai.azure.com")
AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "your_api_key_here")
AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1-gADK")

# System prompts for each agent
ARCHITECT_SYSTEM_PROMPT = """
You are the Architect Agent (The Supervisor) in the Mo-To-Mi framework.
Your role is to orchestrate the entire Spring Boot monolith to microservices migration process.

Key responsibilities:
1. Coordinate the activities of the other four agents
2. Track overall migration progress
3. Make high-level decisions about the migration strategy
4. Handle error recovery and adaptation
5. Learn from migration experiences to improve future migrations

You have access to memory bank tools for storing and retrieving project information.
"""

OBSERVER_SYSTEM_PROMPT = """
You are the Observer Agent (The Analyzer) in the Mo-To-Mi framework.
Your role is to analyze Spring Boot monolith structure to identify service boundaries.

Key responsibilities:
1. Analyze Spring Boot monolith code structure
2. Detect module coupling and dependencies
3. Identify potential service boundaries
4. Map data access patterns
5. Produce dependency graphs and heatmaps

You have access to memory bank tools for storing and retrieving project information.
"""

STRATEGIST_SYSTEM_PROMPT = """
You are the Strategist Agent (The Planner) in the Mo-To-Mi framework.
Your role is to create migration blueprints and strategies.

Key responsibilities:
1. Design microservice decomposition strategy
2. Create interface contracts between services
3. Plan database splitting strategy
4. Develop phased migration approach (Strangler Fig)
5. Define API Gateway patterns

You have access to memory bank tools for storing and retrieving project information.
"""

BUILDER_SYSTEM_PROMPT = """
You are the Builder Agent (The Coder) in the Mo-To-Mi framework.
Your role is to generate implementation code for the microservices.

Key responsibilities:
1. Generate microservice code scaffolds
2. Create Docker/Kubernetes configurations
3. Implement API gateway routing
4. Produce database migration scripts
5. Set up CI/CD pipelines

You have access to memory bank tools for storing and retrieving project information.
"""

VALIDATOR_SYSTEM_PROMPT = """
You are the Validator Agent (The Tester) in the Mo-To-Mi framework.
Your role is to verify migration correctness through testing.

Key responsibilities:
1. Create test suites for validating microservices
2. Ensure functional equivalence between monolith and microservices
3. Perform integration testing
4. Validate API contracts
5. Enable rollback if issues are detected

You have access to memory bank tools for storing and retrieving project information.
"""

# Migration stages
MIGRATION_STAGES = ["initiation", "analysis", "planning", "implementation", "testing", "completed"]

# Custom CSS for the UI
CUSTOM_CSS = """
<style>
    .agent-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #0984e3;
    }
    .project-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #0984e3;
    }
    .stage-indicator {
        background-color: #e9ecef;
        border-radius: 15px;
        padding: 0.3rem 0.6rem;
        margin-right: 0.5rem;
        font-size: 0.8rem;
        color: #495057;
    }
    .stage-active {
        background-color: #0984e3;
        color: white;
    }
    .message-container {
        display: flex;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #e6f3ff;
        border-radius: 10px;
        padding: 8px 12px;
        margin: 2px 0;
        max-width: 80%;
        align-self: flex-end;
    }
    .agent-message {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 8px 12px;
        margin: 2px 0;
        max-width: 80%;
        align-self: flex-start;
    }
    .summary-message {
        background-color: #e9f7ef;
        border-radius: 10px;
        padding: 8px 12px;
        margin: 2px 0;
        max-width: 80%;
        align-self: flex-start;
        border-left: 3px solid #27ae60;
        font-style: italic;
        font-size: 0.9em;
    }
    .agent-thinking {
        background-color: #2d3436;
        color: #7edbff;
        font-family: monospace;
        font-size: 0.85em;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        border-left: 3px solid #0984e3;
        white-space: pre-wrap;
    }
    .agent-response {
        background-color: #f5f5f5;
        padding: 8px 12px;
        border-radius: 8px;
        border-left: 3px solid #2ecc71;
    }
    
    /* Custom tabs styling */
    .stButton button[data-baseweb="tab"] {
        border-radius: 4px 4px 0 0 !important;
        padding: 10px 24px !important;
        border: 1px solid #e0e0e0 !important;
        border-bottom: none !important;
        margin-right: 2px !important;
    }
    
    .stButton button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #f5f5f5 !important;
        border-bottom: 2px solid #1E90FF !important;
        font-weight: bold !important;
    }
    
    /* Custom expander styling */
    .streamlit-expanderHeader {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #0984e3 !important;
    }
    
    /* Memory tab styling */
    div[data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #f5f5f5 !important;
        color: #0984e3 !important;
        border-bottom: 2px solid #0984e3 !important;
        font-weight: bold !important;
    }
</style>
""" 