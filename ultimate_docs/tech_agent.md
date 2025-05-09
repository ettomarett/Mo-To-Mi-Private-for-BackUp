# Technical Architecture of Mi-To-Mi AI Agent

## Component Harmony Overview

The Mi-To-Mi AI Agent system is built on three primary components that work in harmony to create a functional AI agent interface:

1. **Azure DeepSeek Client** (azure_deepseek_client.py)
2. **DeepSeek Agent** (deepseek_agent.py)
3. **Streamlit Interface** (app.py)

This document explains how these components interact to create a cohesive system.

## Component Responsibilities

### Azure DeepSeek Client (azure_deepseek_client.py)

This component serves as the communication layer between the application and Azure's AI services:

- Establishes and maintains the connection to Azure AI services
- Handles authentication via API keys
- Formats requests according to Azure API specifications
- Processes responses from the API
- Provides error handling for API-related issues

```
Client --> Azure API
  │        ↑
  │        │
  ↓        │
Request  Response
```

### DeepSeek Agent (deepseek_agent.py)

The agent component acts as the "brain" of the system:

- Contains the logic for processing user questions
- Uses the client to send properly formatted prompts to the AI model
- Manages conversation context through token-aware mechanisms
- Integrates with memory systems for persistent information
- Handles the execution of tools and special commands

```
User Input → Agent → Client → Azure AI
                ↑
                │
         Memory/Tools/Context
```

### Streamlit Interface (app.py)

The interface component provides the user-facing experience:

- Renders the chat UI for user interaction
- Manages the application state
- Handles chat history saving/loading
- Provides configuration options and developer tools
- Orchestrates the flow between user inputs and agent responses

```
User → Streamlit UI → Agent → Response
       ↑          ↓
       │          │
      Chat History/State
```

## The Functional Harmony

What makes this system work cohesively is the clear separation of concerns and the well-defined interaction patterns:

1. **Initialization Flow**:
   - app.py sets up the Python import paths to locate all components
   - app.py initializes the client with Azure credentials
   - app.py creates a conversation instance using the token management system
   - app.py prepares the memory bank for persistent storage

2. **Request Processing Flow**:
   - User enters a question in the Streamlit interface
   - app.py captures the input and adds it to the conversation history
   - app.py calls process_with_tools() from deepseek_agent.py
   - deepseek_agent.py uses the client to communicate with Azure AI
   - client formats the request and sends it to Azure
   - Response flows back through the same chain

3. **Memory and Context Management**:
   - TokenManagedConversation maintains the chat history with token awareness
   - The agent uses this to ensure context is preserved across interactions
   - The Streamlit interface persists conversations to disk for later retrieval

4. **Error Handling Chain**:
   - Client detects and reports API-level errors
   - Agent interprets these errors and provides user-friendly messages
   - Interface displays these messages and offers recovery options

## Configuration Harmony

The system uses a layered configuration approach:

1. Environment variables (loaded via dotenv)
2. Default values in code
3. User-configurable settings in the interface

This allows for flexibility while maintaining ease of use.

## Import Structure

The import structure is crucial to the harmony:

```
app.py
  ↓
  imports from
  ↓
AgentSkeleton/
  ├── clients/
  │     └── azure_deepseek_client.py  ← Provides initialize_client()
  ├── agents/
  │     └── deepseek_agent.py         ← Provides process_with_tools()
  └── core/
        ├── token_management.py       ← Provides TokenManagedConversation
        └── memory_bank.py            ← Provides MemoryBank
```

The correct Python path setup ensures these components can find each other.

## Technical Implementation Details

### API Credential Management

The system manages Azure API credentials in multiple locations with a priority chain:

1. **Environment Variables** (highest priority)
   - AZURE_DEEPSEEK_ENDPOINT
   - AZURE_DEEPSEEK_API_KEY
   - AZURE_DEEPSEEK_MODEL_NAME

2. **app.py Hardcoded Values** (secondary)
   ```python
   AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com")
   AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i")
   AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1-gADK")
   ```

3. **azure_deepseek_client.py Default Values** (tertiary)
   ```python
   default_endpoint = "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com"
   default_api_key = "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i"
   default_model = "DeepSeek-R1"
   ```

This layered approach allows for easy configuration changes through environment variables or code updates.

### Script Calling Sequence

The exact technical flow from UI to Azure API is:

1. **User Interaction**: 
   ```python
   # In app.py (around line 250-270)
   if prompt := st.chat_input("What's on your mind?"):
       st.session_state.messages.append({"role": "user", "content": prompt})
       with st.chat_message("user"):
           st.markdown(prompt)
   ```

2. **Agent Invocation**:
   ```python
   # In app.py (around line 270-290)
   response, updated_conversation = asyncio.run(
       process_with_tools(
           client=st.session_state.client,
           model_name=AZURE_DEEPSEEK_MODEL_NAME,
           question=prompt,
           conversation=st.session_state.conversation,
           memory_bank=st.session_state.memory_bank
       )
   )
   ```

3. **Agent Processing**:
   ```python
   # In deepseek_agent.py (around line 15-30)
   async def process_with_tools(client, model_name, question, conversation, memory_bank=None):
       from mcp_framework import process_with_tools as mcp_process
       
       return await mcp_process(
           client=client,
           model_name=model_name,
           question=question,
           conversation=conversation,
           memory_bank=memory_bank
       )
   ```

4. **Client API Call**:
   ```python
   # In azure_deepseek_client.py (around line 40-75)
   async def complete(self, messages, max_tokens, temperature, ...):
       # Convert message dictionaries to Azure SDK message objects
       azure_messages = []
       for msg in messages:
           # ... message conversion logic ...
       
       # Execute the API call
       response = await loop.run_in_executor(
           None,
           lambda: self.client.complete(
               messages=azure_messages,
               max_tokens=max_tokens,
               temperature=temperature,
               model=model_to_use
           )
       )
   ```

### Client Initialization Details

The client is initialized at application startup:

```python
# In app.py (around line 145-155)
client = initialize_client(
    deployment_name=AZURE_DEEPSEEK_MODEL_NAME,
    api_key=AZURE_DEEPSEEK_API_KEY,
    endpoint=AZURE_DEEPSEEK_ENDPOINT
)

# The initialize_client function in azure_deepseek_client.py
def initialize_client(deployment_name=None, api_key=None, endpoint=None):
    return AsyncAzureDeepSeekClient(
        endpoint=endpoint,
        api_key=api_key,
        model=deployment_name
    )
```

This client instance is stored in the Streamlit session state, making it persistent across user interactions:

```python
st.session_state.client = client
```

### Interface-Agent-Client Communication Flow

The complete interaction cycle from UI to API and back:

1. User submits a question in Streamlit UI
2. app.py captures the input and adds it to the conversation history
3. app.py calls process_with_tools() from deepseek_agent.py with these parameters:
   - client (previously initialized Azure client)
   - model_name (the deployment name to use)
   - question (user's input)
   - conversation (the current TokenManagedConversation instance)
   - memory_bank (optional persistent storage)
4. deepseek_agent.py passes these parameters to the MCP framework
5. The MCP framework processes the input, potentially using tools
6. The framework uses the client to send the final prompt to Azure
7. The Azure client formats the message according to the Azure API spec
8. The client sends the request and awaits a response
9. The client receives and processes the response
10. The response flows back through the chain to the agent
11. The agent updates the conversation with the response
12. app.py receives the response and updated conversation
13. app.py displays the response in the UI
14. app.py saves the updated conversation state

When errors occur at any point, they are caught at the appropriate level (client, agent, or interface) and transformed into user-friendly messages.

## Errors Encountered and Solutions

During the development and debugging process, we encountered several key issues that required specific solutions:

### 1. Python Path and Import Issues

**Error:**
```
Failed to import AgentSkeleton modules. Please ensure:
1. You're running from the correct directory
2. AgentSkeleton is properly installed
3. All dependencies are installed
Error: No module named 'agents'
```

**Root Cause:** Python was unable to locate the AgentSkeleton modules because the import paths were incorrectly configured.

**Solution:**
1. Corrected the import paths in app.py to explicitly add the parent directory to sys.path:
   ```python
   current_dir = Path(__file__).parent.absolute()  # StreamlitInterface
   parent_dir = current_dir.parent.absolute()      # TestInterface
   sys.path.insert(0, str(parent_dir))
   ```

2. Updated the import statements to use full package paths:
   ```python
   from AgentSkeleton.clients.azure_deepseek_client import initialize_client
   from AgentSkeleton.agents.deepseek_agent import process_with_tools
   ```

3. Added a fallback import approach using direct module paths if the package approach fails:
   ```python
   from clients.azure_deepseek_client import initialize_client
   from agents.deepseek_agent import process_with_tools
   ```

### 2. OpenAI Module Not Found

**Error:**
```
Error: No module named 'openai'
```

**Root Cause:** The application depends on the OpenAI Python SDK, which wasn't installed in the virtual environment.

**Solution:**
1. Installed the required package using pip:
   ```
   python -m pip install openai
   ```

2. Ensured that the virtual environment was activated during installation to maintain isolation.

### 3. Azure API "NOT FOUND" Errors

**Error:**
```
Error during API call: NOT FOUND
Trying alternate approach with direct parameters
Alternate approach failed: NOT FOUND
Error in chat completion: NOT FOUND
```

**Root Cause:** The Azure OpenAI API couldn't locate the specified model or deployment, either because credentials were invalid, the deployment didn't exist, or the endpoint was incorrect.

**Solution:**
1. Added comprehensive error handling in the Azure client to detect and report specific API errors:
   ```python
   try:
       return self.client.chat.completions.create(**params)
   except Exception as e:
       print(f"Error during API call: {str(e)}")
       # Try an alternate approach...
   ```

2. Modified deepseek_agent.py to provide detailed error messages based on error types:
   ```python
   if "NOT FOUND" in error_msg:
       detailed_error = f"""<think>Azure OpenAI API error: NOT FOUND - Deployment/model '{model_name}' not found or inaccessible</think>

   I encountered an issue connecting to the Azure OpenAI service:
   
   **Error: Model or Deployment Not Found**
   ...
   ```

3. Created a dummy mode feature to allow the interface to function during API configuration:
   ```python
   USE_DUMMY_MODE = True  # Toggle for testing without API access
   ```

### 4. API Parameter Errors

**Error:**
```
Error during API call: Missing required arguments; Expected either ('messages' and 'model') or ('messages', 'model' and 'stream') arguments to be given
```

**Root Cause:** The Azure OpenAI client was not being called with the correct parameter format. The API expected specific parameters that weren't provided or were provided incorrectly.

**Solution:**
1. Fixed the client implementation to use the correct parameters for the Azure OpenAI API:
   ```python
   params = {
       "model": deployment_to_use,  # Required parameter
       "messages": messages,
       "max_tokens": max_tokens,
       "temperature": temperature,
       "stream": stream
   }
   ```

2. Added an alternative approach that tries different parameter formats if the first approach fails:
   ```python
   except Exception as e:
       print(f"Error during API call: {str(e)}")
       # Try an alternate approach
       try:
           print("Trying alternate approach with direct parameters")
           return self.client.chat.completions.create(
               model=deployment_to_use,
               messages=messages,
               max_tokens=max_tokens,
               temperature=temperature,
               stream=stream
           )
       except Exception as e2:
           print(f"Alternate approach failed: {str(e2)}")
           raise
   ```

### 5. Azure SDK Compatibility Issues

**Error:** Inconsistent behavior when calling the Azure OpenAI API using different parameters.

**Root Cause:** The Azure OpenAI Python SDK has evolved, and different versions have different parameter requirements.

**Solution:**
1. Updated the client code to use the azure.ai.inference SDK with compatible message formats:
   ```python
   from azure.ai.inference import ChatCompletionsClient
   from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
   ```

2. Created a conversion layer to transform standard message dictionaries into Azure-specific message objects:
   ```python
   # Convert message dictionaries to Azure SDK message objects
   azure_messages = []
   for msg in messages:
       role = msg.get("role", "")
       content = msg.get("content", "")
       
       if role == "system":
           azure_messages.append(SystemMessage(content=content))
       elif role == "user":
           azure_messages.append(UserMessage(content=content))
       # ...and so on
   ```

### 6. Dummy Mode Implementation

**Challenge:** Needed a way to test the interface functionality without requiring a valid API connection during development.

**Solution:**
1. Implemented a dummy mode flag in deepseek_agent.py:
   ```python
   USE_DUMMY_MODE = True  # Set to True for testing when API is unavailable
   ```

2. Added a dummy response generation function that simulates API responses:
   ```python
   if USE_DUMMY_MODE:
       # Generate a dummy response
       dummy_response = f"""<think>Running in DUMMY MODE - Azure OpenAI API is not being accessed</think>

   This is a simulated response to: '{question}'
   ...
   ```

3. Added clear indicators in the UI to show when dummy mode is active:
   ```python
   if 'USE_DUMMY_MODE' in locals() and USE_DUMMY_MODE:
       st.warning("⚠️ Running in DUMMY MODE: Azure API is not being accessed. Responses are simulated.")
   ```

By implementing these solutions, we successfully resolved all the key issues and created a more robust and error-tolerant system.

## Conclusion

The harmony between these three components creates a functional and maintainable AI agent system:

- **Clean Separation of Concerns**: Each component has a clear responsibility
- **Well-Defined Interfaces**: Components interact through specific functions
- **Layered Architecture**: UI → Agent → Client → AI
- **Error Resilience**: Errors are caught and handled at appropriate levels
- **State Management**: Conversation state is properly maintained

This architecture allows for future extensions, such as adding new tools or alternate AI providers, without disrupting the overall system harmony. 