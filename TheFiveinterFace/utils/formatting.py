import sys
from pathlib import Path

# Add the TheFiveinterFace directory to the Python path if not already there
current_dir = Path(__file__).parent.parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))


def format_agent_message(content):
    """
    Format agent messages to separate thinking from response
    
    Args:
        content (str): Raw agent message content
        
    Returns:
        str: HTML-formatted message content
    """
    # Check if the message contains thinking section
    if "<think>" in content and "</think>" in content:
        # Split the thinking part from the response
        thinking_part = content[content.find("<think>"):content.find("</think>") + 8]
        response_part = content.replace(thinking_part, "").strip()
        
        # Extract just the content inside the <think> tags
        thinking_content = thinking_part[7:-8]  # Remove <think> and </think> tags
        
        # Create HTML with the separated components
        formatted_html = f"""
        <div class="agent-thinking">{thinking_content}</div>
        <div class="agent-response">{response_part}</div>
        """
        return formatted_html
    else:
        # If no thinking part, just return the content in the response style
        return f'<div class="agent-response">{content}</div>' 