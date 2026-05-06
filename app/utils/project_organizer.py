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
    
    Klasör yapısı:
    project_dir/
    ├── project.json/yaml (ana proje verileri)
    ├── milestones/ (tüm milestones)
    │   ├── milestone_name/ (her milestone için klasör)
    │   │   ├── milestone_name.json (milestone detayları)
    │   │   ├── issue_XX.json (milestone içindeki issue'lar)
    │   │   └── issue_YY_parent/ (parent issue isimli klasör)
    │   │       └── issue_ZZ.json (bu issue'ya bağlı child issue)
    │   └── no_milestone/ (milestone olmayan issue'lar)
    │       └── issue_XX.json (milestone olmayan issue)
    ├── .cache/ (değişiklik takibi için cache dosyaları)
    │   └── original_state.json (indirilen orijinal veri)
    ├── .pending/ (onaylanan değişiklikler)
    │   └── operations.json (bekleyen işlemler)
    ├── logs/ (log dosyaları)
    └── sync_history/ (senkronizasyon geçmişi)
    """
    
    def __init__(self, project_dir: str):
        """
        Initialize the organizer with the project directory
        
        Args:
            project_dir: Base directory for the project data
        """
        self.project_dir = project_dir
        
        # Create structured subdirectories
        self.milestones_dir = os.path.join(project_dir, "milestones")
        self.cache_dir = os.path.join(project_dir, ".cache")
        self.pending_dir = os.path.join(project_dir, ".pending")
        self.logs_dir = os.path.join(project_dir, "logs")
        self.sync_history_dir = os.path.join(project_dir, "sync_history")
        
        # Ensure all directories exist
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create all required directories if they don't exist"""
        for directory in [
            self.project_dir, 
            self.milestones_dir,
            self.cache_dir,
            self.pending_dir,
            self.logs_dir,
            self.sync_history_dir
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
            print("Organizing project data with improved structure...")
            
            # Save main project data
            self._save_project_data(project_data)
            
            # Extract and save milestones and issues
            self._organize_milestones_and_issues(project_data)
            
            # Prepare .cache directory for change tracking
            self._prepare_change_tracking(project_data)
            
            print("Project organization complete. All data saved in structured folders.")
            return True
        except Exception as e:
            print(f"Error organizing project data: {str(e)}")
            return False
    
    def _save_project_data(self, project_data: Dict[str, Any]):
        """
        Save complete project data to project.json and project.yaml
        
        Args:
            project_data: Complete project data
        """
        # Save in both JSON and YAML formats in the project root directory
        self._save_as_json(project_data, os.path.join(self.project_dir, "project.json"))
        self._save_as_yaml(project_data, os.path.join(self.project_dir, "project.yaml"))
    
    def _organize_milestones_and_issues(self, project_data: Dict[str, Any]):
        """
        Extract and organize milestones and issues into structured folders
        
        Args:
            project_data: Complete project data
        """
        items = project_data.get("items", [])
        
        # Collect unique milestones and their associated items
        milestones = {}
        parent_issues = {}
        child_issues = {}
        
        # For items without milestones
        no_milestone_items = []
        
        # İlk geçiş - issue'ları topla ve parent-child ilişkilerini belirle
        for item in items:
            milestone = item.get("milestone")
            parent = item.get("parent_issue")
            content = item.get("content", {})
            issue_number = content.get("number", 0)
            
            # Milestone'a göre sınıflandır
            if milestone and milestone.get("title"):
                milestone_title = milestone.get("title")
                milestone_id = self._sanitize_name(milestone_title)
                
                if milestone_id not in milestones:
                    milestones[milestone_id] = {
                        "details": milestone,
                        "items": []
                    }
                
                milestones[milestone_id]["items"].append(item)
            else:
                no_milestone_items.append(item)
            
            # Parent-child ilişkilerini belirle
            if parent:
                parent_number = None
                if isinstance(parent, dict) and "number" in parent:
                    parent_number = parent.get("number")
                elif isinstance(parent, int):
                    parent_number = parent
                    
                if parent_number:
                    # Bu child issue'yu parent'ına göre kaydet
                    if parent_number not in child_issues:
                        child_issues[parent_number] = []
                    
                    child_issues[parent_number].append(item)
        
        # Process each milestone
        for milestone_id, milestone_data in milestones.items():
            milestone_details = milestone_data["details"]
            milestone_items = milestone_data["items"]
            
            # Create milestone directory
            milestone_dir = os.path.join(self.milestones_dir, milestone_id)
            os.makedirs(milestone_dir, exist_ok=True)
            
            # Save milestone details
            self._save_as_json(milestone_details, os.path.join(milestone_dir, f"{milestone_id}.json"))
            
            # Save each issue in the milestone directory
            for item in milestone_items:
                content = item.get("content", {})
                issue_number = content.get("number", 0)
                
                # Bu issue child issue mu kontrol et
                is_child = False
                for parent_num, children in child_issues.items():
                    if any(child.get("content", {}).get("number") == issue_number for child in children):
                        is_child = True
                        break
                
                # Child issue'ları parent issue klasörlerinde kaydediyoruz, bu nedenle ana dizine kaydetmiyoruz
                if is_child:
                    continue
                
                # Temel issue dosyasını kaydet
                self._save_as_json(item, os.path.join(milestone_dir, f"issue_{issue_number}.json"))
                
                # Bu issue bir parent issue mu?
                if issue_number in child_issues:
                    # Parent issue için klasör oluştur
                    parent_dir = os.path.join(milestone_dir, f"issue_{issue_number}_parent")
                    os.makedirs(parent_dir, exist_ok=True)
                    
                    # Child issue'ları bu klasöre kaydet
                    for child_item in child_issues[issue_number]:
                        child_number = child_item.get("content", {}).get("number", 0)
                        self._save_as_json(child_item, os.path.join(parent_dir, f"issue_{child_number}.json"))
        
        # Create no_milestone directory and save items without milestones
        if no_milestone_items:
            no_milestone_dir = os.path.join(self.milestones_dir, "no_milestone")
            os.makedirs(no_milestone_dir, exist_ok=True)
            
            for item in no_milestone_items:
                content = item.get("content", {})
                issue_number = content.get("number", 0)
                
                # Bu issue child issue mu kontrol et
                is_child = False
                for parent_num, children in child_issues.items():
                    if any(child.get("content", {}).get("number") == issue_number for child in children):
                        is_child = True
                        break
                
                # Child issue'ları parent issue klasörlerinde kaydediyoruz
                if is_child:
                    continue
                
                # Issue'yu kaydet
                self._save_as_json(item, os.path.join(no_milestone_dir, f"issue_{issue_number}.json"))
                
                # Bu issue bir parent issue mu?
                if issue_number in child_issues:
                    # Parent issue için klasör oluştur
                    parent_dir = os.path.join(no_milestone_dir, f"issue_{issue_number}_parent")
                    os.makedirs(parent_dir, exist_ok=True)
                    
                    # Child issue'ları bu klasöre kaydet
                    for child_item in child_issues[issue_number]:
                        child_number = child_item.get("content", {}).get("number", 0)
                        self._save_as_json(child_item, os.path.join(parent_dir, f"issue_{child_number}.json"))
    
    def _prepare_change_tracking(self, project_data: Dict[str, Any]):
        """
        Prepare .cache directory for change tracking
        
        Args:
            project_data: Complete project data
        """
        # ChangeTracker'ın original_state dosyası oluşturur
        from app.utils.change_tracker import ChangeTracker
        tracker = ChangeTracker(self.project_dir)
        tracker.capture_original_state(project_data)
    
    def _sanitize_name(self, name: str) -> str:
        """Converts a name to a safe directory name"""
        return (name.replace(" ", "_")
                    .replace(":", "_")
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace("*", "_")
                    .replace("?", "_")
                    .replace("\"", "_")
                    .replace("<", "_")
                    .replace(">", "_")
                    .replace("|", "_")
                    .lower())
    
    def _save_as_json(self, data: Any, file_path: str):
        """Save data as JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_as_yaml(self, data: Any, file_path: str):
        """Save data as YAML file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    
    def cleanup_old_versions(self) -> int:
        """
        Cleans up old versions of files in the project directory.
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        # No cleanup needed as we've simplified the structure
        
        return deleted_count 