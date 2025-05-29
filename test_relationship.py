#!/usr/bin/env python
"""
Test script for the component relationship analysis in the Java Analyzer Service.
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the Java analyzer
from python_wrapper import JavaAnalyzer

def main():
    """Test the component relationship analysis capabilities."""
    
    print("=== Component Relationship Analysis Test ===")
    
    # Initialize the analyzer
    analyzer = JavaAnalyzer()
    
    # Define project details
    project_name = "ComplexSpringRelationships"
    source_path = os.path.join(os.path.dirname(__file__), "test_samples/complex_spring/src/main/java")
    
    print(f"Project: {project_name}")
    print(f"Source path: {source_path}")
    print(f"Source exists: {os.path.exists(source_path)}")
    
    # Run the analysis
    try:
        print("Starting analysis...")
        analysis = analyzer.analyze_project(project_name, source_path)
        print("Analysis completed!")
        
        # Print components
        components = analysis.get('components', [])
        print(f"\nComponents found: {len(components)}")
        for comp in components:
            print(f"- {comp.get('name')} ({comp.get('type')}) - Spring: {comp.get('springComponent', False)}")
        
        # Print relationships if available
        relationships = analysis.get('componentRelationships', [])
        print(f"\nComponent relationships found: {len(relationships)}")
        for rel in relationships:
            print(f"- {rel.get('sourceComponent')} -> {rel.get('targetComponent')} ({rel.get('type')})")
        
        # Print coupling metrics if available
        coupling_scores = analysis.get('componentCouplingScores', {})
        print(f"\nComponent coupling scores: {len(coupling_scores)}")
        for comp, score in coupling_scores.items():
            print(f"- {comp}: {score}")
        
        # Print package metrics if available
        package_metrics = analysis.get('packageCouplingScores', {})
        print(f"\nPackage coupling scores: {len(package_metrics)}")
        for pkg, score in package_metrics.items():
            print(f"- {pkg}: {score}")
        
        # Save the analysis to a file for further inspection
        output_file = "relationship_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error analyzing project: {e}", exc_info=True)

if __name__ == "__main__":
    main() 