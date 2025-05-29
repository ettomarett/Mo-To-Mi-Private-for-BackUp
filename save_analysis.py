#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

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

def format_for_human_reading(analysis_data):
    """
    Format the analysis data in a way that's easy for humans to read
    """
    summary = []
    
    # Components summary
    if "componentsSummary" in analysis_data:
        summary.append("# Components Summary")
        cs = analysis_data["componentsSummary"]
        summary.append(f"Total components: {cs.get('totalComponents', 0)}")
        
        if "typeBreakdown" in cs:
            summary.append("\n## Component breakdown:")
            for comp_type, count in cs["typeBreakdown"].items():
                summary.append(f"- {comp_type}: {count}")
        
        if "antiPatterns" in cs:
            summary.append("\n## Detected anti-patterns:")
            for pattern, count in cs["antiPatterns"].items():
                summary.append(f"- {pattern}: {count}")
    
    # Domain distance matrix - this is valuable for service boundary identification
    if "domainDistanceMatrix" in analysis_data:
        summary.append("\n# Domain Distance Matrix")
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
        summary.append("\n# API Endpoints by Domain")
        
        for domain, endpoints in analysis_data["apiEndpointsByDomain"].items():
            summary.append(f"\n## {domain}")
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
        summary.append("\n# Entity Relationships")
        
        for rel in analysis_data["entityRelationships"]:
            source = rel.get("sourceEntity", "")
            target = rel.get("targetEntity", "")
            rel_type = rel.get("type", "")
            field = rel.get("fieldName", "")
            
            summary.append(f"- {source} -[{rel_type}]-> {target} (field: {field})")
    
    return "\n".join(summary)

def ensure_directory_exists(directory_path):
    """
    Ensure the specified directory exists, create it if it doesn't
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_analysis_results(raw_data, formatted_data, output_dir, project_name):
    """
    Save both raw JSON and formatted analysis to the output directory
    """
    # Create timestamp for unique folder naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a directory for this analysis run
    if project_name:
        analysis_dir = ensure_directory_exists(f"{output_dir}/{project_name}_{timestamp}")
    else:
        analysis_dir = ensure_directory_exists(f"{output_dir}/analysis_{timestamp}")
    
    # Save raw JSON
    raw_output_path = f"{analysis_dir}/analysis_raw.json"
    with open(raw_output_path, 'w') as f:
        json.dump(raw_data, f, indent=2)
    
    # Save formatted markdown
    formatted_output_path = f"{analysis_dir}/analysis_report.md"
    with open(formatted_output_path, 'w') as f:
        f.write(formatted_data)
    
    print(f"Analysis saved to directory: {analysis_dir}")
    print(f"- Raw JSON data: {raw_output_path}")
    print(f"- Formatted report: {formatted_output_path}")
    
    return analysis_dir

def main():
    parser = argparse.ArgumentParser(description="Run Java analyzer on Spring Boot project and save results")
    parser.add_argument("project_path", help="Path to the Spring Boot project to analyze")
    parser.add_argument("--project-name", help="Name of the project (used for output folder naming)")
    parser.add_argument("--jar", default="target/java-analyzer.jar", help="Path to the Java analyzer JAR file")
    parser.add_argument("--output-dir", default="analysis_results", help="Directory to save analysis results")
    
    args = parser.parse_args()
    
    # Run the analyzer
    output_file = run_java_analyzer(args.project_path, args.jar)
    
    # Parse the raw JSON output
    analysis_data = parse_analyzer_output(output_file)
    
    # Format for human reading
    formatted_data = format_for_human_reading(analysis_data)
    
    # Save both raw and formatted data to the output directory
    output_dir = save_analysis_results(
        analysis_data, 
        formatted_data, 
        args.output_dir,
        args.project_name
    )
    
    print(f"\nAnalysis complete! Results saved to {output_dir}")

if __name__ == "__main__":
    main() 