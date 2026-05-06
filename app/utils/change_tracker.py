"""
Change tracking module for GitHub Project Sync Tool.
This module provides classes for tracking changes made to local project files.
"""
import hashlib
import json
import os
import re
import shutil
import copy
import time
import traceback
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime

# Takip edilecek alanların listesi
TRACKED_FIELDS = ["title", "state", "body", "due_on", "description"]

class ChangeTracker:
    """
    Tracks changes made to project files in the local filesystem.
    Compares the original state from GitHub with the current state
    and identifies created, updated, and deleted items.
    """
    
    def __init__(self, project_dir: str, project_id: str = "", project_name: str = "", cache_retention_limit: int = 10, auto_save: bool = False):
        """
        Initialize the change tracker.
        
        Args:
            project_dir: Base directory for the project data
            project_id: ID of the project, used for reference
            project_name: Name of the project, used for reference
            cache_retention_limit: Maximum number of history entries to keep (default 10)
            auto_save: Whether to auto-save changes to disk
        """
        self.project_dir = project_dir
        self.project_id = project_id
        self.project_name = project_name
        self.auto_save = auto_save
        self.cache_dir = os.path.join(project_dir, ".cache")
        self.logs_dir = os.path.join(project_dir, "logs")
        self.sync_history_dir = os.path.join(project_dir, "sync_history")
        self.pending_dir = os.path.join(project_dir, ".pending")
        self.cache_retention_limit = cache_retention_limit
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Ensure directories exist
        for directory in [self.cache_dir, self.logs_dir, self.sync_history_dir, self.pending_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Original state file
        self.original_state_file = os.path.join(self.cache_dir, "original_state.json")
        
        # Data structures for tracking changes
        self.original_state = {}  # Original data from GitHub
        self.current_state = {}   # Current state in the filesystem
        self.changes = {
            "created": [],  # New items
            "updated": [],  # Modified items
            "deleted": []   # Removed items
        }
        
        # Cleanup old files on init
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """
        Clean up old cache, logs, and history files based on retention limit.
        """
        # Cleanup sync history files
        history_files = []
        if os.path.exists(self.sync_history_dir):
            for filename in os.listdir(self.sync_history_dir):
                if filename.endswith("_sync_results.json"):
                    file_path = os.path.join(self.sync_history_dir, filename)
                    history_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        history_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old files beyond retention limit
        if len(history_files) > self.cache_retention_limit:
            for file_path, _ in history_files[self.cache_retention_limit:]:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing old history file {file_path}: {str(e)}")
        
        # Cleanup log files
        log_files = []
        if os.path.exists(self.logs_dir):
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("sync_") and filename.endswith(".log"):
                    file_path = os.path.join(self.logs_dir, filename)
                    log_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old files beyond retention limit
        if len(log_files) > self.cache_retention_limit:
            for file_path, _ in log_files[self.cache_retention_limit:]:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing old log file {file_path}: {str(e)}")
                    
        # Only keep a single pending operations file, no cleanup needed
    
    def print_info(self, message: str) -> None:
        """
        Bilgilendirme mesajı yazdırır.
        
        Args:
            message: Gösterilecek mesaj
        """
        try:
            from app.interactive_cli import print_info
            print_info(message)
        except ImportError:
            print(f"INFO: {message}")
    
    def print_warning(self, message: str) -> None:
        """
        Uyarı mesajı yazdırır.
        
        Args:
            message: Gösterilecek uyarı mesajı
        """
        try:
            from app.interactive_cli import print_warning
            print_warning(message)
        except ImportError:
            print(f"UYARI: {message}")
    
    def load_original_state(self) -> bool:
        """
        Loads the original state from the cached file.
        
        Returns:
            Whether the operation was successful
        """
        try:
            if os.path.exists(self.original_state_file):
                with open(self.original_state_file, 'r', encoding='utf-8') as f:
                    self.original_state = json.load(f)
                return True
            else:
                print("Original state file not found. Please download project data first.")
                return False
        except Exception as e:
            print(f"Error loading original state: {str(e)}")
            return False
    
    def scan_current_state(self):
        """
        Scan the current state of the project directory.
        
        This method scans the project directory and creates a dictionary of the current state.
        Only milestone and issue items will be included in the current state.
        
        It sets self.current_state with the result.
        """
        print("Yerel dosyaları taranıyor...")
        
        # Initialize current state dictionary
        self.current_state = {}
        
        try:
            # Create milestones directory
            milestones_dir = os.path.join(self.project_dir, "milestones")
            if os.path.exists(milestones_dir) and os.path.isdir(milestones_dir):
                # Process each milestone directory
                for milestone_name in os.listdir(milestones_dir):
                    milestone_dir = os.path.join(milestones_dir, milestone_name)
                    if os.path.isdir(milestone_dir):
                        # Check for milestone.json file
                        milestone_json = os.path.join(milestone_dir, "milestone.json")
                        if os.path.exists(milestone_json):
                            try:
                                with open(milestone_json, 'r', encoding='utf-8') as f:
                                    milestone_data = json.load(f)
                                    
                                # Create milestone ID
                                milestone_id = f"milestone_{milestone_name}"
                                
                                # Add file path for reference
                                milestone_data["file_path"] = milestone_json
                                milestone_data["type"] = "milestone"
                                
                                # Add to current state
                                self.current_state[milestone_id] = milestone_data
                            except Exception as e:
                                print(f"Milestone dosyası '{milestone_json}' okunurken hata: {str(e)}")
                        
                        # Process issues in this milestone
                        for filename in os.listdir(milestone_dir):
                            if filename.startswith("issue_") and filename.endswith(".json"):
                                issue_path = os.path.join(milestone_dir, filename)
                                
                                try:
                                    with open(issue_path, 'r', encoding='utf-8') as f:
                                        issue_data = json.load(f)
                                        
                                    # Extract issue ID/number from filename
                                    issue_number = filename.replace("issue_", "").replace(".json", "")
                                    issue_id = f"issue_{issue_number}"
                                    
                                    # Add file path for reference
                                    issue_data["file_path"] = issue_path
                                    issue_data["type"] = "issue"
                                    
                                    # Add to current state
                                    self.current_state[issue_id] = issue_data
                                except Exception as e:
                                    print(f"Issue dosyası '{filename}' okunurken hata: {str(e)}")
            
            # Check for no_milestone directory
            no_milestone_dir = os.path.join(milestones_dir, "no_milestone")
            if os.path.exists(no_milestone_dir) and os.path.isdir(no_milestone_dir):
                # Process issues with no milestone
                for filename in os.listdir(no_milestone_dir):
                    if filename.startswith("issue_") and filename.endswith(".json"):
                        issue_path = os.path.join(no_milestone_dir, filename)
                        
                        try:
                            with open(issue_path, 'r', encoding='utf-8') as f:
                                issue_data = json.load(f)
                                
                            # Extract issue ID/number from filename
                            issue_number = filename.replace("issue_", "").replace(".json", "")
                            issue_id = f"issue_{issue_number}"
                            
                            # Add file path for reference
                            issue_data["file_path"] = issue_path
                            issue_data["type"] = "issue"
                            
                            # Add to current state
                            self.current_state[issue_id] = issue_data
                        except Exception as e:
                            print(f"Issue dosyası '{filename}' okunurken hata: {str(e)}")
            
            # Check for parent issue directories
            elif "_parent" in filename and os.path.isdir(os.path.join(no_milestone_dir, filename)):
                parent_dir = os.path.join(no_milestone_dir, filename)
                parent_num_match = re.match(r"issue_(\d+)_parent", filename)
                if parent_num_match:
                    parent_issue_number = parent_num_match.group(1)
                    
                    # Read all child issues in this directory
                    for child_file in os.listdir(parent_dir):
                        if child_file.startswith("issue_") and child_file.endswith(".json"):
                            child_path = os.path.join(parent_dir, child_file)
                            
                            try:
                                with open(child_path, 'r', encoding='utf-8') as f:
                                    child_data = json.load(f)
                                    
                                # Extract issue number from filename
                                child_number = child_file.replace("issue_", "").replace(".json", "")
                                child_id = f"issue_{child_number}"
                                
                                # Add parent issue reference
                                if not "parent_issue" in child_data:
                                    child_data["parent_issue"] = {"number": int(parent_issue_number)}
                                
                                # Add file path for reference
                                child_data["file_path"] = child_path
                                child_data["type"] = "issue"
                                
                                # Add to current state
                                self.current_state[child_id] = child_data
                            except Exception as e:
                                print(f"Child issue dosyası '{child_file}' okunurken hata: {str(e)}")
        except Exception as e:
            print(f"Proje dizini taranırken hata oluştu: {str(e)}\n{traceback.format_exc()}")

    def _load_original_state(self, force=False) -> bool:
        """
        Load the original state from the disk cache.
        
        Args:
            force: If True, force reload even if already loaded
            
        Returns:
            True if successful, False otherwise
        """
        # Skip if already loaded and not forced
        if hasattr(self, 'original_state') and self.original_state and not force:
            return True
        
        # Initialize empty state
        self.original_state = {}
        
        # Define the cache file path
        cache_file = os.path.join(self.project_dir, ".cache", "original_state.json")
        
        # Check if cache file exists
        if not os.path.exists(cache_file):
            return False
        
        # Load from cache file
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Convert original state format to new format if needed
            if "items" in data:
                # Old format with nested "items" dictionary
                for item_id, item_data in data["items"].items():
                    self.original_state[item_id] = item_data
            else:
                # New format (direct dictionary of items)
                self.original_state = data
                
            print(f"Orijinal durum yüklendi: {len(self.original_state)} öğe.")
            return True
        except Exception as e:
            print(f"Orijinal durum yüklenirken hata: {str(e)}")
            # Initialize empty state on failure
            self.original_state = {}
            return False

    def _save_original_state(self, original_state: Dict) -> bool:
        """
        Save the current original state to disk cache.
        
        Args:
            original_state: The original state to save
            
        Returns:
            True if successful, False otherwise
        """
        # Skip if original state is empty
        if not original_state:
            print("Kaydedilecek orijinal durum verisi bulunamadı.")
            return False
        
        # Ensure cache directory exists
        cache_dir = os.path.join(self.project_dir, ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Define cache file path
        cache_file = os.path.join(cache_dir, "original_state.json")
        
        # Count actual items by type
        milestone_count = sum(1 for k in original_state if k.startswith("milestone_"))
        issue_count = sum(1 for k in original_state if k.startswith("issue_"))
        
        # Save to cache file
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(original_state, f, indent=2)
            
            # Only print this message if there are actually items
            if len(original_state) > 0:
                print(f"Orijinal durum kaydedildi: {len(original_state)} öğe ({milestone_count} milestone, {issue_count} issue)")
            return True
        except Exception as e:
            print(f"Orijinal durum kaydedilirken hata: {str(e)}")
            # Daha fazla tanılama bilgisi
            try:
                # Dosya yazma hakkında bilgi göster
                print(f"  Hedef dosya yolu: {cache_file}")
                print(f"  Dosya dizini var mı?: {os.path.exists(os.path.dirname(cache_file))}")
                print(f"  Yazma izni var mı?: {os.access(os.path.dirname(cache_file), os.W_OK)}")
            except Exception as inner_e:
                print(f"  Ek hata bilgisi alınamadı: {str(inner_e)}")
            
            return False

    def capture_original_state(self, project_data: Dict):
        """
        Capture original state from project data fetched from GitHub.
        
        Args:
            project_data: Dictionary containing all project data
        """
        try:
            print("GitHub'dan indirilen proje verilerinin orijinal durumu yakalanıyor...")
            
            # Doğrudan işlenmiş format gönderilmiş olabilir
            if isinstance(project_data, dict) and any(key.startswith(("issue_", "milestone_")) for key in list(project_data.keys())[:20]):
                print("Hazır formatlı veri algılandı, orijinal duruma kaydediliyor...")
                # Veri zaten işlenmiş formatta
                
                # Öğe sayılarını sayalım
                milestone_count = sum(1 for k in project_data.keys() if k.startswith("milestone_"))
                issue_count = sum(1 for k in project_data.keys() if k.startswith("issue_"))
                
                # Orijinal durumu ayarla ve kaydet
                self.original_state = project_data
                self._save_original_state(project_data)
                
                # Senkronizasyon işareti oluştur
                self._create_sync_marker()
                
                print(f"Orijinal durum kaydedildi: {len(project_data)} öğe ({milestone_count} milestone, {issue_count} issue)")
                return True
                
            # API'dan gelen projeyi işlememiz gerekiyor
            original_state = {}
            
            # API'dan gelen projeyi ilk önce kontrol et ve debug bilgisi göster
            if not isinstance(project_data, dict):
                print(f"Uyarı: Proje verisi bir sözlük değil, tip: {type(project_data)}")
                if isinstance(project_data, list) and len(project_data) > 0:
                    print(f"  Liste uzunluğu: {len(project_data)}")
                    # Liste formatında gelmiş olabilir, ilk öğeyi kontrol et
                    if len(project_data) > 0 and isinstance(project_data[0], dict):
                        sample_keys = list(project_data[0].keys())[:5]
                        print(f"  Örnek anahtarlar: {sample_keys}")
            
            # Process milestones - API response format requires different handling
            milestones_processed = 0
            items_processed = 0
            
            # 1. Yeni API Formatı - liste olarak milestones
            if isinstance(project_data, dict) and "milestones" in project_data and isinstance(project_data["milestones"], list):
                for milestone in project_data.get("milestones", []):
                    # Create consistent milestone ID
                    title = milestone.get("title", "")
                    if not title:
                        continue
                    
                    milestone_id = f"milestone_{self._normalize_milestone_value(title).replace(' ', '_').replace(':', '__')}"
                    
                    # Store milestone with its normalized ID
                    milestone_data = {
                        "id": milestone_id,
                        "type": "milestone", 
                        "title": title,
                        "state": milestone.get("state", "OPEN"),
                        "description": milestone.get("description", ""),
                        "due_on": milestone.get("due_on")
                    }
                    original_state[milestone_id] = milestone_data
                    milestones_processed += 1
            
            # 2. Eski API formatı - dictionary olarak items
            elif isinstance(project_data, dict) and "items" in project_data and isinstance(project_data["items"], dict):
                # Extract milestones from old format (nested in items)
                for item_id, item in project_data["items"].items():
                    if item.get("type") == "milestone":
                        original_state[item_id] = item
                        milestones_processed += 1
            
            # 3. Liste formatı items alanında
            elif isinstance(project_data, dict) and "items" in project_data and isinstance(project_data["items"], list):
                # Listedeki her öğeyi kontrol et
                for idx, item in enumerate(project_data["items"]):
                    if isinstance(item, dict):
                        # Milestone kontrolü
                        if item.get("type") == "milestone" or ("title" in item and "due_on" in item):
                            title = item.get("title", "")
                            if title:
                                milestone_id = f"milestone_{self._normalize_milestone_value(title).replace(' ', '_').replace(':', '__')}"
                                original_state[milestone_id] = {
                                    "id": milestone_id,
                                    "type": "milestone",
                                    "title": title,
                                    "state": item.get("state", "OPEN"),
                                    "description": item.get("description", ""),
                                    "due_on": item.get("due_on")
                                }
                                milestones_processed += 1
                        
                        # Issue kontrolü
                        elif "content" in item and isinstance(item["content"], dict) and "number" in item["content"]:
                            item_id = f"issue_{item['content']['number']}"
                            original_state[item_id] = item
                            items_processed += 1
            
            # 4. Liste formatı direkt kendisini kullan
            elif isinstance(project_data, list):
                # Listedeki her öğeyi kontrol et
                for idx, item in enumerate(project_data):
                    if isinstance(item, dict):
                        # Milestone kontrolü
                        if item.get("type") == "milestone" or ("title" in item and "due_on" in item):
                            title = item.get("title", "")
                            if title:
                                milestone_id = f"milestone_{self._normalize_milestone_value(title).replace(' ', '_').replace(':', '__')}"
                                original_state[milestone_id] = {
                                    "id": milestone_id,
                                    "type": "milestone",
                                    "title": title,
                                    "state": item.get("state", "OPEN"),
                                    "description": item.get("description", ""),
                                    "due_on": item.get("due_on")
                                }
                                milestones_processed += 1
                        
                        # Issue kontrolü
                        elif "content" in item and isinstance(item["content"], dict) and "number" in item["content"]:
                            issue_number = item["content"].get("number", 0)
                            if issue_number:
                                item_id = f"issue_{issue_number}"
                                original_state[item_id] = copy.deepcopy(item)
                                items_processed += 1
            
            # Process issues and pull requests - handle different API response formats
            # Yeni API format
            if isinstance(project_data, dict):
                for item_type in ["issues", "pull_requests"]:
                    if item_type in project_data and isinstance(project_data[item_type], list):
                        for item in project_data.get(item_type, []):
                            if "content" in item and "number" in item["content"]:
                                issue_number = item["content"]["number"]
                                item_id = f"issue_{issue_number}"
                                
                                # Make a copy to avoid modifying the original
                                item_data = copy.deepcopy(item)
                                
                                # Ensure milestone is normalized if present
                                if item_data.get("milestone") and isinstance(item_data["milestone"], dict):
                                    milestone_title = item_data["milestone"].get("title")
                                    if milestone_title:
                                        # Store the original milestone format for comparison
                                        item_data["milestone"]["normalized_title"] = self._normalize_milestone_value(milestone_title)
                                
                                # Add to original state dictionary
                                original_state[item_id] = item_data
                                items_processed += 1
            
            # Eski format - items dict
            if items_processed == 0 and "items" in project_data and isinstance(project_data["items"], dict):
                for item_id, item in project_data["items"].items():
                    if item.get("type") == "issue" or "number" in item.get("content", {}):
                        original_state[item_id] = item
                        items_processed += 1
            
            # Check if we've captured any data
            if len(original_state) == 0:
                print("HATA: Proje verilerinden orijinal durum oluşturulamadı. Veri formatı beklenenden farklı.")
                print(f"Veri formatı: {type(project_data)}")
                if isinstance(project_data, dict):
                    print(f"Anahtarlar: {list(project_data.keys())[:10]}")
                elif isinstance(project_data, list) and len(project_data) > 0:
                    print(f"Liste uzunluğu: {len(project_data)}")
                    if isinstance(project_data[0], dict):
                        print(f"İlk öğe anahtarları: {list(project_data[0].keys())[:10]}")
                return False
            
            # Save the original state to disk
            self._save_original_state(original_state)
            
            # Create sync marker file to indicate completion of first sync
            self._create_sync_marker()
            
            print(f"Orijinal durum kaydedildi: {len(original_state)} öğe ({milestones_processed} milestone, {items_processed} issue/PR)")
            
            # Set the internal state to the captured state
            self.original_state = original_state
            
            return True
        
        except Exception as e:
            print(f"Orijinal durum oluşturulurken hata: {str(e)}")
            traceback.print_exc()
            
            # Hata durumunda debug bilgisi göster
            print("\nHata ayıklama bilgisi:")
            print(f"Proje veri tipi: {type(project_data)}")
            if isinstance(project_data, dict):
                print(f"Mevcut anahtarlar: {list(project_data.keys())[:10]}")
            elif isinstance(project_data, list):
                print(f"Liste uzunluğu: {len(project_data)}")
                if len(project_data) > 0:
                    print(f"İlk öğe tipi: {type(project_data[0])}")
                    if isinstance(project_data[0], dict):
                        print(f"İlk öğe anahtarları: {list(project_data[0].keys())[:10]}")
            
            return False

    def auto_sync_issue_titles(self) -> int:
        """
        Automatically synchronize title fields in issue files to maintain consistency.
        
        This method:
        1. Scans all issue files
        2. Checks if content.title matches field_values[Title].value
        3. Updates the file if they don't match
        
        Returns:
            Number of files updated
        """
        updated_count = 0
        
        try:
            # Scan all issue files
            for item_id, item_data in self.current_state.items():
                # Skip non-issue items or items without required fields
                if not isinstance(item_data, dict) or item_data.get("type") != "issue":
                    continue
                
                if "content" not in item_data or not isinstance(item_data["content"], dict):
                    continue
                
                if "field_values" not in item_data or not isinstance(item_data["field_values"], list):
                    continue
                
                # Get content title
                content_title = item_data["content"].get("title")
                if not content_title:
                    continue
                
                # Find field_values title
                field_values_title = None
                for field in item_data["field_values"]:
                    if isinstance(field, dict) and field.get("field_name") == "Title":
                        field_values_title = field.get("value")
                        break
                
                # Skip if no field_values title found
                if field_values_title is None:
                    continue
                
                # Check if titles match
                if content_title != field_values_title:
                    file_path = item_data.get("file_path")
                    issue_number = item_data["content"].get("number", "")
                    
                    # Print inconsistency
                    print(f"Tutarsız başlıklar bulundu #{issue_number}: '{content_title}' -> '{field_values_title}'")
                    
                    # Skip if no file path
                    if not file_path or not os.path.exists(file_path):
                        continue
                    
                    # Synchronize titles by updating the file
                    try:
                        # Read file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            issue_json = json.load(f)
                        
                        # Update file with synchronized titles
                        for field in issue_json.get("field_values", []):
                            if isinstance(field, dict) and field.get("field_name") == "Title":
                                field["value"] = content_title
                                break
                        
                        # Write file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(issue_json, f, indent=2, ensure_ascii=False)
                        
                        # Increment counter
                        updated_count += 1
                        print(f"Başlık güncellendi: {file_path}")
                    except Exception as e:
                        print(f"Dosya güncellenirken hata: {file_path}, {str(e)}")
            
            # Rescan current state if any files were updated
            if updated_count > 0:
                # Reload current_state with updated files
                self.scan_current_state()
                
        except Exception as e:
            print(f"Başlık tutarlılığı kontrolü sırasında hata: {str(e)}")
            traceback.print_exc()
        
        return updated_count
    
    def _find_issue_file(self, issue_id: str) -> str:
        """
        Find the file path for a given issue ID.
        
        Args:
            issue_id: The ID of the issue (e.g., "issue_123")
            
        Returns:
            The full path to the issue file, or None if not found
        """
        if not issue_id.startswith("issue_"):
            return None
        
        # Extract issue number
        try:
            issue_number = int(issue_id.replace("issue_", ""))
        except ValueError:
            return None
        
        # Look in milestone directories
        milestones_dir = os.path.join(self.project_dir, "milestones")
        if not os.path.exists(milestones_dir):
            return None
        
        # Check all milestone directories
        for dir_name in os.listdir(milestones_dir):
            milestone_dir = os.path.join(milestones_dir, dir_name)
            if not os.path.isdir(milestone_dir):
                continue
            
            # Check for the issue file
            issue_file = os.path.join(milestone_dir, f"issue_{issue_number}.json")
            if os.path.exists(issue_file):
                return issue_file
            
            # Check in parent directories
            for parent_dir in os.listdir(milestone_dir):
                if not parent_dir.endswith("_parent") or not os.path.isdir(os.path.join(milestone_dir, parent_dir)):
                    continue
                
                parent_path = os.path.join(milestone_dir, parent_dir)
                issue_file = os.path.join(parent_path, f"issue_{issue_number}.json")
                if os.path.exists(issue_file):
                    return issue_file
        
        # If we're here, the file wasn't found
        return None 

    def detect_changes(self) -> Dict:
        """
        Detect changes between the original state and the current state.
        
        This method compares the original state loaded from disk or captured at first sync
        with the current state of local files.
        
        Returns:
            A dictionary of changes with 'created', 'updated', and 'deleted' lists
        """
        self.debug_print("Değişiklik algılama işlemi başlatılıyor...")
        
        # Initialize changes dictionary
        changes = {"created": [], "updated": [], "deleted": []}
        
        # Ensure original state is loaded
        original_state_loaded = True
        if not hasattr(self, 'original_state') or not self.original_state:
            original_state_loaded = self._load_original_state()
            
            if not original_state_loaded:
                self.debug_print("Karşılaştırma için orijinal durum bulunamadı. Lütfen önce proje verilerini indirin.")
                return changes
        
        # First fix any title inconsistencies to avoid false comparisons
        try:
            fixed_count = self.auto_sync_issue_titles()
            if fixed_count > 0:
                self.debug_print(f"{fixed_count} issue dosyasında başlık tutarsızlığı otomatik olarak düzeltildi.")
                # Re-scan current state after fixing
                self.scan_current_state()
        except Exception as e:
            self.debug_print(f"Başlık tutarlılığı kontrolü sırasında hata: {str(e)}")
        
        # Scan the current state from local files if not already done
        if not self.current_state:
            self.scan_current_state()
        
        # Make sure we have some content to compare
        if not self.current_state:
            self.debug_print("Karşılaştırılacak mevcut durum bulunamadı.")
            return changes
        
        # Convert original_state if it's in old format (with "items" dictionary)
        if "items" in self.original_state:
            # Convert old format to new flat format
            new_orig_state = {}
            for item_id, item_data in self.original_state["items"].items():
                if isinstance(item_data, dict) and "data" in item_data:
                    new_orig_state[item_id] = item_data["data"]
                else:
                    new_orig_state[item_id] = item_data
            self.original_state = new_orig_state
        
        # Debug information
        self.debug_print(f"Karşılaştırma için: {len(self.original_state)} orijinal öğe, {len(self.current_state)} mevcut öğe")
        
        # Daha fazla debug bilgisi için orijinal durum ve mevcut durumdaki öğe ID'lerini karşılaştır
        orig_ids = set(self.original_state.keys())
        current_ids = set(self.current_state.keys())
        
        # Gerçek öğe tiplerini içeren meta anahtarlar (bunlar değişiklik değil, metadata)
        meta_keys = ['captured_at', 'project_id', 'project_name', 'items']
        
        # Meta anahtarları çıkar
        orig_ids = {id for id in orig_ids if id not in meta_keys}
        current_ids = {id for id in current_ids if id not in meta_keys}
        
        # Özel olarak issue_11 kontrol
        if "issue_11" in orig_ids and "issue_11" in current_ids:
            self.debug_print("issue_11 her iki durumda da bulundu. Parmak izleri karşılaştırılıyor:")
            orig_issue_11 = self.original_state["issue_11"]
            curr_issue_11 = self.current_state["issue_11"]
            
            # Parmak izleri oluştur
            orig_fp = self._create_fingerprint(orig_issue_11)
            curr_fp = self._create_fingerprint(curr_issue_11)
            
            self.debug_print(f"issue_11 original fingerprint: {orig_fp}")
            self.debug_print(f"issue_11 current fingerprint: {curr_fp}")
            
            # Field değişiklikleri bul
            field_changes = self._find_specific_changes(orig_issue_11, curr_issue_11)
            self.debug_print(f"issue_11 field changes: {field_changes}")
            
            # Değişiklik varsa güncellenmiş öğeler listesine ekle
            if field_changes:
                self.debug_print("Değişiklik tespit edildi ve listeye eklendi: issue_11")
                # Create detailed change record
                change_record = {
                    "id": "issue_11",
                    "type": "issue",
                    "title": self._get_item_title(curr_issue_11),
                    "file_path": curr_issue_11.get("file_path", ""),
                    "changes": field_changes,
                    "change_details": "Güncellendi"
                }
                
                # Add number for issues
                if "number" in curr_issue_11:
                    change_record["number"] = curr_issue_11["number"]
                
                changes["updated"].append(change_record)
        
        # Yeni öğeler
        new_ids = current_ids - orig_ids
        if new_ids:
            self.debug_print(f"Yeni öğeler (current_state'de var ama original_state'de yok): {sorted(new_ids)}")
        
        # Silinen öğeler 
        deleted_ids = orig_ids - current_ids
        if deleted_ids:
            self.debug_print(f"Silinen öğeler (original_state'de var ama current_state'de yok): {sorted(deleted_ids)}")
        
        # Karşılaştırılacak öğeler (her ikisinde de var)
        common_ids = orig_ids.intersection(current_ids)
        self.debug_print(f"Her iki durumda da bulunan {len(common_ids)} öğe karşılaştırılacak")
        
        # Check for created items (in current but not in original)
        for item_id in new_ids:
            current_item = self.current_state[item_id]
            
            # Skip false positives for milestone directories
            if item_id.startswith("milestone_") and "type" in current_item and current_item["type"] == "milestone":
                # Check if a similar milestone exists with different formatting
                found_match = False
                for orig_id, orig_item in self.original_state.items():
                    if orig_id.startswith("milestone_") and isinstance(orig_item, dict) and "type" in orig_item and orig_item["type"] == "milestone":
                        # Compare normalized titles
                        if isinstance(current_item, dict) and "title" in current_item:
                            current_title = self._normalize_milestone_value(current_item.get("title", ""))
                            orig_title = self._normalize_milestone_value(orig_item.get("title", ""))
                            
                            if current_title and orig_title and current_title.lower() == orig_title.lower():
                                found_match = True
                                break
                
                if found_match:
                    continue  # Skip this milestone as it exists in original state
            
            # Debug bilgisi ekle - ne tür bir öğenin eklendiğini gör
            if isinstance(current_item, dict):
                item_type = current_item.get("type", "unknown")
                title = self._get_item_title(current_item)
                self.debug_print(f"Yeni öğe tespit edildi: {item_id} (Type: {item_type}, Title: {title})")
            
            # Check item has valid type
            if isinstance(current_item, dict) and "type" in current_item:
                # Create detailed change record
                change_record = {
                    "id": item_id,
                    "type": current_item["type"],
                    "title": self._get_item_title(current_item),
                    "file_path": current_item.get("file_path", ""),
                    "change_details": "Yeni oluşturuldu",
                    "is_initial_sync": False
                }
                
                # Add number for issues
                if current_item["type"] == "issue" and "number" in current_item:
                    change_record["number"] = current_item["number"]
                
                changes["created"].append(change_record)
        
        # Check for updated items (in both but with different content)
        for item_id in common_ids:
            # issue_11 için özel işlemi zaten yaptık
            if item_id == "issue_11":
                continue
                
            current_item = self.current_state[item_id]
            orig_item = self.original_state[item_id]
            
            # Ensure both items are dictionaries
            if not isinstance(current_item, dict) or not isinstance(orig_item, dict):
                continue
                
            # Skip if one doesn't have type
            if "type" not in current_item or "type" not in orig_item:
                continue
            
            # Create fingerprints for comparison
            current_fp = self._create_fingerprint(current_item)
            original_fp = self._create_fingerprint(orig_item)
            
            # Debug bilgisi ekle - parmak izlerini karşılaştır
            if current_fp != original_fp:
                item_type = current_item.get("type", "unknown")
                title = self._get_item_title(current_item)
                self.debug_print(f"Değişiklik tespit edildi: {item_id} (Type: {item_type}, Title: {title})")
                self.debug_print(f"  Orijinal parmak izi: {original_fp}")
                self.debug_print(f"  Güncel parmak izi: {current_fp}")
            
            if current_fp != original_fp:
                # Find specific field changes for better reporting
                field_changes = self._find_specific_changes(orig_item, current_item)
                
                # Check for title consistency in issue files
                if current_item["type"] == "issue":
                    # Handle title consistency between content.title and field_values.title
                    content_title = None
                    field_values_title = None
                    
                    if "content" in current_item and isinstance(current_item["content"], dict):
                        content_title = current_item["content"].get("title")
                        
                    # Field values title is no longer used, only content.title is the source of truth
                    
                    # Just warn if we still have field_values with Title somewhere
                    if "field_values" in current_item and isinstance(current_item["field_values"], list):
                        for field in current_item["field_values"]:
                            if isinstance(field, dict) and field.get("field_name") == "Title":
                                self.debug_print(f"UYARI: #{current_item.get('number', '')} hala field_values içinde Title alanı var. Bu silinmeli!")
                
                if field_changes:
                    # Print detected changes for debugging
                    self.debug_print(f"  Tespit edilen değişiklikler:")
                    for field_name, change_info in field_changes.items():
                        self.debug_print(f"    {field_name}: '{change_info['old']}' -> '{change_info['new']}'")
                    
                    # Create detailed change record
                    change_record = {
                        "id": item_id,
                        "type": current_item["type"],
                        "title": self._get_item_title(current_item),
                        "file_path": current_item.get("file_path", ""),
                        "changes": field_changes,
                        "change_details": "Güncellendi"
                    }
                    
                    # Add number for issues
                    if current_item["type"] == "issue" and "number" in current_item:
                        change_record["number"] = current_item["number"]
                    
                    changes["updated"].append(change_record)
        
        # Check for deleted items (in original but not in current)
        for item_id in deleted_ids:
            # Original state'deki öğeyi al
            orig_item = self.original_state[item_id]
            
            # Check if this is a real item and not metadata
            if isinstance(orig_item, dict) and "type" in orig_item:
                # Debug bilgisi ekle - silinen öğe hakkında bilgi göster 
                item_type = orig_item.get("type", "unknown")
                title = self._get_item_title(orig_item)
                self.debug_print(f"Silinen öğe tespit edildi: {item_id} (Type: {item_type}, Title: {title})")
                
                # Create detailed change record
                change_record = {
                    "id": item_id,
                    "type": orig_item["type"],
                    "title": self._get_item_title(orig_item),
                    "data": orig_item,  # Keep original data for possible restore
                    "change_details": "Silindi"
                }
                
                # Add number for issues
                if orig_item["type"] == "issue" and "number" in orig_item:
                    change_record["number"] = orig_item["number"]
                
                changes["deleted"].append(change_record)
        
        # Store the changes for later use
        self.changes = changes
        
        # Print a summary of the changes
        total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
        self.debug_print(f"Toplam {total_changes} değişiklik algılandı: {len(changes['created'])} eklenen, {len(changes['updated'])} güncellenen, {len(changes['deleted'])} silinen")
        
        if total_changes == 0:
            self.debug_print("Not: Değişiklik algılanmadı. Değişiklikleriniz sonrasında hemen değişiklik algılanmasını bekliyorsanız:")
            self.debug_print("1. Her iki başlık alanını da güncelleyin (content.title ve field_values > Title)")
            self.debug_print("2. Dosyaları kaydettikten sonra birkaç saniye bekleyin")
            self.debug_print("3. Değişiklik algılama butonunu tekrar deneyin")
        
        return changes

    def get_changes_summary(self) -> Dict[str, int]:
        """
        Returns a summary of the detected changes.
        
        Returns:
            Dictionary with counts of each change type
        """
        if not hasattr(self, 'changes') or not self.changes:
            return {"created": 0, "updated": 0, "deleted": 0, "total": 0}
        
        summary = {
            "created": len(self.changes.get("created", [])),
            "updated": len(self.changes.get("updated", [])),
            "deleted": len(self.changes.get("deleted", []))
        }
        summary["total"] = summary["created"] + summary["updated"] + summary["deleted"]
        
        return summary
    
    def get_changes_by_type(self, change_type: str) -> List[Dict]:
        """
        Returns changes of a specific type.
        
        Args:
            change_type: The type of changes to return ("created", "updated", or "deleted")
            
        Returns:
            List of changes of the specified type
        """
        if not hasattr(self, 'changes') or not self.changes:
            return []
        
        return self.changes.get(change_type, []) 

    def _create_fingerprint(self, item):
        """
        Create a fingerprint for the given item.
        This fingerprint is used to detect changes in items across syncs.
        
        Args:
            item (dict): The item to create a fingerprint for
            
        Returns:
            str: A fingerprint hash for the item
        """
        fingerprint_data = {}
        
        # Log item type and title for debugging
        item_type = item.get("type", "unknown")
        title = self._get_item_title(item)
        self.debug_print(f"Parmak izi oluşturuluyor: {item_type} - {title}")
        
        try:
            # Start with basic fields
            for basic_field in ["title", "state", "description", "due_on"]:
                if basic_field in item:
                    fingerprint_data[basic_field] = item[basic_field]
                    self.debug_print(f"  - {basic_field}: {item[basic_field]}")
            
            # Add fingerprints for nested content
            if "content" in item:
                fingerprint_data["content"] = {}
                for content_field in ["body", "title", "state"]:
                    if content_field in item["content"]:
                        fingerprint_data["content"][content_field] = item["content"][content_field]
                        self.debug_print(f"  - content.{content_field}: {item['content'][content_field]}")
            
            # Add fingerprints for field values
            if "field_values" in item and isinstance(item["field_values"], list):
                fingerprint_data["field_values"] = {}
                for field in item["field_values"]:
                    if isinstance(field, dict) and "field_name" in field and "value" in field:
                        # Skip duplicate title field to avoid mismatches
                        if field["field_name"] == "Title" and "content" in fingerprint_data and "title" in fingerprint_data["content"]:
                            continue
                            
                        field_name = field["field_name"]
                        field_value = field["value"]
                        
                        # Special handling for Status - fix common variations
                        if field_name == "Status" and isinstance(field_value, str):
                            field_value = field_value.strip()
                        
                        fingerprint_data["field_values"][field_name] = field_value
                        self.debug_print(f"  - field_values.{field_name}: {field_value}")
            
            # Handle milestones (parent milestone for issues or milestone data)
            if "milestone" in item and item["milestone"]:
                if isinstance(item["milestone"], dict):
                    # Include milestone details - normalize milestone title
                    milestone_data = {}
                    if "title" in item["milestone"]:
                        milestone_title = self._normalize_milestone_value(item["milestone"]["title"])
                        milestone_data["title"] = milestone_title
                        self.debug_print(f"  - milestone.title: {milestone_title}")
                    
                    if "due_on" in item["milestone"]:
                        milestone_data["due_on"] = item["milestone"]["due_on"]
                        self.debug_print(f"  - milestone.due_on: {item['milestone']['due_on']}")
                        
                    fingerprint_data["milestone"] = milestone_data
                else:
                    # For a simple string/ID reference
                    fingerprint_data["milestone"] = str(item["milestone"])
                    self.debug_print(f"  - milestone: {item['milestone']}")
            
            # Handle assignees
            if "assignees" in item and isinstance(item["assignees"], list):
                # Store simplified assignee data (usernames only)
                assignee_usernames = []
                for assignee in item["assignees"]:
                    if isinstance(assignee, dict) and "login" in assignee:
                        assignee_usernames.append(assignee["login"])
                    elif isinstance(assignee, str):
                        assignee_usernames.append(assignee)
                
                if assignee_usernames:
                    fingerprint_data["assignees"] = sorted(assignee_usernames)  # Sort for consistent order
                    self.debug_print(f"  - assignees: {fingerprint_data['assignees']}")
            
            # Handle parent issue links
            if "parent_issue" in item and item["parent_issue"]:
                if isinstance(item["parent_issue"], dict):
                    # Include minimal parent issue info
                    parent_data = {}
                    if "number" in item["parent_issue"]:
                        parent_data["number"] = item["parent_issue"]["number"]
                        self.debug_print(f"  - parent_issue.number: {item['parent_issue']['number']}")
                    
                    fingerprint_data["parent_issue"] = parent_data
                else:
                    # For a simple string/ID reference
                    fingerprint_data["parent_issue"] = str(item["parent_issue"])
                    self.debug_print(f"  - parent_issue: {item['parent_issue']}")
            
            # Special case for issue_11 - print more details 
            if item.get("id") == "issue_11" or (item.get("number") == 11 and item.get("type") == "issue"):
                self.debug_print("issue_11 için detaylı parmak izi bilgileri:")
                self.debug_print(f"  - Tam veri: {json.dumps(fingerprint_data, indent=2)}")
                
                # Kontrol et: "Status" alanı var mı?
                if "field_values" in fingerprint_data:
                    if "Status" in fingerprint_data["field_values"]:
                        self.debug_print(f"  - Status alanı mevcut: {fingerprint_data['field_values']['Status']}")
                    else:
                        self.debug_print("  - Status alanı mevcut değil!")
                
                # Kontrol et: "state" alanı var mı?
                if "state" in fingerprint_data:
                    self.debug_print(f"  - state alanı mevcut: {fingerprint_data['state']}")
                else:
                    self.debug_print("  - state alanı mevcut değil!")
            
            # Generate a consistent hash from fingerprint data
            result = hashlib.md5(json.dumps(fingerprint_data, sort_keys=True).encode()).hexdigest()
            self.debug_print(f"Oluşturulan parmak izi: {result}")
            return result
        
        except Exception as e:
            self.debug_print(f"Parmak izi oluşturma hatası: {str(e)}")
            # Fallback to a simple hash if something goes wrong
            try:
                basic_data = {
                    "title": self._get_item_title(item),
                    "type": item.get("type", "unknown"),
                    "id": item.get("id", "")
                }
                return hashlib.md5(json.dumps(basic_data, sort_keys=True).encode()).hexdigest()
            except:
                # Ultra-fallback
                return hashlib.md5(str(item).encode()).hexdigest()

    def _create_sync_marker(self):
        """Create a marker file to indicate completion of first sync"""
        try:
            sync_marker_path = os.path.join(self.project_dir, "sync_completed.mark")
            with open(sync_marker_path, "w") as f:
                f.write(datetime.now().isoformat())
            # Debug mesajını kaldırıldı, sadece hata durumunda bilgi gösteriliyor
        except Exception as e:
            print(f"Senkronizasyon işareti oluşturulurken hata: {str(e)}") 

    def _find_specific_changes(self, orig_item, current_item):
        """
        İki öğe arasındaki değişiklikleri detaylı olarak bulur.
        
        Args:
            orig_item: Orijinal öğe
            current_item: Güncel öğe
            
        Returns:
            dict: Değişiklikleri içeren sözlük, her alan için {'old': eski_değer, 'new': yeni_değer} formatında
        """
        changes = {}
        
        # Her iki öğe de dictionary değilse hata
        if not isinstance(orig_item, dict) or not isinstance(current_item, dict):
            self.debug_print("Öğe karşılaştırılıyor...")
            return changes
        
        # BASIC FIELDS - Temel seviye alanları karşılaştır
        for field in ["title", "state", "description", "due_on"]:
            orig_val = orig_item.get(field)
            current_val = current_item.get(field)
            
            if orig_val != current_val:
                self.debug_print(f"Değişiklik bulundu - {field}: '{orig_val}' -> '{current_val}'")
                changes[field] = {"old": orig_val, "new": current_val}
        
        # CONTENT - İçerik karşılaştırması
        if "content" in orig_item or "content" in current_item:
            orig_content = orig_item.get("content", {})
            current_content = current_item.get("content", {})
            
            if not isinstance(orig_content, dict):
                orig_content = {}
            if not isinstance(current_content, dict):
                current_content = {}
            
            # İçerik alanlarını karşılaştır
            for content_field in ["title", "body", "state"]:
                orig_val = orig_content.get(content_field)
                current_val = current_content.get(content_field)
                
                if orig_val != current_val:
                    self.debug_print(f"Değişiklik bulundu - content.{content_field}: '{orig_val}' -> '{current_val}'")
                    changes[f"content.{content_field}"] = {"old": orig_val, "new": current_val}
        
        # FIELD VALUES - Alan değerleri karşılaştırması
        # İki farklı formatta olabilirler, eski: liste, yeni: sözlük
        orig_fields = {}
        current_fields = {}
        
        # Orijinal değerleri topla
        if "field_values" in orig_item:
            if isinstance(orig_item["field_values"], list):
                # Listeyi sözlüğe çevir
                for field in orig_item["field_values"]:
                    if isinstance(field, dict) and "field_name" in field and "value" in field:
                        orig_fields[field["field_name"]] = field["value"]
            elif isinstance(orig_item["field_values"], dict):
                # Zaten sözlük formatında
                orig_fields = orig_item["field_values"]
        
        # Güncel değerleri topla
        if "field_values" in current_item:
            if isinstance(current_item["field_values"], list):
                # Listeyi sözlüğe çevir
                for field in current_item["field_values"]:
                    if isinstance(field, dict) and "field_name" in field and "value" in field:
                        current_fields[field["field_name"]] = field["value"]
            elif isinstance(current_item["field_values"], dict):
                # Zaten sözlük formatında
                current_fields = current_item["field_values"]
        
        # Tüm field_name değerlerini birleştir
        all_fields = set(orig_fields.keys()).union(set(current_fields.keys()))
        
        # Her alanı karşılaştır
        for field_name in all_fields:
            orig_val = orig_fields.get(field_name)
            current_val = current_fields.get(field_name)
            
            if orig_val != current_val:
                self.debug_print(f"Değişiklik bulundu - field_values.{field_name}: '{orig_val}' -> '{current_val}'")
                changes[f"field_values.{field_name}"] = {"old": orig_val, "new": current_val}
        
        # MILESTONE - Kilometre taşı bilgisi karşılaştırması
        if "milestone" in orig_item or "milestone" in current_item:
            orig_milestone = orig_item.get("milestone", {})
            current_milestone = current_item.get("milestone", {})
            
            if not isinstance(orig_milestone, dict):
                orig_milestone = {}
            if not isinstance(current_milestone, dict):
                current_milestone = {}
            
            # Kilometre taşı alanlarını karşılaştır
            for ms_field in ["title", "due_on", "state"]:
                orig_val = orig_milestone.get(ms_field)
                current_val = current_milestone.get(ms_field)
                
                if orig_val != current_val:
                    self.debug_print(f"Değişiklik bulundu - milestone.{ms_field}: '{orig_val}' -> '{current_val}'")
                    changes[f"milestone.{ms_field}"] = {"old": orig_val, "new": current_val}
        
        # ASSIGNEES - Atananlar karşılaştırması
        if "assignees" in orig_item or "assignees" in current_item:
            orig_assignees = orig_item.get("assignees", [])
            current_assignees = current_item.get("assignees", [])
            
            # Normalize edin (login değerlerini alın)
            orig_logins = self._extract_assignee_logins(orig_assignees)
            current_logins = self._extract_assignee_logins(current_assignees)
            
            # Set olarak karşılaştırın (sıralama önemli değil)
            orig_set = set(orig_logins)
            current_set = set(current_logins)
            
            if orig_set != current_set:
                # Atananlar değişmiş
                self.debug_print(f"Değişiklik bulundu - assignees: '{orig_logins}' -> '{current_logins}'")
                changes["assignees"] = {"old": orig_logins, "new": current_logins}
        
        # PARENT ISSUE - Üst issue karşılaştırması
        if "parent_issue" in orig_item or "parent_issue" in current_item:
            orig_parent = orig_item.get("parent_issue")
            current_parent = current_item.get("parent_issue")
            
            # Normalize edin (number değerini alın)
            orig_number = self._extract_parent_number(orig_parent)
            current_number = self._extract_parent_number(current_parent)
            
            if orig_number != current_number:
                # Üst issue değişmiş
                self.debug_print(f"Değişiklik bulundu - parent_issue: '{orig_number}' -> '{current_number}'")
                changes["parent_issue"] = {"old": orig_number, "new": current_number}
        
        # REPOSITORY - Repository karşılaştırması
        if "repository" in orig_item or "repository" in current_item:
            orig_repo = orig_item.get("repository")
            current_repo = current_item.get("repository")
            
            # İki format olabilir: string veya dict
            if isinstance(orig_repo, dict) and isinstance(current_repo, dict):
                # Her ikisi de dict, name karşılaştır
                orig_name = orig_repo.get("name")
                current_name = current_repo.get("name")
                
                if orig_name != current_name:
                    self.debug_print(f"Değişiklik bulundu - repository.name: '{orig_name}' -> '{current_name}'")
                    changes["repository.name"] = {"old": orig_name, "new": current_name}
                
                # Owner karşılaştır
                if "owner" in orig_repo or "owner" in current_repo:
                    orig_owner = orig_repo.get("owner", {})
                    current_owner = current_repo.get("owner", {})
                    
                    if isinstance(orig_owner, dict) and isinstance(current_owner, dict):
                        orig_login = orig_owner.get("login")
                        current_login = current_owner.get("login")
                        
                        if orig_login != current_login:
                            self.debug_print(f"Değişiklik bulundu - repository.owner.login: '{orig_login}' -> '{current_login}'")
                            changes["repository.owner.login"] = {"old": orig_login, "new": current_login}
                    elif orig_owner != current_owner:
                        self.debug_print(f"Değişiklik bulundu - repository.owner: '{orig_owner}' -> '{current_owner}'")
                        changes["repository.owner"] = {"old": orig_owner, "new": current_owner}
            elif orig_repo != current_repo:
                # İki farklı değer
                self.debug_print(f"Değişiklik bulundu - repository: '{orig_repo}' -> '{current_repo}'")
                changes["repository"] = {"old": orig_repo, "new": current_repo}
        
        return changes
    
    def _extract_assignee_logins(self, assignees):
        """
        Atananlardan login değerlerini çıkarır.
        
        Args:
            assignees: Atananlar listesi veya sözlüğü
            
        Returns:
            list: Login değerleri listesi
        """
        logins = []
        
        if not assignees:
            return logins
        
        if isinstance(assignees, list):
            for assignee in assignees:
                if isinstance(assignee, dict) and "login" in assignee:
                    logins.append(assignee["login"])
                elif isinstance(assignee, str):
                    logins.append(assignee)
        elif isinstance(assignees, str):
            logins.append(assignees)
        
        return sorted(logins)  # Consistent order
    
    def _extract_parent_number(self, parent):
        """
        Üst issue'dan numara değerini çıkarır.
        
        Args:
            parent: Üst issue bilgisi
            
        Returns:
            int or None: Üst issue numarası, yoksa None
        """
        if not parent:
            return None
        
        if isinstance(parent, dict) and "number" in parent:
            return parent["number"]
        elif isinstance(parent, int):
            return parent
        elif isinstance(parent, str) and parent.isdigit():
            return int(parent)
        
        return None

    def debug_print(self, message):
        """
        Debug mesajlarını hem konsola hem de debug.log dosyasına yazdırır.
        Bu metod sadece geliştirme aşamasında kullanılmalıdır.
        
        Args:
            message (str): Yazdırılacak debug mesajı
        """
        print(message)
        try:
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"{message}\n")
        except Exception as e:
            print(f"Debug log yazma hatası: {e}")
            
    def _get_item_title(self, item):
        """
        Bir öğenin başlığını bir dizi olası yerden alır.
        
        Args:
            item (dict): Başlığı alınacak öğe
            
        Returns:
            str: Öğenin başlığı, bulunamadıysa "Başlık bulunamadı" döner
        """
        if not isinstance(item, dict):
            return "Geçersiz öğe tipi"
        
        # Content içindeki başlığı kontrol et
        if "content" in item and isinstance(item["content"], dict):
            if "title" in item["content"]:
                return item["content"]["title"]
        
        # Doğrudan title alanını kontrol et
        if "title" in item:
            return item["title"]
        
        # field_values içinde Title alanını kontrol et
        if "field_values" in item and isinstance(item["field_values"], list):
            for field in item["field_values"]:
                if isinstance(field, dict) and field.get("field_name") == "Title" and "value" in field:
                    return field["value"]
        
        # Number alanı varsa onu göster
        if "number" in item:
            return f"Issue #{item['number']}"
            
        # Hiçbir şey bulunamadıysa
        return "Başlık bulunamadı"
        
    def _normalize_milestone_value(self, value):
        """
        Milestone başlığını normalleştirerek karşılaştırma için standart hale getirir.
        
        Args:
            value: Normalleştirilecek değer
            
        Returns:
            str: Normalleştirilmiş değer
        """
        if not value:
            return ""
            
        # String'e çevir
        value_str = str(value)
        
        # Yaygın milestone formatlarını standartlaştır
        # 1. "Sprint 1: Something" -> "sprint_1__something"
        # 2. "Sprint 1 - Something" -> "sprint_1__something"
        
        # Küçük harfe çevir
        normalized = value_str.lower()
        
        # Tire ve iki nokta formatlarını aynı hale getir
        normalized = normalized.replace(": ", " - ")
        normalized = normalized.replace(":", " - ")
        
        # Boşlukları ve noktalama işaretlerini temizle
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Çoklu boşlukları tek boşluğa indirge
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Baş ve sondaki boşlukları temizle
        normalized = normalized.strip()
        
        # Boşlukları alt çizgiye çevir
        normalized = normalized.replace(' ', '_')
        
        # Çoklu alt çizgileri tek alt çizgiye indirge
        normalized = re.sub(r'_+', '_', normalized)
        
        return normalized
        
    def save_current_as_original(self):
        """
        Mevcut durumu yeni orijinal durum olarak kaydeder.
        Bu fonksiyon, değişiklikleri GitHub'a göndermeden "yok saymak" için kullanılır.
        
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        if not self.current_state:
            self.debug_print("Mevcut durum boş, önce tarama yapılmalı.")
            return False
            
        # Mevcut durumu orijinal durum olarak ayarla
        self.original_state = copy.deepcopy(self.current_state)
        
        # Diskte sakla
        try:
            # Önce cache dizininin varlığını kontrol et
            cache_dir = os.path.join(self.project_dir, ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Orijinal durum dosyasını oluştur
            original_state_file = os.path.join(cache_dir, "original_state.json")
            
            # Dosyaya yaz
            with open(original_state_file, "w", encoding="utf-8") as f:
                json.dump(self.original_state, f, indent=2, ensure_ascii=False)
                
            self.debug_print(f"Mevcut durum başarıyla yeni orijinal durum olarak kaydedildi. ({len(self.original_state)} öğe)")
            return True
        except Exception as e:
            self.debug_print(f"Orijinal durum kaydedilirken hata: {str(e)}")
            return False 

    def apply_changes_from_file(self, file_path, target_file_path=None):
        """
        Belirtilen dosyadaki değişiklikleri hedef dosyaya uygular.
        Bu metod, bir dosyadaki değişiklikleri alıp başka bir dosyaya uygulamak için kullanılır.
        
        Args:
            file_path (str): Değişikliklerin alınacağı kaynak dosya
            target_file_path (str, optional): Değişikliklerin uygulanacağı hedef dosya.
                                             Belirtilmezse aynı dosya güncellenir.
                                             
        Returns:
            bool: Başarılı ise True, değilse False
        """
        if not os.path.exists(file_path):
            print(f"Kaynak dosya bulunamadı: {file_path}")
            return False
            
        # Hedef dosya belirtilmemişse, kaynak dosya hedef olarak kullanılır
        if target_file_path is None:
            target_file_path = file_path
        
        try:
            # Kaynak dosyayı oku
            with open(file_path, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
                
            # Hedef dosya varsa oku, yoksa kaynak veriyi kullan
            if os.path.exists(target_file_path) and file_path != target_file_path:
                with open(target_file_path, 'r', encoding='utf-8') as f:
                    target_data = json.load(f)
            else:
                target_data = copy.deepcopy(source_data)
                
            # Değişiklikleri uygula
            if "content" in source_data and "content" in target_data:
                # Title ve State güncelleme
                if "title" in source_data["content"]:
                    target_data["content"]["title"] = source_data["content"]["title"]
                if "state" in source_data["content"]:
                    target_data["content"]["state"] = source_data["content"]["state"]
                    
            # Field Values güncelleme
            if "field_values" in source_data and "field_values" in target_data:
                for key, value in source_data["field_values"].items():
                    target_data["field_values"][key] = value
                    
            # Hedef dosyaya yaz
            with open(target_file_path, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2, ensure_ascii=False)
                
            print(f"Değişiklikler başarıyla uygulandı: {target_file_path}")
            return True
            
        except Exception as e:
            print(f"Değişiklik uygulama hatası: {e}")
            return False
            
    def sync_all_issue_titles(self):
        """
        Tüm sorun dosyalarında başlık tutarsızlıklarını kontrol eder ve düzeltir.
        
        Returns:
            int: Güncellenen dosya sayısı
        """
        updated_count = 0
        
        # Şu anki durumu tara
        current_state = self.scan_current_state()
        
        for item_id, item in current_state.items():
            if item["type"] == "issue":
                file_path = item["file_path"]
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    title_in_content = data.get("content", {}).get("title")
                    title_in_fields = None
                    
                    # Field values içinde title alanını bul
                    if "field_values" in data:
                        for key, value in data["field_values"].items():
                            if key.lower() == "title":
                                title_in_fields = value
                                break
                    
                    # Başlıklar tutarsız mı kontrol et
                    if title_in_content and title_in_fields and title_in_content != title_in_fields:
                        # Başlıkları eşitle (content.title değerini kullan)
                        for key in data["field_values"]:
                            if key.lower() == "title":
                                data["field_values"][key] = title_in_content
                                break
                        
                        # Dosyayı kaydet
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            
                        updated_count += 1
                        print(f"Başlık güncellendi: {file_path}")
                        print(f"  Eski başlık (field): {title_in_fields}")
                        print(f"  Yeni başlık: {title_in_content}")
                        
                except Exception as e:
                    print(f"Dosya işleme hatası: {file_path}, Hata: {e}")
        
        return updated_count 