# DeepSeek AI Assistant - Streamlit Interface

This is a Streamlit-based web interface for the DeepSeek AI Assistant. It provides a user-friendly way to interact with the AI agent while maintaining all the functionality of the original command-line interface.

## Features

- Modern chat interface with message history
- Token usage monitoring in the sidebar
- Full integration with DeepSeek agent's capabilities
- Persistent memory across chat sessions
- Real-time response streaming

## Setup

1. Create a virtual environment:
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

3. Make sure the AgentSkeleton project is properly set up with its environment variables.

## Running the Application

To start the Streamlit interface:

```bash
streamlit run app.py
```

The interface will be available at `http://localhost:8501` by default.

## Usage

1. Type your message in the chat input at the bottom of the screen
2. View the conversation history in the main chat area
3. Check token usage statistics in the sidebar
4. The agent maintains memory across sessions using the same memory bank as the CLI version

## Notes

- This interface uses the same backend as the original DeepSeek agent
- All tools and capabilities from the original agent are available
- The interface maintains session state, so your conversation history persists during your session 