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
    
    # Explicitly set the system prompt like the main TheFive interface does
    # Import the MCP framework function
    sys.path.insert(0, str(Path(__file__).parent.parent / "AgentSkeleton" / "mcp_framework"))
    from protocol import create_system_prompt_with_tools
    
    # Set the system prompt explicitly
    system_prompt = create_system_prompt_with_tools()
    conversation.set_system_prompt(system_prompt)
    print(f"DEBUG: Explicitly set ObserverAgent system prompt: {system_prompt[:100]}...")
    
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
    
    # Create a fresh conversation instance
    st.session_state.conversation = create_fresh_conversation(client)

def initialize_conversation_with_history(messages: list):
    """Initialize a new conversation with existing chat history"""
    conversation = TokenManagedConversation(
        max_tokens=100000,
        client=st.session_state.client,
        model_name=AZURE_DEEPSEEK_MODEL_NAME
    )
    
    # Explicitly set the system prompt like the main TheFive interface does
    # Import the MCP framework function
    sys.path.insert(0, str(Path(__file__).parent.parent / "AgentSkeleton" / "mcp_framework"))
    from protocol import create_system_prompt_with_tools
    
    # Set the system prompt explicitly
    system_prompt = create_system_prompt_with_tools()
    conversation.set_system_prompt(system_prompt)
    print(f"DEBUG: Explicitly set ObserverAgent system prompt for history: {system_prompt[:100]}...")
    
    # Add message history to conversation context
    # Add each message using the add_message method
    for msg in messages:
        if msg["role"] != "system":  # Skip system messages as we've already set the system prompt
            conversation.add_message(content=msg["content"], role=msg["role"])
    
    return conversation

# Streamlit UI
st.title("🔍 ObserverAgent - Java/Spring Boot Analysis Expert")

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