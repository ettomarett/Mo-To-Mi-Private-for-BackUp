import json
import uuid
from datetime import datetime
from pathlib import Path
import sys
import importlib.util

# Get absolute paths
current_dir = Path(__file__).parent.absolute()  # models directory
root_dir = current_dir.parent  # TheFiveinterFace root

# Direct import of needed modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the paths module
paths_path = root_dir / "config" / "paths.py"
paths = load_module("paths", paths_path)


class Project:
    """
    Class representing a migration project
    """
    def __init__(self, id=None, name=None, description=None, repository_url=None, 
                 created_at=None, updated_at=None, status="active", stage="initiation", 
                 agent_outputs=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.repository_url = repository_url
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.status = status
        self.stage = stage
        self.agent_outputs = agent_outputs or {
            "architect": {},
            "observer": {},
            "strategist": {},
            "builder": {},
            "validator": {}
        }
    
    def save(self):
        """Save project to file"""
        file_path = paths.PROJECTS_DIR / f"{self.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def to_dict(self):
        """Convert project to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "repository_url": self.repository_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "stage": self.stage,
            "agent_outputs": self.agent_outputs
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create project from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            repository_url=data.get("repository_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            status=data.get("status"),
            stage=data.get("stage"),
            agent_outputs=data.get("agent_outputs")
        )
    
    def update_timestamp(self):
        """Update the project's updated_at timestamp"""
        self.updated_at = datetime.now().isoformat()
    
    def advance_stage(self):
        """Advance the project to the next stage"""
        stages = ["initiation", "analysis", "planning", "implementation", "testing", "completed"]
        current_index = stages.index(self.stage)
        if current_index < len(stages) - 1:
            self.stage = stages[current_index + 1]
            self.update_timestamp()
            return True
        return False
    
    def add_agent_output(self, agent_type, input_text, output_text):
        """Add a new agent output to the project"""
        self.agent_outputs[agent_type][datetime.now().isoformat()] = {
            "input": input_text,
            "output": output_text
        }
        self.update_timestamp()


def save_project(project_id, project_data):
    """Save project data to a JSON file"""
    file_path = paths.PROJECTS_DIR / f"{project_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2)


def load_project(project_id):
    """Load project data from a JSON file"""
    file_path = paths.PROJECTS_DIR / f"{project_id}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_projects():
    """List all saved projects"""
    return [f.stem for f in paths.PROJECTS_DIR.glob("*.json")]


def get_all_projects():
    """Get all projects as dictionaries"""
    projects = {}
    for project_id in list_projects():
        project_data = load_project(project_id)
        if project_data:
            projects[project_id] = project_data
    return projects


def create_new_project(name, description, repository_url=None):
    """Create a new project"""
    project = Project(
        name=name,
        description=description,
        repository_url=repository_url
    )
    project.save()
    return project


def delete_project(project_id):
    """Delete a project"""
    file_path = paths.PROJECTS_DIR / f"{project_id}.json"
    if file_path.exists():
        file_path.unlink()
        return True
    return False 