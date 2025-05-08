# The Five As Interface

A specialized Streamlit interface for the Mo-To-Mi five-agent architecture that assists in migrating Spring Boot monoliths to microservices.

## Overview

The Five As Interface provides a user-friendly interface to:

- Create and manage migration projects
- Interact with each of the five specialized agents:
  - **Architect Agent (The Supervisor)** - Orchestrates the entire migration process
  - **Observer Agent (The Analyzer)** - Analyzes the monolith structure
  - **Strategist Agent (The Planner)** - Creates the migration blueprint
  - **Builder Agent (The Coder)** - Generates implementation code
  - **Validator Agent (The Tester)** - Verifies migration correctness
- Track project progress through different migration stages
- Store and retrieve project data

## Features

- **Project Management**: Create, open, and manage migration projects
- **Stage-Based Migration**: Progress through well-defined migration stages
- **Agent Conversations**: Chat with each specialized agent about the migration
- **Memory Persistence**: Store important information across sessions
- **Progress Tracking**: Visualize migration progress through stages

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows CMD
# or
venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

To run the application:

```bash
# Method 1: Using the run script
python run.py

# Method 2: Using Streamlit directly
streamlit run app.py
```

Then open your browser to http://localhost:8501.

## Project Structure

- `app.py`: Main Streamlit application
- `run.py`: Launcher script
- `requirements.txt`: Package dependencies
- `projects/`: Directory for saved migration projects
- `permanent_memories/`: Directory for memory bank storage

## Dependencies

- Python 3.8+
- Streamlit 1.32.0+
- Azure DeepSeek AI integration
- Other packages listed in requirements.txt

## Integration with AgentSkeleton

This interface integrates with the AgentSkeleton framework, using:

- TokenManagedConversation for handling chat context
- MemoryBank for persistent storage
- DeepSeek AI client for LLM capabilities
- MCP tools for various agent actions 