#!/usr/bin/env python
import os
import subprocess
import sys
import argparse
from pathlib import Path

def main():
    """
    Run the TheFiveinterFace Streamlit application.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the TheFiveinterFace application")
    parser.add_argument("--port", type=int, default=8501, help="Port to run the application on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()
    
    print(f"Starting Mo-To-Mi Five As Interface on port {args.port}...")
    
    # Get the current directory (where this script is located)
    current_dir = Path(__file__).parent.absolute()
    
    # Path to the app.py file
    app_path = current_dir / "app.py"
    
    if not app_path.exists():
        print(f"Error: Could not find app.py in {current_dir}")
        return 1
    
    # Create necessary directories
    projects_dir = current_dir / "projects"
    projects_dir.mkdir(exist_ok=True)
    
    memory_dir = current_dir / "permanent_memories"
    memory_dir.mkdir(exist_ok=True)
    
    # Run the Streamlit app
    try:
        # Use streamlit run command
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), f"--server.port={args.port}"]
        
        # Add arguments to prevent browser from opening automatically if specified
        if args.no_browser:
            cmd.append("--server.headless=true")
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        return 0
    except Exception as e:
        print(f"Error running Streamlit app: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 