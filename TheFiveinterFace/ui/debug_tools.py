import streamlit as st
import os
import json
from pathlib import Path
import sys
import datetime

def display_debug_tools():
    """
    Display debugging tools UI for inspecting system state
    """
    st.title("🔍 Debug Tools")
    
    # Create tabs for different debug functions
    debug_tabs = st.tabs(["Memory Paths", "Memory Content", "Agent Info", "System State", "Tool Execution"])
    
    # Tab 1: Memory Paths
    with debug_tabs[0]:
        st.markdown("### Memory Storage Paths")
        
        # Check all potential memory paths
        memory_paths = []
        
        # Root directory memory paths
        root_dir = Path(__file__).parent.parent.absolute()
        permanent_memories_path = root_dir / "permanent_memories"
        if permanent_memories_path.exists():
            memory_paths.append(("TheFiveinterFace/permanent_memories", permanent_memories_path))
        
        # Agent-specific paths (proposed naming scheme)
        agent_types = ["Architect", "Observer", "Strategist", "Builder", "Validator"]
        for agent_type in agent_types:
            agent_memory_path = root_dir.parent / "TheFive" / f"{agent_type}Agent" / f"{agent_type}Agent_memories"
            if agent_memory_path.exists():
                memory_paths.append((f"TheFive/{agent_type}Agent/{agent_type}Agent_memories", agent_memory_path))
            
            # Check for old-style paths
            old_path = root_dir.parent / "TheFive" / f"{agent_type}Agent" / "permanent_memories"
            if old_path.exists():
                memory_paths.append((f"TheFive/{agent_type}Agent/permanent_memories", old_path))
            
            # Check AgentSkeleton paths
            skeleton_path = root_dir.parent / "TheFive" / f"{agent_type}Agent" / "AgentSkeleton" / "permanent_memories"
            if skeleton_path.exists():
                memory_paths.append((f"TheFive/{agent_type}Agent/AgentSkeleton/permanent_memories", skeleton_path))
        
        # Display all found memory paths
        if memory_paths:
            st.success(f"Found {len(memory_paths)} memory storage locations")
            for name, path in memory_paths:
                st.markdown(f"**{name}**")
                st.code(str(path))
                
                # Count files
                try:
                    files = list(path.glob("*.txt"))
                    st.text(f"Contains {len(files)} text files")
                except Exception as e:
                    st.error(f"Error counting files: {str(e)}")
        else:
            st.warning("No memory storage locations found")
            
        # Trace the file resolution path for storing memories
        st.markdown("### Memory Path Resolution Test")
        
        test_code = """
        import os
        from pathlib import Path

        # Common path resolution logic
        def test_path_resolution(agent_type):
            # Direct initialization
            direct_path = f"permanent_memories"
            
            # Agent-specific (new style)
            current_dir = Path(__file__).parent.absolute()
            agent_dir = current_dir.parent.parent
            agent_path = agent_dir / f"{agent_type}Agent_memories"
            
            return {
                "direct_path": direct_path,
                "agent_specific_path": str(agent_path),
                "current_dir": str(current_dir),
                "resolved_direct_path": os.path.abspath(direct_path)
            }
            
        # Test for all agent types
        agent_types = ["Architect", "Observer", "Strategist", "Builder", "Validator"]
        for agent in agent_types:
            print(f"Testing paths for {agent}:")
            paths = test_path_resolution(agent)
            for k, v in paths.items():
                print(f"  {k}: {v}")
            print("")
        """
        
        st.code(test_code, language="python")
        
        if st.button("Run Path Resolution Test"):
            st.info("This would execute the test in a real environment")
            
    # Tab 2: Memory Content
    with debug_tabs[1]:
        st.markdown("### Memory Content Explorer")
        
        # Select memory location to explore
        memory_paths_dict = {name: path for name, path in memory_paths} if 'memory_paths' in locals() else {}
        
        if memory_paths_dict:
            selected_path = st.selectbox(
                "Select memory location",
                options=list(memory_paths_dict.keys())
            )
            
            if selected_path:
                path = memory_paths_dict[selected_path]
                try:
                    # Look for index.json
                    index_path = path / "index.json"
                    if index_path.exists():
                        with open(index_path, 'r') as f:
                            index_data = json.load(f)
                            
                        st.markdown("### Memory Index")
                        st.json(index_data)
                        
                        # Show specific memory contents
                        if index_data:
                            selected_memory = st.selectbox(
                                "Select memory to view",
                                options=list(index_data.keys())
                            )
                            
                            if selected_memory:
                                memory_file = path / index_data[selected_memory]["filename"]
                                if memory_file.exists():
                                    with open(memory_file, 'r') as f:
                                        content = f.read()
                                    
                                    st.markdown(f"### Memory Content: {selected_memory}")
                                    st.text_area("Content", value=content, height=200)
                                    
                                    # Show metadata
                                    st.markdown("### Metadata")
                                    st.json(index_data[selected_memory])
                                else:
                                    st.error(f"Memory file not found: {memory_file}")
                    else:
                        # No index file, just list TXT files
                        files = list(path.glob("*.txt"))
                        st.markdown(f"### Memory Files ({len(files)})")
                        
                        for file in files:
                            st.text(file.name)
                        
                        selected_file = st.selectbox(
                            "Select file to view",
                            options=[f.name for f in files]
                        )
                        
                        if selected_file:
                            file_path = path / selected_file
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            st.markdown(f"### File Content: {selected_file}")
                            st.text_area("Content", value=content, height=200)
                            
                except Exception as e:
                    st.error(f"Error reading memory data: {str(e)}")
        else:
            st.warning("No memory locations found to explore")
    
    # Tab 3: Agent Info
    with debug_tabs[2]:
        st.markdown("### Agent Information")
        
        # Display agent module information
        if 'agent_modules' in st.session_state:
            agents = st.session_state.agent_modules
            st.success(f"Found {len(agents)} agent modules")
            
            for agent_name, agent_module in agents.items():
                with st.expander(f"{agent_name.capitalize()} Agent"):
                    st.markdown(f"**Module:** {agent_module.__name__}")
                    st.markdown(f"**Path:** {agent_module.__file__}")
                    
                    # Get agent attributes
                    attributes = [attr for attr in dir(agent_module) if not attr.startswith('__')]
                    st.markdown(f"**Attributes:** {', '.join(attributes)}")
                    
                    # Check for memory bank related attributes/methods
                    memory_related = [attr for attr in attributes if 'mem' in attr.lower()]
                    if memory_related:
                        st.markdown(f"**Memory-related attributes:** {', '.join(memory_related)}")
        else:
            st.warning("No agent modules found in session state")
    
    # Tab 4: System State
    with debug_tabs[3]:
        st.markdown("### System State")
        
        # Display session state
        with st.expander("Session State", expanded=False):
            # Filter out large objects from session state for display
            filtered_state = {k: v for k, v in st.session_state.items() 
                             if not str(type(v)).endswith("module'>") 
                             and not str(type(v)).endswith("function'>")
                             and not str(type(v)).endswith("method'>")}
            
            st.json(filtered_state)
        
        # Display environment variables
        with st.expander("Environment Variables", expanded=False):
            env_vars = {k: v for k, v in os.environ.items() 
                       if not k.startswith('PYTHON') and not k.startswith('_')}
            st.json(env_vars)
        
        # Display system paths
        with st.expander("System Paths", expanded=False):
            st.code("\n".join(sys.path))
            
    # Tab 5: Tool Execution Debugging
    with debug_tabs[4]:
        st.markdown("### Tool Execution Debugging")
        
        # Enable tool debugging
        if 'tool_debug_enabled' not in st.session_state:
            st.session_state.tool_debug_enabled = False
            
        if 'tool_debug_log' not in st.session_state:
            st.session_state.tool_debug_log = []
            
        # Tool debugging controls
        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.tool_debug_enabled = st.toggle(
                "Enable tool execution logging", 
                value=st.session_state.tool_debug_enabled
            )
        with col2:
            if st.button("Clear logs"):
                st.session_state.tool_debug_log = []
                st.success("Debug logs cleared")
        
        # Debug log mode selection
        debug_level = st.radio(
            "Debug log level",
            ["Basic", "Detailed", "Verbose"],
            horizontal=True
        )
        
        st.markdown("### Debugging Setup Instructions")
        
        # Code snippet for tool_executor.py
        tool_executor_debug_code = """
        # Add at top of file
        import logging
        import datetime
        import streamlit as st
        
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("tool_executor")
        
        # Modify the execute_tool function
        def execute_tool(tool_name: str, params: Dict[str, Any], conversation=None, memory_bank=None) -> Dict[str, Any]:
            '''Execute the specified tool with the given parameters'''
            
            # Debug logging
            debug_enabled = getattr(st.session_state, 'tool_debug_enabled', False)
            if debug_enabled:
                timestamp = datetime.datetime.now().isoformat()
                debug_entry = {
                    "timestamp": timestamp,
                    "tool": tool_name,
                    "params": params,
                    "memory_bank_type": str(type(memory_bank)),
                    "memory_bank_dir": getattr(memory_bank, "storage_dir", "unknown") if memory_bank else "none"
                }
                
                # Log the tool call
                logger.debug(f"Tool call: {tool_name} with params: {params}")
                
                # Store in session state for UI display
                if 'tool_debug_log' in st.session_state:
                    st.session_state.tool_debug_log.append(debug_entry)
                    
            # Continue with existing code...
        """
        
        # Code snippet for memory_bank store_memory function debugging
        memory_bank_debug_code = """
        # Add to store_memory function in memory_bank.py
        
        def store_memory(self, content: str, key: Optional[str] = None, tags: Optional[List[str]] = None, has_explicit_permission: bool = False) -> str:
            '''
            Store a new memory
            
            Args:
                content: The content to store
                key: Optional key to use (if None, one will be generated)
                tags: Optional list of tags for categorization
                has_explicit_permission: Flag indicating if explicit permission was granted
                
            Returns:
                The key of the stored memory or error message
            '''
            # Debug logging at the start of the function
            debug_enabled = getattr(st.session_state, 'tool_debug_enabled', False)
            if debug_enabled:
                debug_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "operation": "store_memory",
                    "storage_dir": self.storage_dir,
                    "content": content[:50] + "..." if len(content) > 50 else content,
                    "key": key,
                    "has_permission": has_explicit_permission
                }
                
                # Log the memory operation
                logging.debug(f"Memory store operation: {debug_entry}")
                
                # Store in session state for UI display
                if 'tool_debug_log' in st.session_state:
                    st.session_state.tool_debug_log.append(debug_entry)
                    
            # Add debug points for permission checking
            if not has_explicit_permission and (
                "prefer" in content.lower() or 
                "like" in content.lower() or 
                "my " in content.lower() or
                "I am" in content or
                "I'm" in content or
                "we use" in content.lower() or
                "our team" in content.lower()
            ):
                if debug_enabled and 'tool_debug_log' in st.session_state:
                    st.session_state.tool_debug_log.append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "operation": "permission_check_failed",
                        "content": content[:50] + "..." if len(content) > 50 else content,
                        "result": "ERROR: Permission required but not provided"
                    })
                return "ERROR: Cannot store user preferences or personal information without explicit permission"
                
            # Continue with the rest of the function...
        """
        
        # Instructions
        st.markdown("#### 1. Modify tool_executor.py")
        st.code(tool_executor_debug_code, language="python")
        
        st.markdown("#### 2. Modify memory_bank.py")
        st.code(memory_bank_debug_code, language="python")
        
        # View debug logs
        st.markdown("### Debug Logs")
        if not st.session_state.tool_debug_log:
            st.info("No tool execution logs yet. Enable debugging and perform some actions to see logs here.")
        else:
            # Display logs based on selected level
            logs_to_show = st.session_state.tool_debug_log
            
            # Show logs in a dataframe for cleaner display
            log_data = []
            for log in logs_to_show:
                # Adjust displayed fields based on debug level
                if debug_level == "Basic":
                    # Show minimal info
                    log_data.append({
                        "Time": log.get("timestamp", "").split("T")[1][:8],
                        "Tool/Operation": log.get("tool", log.get("operation", "Unknown")),
                        "Key": log.get("key", log.get("params", {}).get("key", "None")),
                        "Status": "Failed" if "ERROR" in str(log) else "Success"
                    })
                elif debug_level == "Detailed":
                    # Show more details
                    log_data.append({
                        "Time": log.get("timestamp", "").split("T")[1][:8],
                        "Tool/Operation": log.get("tool", log.get("operation", "Unknown")),
                        "Parameters": str(log.get("params", {})),
                        "Storage Dir": log.get("storage_dir", log.get("memory_bank_dir", "Unknown")),
                        "Result": log.get("result", "No result recorded")
                    })
                else:  # Verbose
                    # Show everything as JSON
                    st.json(log)
            
            # Show as dataframe for Basic and Detailed views
            if debug_level != "Verbose" and log_data:
                st.dataframe(log_data)
                
        # Tool execution tester
        st.markdown("### Tool Execution Tester")
        with st.form("tool_tester"):
            test_tool = st.selectbox(
                "Select tool to test",
                ["memory", "calculator", "filesystem", "token_manager"]
            )
            
            # Dynamic parameters based on selected tool
            if test_tool == "memory":
                operation = st.selectbox(
                    "Operation",
                    ["store", "retrieve", "search", "delete", "list"]
                )
                
                key = st.text_input("Key", value="test_key")
                content = st.text_area("Content", value="This is test content")
                has_permission = st.checkbox("has_explicit_permission", value=True)
                
                # Build parameters dictionary
                test_params = {
                    "operation": operation,
                    "key": key,
                }
                
                if operation == "store":
                    test_params["content"] = content
                    test_params["has_explicit_permission"] = has_permission
                
            elif test_tool == "calculator":
                expression = st.text_input("Expression", value="2 + 2")
                test_params = {"expression": expression}
                
            elif test_tool == "filesystem":
                operation = st.selectbox(
                    "Operation",
                    ["list_dir", "read_file", "search_files"]
                )
                path = st.text_input("Path", value=".")
                test_params = {"operation": operation, "path": path}
                
            elif test_tool == "token_manager":
                operation = st.selectbox(
                    "Operation",
                    ["status", "reset", "summarize"]
                )
                test_params = {"operation": operation}
            
            submitted = st.form_submit_button("Run Tool Test")
            
            if submitted:
                st.info(f"This would execute the {test_tool} tool with parameters: {test_params}")
                st.warning("Tool execution testing requires server-side implementation") 