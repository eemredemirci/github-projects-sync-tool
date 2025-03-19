"""
Project data organizer module.
This module handles the organization of GitHub project data into a structured folder format.
"""
import os
import json
import yaml
from typing import Dict, Any, List, Optional, Tuple
import shutil
import re
from datetime import datetime

class ProjectOrganizer:
    """
    Organizes GitHub project data into a structured format with separate folders for
    different components (project details, milestones, issues, etc.)
    """
    
    def __init__(self, project_dir: str):
        """
        Initialize the organizer with the project directory
        
        Args:
            project_dir: Base directory for the project data
        """
        self.project_dir = project_dir
        
        # Create structured subdirectories
        self.details_dir = os.path.join(project_dir, "details")
        self.milestones_dir = os.path.join(project_dir, "milestones")
        self.issues_dir = os.path.join(project_dir, "issues")
        self.fields_dir = os.path.join(project_dir, "fields")
        
        # Ensure all directories exist
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create all required directories if they don't exist"""
        for directory in [
            self.project_dir, 
            self.details_dir,
            self.milestones_dir, 
            self.issues_dir,
            self.fields_dir
        ]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def organize(self, project_data: Dict[str, Any]) -> bool:
        """
        Organize project data into structured folders
        
        Args:
            project_data: The complete project data from GitHub
            
        Returns:
            Whether the organization was successful
        """
        try:
            # Extract and save project details
            self._save_project_details(project_data)
            
            # Extract and save fields
            self._save_fields(project_data)
            
            # Extract and save items (issues)
            self._save_issues(project_data)
            
            # Extract and save milestones (from issues)
            self._save_milestones(project_data)
            
            return True
        except Exception as e:
            print(f"Error organizing project data: {str(e)}")
            return False
    
    def _save_project_details(self, project_data: Dict[str, Any]):
        """
        Extract and save project details
        
        Args:
            project_data: Complete project data
        """
        details = {
            "id": project_data.get("id", ""),
            "name": project_data.get("name", ""),
            "number": project_data.get("number", 0),
            "state": project_data.get("state", ""),
            "created_at": project_data.get("created_at", ""),
            "updated_at": project_data.get("updated_at", ""),
            "html_url": project_data.get("html_url", ""),
            "description": project_data.get("description", ""),
            "is_v2": project_data.get("is_v2", False),
        }
        
        # Save in both JSON and YAML formats
        self._save_as_json(details, os.path.join(self.details_dir, "project_info.json"))
        self._save_as_yaml(details, os.path.join(self.details_dir, "project_info.yaml"))
    
    def _save_fields(self, project_data: Dict[str, Any]):
        """
        Extract and save project fields
        
        Args:
            project_data: Complete project data
        """
        fields = project_data.get("fields", [])
        
        # Save all fields together
        self._save_as_json(fields, os.path.join(self.fields_dir, "all_fields.json"))
        self._save_as_yaml(fields, os.path.join(self.fields_dir, "all_fields.yaml"))
        
        # Save individual fields
        for field in fields:
            field_id = field.get("id", "unknown")
            field_name = field.get("name", "").replace(" ", "_").lower()
            filename = f"{field_name}_{field_id[-8:]}"
            
            self._save_as_json(field, os.path.join(self.fields_dir, f"{filename}.json"))
            self._save_as_yaml(field, os.path.join(self.fields_dir, f"{filename}.yaml"))
    
    def _save_issues(self, project_data: Dict[str, Any]):
        """
        Extract and save project items (issues)
        
        Args:
            project_data: Complete project data
        """
        items = project_data.get("items", [])
        
        # Save all issues together
        self._save_as_json(items, os.path.join(self.issues_dir, "all_issues.json"))
        self._save_as_yaml(items, os.path.join(self.issues_dir, "all_issues.yaml"))
        
        # Save individual issues
        for item in items:
            issue_id = item.get("id", "unknown")
            issue_title = item.get("content", {}).get("title", "").replace(" ", "_").lower()
            issue_number = item.get("content", {}).get("number", 0)
            filename = f"issue_{issue_number}_{issue_id[-8:]}"
            
            self._save_as_json(item, os.path.join(self.issues_dir, f"{filename}.json"))
            self._save_as_yaml(item, os.path.join(self.issues_dir, f"{filename}.yaml"))
    
    def _save_milestones(self, project_data: Dict[str, Any]):
        """
        Extract and save milestones from items, creating a hierarchical structure 
        of repository > milestone > issues
        
        Args:
            project_data: Complete project data
        """
        items = project_data.get("items", [])
        
        # Collect unique milestones and their associated items
        milestones = {}
        milestone_items = {}
        repositories = {}
        
        # For items without milestones
        no_milestone_items = {}
        
        # Process items to check for parent-child relations based on title and body text
        # Key is "repo_owner/repo_name#issue_number"
        issue_references = {}
        issue_by_number = {}
        
        # First pass - collect all issues
        for item in items:
            repository = item.get("repository", {})
            repo_owner = repository.get("owner", "unknown")
            repo_name = repository.get("name", "unknown")
            
            content = item.get("content", {})
            issue_number = content.get("number")
            
            if issue_number:
                key = f"{repo_owner}/{repo_name}#{issue_number}"
                issue_by_number[key] = item
        
        # Second pass - analyze body and look for references
        for item in items:
            repository = item.get("repository", {})
            repo_owner = repository.get("owner", "unknown")
            repo_name = repository.get("name", "unknown")
            
            content = item.get("content", {})
            issue_number = content.get("number")
            
            if issue_number:
                key = f"{repo_owner}/{repo_name}#{issue_number}"
                body = content.get("body", "")
                title = content.get("title", "")
                
                # Look for references in body
                if body:
                    # Find all #XX references in the body
                    import re
                    references = re.findall(r"#(\d+)", body)
                    
                    # Check for specific parent-child patterns
                    parent_matches = re.findall(r"(?:Parent|Child of|Depends on|Related to):?\s+#?(\d+)", body, re.IGNORECASE)
                    if parent_matches:
                        for parent_num in parent_matches:
                            parent_key = f"{repo_owner}/{repo_name}#{parent_num}"
                            if parent_key in issue_by_number:
                                if key not in issue_references:
                                    issue_references[key] = []
                                issue_references[key].append(parent_key)
                    
                    # Also add all other #XX references as potential relationships
                    if references:
                        for ref_num in references:
                            if ref_num != str(issue_number):  # Don't self-reference
                                ref_key = f"{repo_owner}/{repo_name}#{ref_num}"
                                if ref_key in issue_by_number:
                                    if key not in issue_references:
                                        issue_references[key] = []
                                    issue_references[key].append(ref_key)
        
        # Process each item again with references information
        for item in items:
            repository = item.get("repository", {})
            repo_owner = repository.get("owner", "unknown")
            repo_name = repository.get("name", "unknown")
            repo_id = f"{repo_owner}_{repo_name}"
            
            # Create repository structure if it doesn't exist
            if repo_id not in repositories:
                repositories[repo_id] = {
                    "details": repository,
                    "milestones": {},
                    "no_milestone_items": []
                }
            
            milestone = item.get("milestone")
            if milestone and milestone.get("title"):
                milestone_title = milestone.get("title")
                milestone_id = milestone_title.replace(" ", "_").lower().replace(":", "_").replace("/", "_")
                
                # Create milestone entry if it doesn't exist
                if milestone_id not in repositories[repo_id]["milestones"]:
                    repositories[repo_id]["milestones"][milestone_id] = {
                        "details": milestone,
                        "items": []
                    }
                
                # Add item to the milestone
                repositories[repo_id]["milestones"][milestone_id]["items"].append(item)
            else:
                # Add to no milestone items for this repository
                repositories[repo_id]["no_milestone_items"].append(item)
            
            # Add parent-child relationship information if available
            if issue_number:
                key = f"{repo_owner}/{repo_name}#{issue_number}"
                
                # API'den gelen parent issue bilgisi varsa ve direct_parent ise
                if item.get("parent_issue") and item["parent_issue"].get("source") == "direct_parent":
                    print(f"Using direct parent for {key}: {item['parent_issue'].get('title')}")
                # API'den gelen parent direct_parent değilse, kaldır
                elif item.get("parent_issue"):
                    print(f"Removing non-direct parent for {key}: {item['parent_issue'].get('title')} (source: {item['parent_issue'].get('source', 'unknown')})")
                    del item["parent_issue"]
                # Metin analizine dayalı tespiti kullanmıyoruz
        
        # Save all milestones in the main milestones directory
        all_milestones = []
        for repo_data in repositories.values():
            for milestone_data in repo_data["milestones"].values():
                all_milestones.append(milestone_data["details"])
                
        self._save_as_json(all_milestones, os.path.join(self.milestones_dir, "all_milestones.json"))
        self._save_as_yaml(all_milestones, os.path.join(self.milestones_dir, "all_milestones.yaml"))
        
        # Create repository and milestone directory structure
        for repo_id, repo_data in repositories.items():
            # Create repository directory
            repo_dir = os.path.join(self.project_dir, repo_id)
            os.makedirs(repo_dir, exist_ok=True)
            
            # Create milestones directory inside repository
            repo_milestones_dir = os.path.join(repo_dir, "milestones")
            os.makedirs(repo_milestones_dir, exist_ok=True)
            
            # Save repository milestone list
            repo_milestones = [m["details"] for m in repo_data["milestones"].values()]
            self._save_as_json(repo_milestones, os.path.join(repo_milestones_dir, "all_milestones.json"))
            self._save_as_yaml(repo_milestones, os.path.join(repo_milestones_dir, "all_milestones.yaml"))
            
            # Process each milestone
            for milestone_id, milestone_data in repo_data["milestones"].items():
                milestone_details = milestone_data["details"]
                milestone_items = milestone_data["items"]
                
                # Create milestone directory
                milestone_dir = os.path.join(repo_milestones_dir, milestone_id)
                os.makedirs(milestone_dir, exist_ok=True)
                
                # Save milestone details
                self._save_as_json(milestone_details, os.path.join(milestone_dir, f"{milestone_id}.json"))
                self._save_as_yaml(milestone_details, os.path.join(milestone_dir, f"{milestone_id}.yaml"))
                
                # Save each issue in the milestone directory
                for item in milestone_items:
                    issue_number = item.get("content", {}).get("number", 0)
                    issue_id = item.get("id", "unknown")[-8:]
                    
                    self._save_as_json(item, os.path.join(milestone_dir, f"issue_{issue_number}.json"))
                    self._save_as_yaml(item, os.path.join(milestone_dir, f"issue_{issue_number}.yaml"))
            
            # Process items without milestones
            if repo_data["no_milestone_items"]:
                # Create no_milestone directory
                no_milestone_dir = os.path.join(repo_milestones_dir, "no_milestone")
                os.makedirs(no_milestone_dir, exist_ok=True)
                
                # Save each issue in the no_milestone directory
                for item in repo_data["no_milestone_items"]:
                    issue_number = item.get("content", {}).get("number", 0)
                    issue_id = item.get("id", "unknown")[-8:]
                    
                    self._save_as_json(item, os.path.join(no_milestone_dir, f"issue_{issue_number}.json"))
                    self._save_as_yaml(item, os.path.join(no_milestone_dir, f"issue_{issue_number}.yaml"))
                
                # Create summary file
                no_milestone_summary = {
                    "count": len(repo_data["no_milestone_items"]),
                    "items": [
                        {
                            "id": item.get("id"),
                            "number": item.get("content", {}).get("number", 0),
                            "title": item.get("content", {}).get("title", "")
                        }
                        for item in repo_data["no_milestone_items"]
                    ]
                }
                
                self._save_as_json(no_milestone_summary, os.path.join(no_milestone_dir, "summary.json"))
                self._save_as_yaml(no_milestone_summary, os.path.join(no_milestone_dir, "summary.yaml"))
    
    def _save_as_json(self, data: Any, file_path: str):
        """
        Save data as JSON
        
        Args:
            data: Data to save
            file_path: Path to save the file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_as_yaml(self, data: Any, file_path: str):
        """
        Save data as YAML
        
        Args:
            data: Data to save
            file_path: Path to save the file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
    def cleanup_old_versions(self) -> int:
        """
        Removes all date-stamped files from the project directory
        leaving only the main project.json and project.yaml files
        
        Returns:
            Number of files removed
        """
        removed_count = 0
        
        # Compile regex pattern for date-stamped files
        pattern = re.compile(r"project_\d{8}_\d{6}\.(json|yaml)")
        
        try:
            # Check all files in the project directory
            for filename in os.listdir(self.project_dir):
                file_path = os.path.join(self.project_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # Check if file matches the date-stamped pattern
                if pattern.match(filename):
                    # Remove the file
                    os.remove(file_path)
                    print(f"Removed old version file: {file_path}")
                    removed_count += 1
            
            return removed_count
        except Exception as e:
            print(f"Error cleaning up old versions: {str(e)}")
            return removed_count 