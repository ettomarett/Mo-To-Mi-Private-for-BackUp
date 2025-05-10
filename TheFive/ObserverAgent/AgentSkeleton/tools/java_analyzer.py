"""
Java Analyzer for Spring Boot applications
This module provides tools for analyzing Spring Boot monolithic applications,
identifying dependencies, and detecting potential microservice boundaries.
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JavaAnalyzer:
    """Main class for analyzing Java/Spring Boot applications"""
    
    def __init__(self, project_path=None):
        self.project_path = project_path
        self.analysis_dir = None
        self.metadata = {
            "project_name": os.path.basename(project_path) if project_path else None,
            "analysis_date": None,
            "files_analyzed": 0,
            "components_found": {
                "controllers": 0,
                "services": 0,
                "repositories": 0,
                "entities": 0
            }
        }
        
    def setup_analysis_directory(self, project_name=None):
        """Set up the directory structure for analysis outputs"""
        if not project_name and not self.metadata["project_name"]:
            raise ValueError("Project name must be provided")
            
        project_name = project_name or self.metadata["project_name"]
        base_dir = Path("analysis") / project_name
        
        # Create main directories
        dirs = [
            base_dir / "source_code",
            base_dir / "parsed_structure",
            base_dir / "visualizations",
            base_dir / "reports"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.analysis_dir = base_dir
        return str(base_dir)
        
    def parse_java_code(self, file_path):
        """Parse a Java file to extract class structure and annotations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic parsing logic - in a real implementation, this would use JavaParser or similar
            component_type = self._detect_component_type(content)
            dependencies = self._extract_dependencies(content)
            class_info = {
                "file_path": file_path,
                "component_type": component_type,
                "dependencies": dependencies,
                "package": self._extract_package(content),
                "imports": self._extract_imports(content)
            }
            
            return class_info
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return None
            
    def _detect_component_type(self, content):
        """Detect Spring component type from annotations"""
        if "@RestController" in content or "@Controller" in content:
            self.metadata["components_found"]["controllers"] += 1
            return "controller"
        elif "@Service" in content:
            self.metadata["components_found"]["services"] += 1
            return "service"
        elif "@Repository" in content:
            self.metadata["components_found"]["repositories"] += 1
            return "repository"
        elif "@Entity" in content:
            self.metadata["components_found"]["entities"] += 1
            return "entity"
        else:
            return "unknown"
            
    def _extract_package(self, content):
        """Extract package name from Java file"""
        package_line = next((line for line in content.split('\n') if line.strip().startswith("package ")), "")
        if package_line:
            return package_line.strip().replace("package ", "").replace(";", "")
        return None
        
    def _extract_imports(self, content):
        """Extract import statements from Java file"""
        imports = []
        for line in content.split('\n'):
            if line.strip().startswith("import "):
                imp = line.strip().replace("import ", "").replace(";", "")
                imports.append(imp)
        return imports
        
    def _extract_dependencies(self, content):
        """Extract declared dependencies in the class"""
        dependencies = []
        # Simple regex-based approach - real implementation would use AST
        # Look for @Autowired, constructor injection, etc
        return dependencies
        
    def analyze_project(self, project_path=None):
        """Main method to analyze an entire Spring Boot project"""
        path = project_path or self.project_path
        if not path:
            raise ValueError("Project path not specified")
            
        self.project_path = path
        self.metadata["project_name"] = os.path.basename(path)
        
        # Set up analysis directory
        self.setup_analysis_directory()
        
        # Find all Java files
        java_files = self._find_java_files(path)
        self.metadata["files_analyzed"] = len(java_files)
        
        # Parse all files
        parsed_files = []
        for file in java_files:
            parsed = self.parse_java_code(file)
            if parsed:
                parsed_files.append(parsed)
                
        # Save parsed structure
        self._save_parsed_structure(parsed_files)
        
        # Generate dependency graph
        self.generate_dependency_graph(parsed_files)
        
        # Generate analysis report
        self.generate_report(parsed_files)
        
        return self.metadata
        
    def _find_java_files(self, directory):
        """Find all Java files in the project"""
        java_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(os.path.join(root, file))
        return java_files
        
    def _save_parsed_structure(self, parsed_files):
        """Save parsed structure as JSON"""
        if not self.analysis_dir:
            self.setup_analysis_directory()
            
        output_path = self.analysis_dir / "parsed_structure" / "structure.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_files, f, indent=2)
            
        return str(output_path)
        
    def generate_dependency_graph(self, parsed_files=None):
        """Generate a dependency graph visualization"""
        # Placeholder for dependency graph generation
        # Real implementation would use networkx or similar to create visualizations
        if not self.analysis_dir:
            self.setup_analysis_directory()
            
        # Mock output file
        output_path = self.analysis_dir / "visualizations" / "dependency_graph.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Dependency Graph Placeholder\n")
        
        return str(output_path)
        
    def generate_report(self, parsed_files=None):
        """Generate an analysis report with findings"""
        if not self.analysis_dir:
            self.setup_analysis_directory()
            
        # Create a basic report
        report = {
            "project_name": self.metadata["project_name"],
            "component_summary": self.metadata["components_found"],
            "findings": {
                "architecture_type": self._determine_architecture_type(parsed_files),
                "potential_microservices": self._identify_microservice_boundaries(parsed_files),
                "anti_patterns": self._identify_anti_patterns(parsed_files)
            }
        }
        
        # Save the report
        output_path = self.analysis_dir / "reports" / "analysis_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        return str(output_path)
        
    def _determine_architecture_type(self, parsed_files):
        """Determine if architecture is package-by-layer or package-by-feature"""
        # Simplified logic - real implementation would be more sophisticated
        if not parsed_files:
            return "unknown"
            
        packages = {}
        for file in parsed_files:
            package = file.get("package")
            if package:
                component_type = file.get("component_type", "unknown")
                if package not in packages:
                    packages[package] = []
                packages[package].append(component_type)
                
        # If multiple component types in same packages, likely package-by-feature
        mixed_packages = sum(1 for types in packages.values() if len(set(types)) > 1)
        if mixed_packages > len(packages) / 2:
            return "package-by-feature"
        else:
            return "package-by-layer"
            
    def _identify_microservice_boundaries(self, parsed_files):
        """Identify potential microservice boundaries"""
        # Placeholder - real implementation would use graph analysis
        return [
            {
                "name": "user-service",
                "components": ["UserController", "UserService", "UserRepository"]
            },
            {
                "name": "product-service",
                "components": ["ProductController", "ProductService", "ProductRepository"]
            }
        ]
        
    def _identify_anti_patterns(self, parsed_files):
        """Identify anti-patterns in the codebase"""
        # Placeholder - real implementation would detect god classes, etc.
        return [
            {
                "type": "god_class",
                "location": "com.example.service.LargeService",
                "description": "Class has too many methods and responsibilities"
            }
        ]

# Simplified function interface for the agent
def analyze_spring_boot_project(project_path):
    """Analyze a Spring Boot project at the specified path"""
    analyzer = JavaAnalyzer(project_path)
    metadata = analyzer.analyze_project()
    return {
        "status": "success",
        "message": f"Analyzed {metadata['files_analyzed']} files in {metadata['project_name']}",
        "output_directory": str(analyzer.analysis_dir),
        "component_count": metadata["components_found"]
    }

def get_project_architecture_type(project_path):
    """Determine the architecture type of a Spring Boot project"""
    analyzer = JavaAnalyzer(project_path)
    parsed_files = [analyzer.parse_java_code(f) for f in analyzer._find_java_files(project_path)]
    parsed_files = [f for f in parsed_files if f]  # Remove None values
    architecture_type = analyzer._determine_architecture_type(parsed_files)
    return {
        "status": "success",
        "architecture_type": architecture_type
    }

def identify_microservice_boundaries(project_path):
    """Identify potential microservice boundaries in a Spring Boot project"""
    analyzer = JavaAnalyzer(project_path)
    parsed_files = [analyzer.parse_java_code(f) for f in analyzer._find_java_files(project_path)]
    parsed_files = [f for f in parsed_files if f]  # Remove None values
    boundaries = analyzer._identify_microservice_boundaries(parsed_files)
    return {
        "status": "success",
        "microservice_boundaries": boundaries
    }

def generate_dependency_visualization(project_path):
    """Generate a dependency visualization for a Spring Boot project"""
    analyzer = JavaAnalyzer(project_path)
    analyzer.setup_analysis_directory(os.path.basename(project_path))
    output_path = analyzer.generate_dependency_graph()
    return {
        "status": "success",
        "visualization_path": output_path
    }

def get_component_summary(project_path):
    """Get a summary of Spring components in the project"""
    analyzer = JavaAnalyzer(project_path)
    analyzer.analyze_project()
    return {
        "status": "success",
        "components": analyzer.metadata["components_found"]
    } 