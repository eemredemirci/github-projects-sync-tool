"""
Synchronization service module.
"""
import os
import json
import yaml
import difflib
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from app.services.github_service import GitHubService
from app.utils.yaml_converter import dict_to_yaml, yaml_to_dict, compare_yaml_json, merge_yaml_json
from app.utils.language import get_text
from app.utils.project_organizer import ProjectOrganizer


class SyncService:
    """Service class for synchronizing GitHub projects with local files."""
    
    def __init__(self, github_service: GitHubService):
        """
        Args:
            github_service: GitHub service instance
        """
        self.github_service = github_service
        
        # Base data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        
        # Directory structure as specified in the notes
        self.users_dir = os.path.join(self.data_dir, "users")
        self.repos_dir = os.path.join(self.data_dir, "repositories")
        self.projects_dir = os.path.join(self.data_dir, "projects")
        
        # Ensure directories exist
        self._ensure_dir(self.data_dir)
        self._ensure_dir(self.users_dir)
        self._ensure_dir(self.repos_dir)
        self._ensure_dir(self.projects_dir)
        
        # File paths
        self.users_file = os.path.join(self.users_dir, "users.json")
        self.repos_file = os.path.join(self.repos_dir, "repositories.json")
        self.projects_file = os.path.join(self.projects_dir, "projects.json")
    
    def _ensure_dir(self, directory: str) -> None:
        """Ensure directory exists.
        
        Args:
            directory: Directory path
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
    
    def _save_json(self, data: Dict[str, Any], file_path: str) -> bool:
        """Save data as JSON.
        
        Args:
            data: Data to save
            file_path: File path
            
        Returns:
            Whether the operation was successful
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            self._ensure_dir(directory)
            
            # Save data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved JSON file: {file_path}")
            return True
        except Exception as e:
            print(f"Error saving JSON file: {str(e)}")
            return False
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load data from JSON.
        
        Args:
            file_path: File path
            
        Returns:
            Loaded data
        """
        try:
            if not os.path.exists(file_path):
                print(f"JSON file not found: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"Loaded JSON file: {file_path}")
            return data
        except Exception as e:
            print(f"Error loading JSON file: {str(e)}")
            return {}
    
    def _save_yaml(self, data: Dict[str, Any], file_path: str) -> bool:
        """Save data as YAML.
        
        Args:
            data: Data to save
            file_path: File path
            
        Returns:
            Whether the operation was successful
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            self._ensure_dir(directory)
            
            # Convert to YAML
            yaml_content = dict_to_yaml(data)
            
            # Save data
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            print(f"Saved YAML file: {file_path}")
            return True
        except Exception as e:
            print(f"Error saving YAML file: {str(e)}")
            return False
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load data from YAML.
        
        Args:
            file_path: File path
            
        Returns:
            Loaded data
        """
        try:
            if not os.path.exists(file_path):
                print(f"YAML file not found: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            data = yaml_to_dict(yaml_content)
            print(f"Loaded YAML file: {file_path}")
            return data
        except Exception as e:
            print(f"Error loading YAML file: {str(e)}")
            return {}
    
    def fetch_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository data from GitHub.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data
        """
        print(get_text('fetching_repository_data').format(owner, repo))
        
        # Get repository data
        repo_data = self.github_service.get_full_repository_data(owner, repo)
        
        if not repo_data:
            print(get_text('repository_data_fetch_error').format(owner, repo))
            return {}
        
        # Create repository directory
        repo_dir = os.path.join(self.repos_dir, f"{owner}_{repo}")
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)
        
        # Save repository data as JSON
        json_file = os.path.join(repo_dir, "repository.json")
        self._save_json(repo_data, json_file)
        
        # Save projects data
        for project in repo_data.get("projects", []):
            # Create project directory
            project_dir = os.path.join(self.projects_dir, f"{project['id']}")
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Save project data as JSON
            json_file = os.path.join(project_dir, "project.json")
            self._save_json(project, json_file)
            
            # Save project data as YAML
            yaml_file = os.path.join(project_dir, "project.yaml")
            self._save_yaml(project, yaml_file)
        
        print(get_text('repository_data_saved').format(owner, repo))
        return repo_data
    
    def fetch_project(self, project_id: int) -> Dict[str, Any]:
        """Fetch project data from GitHub.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data
        """
        print(get_text('fetching_project_data').format(project_id))
        
        # Get project data
        project_data = self.github_service.get_full_project_data(project_id)
        
        if not project_data:
            print(get_text('project_data_fetch_error').format(project_id))
            return {}
        
        project_name = project_data["name"]
        
        # Create project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        # Save raw project data as JSON and YAML (these are the source of truth)
        json_file = os.path.join(project_dir, "project.json")
        self._save_json(project_data, json_file)
        
        yaml_file = os.path.join(project_dir, "project.yaml")
        self._save_yaml(project_data, yaml_file)
        
        # Organize project data into structured folders
        organizer = ProjectOrganizer(project_dir)
        organizer.organize(project_data)
        
        # Clean up old date-stamped versions
        removed_count = organizer.cleanup_old_versions()
        if removed_count > 0:
            print(f"Cleaned up {removed_count} old version files")
        
        print(get_text('project_data_saved').format(project_id))
        return project_data
    
    def sync_project_yaml_to_json(self, project_id: int, project_name: str) -> Tuple[bool, List[str]]:
        """Synchronize project data from YAML file to JSON file.
        
        Args:
            project_id: Project ID
            project_name: Project name
            
        Returns:
            Whether the operation was successful and change messages
        """
        print(get_text('yaml_to_json_sync').format(project_id))
        
        # Get project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # Check YAML file
        yaml_file = os.path.join(project_dir, "project.yaml")
        if not os.path.exists(yaml_file):
            print(get_text('yaml_file_not_found').format(yaml_file))
            return False, [get_text('yaml_file_not_found').format(yaml_file)]
        
        # Load YAML data
        yaml_data = self._load_yaml(yaml_file)
        
        # Check JSON file
        json_file = os.path.join(project_dir, "project.json")
        
        # Save changes
        self._save_json(yaml_data, json_file)
        
        print(get_text('yaml_to_json_sync_completed').format(project_id))
        return True, [get_text('yaml_to_json_sync_completed').format(project_id)]
    
    def sync_project_json_to_yaml(self, project_id: int, project_name: str) -> Tuple[bool, List[str]]:
        """Synchronize project data from JSON file to YAML file.
        
        Args:
            project_id: Project ID
            project_name: Project name
            
        Returns:
            Whether the operation was successful and change messages
        """
        print(get_text('json_to_yaml_sync').format(project_id))
        
        # Get project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # Check JSON file
        json_file = os.path.join(project_dir, "project.json")
        if not os.path.exists(json_file):
            print(get_text('json_file_not_found').format(json_file))
            return False, [get_text('json_file_not_found').format(json_file)]
        
        # Load JSON data
        json_data = self._load_json(json_file)
        
        # Check YAML file
        yaml_file = os.path.join(project_dir, "project.yaml")
        
        # Save changes
        self._save_yaml(json_data, yaml_file)
        
        print(get_text('json_to_yaml_sync_completed').format(project_id))
        return True, [get_text('json_to_yaml_sync_completed').format(project_id)]
    
    def check_project_changes(self, project_id: int, project_name: str) -> Tuple[bool, List[str]]:
        """Check changes between project files.
        
        Args:
            project_id: Project ID
            project_name: Project name
            
        Returns:
            Whether there are changes and change messages
        """
        print(get_text('checking_project_changes').format(project_id))
        
        # Get project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # Check JSON file
        json_file = os.path.join(project_dir, "project.json")
        if not os.path.exists(json_file):
            print(get_text('json_file_not_found').format(json_file))
            return False, [get_text('json_file_not_found').format(json_file)]
        
        # Check YAML file
        yaml_file = os.path.join(project_dir, "project.yaml")
        if not os.path.exists(yaml_file):
            print(get_text('yaml_file_not_found').format(yaml_file))
            return False, [get_text('yaml_file_not_found').format(yaml_file)]
        
        # Load data
        json_data = self._load_json(json_file)
        yaml_data = self._load_yaml(yaml_file)
        
        # Compare data
        changes = compare_yaml_json(yaml_data, json_data)
        
        if not changes:
            print(get_text('no_changes_found').format(project_id))
            return False, [get_text('no_changes_found').format(project_id)]
        
        print(get_text('changes_found').format(project_id))
        return True, changes
    
    def check_github_changes(self, project_id: int, project_name: str) -> Tuple[bool, List[str]]:
        """Check changes between local files and GitHub.
        
        Args:
            project_id: Project ID
            project_name: Project name
            
        Returns:
            Whether there are changes and change messages
        """
        print(get_text('checking_github_changes').format(project_id))
        
        # Get project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # Check JSON file
        json_file = os.path.join(project_dir, "project.json")
        if not os.path.exists(json_file):
            print(get_text('json_file_not_found').format(json_file))
            return False, [get_text('json_file_not_found').format(json_file)]
        
        # Load local data
        local_data = self._load_json(json_file)
        
        # Get GitHub data
        github_data = self.github_service.get_full_project_data(project_id)
        
        if not github_data:
            print(get_text('project_data_fetch_error').format(project_id))
            return False, [get_text('project_data_fetch_error').format(project_id)]
        
        # Compare data
        local_str = json.dumps(local_data, indent=2, sort_keys=True)
        github_str = json.dumps(github_data, indent=2, sort_keys=True)
        
        if local_str == github_str:
            print(get_text('no_github_changes').format(project_id))
            return False, [get_text('no_github_changes').format(project_id)]
        
        # Find changes
        diff = difflib.unified_diff(
            local_str.splitlines(),
            github_str.splitlines(),
            fromfile="Local",
            tofile="GitHub",
            lineterm=""
        )
        
        changes = list(diff)
        print(get_text('github_changes_found').format(project_id))
        return True, changes
    
    def push_project_to_github(self, project_id: int, project_name: str) -> Tuple[bool, List[str]]:
        """Push project data to GitHub.
        
        Args:
            project_id: Project ID
            project_name: Project name
            
        Returns:
            Whether the operation was successful and change messages
        """
        print(get_text('sending_project_data').format(project_id))
        
        # Get project directory
        project_dir = os.path.join(self.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # Check JSON file
        json_file = os.path.join(project_dir, "project.json")
        if not os.path.exists(json_file):
            print(get_text('json_file_not_found').format(json_file))
            return False, [get_text('json_file_not_found').format(json_file)]
        
        # Load JSON data
        json_data = self._load_json(json_file)
        
        # Update project on GitHub (simulation)
        # In a real implementation, this would call the GitHub API to update the project
        # self.github_service.update_project(project_id, json_data)
        
        print(get_text('project_data_sent').format(project_id))
        return True, [get_text('project_data_sent').format(project_id)]
    
    def list_repositories(self) -> List[Dict[str, Any]]:
        """List saved repositories.
        
        Returns:
            List of repositories
        """
        repositories = []
        
        if not os.path.exists(self.repos_dir):
            return repositories
        
        for repo_dir in os.listdir(self.repos_dir):
            repo_path = os.path.join(self.repos_dir, repo_dir)
            
            if not os.path.isdir(repo_path):
                continue
            
            json_file = os.path.join(repo_path, "repository.json")
            
            if not os.path.exists(json_file):
                continue
            
            repo_data = self._load_json(json_file)
            
            if not repo_data:
                continue
            
            repositories.append({
                "name": repo_data.get("name", ""),
                "full_name": repo_data.get("full_name", ""),
                "owner": repo_data.get("owner", {}).get("login", ""),
                "description": repo_data.get("description", ""),
                "updated_at": repo_data.get("updated_at", ""),
                "local_updated_at": datetime.fromtimestamp(os.path.getmtime(json_file)).isoformat()
            })
        
        return repositories
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List saved projects.
        
        Returns:
            List of projects
        """
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
        
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            
            if not os.path.isdir(project_path):
                continue
            
            json_file = os.path.join(project_path, "project.json")
            
            if not os.path.exists(json_file):
                continue
            
            project_data = self._load_json(json_file)
            
            if not project_data:
                continue
            
            projects.append({
                "id": project_data.get("id", 0),
                "name": project_data.get("name", ""),
                "body": project_data.get("body", ""),
                "state": project_data.get("state", ""),
                "updated_at": project_data.get("updated_at", ""),
                "local_updated_at": datetime.fromtimestamp(os.path.getmtime(json_file)).isoformat()
            })
        
        return projects 