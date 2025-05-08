import streamlit as st
import sys
from pathlib import Path
import importlib.util

# Get absolute paths
current_dir = Path(__file__).parent.absolute()  # ui directory
root_dir = current_dir.parent  # TheFiveinterFace root

# Direct import of needed modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the constants module
constants_path = root_dir / "config" / "constants.py"
constants = load_module("constants", constants_path)


def apply_custom_styles():
    """Apply custom CSS styles to the app"""
    st.markdown(constants.CUSTOM_CSS, unsafe_allow_html=True)


def display_agent_header(agent_type):
    """
    Display the header for an agent tab
    
    Args:
        agent_type (str): Agent type
    """
    headers = {
        "architect": "Architect Agent (The Supervisor)",
        "observer": "Observer Agent (The Analyzer)",
        "strategist": "Strategist Agent (The Planner)",
        "builder": "Builder Agent (The Coder)",
        "validator": "Validator Agent (The Tester)"
    }
    
    descriptions = {
        "architect": "Orchestrates the entire migration process and coordinates other agents.",
        "observer": "Analyzes the monolith structure to identify service boundaries.",
        "strategist": "Creates migration blueprints and strategies.",
        "builder": "Generates implementation code for the microservices.",
        "validator": "Verifies migration correctness through testing."
    }
    
    header = headers.get(agent_type, "Unknown Agent")
    description = descriptions.get(agent_type, "")
    
    st.markdown(f'<div class="agent-header">{header}</div>', unsafe_allow_html=True)
    st.write(description)


def display_migration_stages(current_stage):
    """
    Display the migration stages with the current stage highlighted
    
    Args:
        current_stage (str): Current migration stage
    """
    stages = ["initiation", "analysis", "planning", "implementation", "testing", "completed"]
    stages_display = ["1. Initiation", "2. Analysis", "3. Planning", 
                     "4. Implementation", "5. Testing", "6. Completed"]
    
    html_parts = []
    for i, stage in enumerate(stages):
        active_class = "stage-active" if stage == current_stage else ""
        html_parts.append(f'<span class="stage-indicator {active_class}">{stages_display[i]}</span>')
    
    html = f"""
    <div style="display: flex; margin-bottom: 20px;">
        {"".join(html_parts)}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def display_stage_progress(current_stage):
    """
    Display a progress bar for the current stage
    
    Args:
        current_stage (str): Current migration stage
    """
    stages = ["initiation", "analysis", "planning", "implementation", "testing", "completed"]
    current_index = stages.index(current_stage) if current_stage in stages else 0
    progress_percentage = (current_index / (len(stages) - 1))
    
    st.progress(progress_percentage)
    st.write(f"Stage: **{current_stage.capitalize()}**")


def display_agent_chat(messages, format_function):
    """
    Display a chat history
    
    Args:
        messages (list): List of messages
        format_function (function): Function to format agent messages
    """
    for message in messages:
        if message["role"] == "user":
            st.markdown(
                f"<div class='message-container'><div class='user-message'>{message['content']}</div></div>", 
                unsafe_allow_html=True
            )
        elif message["role"] == "system" and "[SUMMARY" in message["content"]:
            # Display summaries with special styling
            st.markdown(
                f"<div class='message-container'><div class='summary-message'>{message['content']}</div></div>", 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='message-container'><div class='agent-message'>{format_function(message['content'])}</div></div>", 
                unsafe_allow_html=True
            ) 