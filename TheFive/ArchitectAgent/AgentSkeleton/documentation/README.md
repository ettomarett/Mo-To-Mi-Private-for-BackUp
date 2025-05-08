# Basic ADK Agent

A simple Google ADK agent with a calculator tool.

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

3. Set up your environment:
```bash
# Edit .env and add your DeepSeek Azure endpoint
# The API key is already included, but you need to update:
# AZURE_DEEPSEEK_ENDPOINT=https://your-azure-deepseek-endpoint.com
```

## Running the agent

```bash
# To run the DeepSeek R1 agent:
python deepseek_agent.py

# Or to run the original Gemini-based agent (requires Google API key):
python basic_agent.py
```

## Example interactions

- "What's 245 + 378?"
- "Can you help me calculate the tip on a $45 bill at 15%?"
- "What's the weather like today?" (This will be handled by the LLM itself)

## Extending the agent

To add more capabilities:
1. Define new functions for tools
2. Create FunctionTool instances for each function
3. Add the tools to the agent's tools list

## Important Notes

- **Security**: Keep your API keys secure. Never share them in public repositories or messages.
- **Endpoint Format**: The Azure endpoint should be in this format: `https://your-resource-name.openai.azure.com/openai`
- **API Format**: This implementation assumes your DeepSeek API follows the OpenAI-compatible format. You might need to adjust the payload format based on your specific deployment. 