import os
import sys
from pathlib import Path

# Add the TheFive directory to the Python path for importing centralized system prompts
current_dir = Path(__file__).parent.absolute()  # config directory
root_dir = current_dir.parent  # TheFiveinterFace root
project_root = root_dir.parent  # Project root
thefive_dir = project_root / "TheFive"

if str(thefive_dir) not in sys.path:
    sys.path.append(str(thefive_dir))

# Import system prompts from the centralized file
from Agents_System_Prompts import (
    ARCHITECT_SYSTEM_PROMPT,
    OBSERVER_SYSTEM_PROMPT,
    STRATEGIST_SYSTEM_PROMPT,
    BUILDER_SYSTEM_PROMPT,
    VALIDATOR_SYSTEM_PROMPT
)

# Azure DeepSeek settings - Update these with your actual endpoint values
AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com")
AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i")
AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1")

# System prompts are now imported from Agents_System_Prompts.py
# This file now just imports them for backward compatibility
# To modify system prompts, edit TheFive/Agents_System_Prompts.py

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