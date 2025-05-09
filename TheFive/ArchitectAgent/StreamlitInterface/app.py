import os
import sys
import asyncio
import streamlit as st
from pathlib import Path
import json
from datetime import datetime

# Add the parent directory to sys.path so we can import AgentSkeleton
current_dir = Path(__file__).parent.absolute()  # StreamlitInterface
parent_dir = current_dir.parent.absolute()  # TestInterface
sys.path.insert(0, str(parent_dir))

# Import our comprehensive logging system
from tool_logger import log_tool_parse, log_tool_execution, get_parse_logs, get_execution_logs, clear_logs

try:
    # First try direct imports
    from AgentSkeleton.clients.azure_deepseek_client import initialize_client
    from AgentSkeleton.agents.deepseek_agent import process_with_tools
    from AgentSkeleton.core.token_management import TokenManagedConversation
    from AgentSkeleton.core.memory_bank import MemoryBank
    
    st.success("✅ Modules imported successfully!")
except ImportError as e:
    # Try adding each component directory individually
    agent_skeleton_dir = parent_dir / 'AgentSkeleton'
    sys.path.insert(0, str(agent_skeleton_dir))
    sys.path.insert(0, str(agent_skeleton_dir / 'agents'))
    sys.path.insert(0, str(agent_skeleton_dir / 'core'))
    sys.path.insert(0, str(agent_skeleton_dir / 'clients'))
    
    try:
        # Try importing with direct module names
        from clients.azure_deepseek_client import initialize_client
        from agents.deepseek_agent import process_with_tools
        from core.token_management import TokenManagedConversation
        from core.memory_bank import MemoryBank
        
        st.success("✅ Modules imported successfully with alternative approach!")
    except ImportError as e2:
        st.error(f"""
        Failed to import AgentSkeleton modules. Please ensure:
        1. You're running from the correct directory
        2. AgentSkeleton is properly installed
        3. All dependencies are installed
        
        First error: {str(e)}
        Second error: {str(e2)}
        
        Current paths:
        - Current directory: {os.getcwd()}
        - Parent directory: {parent_dir}
        - Python path: {sys.path}
        """)
        st.stop()

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Monkey patch the tool parsing and execution to capture all related activity
try:
    # Patch tool execution
    import AgentSkeleton.mcp_framework.tool_executor as tool_executor
    original_execute_tool = tool_executor.execute_tool
    
    def patched_execute_tool(*args, **kwargs):
        """Patched version of execute_tool that logs all calls"""
        # Get parameters
        tool_name = args[0]
        params = args[1]
        memory_bank = args[3] if len(args) > 3 else None
        
        # Log the tool call
        memory_dir = getattr(memory_bank, "storage_dir", "unknown") if memory_bank else None
        log_tool_execution(tool_name, params, memory_dir)
        
        # Call the original function
        result = original_execute_tool(*args, **kwargs)
        
        # Log the result
        log_tool_execution(tool_name, params, memory_dir, result)
        
        # Make sure streamlit knows there's a new log
        if 'tool_execution_log' in st.session_state:
            st.session_state.tool_execution_log = get_execution_logs()
        
        return result
    
    # Apply the execution patch
    tool_executor.execute_tool = patched_execute_tool
    print("✓ Tool executor successfully patched for debugging")
    
    # Patch tool parsing
    import AgentSkeleton.mcp_framework.protocol as protocol
    original_extract_tool_calls = protocol.extract_tool_calls
    
    def patched_extract_tool_calls(text):
        """Patched version of extract_tool_calls that logs all parsing"""
        # Call the original function
        tool_calls = original_extract_tool_calls(text)
        
        # Log the parsed tools
        log_tool_parse(text, tool_calls)
        
        # Make sure streamlit knows there's a new log
        if 'tool_parse_log' in st.session_state:
            st.session_state.tool_parse_log = get_parse_logs()
        
        return tool_calls
    
    # Apply the parsing patch
    protocol.extract_tool_calls = patched_extract_tool_calls
    print("✓ Tool parser successfully patched for debugging")
    
except Exception as e:
    print(f"Failed to patch MCP framework: {str(e)}")

# Create chats directory if it doesn't exist
CHATS_DIR = Path("saved_chats")
CHATS_DIR.mkdir(exist_ok=True)

# Helper functions for chat management
def save_chat(name: str, messages: list, timestamp: str = None):
    """Save chat to a JSON file"""
    if not timestamp:
        timestamp = datetime.now().isoformat()
    
    chat_data = {
        "name": name,
        "messages": messages,
        "timestamp": timestamp
    }
    
    file_path = CHATS_DIR / f"{name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=2)

def load_chat(name: str):
    """Load chat from a JSON file"""
    file_path = CHATS_DIR / f"{name}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def list_saved_chats():
    """List all saved chats"""
    return [f.stem for f in CHATS_DIR.glob("*.json")]

def get_enumerated_name(base_name: str) -> str:
    """Generate an enumerated name if the base name already exists"""
    existing_chats = list_saved_chats()
    if base_name not in existing_chats:
        return base_name
        
    counter = 1
    while f"{base_name}_{counter}" in existing_chats:
        counter += 1
    return f"{base_name}_{counter}"

def delete_chat(name: str) -> bool:
    """Delete a saved chat file"""
    file_path = CHATS_DIR / f"{name}.json"
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False

# Define custom CSS for think sections
st.markdown("""
<style>
    .think-section {
        background-color: #2d3436;
        border-left: 3px solid #0984e3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        font-style: italic;
        color: #dfe6e9;
    }
</style>
""", unsafe_allow_html=True)

# Define the Azure DeepSeek settings
AZURE_DEEPSEEK_ENDPOINT = os.getenv("AZURE_DEEPSEEK_ENDPOINT", "https://DeepSeek-R1-gADK.eastus.models.ai.azure.com")
AZURE_DEEPSEEK_API_KEY = os.getenv("AZURE_DEEPSEEK_API_KEY", "sczzACCarm4XtyfSQz5GQ3v5Hc2hSB2i")
AZURE_DEEPSEEK_MODEL_NAME = os.getenv("AZURE_DEEPSEEK_MODEL_NAME", "DeepSeek-R1-gADK")

def create_fresh_conversation(client) -> TokenManagedConversation:
    """Create a fresh conversation instance with default system prompt"""
    conversation = TokenManagedConversation(
        max_tokens=100000,  # Adjust based on model's context window
        client=client,
        model_name=AZURE_DEEPSEEK_MODEL_NAME
    )
    
    # Set the system prompt
    conversation.set_system_prompt(
        "You are a helpful AI assistant with an Azure DeepSeek backend. "
        "You have access to tools for permanent memory storage and other operations. "
        "Use the built-in memory tool to store and retrieve important information. "
        "Remember to ask for explicit permission before storing any user preferences or personal information."
    )
    
    return conversation

# Initialize session state
if 'conversation' not in st.session_state:
    # Initialize the Azure DeepSeek client
    client = initialize_client(
        deployment_name=AZURE_DEEPSEEK_MODEL_NAME,
        api_key=AZURE_DEEPSEEK_API_KEY,
        endpoint=AZURE_DEEPSEEK_ENDPOINT
    )
    
    st.session_state.client = client
    st.session_state.memory_bank = MemoryBank("permanent_memories")
    st.session_state.messages = []
    st.session_state.show_token_status = False
    st.session_state.current_chat_name = "New Chat"
    st.session_state.last_saved_messages = []
    st.session_state.dev_mode = False  # Initialize developer mode setting
    
    # Initialize debug tracking variables
    st.session_state.tool_debug_enabled = True  # Enable tool debugging by default
    if 'tool_execution_log' not in st.session_state:
        st.session_state.tool_execution_log = get_execution_logs()  # Load logs from file
    
    # Last time we loaded logs from file
    st.session_state.last_log_check = datetime.now().timestamp()
    
    # Create a fresh conversation instance
    st.session_state.conversation = create_fresh_conversation(client)

# Function to load debug logs from file
def load_debug_logs_from_file():
    """Load debug logs from our local file"""
    logs = get_execution_logs()
    if logs:
        if len(logs) > len(st.session_state.tool_execution_log):
            st.session_state.tool_execution_log = logs
            st.session_state.last_log_check = datetime.now().timestamp()
            return True
    return False

# Check for new logs periodically
current_time = datetime.now().timestamp()
if (current_time - st.session_state.last_log_check) > 5:  # Check every 5 seconds
    if load_debug_logs_from_file():
        st.rerun()
    st.session_state.last_log_check = current_time

def initialize_conversation_with_history(messages: list):
    """Initialize a new conversation with existing chat history"""
    conversation = TokenManagedConversation(
        max_tokens=100000,
        client=st.session_state.client,
        model_name=AZURE_DEEPSEEK_MODEL_NAME
    )
    
    # Set the system prompt with clear instructions about memory tools
    conversation.set_system_prompt(
        "You are a helpful AI assistant with an Azure DeepSeek backend. "
        "You have access to tools for permanent memory storage and other operations. "
        "Use the built-in memory tool to store and retrieve important information. "
        "Remember to ask for explicit permission before storing any user preferences or personal information."
    )
    
    # Add message history to conversation context
    # Add each message using the add_message method
    for msg in messages:
        if msg["role"] != "system":  # Skip system messages as we've already set the system prompt
            conversation.add_message(content=msg["content"], role=msg["role"])
    
    return conversation

# Streamlit UI
st.title("Mi-To-Mi AI Agent (Based on DeepSeek R1)")

# Add a debug tab to display tool execution logs if debug mode is enabled
if st.session_state.tool_debug_enabled:
    # Create a debug tab using an expander to keep it compact
    with st.expander("🔍 Debug: Tool Logs", expanded=True):
        st.markdown("### Tool Execution and Parsing Logs")
        
        # Create tabs for the different log types
        debug_tabs = st.tabs(["Tool Execution", "Tool Parsing"])
        
        # Tab 1: Tool Execution Logs
        with debug_tabs[0]:
            st.info("Showing logs for tool execution")
            
            # Manual test logging button
            if st.button("Test Execution Logging"):
                test_log = log_tool_execution(
                    tool_name="test_tool",
                    params={"test_param": "test_value"},
                    memory_dir="test_dir",
                    result={"status": "success", "message": "Test log created successfully!"}
                )
                if test_log:
                    st.success("Test execution log created successfully!")
                    st.session_state.tool_execution_log = get_execution_logs()
                    st.rerun()
                else:
                    st.error("Failed to create test log")
            
            # Show log file status
            exec_log_file = Path(__file__).parent / "tool_execute_logs.json"
            if exec_log_file.exists():
                log_size = exec_log_file.stat().st_size / 1024  # Size in KB
                last_modified = datetime.fromtimestamp(exec_log_file.stat().st_mtime)
                st.success(f"Execution log file exists ({log_size:.1f} KB) - Last modified: {last_modified.isoformat()[11:19]}")
                
                # Refresh button
                if st.button("Refresh Execution Logs"):
                    st.session_state.tool_execution_log = get_execution_logs()
                    st.rerun()
            else:
                st.warning("Execution log file not created yet. Perform tool operations to generate logs.")
            
            # Display execution logs if available
            if 'tool_execution_log' in st.session_state and st.session_state.tool_execution_log:
                # Show logs in a formatted way
                for log in st.session_state.tool_execution_log:
                    with st.container(border=True):
                        # Get key information
                        timestamp = log.get("timestamp", "").split("T")[1][:8] if "timestamp" in log else "Unknown"
                        agent = log.get("agent", "Unknown")
                        tool = log.get("tool", log.get("operation", "Unknown"))
                        status = log.get("status", "Unknown")
                        
                        # Format header
                        st.markdown(f"**{timestamp} | {agent} | {tool} | {status}**")
                        
                        # Show details in columns
                        col1, col2 = st.columns(2)
                        with col1:
                            if "params" in log:
                                st.markdown("**Parameters:**")
                                st.json(log["params"])
                            elif "key" in log:
                                st.markdown(f"**Key:** {log['key']}")
                        
                        with col2:
                            if "result" in log:
                                st.markdown("**Result:**")
                                st.write(log["result"])
                            if "memory_dir" in log or "storage_dir" in log:
                                dir_value = log.get("memory_dir", log.get("storage_dir", "Unknown"))
                                st.markdown(f"**Storage Dir:** {dir_value}")
            else:
                st.warning("No tool execution logs available yet. Try performing some actions that use tools.")
        
        # Tab 2: Tool Parse Logs
        with debug_tabs[1]:
            st.info("Showing logs for tool parsing")
            
            # Initialize parse logs if not already done
            if 'tool_parse_log' not in st.session_state:
                st.session_state.tool_parse_log = get_parse_logs()
            
            # Manual test parsing button
            if st.button("Test Parse Logging"):
                test_log = log_tool_parse(
                    text="This is a test text that contains a tool call <mcp:tool name='test_tool'></mcp:tool>",
                    extracted_tools=[{"name": "test_tool", "parameters": {}}]
                )
                if test_log:
                    st.success("Test parse log created successfully!")
                    st.session_state.tool_parse_log = get_parse_logs()
                    st.rerun()
                else:
                    st.error("Failed to create test parse log")
            
            # Show log file status
            parse_log_file = Path(__file__).parent / "tool_parse_logs.json"
            if parse_log_file.exists():
                log_size = parse_log_file.stat().st_size / 1024  # Size in KB
                last_modified = datetime.fromtimestamp(parse_log_file.stat().st_mtime)
                st.success(f"Parse log file exists ({log_size:.1f} KB) - Last modified: {last_modified.isoformat()[11:19]}")
                
                # Refresh button
                if st.button("Refresh Parse Logs"):
                    st.session_state.tool_parse_log = get_parse_logs()
                    st.rerun()
            else:
                st.warning("Parse log file not created yet. LLM responses with tool calls will generate logs.")
            
            # Display parse logs if available
            if st.session_state.tool_parse_log:
                for log in st.session_state.tool_parse_log:
                    with st.container(border=True):
                        # Get key information
                        timestamp = log.get("timestamp", "").split("T")[1][:8] if "timestamp" in log else "Unknown"
                        tool_count = log.get("tool_count", 0)
                        
                        # Format header
                        st.markdown(f"**{timestamp} | Tools Found: {tool_count}**")
                        
                        # Preview the text
                        st.markdown("**Text Preview:**")
                        st.code(log.get("text_preview", "No preview available"))
                        
                        # Show extracted tools
                        if log.get("extracted_tools"):
                            st.markdown("**Extracted Tools:**")
                            st.json(log["extracted_tools"])
            else:
                st.warning("No tool parsing logs available yet. Try chatting with the AI to generate tool calls.")
            
# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        
        if st.session_state.dev_mode:
            # In dev mode, show everything but with better formatting
            if "<think>" in content and "</think>" in content:
                parts = content.split("<think>")
                if parts[0].strip():
                    st.markdown(parts[0].strip())
                
                for part in parts[1:]:
                    if "</think>" in part:
                        think_content, rest = part.split("</think>", 1)
                        # Format tool calls differently
                        if "<mcp:tool" in think_content or "name: memory" in think_content:
                            st.markdown(f'<div style="background-color: #2d2d2d; border-left: 3px solid #e74c3c; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 0.9em;">{think_content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="think-section">{think_content}</div>', unsafe_allow_html=True)
                        if rest.strip():
                            st.markdown(rest)
                    else:
                        st.markdown(part)
            else:
                st.markdown(content)
        else:
            # In normal mode, show clean output
            if "<mcp:tool" in content:
                parts = content.split("</mcp:tool>")
                if len(parts) > 1:
                    content = parts[-1].strip()
                else:
                    content = content.split("<mcp:tool")[0].strip()
            
            if "<think>" in content and "</think>" in content:
                parts = content.split("<think>")
                if parts[0].strip():
                    st.markdown(parts[0].strip())
                
                for part in parts[1:]:
                    if "</think>" in part:
                        think_content, rest = part.split("</think>", 1)
                        if not any(tool_marker in think_content for tool_marker in ["<mcp:tool", "name: memory"]):
                            st.markdown(f'<div class="think-section">{think_content}</div>', unsafe_allow_html=True)
                        if rest.strip():
                            st.markdown(rest)
                    else:
                        if not any(tool_marker in part for tool_marker in ["<mcp:tool", "name: memory"]):
                            st.markdown(part)
            else:
                st.markdown(content)

# Chat input
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Add debug information to the response
            debug_before = len(st.session_state.tool_execution_log) if 'tool_execution_log' in st.session_state else 0
            
            # Process the message with the agent
            response, updated_conversation = asyncio.run(
                process_with_tools(
                    client=st.session_state.client,
                    model_name=AZURE_DEEPSEEK_MODEL_NAME,
                    question=prompt,
                    conversation=st.session_state.conversation,
                    memory_bank=st.session_state.memory_bank
                )
            )
            
            # Update conversation in session state
            st.session_state.conversation = updated_conversation
            
            # Check if debug logs were updated
            debug_after = len(st.session_state.tool_execution_log) if 'tool_execution_log' in st.session_state else 0
            if debug_after > debug_before and st.session_state.tool_debug_enabled:
                st.success(f"Captured {debug_after - debug_before} new tool execution logs")
            
            # Display response
            if "<think>" in response and "</think>" in response:
                # Split the message into parts
                parts = response.split("<think>")
                for part in parts[1:]:  # Process all parts after the first split
                    if "</think>" in part:
                        think_content, rest = part.split("</think>", 1)
                        # Display think section with custom styling
                        st.markdown(f'<div class="think-section">{think_content}</div>', unsafe_allow_html=True)
                        if rest.strip():  # If there's content after </think>
                            st.markdown(rest)
                    else:
                        st.markdown(part)
            else:
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Auto-save if chat was previously saved
            if st.session_state.current_chat_name != "New Chat":
                save_chat(st.session_state.current_chat_name, st.session_state.messages)
                st.session_state.last_saved_messages = st.session_state.messages.copy()

# Display chat management and token status in sidebar
with st.sidebar:
    st.title("Chat Management")
    
    # Developer Mode toggle
    st.subheader("Developer Options")
    st.session_state.dev_mode = st.toggle("Developer Mode", st.session_state.dev_mode)
    if st.session_state.dev_mode:
        st.info("Developer mode enabled: Showing technical details and tool calls")
    
    # Debug Mode toggle
    st.session_state.tool_debug_enabled = st.toggle("Enable Tool Debug Logging", st.session_state.tool_debug_enabled)
    if st.session_state.tool_debug_enabled:
        st.info("Tool debug logging enabled: Check tool execution logs in the Debug tab")
        if st.button("Clear Debug Logs"):
            clear_logs()  # Use our direct clear function
            st.session_state.tool_execution_log = []
            st.success("Debug logs cleared")
    
    # Save current chat section
    st.subheader("Save Current Chat")
    chat_name = st.text_input("Chat Name", value=st.session_state.current_chat_name)
    
    if st.button("Save Chat"):
        if chat_name.strip():
            try:
                # Generate enumerated name if needed
                final_name = get_enumerated_name(chat_name.strip())
                save_chat(final_name, st.session_state.messages)
                st.session_state.current_chat_name = final_name
                st.session_state.last_saved_messages = st.session_state.messages.copy()
                st.success(f"Chat saved as: {final_name}")
            except Exception as e:
                st.error(f"Failed to save chat: {str(e)}")
    
    # New chat button
    if st.button("Start New Chat"):
        # Auto-save if the chat was previously saved
        if st.session_state.current_chat_name != "New Chat":
            save_chat(st.session_state.current_chat_name, st.session_state.messages)
        elif st.session_state.messages:  # If it's a new chat with messages, show save dialog
            st.session_state['show_save_dialog'] = True
            st.rerun()
        
        # Clear the chat and create fresh conversation
        st.session_state.messages = []
        st.session_state.last_saved_messages = []
        st.session_state.current_chat_name = "New Chat"
        st.session_state.conversation = create_fresh_conversation(st.session_state.client)
        st.rerun()
    
    # Save dialog for unsaved new chats
    if st.session_state.get('show_save_dialog', False):
        st.warning("Would you like to save this chat first?")
        
        save_name = st.text_input("Enter a name for the chat:", key="save_dialog_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Discard and Start New", type="secondary"):
                st.session_state.messages = []
                st.session_state.last_saved_messages = []
                st.session_state.current_chat_name = "New Chat"
                st.session_state.show_save_dialog = False
                st.session_state.conversation = create_fresh_conversation(st.session_state.client)
                st.rerun()
        
        with col2:
            if st.button("Save and Start New"):
                if save_name.strip():
                    try:
                        final_name = get_enumerated_name(save_name.strip())
                        save_chat(final_name, st.session_state.messages)
                        st.success(f"Chat saved as: {final_name}")
                        st.session_state.messages = []
                        st.session_state.last_saved_messages = []
                        st.session_state.current_chat_name = "New Chat"
                        st.session_state.show_save_dialog = False
                        st.session_state.conversation = create_fresh_conversation(st.session_state.client)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save chat: {str(e)}")
                else:
                    st.error("Please enter a name for the chat")

    # Load saved chats section
    st.subheader("Saved Chats")
    saved_chats = list_saved_chats()
    
    if saved_chats:
        col1, col2 = st.columns(2)
        with col1:
            selected_chat = st.selectbox(
                "Select a chat",
                options=saved_chats
            )
        
        with col2:
            st.write("")  # Add some spacing
            st.write("")  # Add some spacing
            if st.button("🗑️ Delete", key="delete_chat_btn", help="Delete selected chat"):
                if delete_chat(selected_chat):
                    if selected_chat == st.session_state.current_chat_name:
                        st.session_state.current_chat_name = "New Chat"
                    st.success(f"Deleted chat: {selected_chat}")
                    st.rerun()
                else:
                    st.error("Failed to delete chat")
        
        # Check if we're in the middle of confirming a load operation
        if 'confirming_load' not in st.session_state:
            st.session_state['confirming_load'] = False
            st.session_state['load_target'] = None
            st.session_state['saving_before_load'] = False
            
        # Load chat button - outside any conditional blocks
        if st.button("Load Selected Chat"):
            # Set the flags to show confirmation UI
            st.session_state['confirming_load'] = True
            st.session_state['load_target'] = selected_chat
            st.rerun()
            
        # If we're confirming a load and there are unsaved changes
        if st.session_state['confirming_load']:
            needs_save = False
            
            if st.session_state.current_chat_name == "New Chat" and len(st.session_state.messages) > 0:
                needs_save = True
            elif st.session_state.messages != st.session_state.last_saved_messages and len(st.session_state.messages) > 0:
                needs_save = True
                
            if needs_save:
                st.warning("Current chat has unsaved changes.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save current chat before loading?"):
                        st.session_state['saving_before_load'] = True
                        st.rerun()
                with col2:
                    if st.button("Don't Save, Just Load"):
                        # Proceed with loading without saving
                        try:
                            chat_data = load_chat(st.session_state['load_target'])
                            if chat_data:
                                st.session_state.conversation = initialize_conversation_with_history(chat_data["messages"])
                                st.session_state.messages = chat_data["messages"]
                                st.session_state.last_saved_messages = chat_data["messages"].copy()
                                st.session_state.current_chat_name = chat_data["name"]
                                st.session_state['confirming_load'] = False
                                st.session_state['load_target'] = None
                                st.success(f"Loaded chat: {st.session_state['load_target']}")
                                st.rerun()
                            else:
                                st.error("Failed to load chat: Chat file not found")
                                st.session_state['confirming_load'] = False
                        except Exception as e:
                            st.error(f"Failed to load chat: {str(e)}")
                            st.session_state['confirming_load'] = False
                
                # Handle saving before loading
                if st.session_state['saving_before_load']:
                    if st.session_state.current_chat_name == "New Chat":
                        # Get a name for the unsaved chat
                        save_name = st.text_input("Enter a name for the current chat:", key="save_current_name")
                        
                        if st.button("Confirm Save"):
                            if save_name.strip():
                                try:
                                    final_name = get_enumerated_name(save_name.strip())
                                    save_chat(final_name, st.session_state.messages)
                                    st.session_state.current_chat_name = final_name
                                    st.session_state.last_saved_messages = st.session_state.messages.copy()
                                    st.success(f"Current chat saved as: {final_name}")
                                    
                                    # Now load the target chat
                                    chat_data = load_chat(st.session_state['load_target'])
                                    if chat_data:
                                        st.session_state.conversation = initialize_conversation_with_history(chat_data["messages"])
                                        st.session_state.messages = chat_data["messages"]
                                        st.session_state.last_saved_messages = chat_data["messages"].copy()
                                        st.session_state.current_chat_name = chat_data["name"]
                                        st.session_state['confirming_load'] = False
                                        st.session_state['saving_before_load'] = False
                                        st.session_state['load_target'] = None
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            else:
                                st.error("Please enter a name to save the current chat")
                    else:
                        # Save to existing chat name
                        try:
                            save_chat(st.session_state.current_chat_name, st.session_state.messages)
                            st.session_state.last_saved_messages = st.session_state.messages.copy()
                            st.success(f"Saved current chat: {st.session_state.current_chat_name}")
                            
                            # Now load the target chat
                            chat_data = load_chat(st.session_state['load_target'])
                            if chat_data:
                                st.session_state.conversation = initialize_conversation_with_history(chat_data["messages"])
                                st.session_state.messages = chat_data["messages"]
                                st.session_state.last_saved_messages = chat_data["messages"].copy()
                                st.session_state.current_chat_name = chat_data["name"]
                                st.session_state['confirming_load'] = False
                                st.session_state['saving_before_load'] = False
                                st.session_state['load_target'] = None
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # Don't proceed with normal loading code below
                st.stop()
            else:
                # No need to save, just load directly
                try:
                    chat_data = load_chat(st.session_state['load_target'])
                    if chat_data:
                        st.session_state.conversation = initialize_conversation_with_history(chat_data["messages"])
                        st.session_state.messages = chat_data["messages"]
                        st.session_state.last_saved_messages = chat_data["messages"].copy()
                        st.session_state.current_chat_name = chat_data["name"]
                        st.session_state['confirming_load'] = False
                        st.session_state['load_target'] = None
                        st.success(f"Loaded chat: {selected_chat}")
                        st.rerun()
                    else:
                        st.error("Failed to load chat: Chat file not found")
                        st.session_state['confirming_load'] = False
                except Exception as e:
                    st.error(f"Failed to load chat: {str(e)}")
                    st.session_state['confirming_load'] = False
    else:
        st.info("No saved chats found")

    # Token Status section
    st.title("Token Status")
    if st.button("Toggle Token Status"):
        st.session_state.show_token_status = not st.session_state.show_token_status
        
    if st.session_state.show_token_status:
        token_info = st.session_state.conversation.get_token_status()
        st.write(f"Current usage: {token_info.get('current_tokens', 0)} tokens")
        st.write(f"Maximum allowed: {token_info.get('max_tokens', 0)} tokens")
        st.write(f"Percentage used: {(token_info.get('current_tokens', 0) / token_info.get('max_tokens', 1) * 100):.1f}%")
        st.write(f"Summarized messages: {token_info.get('num_summarized', 0)}")