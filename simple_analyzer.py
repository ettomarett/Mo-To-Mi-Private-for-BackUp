#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import argparse
from pathlib import Path

def run_java_analyzer(project_path, jar_path="target/java-analyzer.jar"):
    """
    Run the Java analyzer on the target Spring Boot project
    """
    print(f"Analyzing Spring Boot project at: {project_path}")
    
    # Ensure the JAR file exists
    if not os.path.exists(jar_path):
        print(f"Error: Java analyzer JAR not found at {jar_path}")
        print("Please build the analyzer first with 'mvn package'")
        sys.exit(1)
    
    # Run the Java analyzer
    try:
        result = subprocess.run(
            ["java", "-jar", jar_path, project_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running Java analyzer: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)
    
    # Check if the output file was created
    output_file = "analysis_output.json"
    if not os.path.exists(output_file):
        print(f"Error: Expected output file {output_file} was not created")
        sys.exit(1)
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Run Java analyzer on Spring Boot project")
    parser.add_argument("project_path", help="Path to the Spring Boot project to analyze")
    parser.add_argument("--jar", default="target/java-analyzer.jar", help="Path to the Java analyzer JAR file")
    
    args = parser.parse_args()
    
    # Run the analyzer
    output_file = run_java_analyzer(args.project_path, args.jar)
    
    print(f"Analysis complete! Results in {output_file}")

if __name__ == "__main__":
    main() 