import streamlit as st
from datetime import datetime
import sys
from pathlib import Path
import importlib.util

# Get absolute paths
current_dir = Path(__file__).parent.absolute()  # ui directory
root_dir = current_dir.parent  # TheFiveinterFace root

# Direct import of needed modules
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the project and session modules
project_path = root_dir / "models" / "project.py"
project = load_module("project", project_path)

session_path = root_dir / "utils" / "session.py"
session = load_module("session", session_path)


def display_project_dashboard():
    """Display the project dashboard with list of projects and creation form"""
    st.header("Projects Dashboard")
    
    # Create new project form
    with st.expander("Create New Project", expanded=len(st.session_state.projects) == 0):
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name")
            project_description = st.text_area("Project Description")
            project_repo_url = st.text_input("Monolith Repository URL (optional)")
            
            submit_button = st.form_submit_button("Create Project")
            
            if submit_button and project_name:
                # Create new project
                new_project = project.create_new_project(
                    name=project_name,
                    description=project_description,
                    repository_url=project_repo_url
                )
                
                # Add to session state
                st.session_state.projects[new_project.id] = new_project.to_dict()
                
                # Set as current project and go to migration workflow
                session.set_current_project(new_project.id)
                st.rerun()
    
    # List existing projects
    if st.session_state.projects:
        st.subheader("Your Projects")
        
        for project_id, project_data in st.session_state.projects.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="project-card">
                    <h3>{project_data['name']}</h3>
                    <p>{project_data['description'][:100]}{'...' if len(project_data['description']) > 100 else ''}</p>
                    <p><strong>Status:</strong> {project_data['status']}</p>
                    <p><strong>Stage:</strong> {project_data['stage']}</p>
                    <p><strong>Updated:</strong> {datetime.fromisoformat(project_data['updated_at']).strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                if st.button("Open", key=f"open_{project_id}"):
                    session.set_current_project(project_id)
                    st.rerun()
                
                if st.button("Delete", key=f"delete_{project_id}"):
                    # Remove from session state
                    del st.session_state.projects[project_id]
                    
                    # Remove file
                    project.delete_project(project_id)
                    
                    st.rerun()
    else:
        st.info("No projects found. Create a new project to get started.") 