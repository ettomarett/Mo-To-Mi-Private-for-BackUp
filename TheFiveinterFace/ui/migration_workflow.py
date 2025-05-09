import asyncio
import streamlit as st
from datetime import datetime
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

# Import the project and session modules
project_path = root_dir / "models" / "project.py"
project = load_module("project", project_path)

session_path = root_dir / "utils" / "session.py"
session = load_module("session", session_path)

formatting_path = root_dir / "utils" / "formatting.py"
formatting = load_module("formatting", formatting_path)

common_path = root_dir / "ui" / "common.py"
common = load_module("common", common_path)

# Import the conversation manager
conversation_manager_path = root_dir / "utils" / "conversation_manager.py"
conversation_manager = load_module("conversation_manager", conversation_manager_path)

# Import the agents chat module - using this name to avoid confusion
agents_chat_path = root_dir / "agents" / "chat.py"
chat = load_module("chat", agents_chat_path)


def display_migration_workflow(project_data, agent_modules):
    """
    Display the migration workflow with tabs for each agent
    
    Args:
        project_data (dict): Current project data
        agent_modules (dict): Dictionary of agent modules
    """
    if not project_data:
        st.error("No project selected. Please select a project first.")
        st.session_state.stage = "project_selection"
        st.rerun()
    
    # Display migration stages
    common.display_migration_stages(project_data['stage'])
    
    # Initialize selected tab index if not already set
    if 'selected_agent_tab' not in st.session_state:
        st.session_state.selected_agent_tab = 0
    
    # Tabs for different agents
    tab_titles = ["Architect", "Observer", "Strategist", "Builder", "Validator"]
    
    # Use columns for tab selection
    cols = st.columns(len(tab_titles))
    for i, col in enumerate(cols):
        tab_style = "primary" if i == st.session_state.selected_agent_tab else "secondary"
        if col.button(tab_titles[i], key=f"tab_{i}", type=tab_style, use_container_width=True):
            st.session_state.selected_agent_tab = i
            st.rerun()
    
    # Get the current selected tab
    selected_tab = st.session_state.selected_agent_tab
    
    # Display agent based on selected tab
    if selected_tab == 0:  # Architect
        display_agent_tab(
            agent_type="architect",
            project_data=project_data,
            agent_modules=agent_modules,
            always_active=True
        )
    elif selected_tab == 1:  # Observer
        is_active = project_data["stage"] in ["analysis", "planning", "implementation", "testing", "completed"]
        display_agent_tab(
            agent_type="observer",
            project_data=project_data,
            agent_modules=agent_modules,
            is_active=is_active,
            inactive_message="This agent will be available once the project reaches the Analysis stage.",
            can_advance=project_data["stage"] == "analysis",
            advance_button_text="Complete Analysis",
            next_stage="planning"
        )
    elif selected_tab == 2:  # Strategist
        is_active = project_data["stage"] in ["planning", "implementation", "testing", "completed"]
        display_agent_tab(
            agent_type="strategist",
            project_data=project_data,
            agent_modules=agent_modules,
            is_active=is_active,
            inactive_message="This agent will be available once the project reaches the Planning stage.",
            can_advance=project_data["stage"] == "planning",
            advance_button_text="Complete Planning",
            next_stage="implementation"
        )
    elif selected_tab == 3:  # Builder
        is_active = project_data["stage"] in ["implementation", "testing", "completed"]
        display_agent_tab(
            agent_type="builder",
            project_data=project_data,
            agent_modules=agent_modules,
            is_active=is_active,
            inactive_message="This agent will be available once the project reaches the Implementation stage.",
            can_advance=project_data["stage"] == "implementation",
            advance_button_text="Complete Implementation",
            next_stage="testing"
        )
    elif selected_tab == 4:  # Validator
        is_active = project_data["stage"] in ["testing", "completed"]
        display_agent_tab(
            agent_type="validator",
            project_data=project_data,
            agent_modules=agent_modules,
            is_active=is_active,
            inactive_message="This agent will be available once the project reaches the Testing stage.",
            can_advance=project_data["stage"] == "testing",
            advance_button_text="Complete Testing",
            next_stage="completed"
        )


def display_agent_tab(agent_type, project_data, agent_modules, is_active=True, always_active=False,
                     inactive_message="", can_advance=False, advance_button_text="", next_stage=""):
    """
    Display an agent tab with chat interface and actions
    
    Args:
        agent_type (str): Agent type
        project_data (dict): Current project data
        agent_modules (dict): Dictionary of agent modules
        is_active (bool): Whether the agent is active in the current stage
        always_active (bool): Whether the agent is always active regardless of stage
        inactive_message (str): Message to display when agent is inactive
        can_advance (bool): Whether the agent can advance to the next stage
        advance_button_text (str): Text for the advance button
        next_stage (str): Next stage to advance to
    """
    # Display agent header
    common.display_agent_header(agent_type)
    
    # Only show chat interface if agent is active
    if is_active or always_active:
        # Display current conversation name
        current_name = st.session_state.current_conversation_names.get(agent_type, "New Conversation")
        if current_name != "New Conversation":
            st.caption(f"Current conversation: **{current_name}**")
        else:
            st.caption("New conversation (not saved)")
        
        # Display message history
        st.subheader("Conversation")
        messages = session.get_agent_message_history(agent_type)
        common.display_agent_chat(messages, formatting.format_agent_message)
        
        # Reorganized sidebar with distinct zones
        with st.sidebar:
            st.subheader(f"{agent_type.capitalize()} Agent Memory & Tools")
            
            # Create tabs for the different memory zones
            memory_tabs = st.tabs(["💬 Conversations", "🧠 Permanent Memory", "🔢 Token Status"])
            
            # Tab 1: Conversation Memory Management
            with memory_tabs[0]:
                st.markdown("### Conversation Memory")
                
                # Current conversation info
                st.markdown(f"**Current:** {current_name}")
                
                # Save current conversation section
                with st.expander("Save Conversation", expanded=False):
                    if len(messages) > 0:
                        st.markdown("#### Name Your Conversation")
                        st.info("This name will be displayed exactly as entered")
                        
                        chat_name = st.text_input(
                            "Enter a descriptive name", 
                            value=current_name if current_name != "New Conversation" else "",
                            key=f"conv_name_{agent_type}",
                            placeholder=f"My {agent_type} conversation"
                        )
                        
                        if st.button("Save Conversation", key=f"save_conv_{agent_type}", use_container_width=True, type="primary"):
                            # Only pass name to save_current_conversation if user provided a non-empty name
                            name_to_save = chat_name.strip() if chat_name.strip() else None
                            if session.save_current_conversation(agent_type, name_to_save):
                                st.success(f"Conversation saved successfully as: \"{chat_name if chat_name.strip() else 'Auto-generated name'}\"")
                                st.rerun()
                            else:
                                st.error("Failed to save conversation.")
                    else:
                        st.info("Start a conversation first to save it.")
                
                # Load conversation section
                with st.expander("Load Conversation", expanded=False):
                    # Get saved conversations for this agent
                    saved_conversations = conversation_manager.list_conversations(agent_type)
                    
                    if saved_conversations and agent_type in saved_conversations and saved_conversations[agent_type]:
                        # Sort by timestamp (newest first)
                        conversations = sorted(
                            saved_conversations[agent_type],
                            key=lambda x: x.get("timestamp", ""),
                            reverse=True
                        )
                        
                        # Create a list of conversation names
                        options = [conv["name"] for conv in conversations]
                        
                        selected_conversation = st.selectbox(
                            "Select conversation",
                            options=options,
                            key=f"select_conv_{agent_type}"
                        )
                        
                        # Display selected conversation info
                        if selected_conversation:
                            selected_conv_data = next((c for c in conversations if c["name"] == selected_conversation), None)
                            if selected_conv_data:
                                st.text(f"Messages: {selected_conv_data.get('message_count', 0)}")
                                
                                # Warn if there are unsaved changes
                                if (len(messages) > 0 and 
                                    current_name != selected_conversation and 
                                    messages != st.session_state.last_saved_messages.get(agent_type, [])):
                                    st.warning("⚠️ Loading will replace your current conversation.")
                                
                                # Load and Delete buttons
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Load", key=f"load_conv_{agent_type}", use_container_width=True):
                                        if session.load_conversation_for_agent(agent_type, selected_conversation):
                                            st.success(f"Loaded conversation: {selected_conversation}")
                                            st.rerun()
                                        else:
                                            st.error("Failed to load conversation.")
                                
                                with col2:
                                    if st.button("Delete", key=f"delete_conv_{agent_type}", use_container_width=True):
                                        if conversation_manager.delete_conversation(agent_type, selected_conversation):
                                            st.success(f"Deleted conversation: {selected_conversation}")
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete conversation.")
                    else:
                        st.info("No saved conversations found for this agent.")
                
                # New conversation button
                if st.button("Start New Conversation", key=f"new_conv_{agent_type}", use_container_width=True):
                    # Warning if there are unsaved changes
                    if (len(messages) > 0 and 
                        messages != st.session_state.last_saved_messages.get(agent_type, [])):
                        st.session_state[f"confirm_new_{agent_type}"] = True
                        st.rerun()
                    else:
                        if session.start_new_conversation(agent_type):
                            st.success("Started new conversation!")
                            st.rerun()
                
                # Confirmation dialog for starting new conversation
                if st.session_state.get(f"confirm_new_{agent_type}", False):
                    st.warning("⚠️ You have unsaved changes. Save first?")
                    
                    save_col1, save_col2 = st.columns(2)
                    
                    with save_col1:
                        if st.button("Save & New", key=f"save_new_{agent_type}", use_container_width=True):
                            if session.save_current_conversation(agent_type):
                                session.start_new_conversation(agent_type)
                                st.session_state[f"confirm_new_{agent_type}"] = False
                                st.rerun()
                    
                    with save_col2:
                        if st.button("Just New", key=f"just_new_{agent_type}", use_container_width=True):
                            session.start_new_conversation(agent_type)
                            st.session_state[f"confirm_new_{agent_type}"] = False
                            st.rerun()
                    
                    if st.button("Cancel", key=f"cancel_new_{agent_type}", use_container_width=True):
                        st.session_state[f"confirm_new_{agent_type}"] = False
                        st.rerun()
            
            # Tab 2: Permanent Memory Management
            with memory_tabs[1]:
                st.markdown("### Permanent Memory")
                
                # Get agent-specific memory bank
                memory_bank = st.session_state.memory_banks.get(agent_type, st.session_state.memory_bank)
                
                # Get all memories from memory bank
                all_memories = memory_bank.get_all_memories()
                
                # Create a new memory section
                with st.expander("Create New Memory", expanded=False):
                    with st.form(f"new_memory_form_{agent_type}"):
                        memory_content = st.text_area("Content", key=f"memory_content_{agent_type}")
                        memory_key = st.text_input("Memory Key (Optional)", key=f"memory_key_{agent_type}")
                        memory_tags = st.text_input("Tags (comma separated)", key=f"memory_tags_{agent_type}")
                        
                        # Add explicit permission checkbox
                        st.markdown("**⚠️ Permission Required ⚠️**")
                        explicit_permission = st.checkbox(
                            "I explicitly give permission to store this information permanently", 
                            key=f"explicit_permission_{agent_type}",
                            help="Required for storing preferences or personal information"
                        )
                        
                        submit = st.form_submit_button("Store Memory", use_container_width=True)
                        if submit and memory_content:
                            tags_list = [tag.strip() for tag in memory_tags.split(",") if tag.strip()]
                            key = memory_bank.store_memory(
                                content=memory_content,
                                key=memory_key if memory_key else None,
                                tags=tags_list,
                                has_explicit_permission=explicit_permission
                            )
                            
                            # Handle potential error responses
                            if isinstance(key, str) and key.startswith("ERROR:"):
                                st.error(key)
                            else:
                                st.success(f"Memory stored with key: {key}")
                                st.rerun()
                
                # Browse memories section
                with st.expander("Browse Memories", expanded=True):
                    # Search box for memories
                    memory_search = st.text_input("Search memories", key=f"memory_search_{agent_type}")
                    
                    if all_memories:
                        # Apply search filter if provided
                        filtered_keys = list(all_memories.keys())
                        if memory_search:
                            filtered_keys = [k for k in filtered_keys if memory_search.lower() in k.lower() or 
                                            memory_search.lower() in all_memories[k].get('preview', '').lower()]
                        
                        # Sort by creation time (newest first)
                        sorted_keys = sorted(
                            filtered_keys,
                            key=lambda k: all_memories[k].get("created", ""),
                            reverse=True
                        )
                        
                        if not sorted_keys:
                            st.info("No memories match your search.")
                        else:
                            # Use a selectbox instead of nested expanders
                            memory_options = ["Select a memory..."] + sorted_keys[:20]  # Limit to 20 for performance
                            selected_memory = st.selectbox(
                                "Select memory to view",
                                options=memory_options,
                                key=f"select_memory_{agent_type}"
                            )
                            
                            # Display selected memory details
                            if selected_memory and selected_memory != "Select a memory...":
                                memory_data = all_memories[selected_memory]
                                content = memory_bank.retrieve_memory(selected_memory)
                                tags = ", ".join(memory_data.get("tags", []))
                                
                                st.markdown("---")
                                st.markdown(f"**Memory:** {selected_memory}")
                                st.markdown(f"**Content:** {content if content else 'No content'}")
                                st.markdown(f"**Tags:** {tags or 'None'}")
                                
                                # Delete button
                                if st.button("Delete Memory", key=f"delete_mem_{agent_type}", use_container_width=True):
                                    if memory_bank.delete_memory(selected_memory):
                                        st.success(f"Memory '{selected_memory}' deleted successfully.")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete memory '{selected_memory}'.")
                            
                            if len(sorted_keys) > 20:
                                st.caption(f"Showing 20 of {len(sorted_keys)} memories. Use search to narrow results.")
                    else:
                        st.info("No memories stored yet.")
            
            # Tab 3: Token Status
            with memory_tabs[2]:
                st.markdown("### Token Status")
                
                token_info = session.get_token_status(agent_type)
                
                current_tokens = token_info.get('current_tokens', 0)
                max_tokens = token_info.get('max_tokens', 100000)
                percentage = (current_tokens / max_tokens * 100) if max_tokens > 0 else 0
                
                # Create a colorful gauge for token usage
                if percentage < 50:
                    color = "green"
                elif percentage < 80:
                    color = "orange"
                else:
                    color = "red"
                
                st.markdown(f"""
                <div style="border-radius:10px; padding:10px; background-color: #f0f2f6;">
                    <h4 style="margin:0; padding:0;">Token Usage</h4>
                    <div style="margin-top:10px;">
                        <div style="font-size:2rem; text-align:center; color:{color}; font-weight:bold;">
                            {percentage:.1f}%
                        </div>
                        <div style="width:100%; background-color:#ddd; height:20px; border-radius:10px; margin-top:10px;">
                            <div style="width:{min(percentage, 100)}%; background-color:{color}; height:20px; border-radius:10px;"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-top:5px;">
                            <div>0%</div>
                            <div>100%</div>
                        </div>
                    </div>
                    <div style="margin-top:15px;">
                        <div style="display:flex; justify-content:space-between;">
                            <div>Current tokens:</div>
                            <div>{current_tokens:,}</div>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <div>Maximum allowed:</div>
                            <div>{max_tokens:,}</div>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <div>Summarized message groups:</div>
                            <div>{token_info.get('num_summarized', 0)}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Information about token management
                with st.expander("About Token Management", expanded=False):
                    st.markdown("""
                    **What are tokens?**
                    
                    Tokens are pieces of text that the AI processes. A token is roughly 4 characters or 3/4 of a word in English.
                    
                    **Why is token management important?**
                    
                    AI models have a limit on how many tokens they can process at once. When this limit is approached, older parts of the conversation are automatically summarized to save space while preserving important information.
                    
                    **What happens when tokens get high?**
                    
                    * At around 80% capacity: System prepares for summarization
                    * At around 90% capacity: Older messages are automatically summarized
                    * Summarization preserves key information while reducing token usage
                    """)
                    
                    # Option to manually trigger summarization
                    if percentage > 50:
                        if st.button("Summarize Now", key=f"summarize_{agent_type}", use_container_width=True):
                            conversation = session.get_conversation(agent_type)
                            asyncio.run(conversation.maybe_summarize())
                            session.update_conversation(agent_type, conversation)
                            st.success("Conversation summarized successfully!")
                            st.rerun()
        
        # Chat input
        user_input = st.chat_input(f"Message the {agent_type.capitalize()} Agent...", key=f"{agent_type}_input")
        if user_input:
            # Add user message to history
            session.add_user_message(agent_type, user_input)
            
            # Get response from the agent
            with st.spinner(f"{agent_type.capitalize()} Agent is thinking..."):
                conversation = session.get_conversation(agent_type)
                # Get agent-specific memory bank
                memory_bank = st.session_state.memory_banks.get(agent_type, st.session_state.memory_bank)
                
                response, updated_conversation = asyncio.run(chat.chat_with_agent(
                    agent_type=agent_type,
                    prompt=user_input,
                    agent_modules=agent_modules,
                    client=st.session_state.client,
                    conversation=conversation,
                    project_data=project_data,
                    memory_bank=memory_bank
                ))
                
                # Update conversation
                session.update_conversation(agent_type, updated_conversation)
            
            # Add response to history
            session.add_agent_message(agent_type, response)
            
            # Save agent output to project data
            project_data["agent_outputs"][agent_type][datetime.now().isoformat()] = {
                "input": user_input,
                "output": response
            }
            
            # Update project data
            project_data["updated_at"] = datetime.now().isoformat()
            st.session_state.projects[st.session_state.current_project_id] = project_data
            project.save_project(st.session_state.current_project_id, project_data)
            
            # Auto-save conversation if already saved before
            if current_name != "New Conversation":
                session.save_current_conversation(agent_type)
            
            st.rerun()
        
        # Actions based on current stage
        if can_advance:
            st.subheader("Actions")
            if st.button(advance_button_text, key=f"complete_{agent_type}"):
                # Update project stage
                project_data["stage"] = next_stage
                project_data["updated_at"] = datetime.now().isoformat()
                
                # Save project data
                st.session_state.projects[st.session_state.current_project_id] = project_data
                project.save_project(st.session_state.current_project_id, project_data)
                
                st.rerun()
        
        # Special case for architect in initiation stage
        if agent_type == "architect" and project_data["stage"] == "initiation":
            st.subheader("Actions")
            if st.button("Start Migration Process", key="start_migration"):
                # Update project stage
                project_data["stage"] = "analysis"
                project_data["updated_at"] = datetime.now().isoformat()
                
                # Save project data
                st.session_state.projects[st.session_state.current_project_id] = project_data
                project.save_project(st.session_state.current_project_id, project_data)
                
                st.rerun()
    else:
        st.info(inactive_message) 