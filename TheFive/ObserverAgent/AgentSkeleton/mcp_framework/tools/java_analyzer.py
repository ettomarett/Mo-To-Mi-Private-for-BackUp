"""
Java analyzer tool for the Observer Agent.

This module integrates the JavaParser-based analyzer with the MCP framework.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the base path to the Java analyzer service
base_dir = Path(__file__).parent.parent.parent.parent.parent  # TheFive
java_analyzer_path = base_dir / "ObserverAgent" / "java_analyzer_service"

# Add the Java analyzer path to sys.path
if str(java_analyzer_path) not in sys.path:
    sys.path.append(str(java_analyzer_path))

def execute_java_analysis(params):
    """
    Execute the Java analyzer with the given parameters.
    
    Args:
        params (dict): Parameters for the Java analyzer
        
    Returns:
        dict: The result of the operation
    """
    try:
        # Import the Java analyzer
        from java_analyzer_service.java_analyzer_tool import execute_java_analyzer
        
        # Execute the analyzer
        result = execute_java_analyzer(params)
        
        return result
    except ImportError as e:
        logger.error(f"Error importing Java analyzer: {str(e)}")
        return {
            "error": f"Java analyzer module not found: {str(e)}",
            "status": "error",
            "note": "Make sure the Java analyzer service is properly installed and the path is correct."
        }
    except Exception as e:
        logger.exception(f"Error executing Java analyzer: {str(e)}")
        return {
            "error": f"Error executing Java analyzer: {str(e)}",
            "status": "error"
        } 