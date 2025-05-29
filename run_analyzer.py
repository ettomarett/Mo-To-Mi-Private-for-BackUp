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

def parse_analyzer_output(output_file):
    """
    Parse the JSON output from the analyzer
    """
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading output file: {e}")
        sys.exit(1)

def format_for_llm(analysis_data):
    """
    Format the analysis data in a way that's optimized for LLM consumption
    """
    # Create a summary string to send to the LLM
    summary = []
    
    # Components summary
    if "componentsSummary" in analysis_data:
        summary.append("## Components Summary")
        cs = analysis_data["componentsSummary"]
        summary.append(f"Total components: {cs.get('totalComponents', 0)}")
        
        if "typeBreakdown" in cs:
            summary.append("\nComponent breakdown:")
            for comp_type, count in cs["typeBreakdown"].items():
                summary.append(f"- {comp_type}: {count}")
        
        if "antiPatterns" in cs:
            summary.append("\nDetected anti-patterns:")
            for pattern, count in cs["antiPatterns"].items():
                summary.append(f"- {pattern}: {count}")
    
    # Domain distance matrix - this is valuable for service boundary identification
    if "domainDistanceMatrix" in analysis_data:
        summary.append("\n## Domain Distance Matrix")
        summary.append("(Lower values indicate stronger coupling - harder to separate)")
        
        # Format as a table for better readability
        matrix = analysis_data["domainDistanceMatrix"]
        domains = list(matrix.keys())
        
        # Table header
        header = "Domain | " + " | ".join(domains)
        separator = "--- | " + " | ".join(["---"] * len(domains))
        summary.append("\n" + header)
        summary.append(separator)
        
        # Table rows
        for domain in domains:
            distances = matrix[domain]
            row = f"{domain} | "
            row += " | ".join([f"{distances.get(d, 'N/A')}" for d in domains])
            summary.append(row)
    
    # API endpoints by domain
    if "apiEndpointsByDomain" in analysis_data:
        summary.append("\n## API Endpoints by Domain")
        
        for domain, endpoints in analysis_data["apiEndpointsByDomain"].items():
            summary.append(f"\n### {domain}")
            for endpoint in endpoints:
                path = endpoint.get("path", "")
                method = endpoint.get("method", "")
                controller = endpoint.get("controller", "")
                entities = endpoint.get("accessedEntities", [])
                
                summary.append(f"- {method} {path}")
                if entities:
                    summary.append(f"  - Accessed entities: {', '.join(entities)}")
    
    # Entity relationships
    if "entityRelationships" in analysis_data:
        summary.append("\n## Entity Relationships")
        
        for rel in analysis_data["entityRelationships"]:
            source = rel.get("sourceEntity", "")
            target = rel.get("targetEntity", "")
            rel_type = rel.get("type", "")
            field = rel.get("fieldName", "")
            
            summary.append(f"- {source} -[{rel_type}]-> {target} (field: {field})")
    
    return "\n".join(summary)

def save_formatted_output(formatted_data, output_file="analysis_for_llm.txt"):
    """
    Save the formatted analysis for easy consumption by the LLM
    """
    with open(output_file, 'w') as f:
        f.write(formatted_data)
    print(f"Formatted analysis saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Run Java analyzer on Spring Boot project and format output for LLM")
    parser.add_argument("project_path", help="Path to the Spring Boot project to analyze")
    parser.add_argument("--jar", default="target/java-analyzer.jar", help="Path to the Java analyzer JAR file")
    parser.add_argument("--output", default="analysis_for_llm.txt", help="Output file for formatted analysis")
    
    args = parser.parse_args()
    
    # Run the analyzer
    output_file = run_java_analyzer(args.project_path, args.jar)
    
    # Parse the output
    analysis_data = parse_analyzer_output(output_file)
    
    # Format for LLM
    formatted_data = format_for_llm(analysis_data)
    
    # Save formatted output
    save_formatted_output(formatted_data, args.output)
    
    print(f"\nAnalysis complete! You can now use {args.output} with your LLM for microservice boundary identification.")

if __name__ == "__main__":
    main() 