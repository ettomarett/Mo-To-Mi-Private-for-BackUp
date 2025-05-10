#!/usr/bin/env python3
"""
Prompt Injector for Observer Agent

This script injects the Observer Agent system prompt and knowledge base
into the agent's context during initialization.
"""

import os
import sys
import json

def read_file(file_path):
    """Read file content as string"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def main():
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths to prompt and knowledge base files
    system_prompt_path = os.path.join(base_dir, 'observer_agent_system_prompt.md')
    knowledge_base_path = os.path.join(base_dir, 'spring_boot_architecture.md')
    
    # Read the files
    try:
        system_prompt = read_file(system_prompt_path)
        knowledge_base = read_file(knowledge_base_path)
        
        print(f"✓ Successfully loaded system prompt: {len(system_prompt)} characters")
        print(f"✓ Successfully loaded knowledge base: {len(knowledge_base)} characters")
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 1
    
    # Create the configuration object
    config = {
        "agent_name": "Observer Agent",
        "system_prompt": system_prompt,
        "knowledge_base": knowledge_base,
        "version": "1.0.0"
    }
    
    # Write configuration to output file
    output_path = os.path.join(base_dir, 'observer_agent_config.json')
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Agent configuration written to: {output_path}")
    except Exception as e:
        print(f"Error writing configuration: {e}", file=sys.stderr)
        return 1
    
    print("\nThe Observer Agent has been configured with the system prompt and knowledge base.")
    print("Use this configuration file when initializing the agent in the Mo-To-Mi framework.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 