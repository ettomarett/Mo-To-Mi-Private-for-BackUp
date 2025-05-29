#!/usr/bin/env python
"""
Test script for analyzing the complex Spring Boot application.
This script will test the Java analyzer's ability to handle complex Spring applications
with nested package structures, inheritance hierarchies, annotations, and dependencies.
"""

import os
import sys
import json
import logging
import time  # Added for timing information
from pathlib import Path

# Set up logging - make it more verbose
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("complex_spring_analysis.log"),
        logging.StreamHandler(sys.stdout)  # Explicitly log to stdout
    ]
)
logger = logging.getLogger(__name__)

# Print script info immediately
print("=== Complex Spring Boot Application Analyzer ===")
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")

# Import the Java analyzer
try:
    print("Importing JavaAnalyzer...")
    from python_wrapper import JavaAnalyzer
    print("JavaAnalyzer imported successfully")
except ImportError as e:
    print(f"Error importing JavaAnalyzer: {e}")
    logger.error(f"Error importing JavaAnalyzer: {e}")
    sys.exit(1)

def print_component_details(component, indent=""):
    """Print detailed information about a component."""
    component_type = ""
    if component.get('springComponent') == True:
        component_type = f"@{component.get('springComponentType', 'Unknown')}"
    
    print(f"{indent}- {component.get('name')} ({component.get('type')}) {component_type}")
    print(f"{indent}  Package: {component.get('packageName')}")
    print(f"{indent}  Methods: {len(component.get('methods', []))}")
    
    # Display dependencies
    if component.get('dependencies'):
        print(f"{indent}  Dependencies:")
        for dep in component.get('dependencies', []):
            print(f"{indent}    → {dep.get('target')}")
    
    # Display Spring specific info
    if component.get('springComponent') == True:
        spring_annotations = component.get('annotations', [])
        if spring_annotations:
            print(f"{indent}  Spring Annotations:")
            for annotation in spring_annotations:
                print(f"{indent}    → @{annotation}")

def analyze_complex_spring():
    """Analyze the complex Spring Boot application."""
    
    # Initialize the analyzer
    print("Initializing JavaAnalyzer...")
    analyzer = JavaAnalyzer()
    
    # Define project details
    project_name = "ComplexSpringProject"
    source_path = os.path.join(os.path.dirname(__file__), "test_samples/complex_spring/src/main/java")
    
    # Verify source_path exists
    if not os.path.exists(source_path):
        print(f"ERROR: Source path does not exist: {source_path}")
        logger.error(f"Source path does not exist: {source_path}")
        return False
    
    print(f"Project name: {project_name}")
    print(f"Source path: {source_path}")
    print(f"Source path exists: {os.path.exists(source_path)}")
    
    logger.info(f"Analyzing project: {project_name}")
    logger.info(f"Source path: {source_path}")
    
    # Run the analysis
    try:
        print("\nStarting analysis...")
        start_time = time.time()
        
        print("Calling analyzer.analyze_project...")
        analysis = analyzer.analyze_project(project_name, source_path)
        
        end_time = time.time()
        print(f"Analysis completed in {end_time - start_time:.2f} seconds")
        
        # Verify we have analysis data
        if not analysis or 'components' not in analysis:
            print("ERROR: Analysis did not return expected data structure")
            return False
        
        # Count Spring components
        spring_components = [c for c in analysis.get('components', []) if c.get('springComponent') == True]
        
        # Print summary
        print(f"\nAnalysis Summary:")
        print(f"Total components: {len(analysis.get('components', []))}")
        print(f"Spring components: {len(spring_components)}")
        
        # Print Spring component types breakdown
        spring_types = {}
        for comp in spring_components:
            comp_type = comp.get('springComponentType')
            spring_types[comp_type] = spring_types.get(comp_type, 0) + 1
        
        print(f"\nSpring Component Types:")
        for comp_type, count in spring_types.items():
            print(f"- {comp_type}: {count}")
        
        # Print package structure
        packages = {}
        for comp in analysis.get('components', []):
            pkg = comp.get('packageName')
            if pkg not in packages:
                packages[pkg] = []
            packages[pkg].append(comp)
        
        print(f"\nPackage Structure ({len(packages)} packages):")
        for pkg_name, pkg_components in sorted(packages.items()):
            spring_count = len([c for c in pkg_components if c.get('springComponent') == True])
            print(f"- {pkg_name} ({len(pkg_components)} components, {spring_count} Spring components)")
        
        # Print inheritance relationships
        print(f"\nInheritance Relationships:")
        for comp in analysis.get('components', []):
            if comp.get('superClassName'):
                print(f"- {comp.get('name')} → extends → {comp.get('superClassName')}")
        
        # Print circular dependencies if any
        print(f"\nCircular Dependencies:")
        circular_deps_found = False
        for comp in analysis.get('components', []):
            deps = comp.get('dependencies', [])
            for dep in deps:
                # Check if any of this component's dependencies also depend on it
                target_name = dep.get('target')
                target_comp = next((c for c in analysis.get('components', []) if c.get('name') == target_name), None)
                if target_comp:
                    target_deps = target_comp.get('dependencies', [])
                    if any(d.get('target') == comp.get('name') for d in target_deps):
                        print(f"- {comp.get('name')} ↔ {target_name}")
                        circular_deps_found = True
        
        if not circular_deps_found:
            print("  None detected")
        
        # Print suggested boundaries
        boundaries = analysis.get('suggestedBoundaries', [])
        print(f"\nSuggested Service Boundaries ({len(boundaries)}):")
        if boundaries:
            for boundary in boundaries:
                confidence = boundary.get('confidence', 0) * 100
                print(f"- {boundary.get('name')}")
                print(f"  Package: {boundary.get('package')}")
                print(f"  Components: {len(boundary.get('components', []))}")
                print(f"  Confidence: {confidence:.1f}%")
        else:
            print("  None detected - application may be too small or already well-structured")
        
        # Print detailed component information for key Spring components
        print(f"\nKey Spring Components:")
        for comp in spring_components:
            print_component_details(comp)
            print()
            
        # Save the analysis to a file for further inspection
        output_file = "complex_spring_analysis.json"
        print(f"Saving analysis to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Analysis saved to {output_file}")
        
        print("Analysis complete!")
        return True
        
    except Exception as e:
        print(f"ERROR analyzing project: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error analyzing project: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("Starting complex_spring analysis script...")
    if analyze_complex_spring():
        logger.info("Complex Spring analysis completed successfully")
        print("ANALYSIS COMPLETED SUCCESSFULLY")
    else:
        logger.error("Complex Spring analysis failed")
        print("ANALYSIS FAILED")
        sys.exit(1) 