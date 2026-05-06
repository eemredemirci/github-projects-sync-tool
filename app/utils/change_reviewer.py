"""
Change reviewing module for GitHub Project Sync Tool.
This module provides classes for reviewing and approving detected changes.
"""
import os
import json
import yaml
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from app.utils.change_tracker import ChangeTracker

class ChangeReviewer:
    """
    Reviews and approves changes detected by the ChangeTracker.
    Allows for individual or bulk approval of changes before they are sent to GitHub.
    """
    
    def __init__(self, change_tracker: ChangeTracker):
        """
        Initialize the change reviewer.
        
        Args:
            change_tracker: The ChangeTracker instance with detected changes
        """
        self.change_tracker = change_tracker
        self.project_dir = change_tracker.project_dir
        self.pending_dir = os.path.join(self.project_dir, ".pending")
        self.pending_operations_file = os.path.join(self.pending_dir, "pending_operations.json")
        
        # Ensure pending directory exists
        if not os.path.exists(self.pending_dir):
            os.makedirs(self.pending_dir)
        
        # Data structures for tracking reviews
        self.approved_changes = {
            "created": [],
            "updated": [],
            "deleted": []
        }
        self.rejected_changes = {
            "created": [],
            "updated": [],
            "deleted": []
        }
        
        # Load any existing pending operations
        self.load_pending_operations()
    
    def display_changes_summary(self) -> Dict[str, int]:
        """
        Returns a summary of the detected changes.
        
        Returns:
            Dictionary with counts of each change type
        """
        return self.change_tracker.get_changes_summary()
    
    def display_changes_by_type(self, change_type: str) -> List[Dict]:
        """
        Returns changes of a specific type.
        
        Args:
            change_type: The type of changes to return ("created", "updated", or "deleted")
            
        Returns:
            List of changes of the specified type
        """
        return self.change_tracker.get_changes_by_type(change_type)
    
    def get_change_by_id(self, change_type: str, index: int) -> Optional[Dict]:
        """
        Gets a specific change by its index within a change type.
        
        Args:
            change_type: The type of change ("created", "updated", or "deleted")
            index: The index of the change in the list
            
        Returns:
            The change data or None if not found
        """
        changes = self.change_tracker.get_changes_by_type(change_type)
        if 0 <= index < len(changes):
            return changes[index]
        return None
    
    def format_change_details(self, change: Dict) -> str:
        """
        Formats change details for display.
        
        Args:
            change: The change data
            
        Returns:
            Formatted string representation of the change
        """
        change_type = change.get("type", "unknown")
        
        if change_type == "issue":
            number = change.get("number", "?")
            title = change.get("title", "No title")
            return f"Issue #{number}: {title}"
        
        elif change_type == "milestone":
            title = change.get("title", "No title")
            return f"Milestone: {title}"
        
        else:
            return f"Item: {change.get('key', 'unknown')}"
    
    def format_specific_changes(self, changes: List[Dict]) -> str:
        """
        Formats specific field changes for display.
        
        Args:
            changes: List of specific field changes
            
        Returns:
            Formatted string representation of the changes
        """
        if not changes:
            return "No specific field changes detected."
        
        result = []
        for change in changes:
            field = change.get("field", "unknown")
            old_value = change.get("old_value", "")
            new_value = change.get("new_value", "")
            
            # Truncate long values
            if isinstance(old_value, str) and len(old_value) > 50:
                old_value = old_value[:47] + "..."
            if isinstance(new_value, str) and len(new_value) > 50:
                new_value = new_value[:47] + "..."
            
            result.append(f"- {field}: '{old_value}' → '{new_value}'")
        
        return "\n".join(result)
    
    def approve_change(self, change_type: str, index: int) -> bool:
        """
        Approves a specific change.
        
        Args:
            change_type: The type of change ("created", "updated", or "deleted")
            index: The index of the change in the list
            
        Returns:
            Whether the operation was successful
        """
        change = self.get_change_by_id(change_type, index)
        if not change:
            return False
        
        # Add to approved changes if not already there
        if change not in self.approved_changes[change_type]:
            self.approved_changes[change_type].append(change)
        
        # Remove from rejected changes if it was there
        if change in self.rejected_changes[change_type]:
            self.rejected_changes[change_type].remove(change)
        
        # Save pending operations
        self.save_pending_operations()
        
        return True
    
    def reject_change(self, change_type: str, index: int) -> bool:
        """
        Rejects a specific change.
        
        Args:
            change_type: The type of change ("created", "updated", or "deleted")
            index: The index of the change in the list
            
        Returns:
            Whether the operation was successful
        """
        change = self.get_change_by_id(change_type, index)
        if not change:
            return False
        
        # Add to rejected changes if not already there
        if change not in self.rejected_changes[change_type]:
            self.rejected_changes[change_type].append(change)
        
        # Remove from approved changes if it was there
        if change in self.approved_changes[change_type]:
            self.approved_changes[change_type].remove(change)
        
        # Save pending operations
        self.save_pending_operations()
        
        return True
    
    def bulk_approve(self, change_type: Optional[str] = None) -> int:
        """
        Approves all changes of a specific type, or all changes if type is None.
        
        Args:
            change_type: The type of changes to approve, or None for all types
            
        Returns:
            Number of changes approved
        """
        count = 0
        
        if change_type:
            # Approve all changes of a specific type
            changes = self.change_tracker.get_changes_by_type(change_type)
            for i in range(len(changes)):
                if self.approve_change(change_type, i):
                    count += 1
        else:
            # Approve all changes of all types
            for type_name in ["created", "updated", "deleted"]:
                changes = self.change_tracker.get_changes_by_type(type_name)
                for i in range(len(changes)):
                    if self.approve_change(type_name, i):
                        count += 1
        
        return count
    
    def bulk_reject(self, change_type: Optional[str] = None) -> int:
        """
        Rejects all changes of a specific type, or all changes if type is None.
        
        Args:
            change_type: The type of changes to reject, or None for all types
            
        Returns:
            Number of changes rejected
        """
        count = 0
        
        if change_type:
            # Reject all changes of a specific type
            changes = self.change_tracker.get_changes_by_type(change_type)
            for i in range(len(changes)):
                if self.reject_change(change_type, i):
                    count += 1
        else:
            # Reject all changes of all types
            for type_name in ["created", "updated", "deleted"]:
                changes = self.change_tracker.get_changes_by_type(type_name)
                for i in range(len(changes)):
                    if self.reject_change(type_name, i):
                        count += 1
        
        return count
    
    def save_pending_operations(self) -> bool:
        """
        Saves the current approved and rejected changes to a file.
        
        Returns:
            Whether the operation was successful
        """
        try:
            pending_data = {
                "timestamp": datetime.now().isoformat(),
                "project_id": self.change_tracker.original_state.get("project_id", ""),
                "project_name": self.change_tracker.original_state.get("project_name", ""),
                "approved_changes": self.approved_changes,
                "rejected_changes": self.rejected_changes
            }
            
            with open(self.pending_operations_file, 'w', encoding='utf-8') as f:
                json.dump(pending_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving pending operations: {str(e)}")
            return False
    
    def load_pending_operations(self) -> bool:
        """
        Loads previously saved approved and rejected changes from a file.
        
        Returns:
            Whether the operation was successful
        """
        try:
            if os.path.exists(self.pending_operations_file):
                with open(self.pending_operations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "approved_changes" in data:
                    self.approved_changes = data["approved_changes"]
                
                if "rejected_changes" in data:
                    self.rejected_changes = data["rejected_changes"]
                
                return True
            
            return False
        except Exception as e:
            print(f"Error loading pending operations: {str(e)}")
            return False
    
    def clear_pending_operations(self) -> bool:
        """
        Clears all pending operations.
        
        Returns:
            Whether the operation was successful
        """
        try:
            self.approved_changes = {
                "created": [],
                "updated": [],
                "deleted": []
            }
            self.rejected_changes = {
                "created": [],
                "updated": [],
                "deleted": []
            }
            
            # Remove the pending operations file if it exists
            if os.path.exists(self.pending_operations_file):
                os.remove(self.pending_operations_file)
            
            return True
        except Exception as e:
            print(f"Error clearing pending operations: {str(e)}")
            return False
    
    def get_approved_operations(self) -> Dict[str, List]:
        """
        Returns all approved changes ready for sending to GitHub.
        
        Returns:
            Dictionary of approved changes
        """
        return self.approved_changes
    
    def get_rejected_operations(self) -> Dict[str, List]:
        """
        Returns all rejected changes.
        
        Returns:
            Dictionary of rejected changes
        """
        return self.rejected_changes
    
    def revert_rejected_changes(self) -> bool:
        """
        Reverts all rejected changes in the local filesystem.
        For example, restores deleted files or reverts modified files.
        
        Returns:
            Whether the operation was successful
        """
        try:
            # Revert created items (delete them)
            for item in self.rejected_changes["created"]:
                item_type = item.get("type")
                if item_type == "issue":
                    self._revert_created_issue(item)
                elif item_type == "milestone":
                    self._revert_created_milestone(item)
            
            # Revert updated items (restore original)
            for item in self.rejected_changes["updated"]:
                item_type = item.get("type")
                if item_type == "issue":
                    self._revert_updated_issue(item)
                elif item_type == "milestone":
                    self._revert_updated_milestone(item)
            
            # Revert deleted items (restore them)
            for item in self.rejected_changes["deleted"]:
                item_type = item.get("type")
                if item_type == "issue":
                    self._restore_deleted_issue(item)
                elif item_type == "milestone":
                    self._restore_deleted_milestone(item)
            
            # Clear the rejected changes after reverting
            self.rejected_changes = {
                "created": [],
                "updated": [],
                "deleted": []
            }
            
            # Save pending operations
            self.save_pending_operations()
            
            return True
        except Exception as e:
            print(f"Error reverting rejected changes: {str(e)}")
            return False
    
    def _revert_created_issue(self, item: Dict) -> bool:
        """Reverts a created issue by deleting it from the filesystem"""
        try:
            number = item.get("number")
            if not number:
                return False
            
            # Find issue file paths
            milestones_dir = os.path.join(self.project_dir, "milestones")
            for milestone_name in os.listdir(milestones_dir):
                milestone_dir = os.path.join(milestones_dir, milestone_name)
                
                if not os.path.isdir(milestone_dir):
                    continue
                
                # Check for the issue file
                issue_json = os.path.join(milestone_dir, f"issue_{number}.json")
                issue_yaml = os.path.join(milestone_dir, f"issue_{number}.yaml")
                
                if os.path.exists(issue_json):
                    os.remove(issue_json)
                
                if os.path.exists(issue_yaml):
                    os.remove(issue_yaml)
            
            return True
        except Exception as e:
            print(f"Error reverting created issue: {str(e)}")
            return False
    
    def _revert_created_milestone(self, item: Dict) -> bool:
        """Reverts a created milestone by deleting it from the filesystem"""
        try:
            title = item.get("title")
            if not title:
                return False
            
            # Convert title to safe filename
            safe_title = title.replace(" ", "_").lower().replace(":", "_").replace("/", "_")
            
            # Find milestone directory
            milestones_dir = os.path.join(self.project_dir, "milestones")
            milestone_dir = os.path.join(milestones_dir, safe_title)
            
            if os.path.exists(milestone_dir) and os.path.isdir(milestone_dir):
                # Delete all files in the milestone directory
                for filename in os.listdir(milestone_dir):
                    file_path = os.path.join(milestone_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                # Delete the milestone directory
                os.rmdir(milestone_dir)
            
            return True
        except Exception as e:
            print(f"Error reverting created milestone: {str(e)}")
            return False
    
    def _revert_updated_issue(self, item: Dict) -> bool:
        """Reverts an updated issue by restoring the original data"""
        try:
            number = item.get("number")
            original_data = item.get("original_data")
            
            if not number or not original_data:
                return False
            
            # Find issue file paths
            milestones_dir = os.path.join(self.project_dir, "milestones")
            for milestone_name in os.listdir(milestones_dir):
                milestone_dir = os.path.join(milestones_dir, milestone_name)
                
                if not os.path.isdir(milestone_dir):
                    continue
                
                # Check for the issue file
                issue_json = os.path.join(milestone_dir, f"issue_{number}.json")
                issue_yaml = os.path.join(milestone_dir, f"issue_{number}.yaml")
                
                if os.path.exists(issue_json):
                    # Restore original JSON
                    with open(issue_json, 'w', encoding='utf-8') as f:
                        json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                if os.path.exists(issue_yaml):
                    # Restore original YAML
                    with open(issue_yaml, 'w', encoding='utf-8') as f:
                        yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"Error reverting updated issue: {str(e)}")
            return False
    
    def _revert_updated_milestone(self, item: Dict) -> bool:
        """Reverts an updated milestone by restoring the original data"""
        try:
            title = item.get("title")
            original_data = item.get("original_data")
            
            if not title or not original_data:
                return False
            
            # Convert title to safe filename
            safe_title = title.replace(" ", "_").lower().replace(":", "_").replace("/", "_")
            
            # Find milestone file paths
            milestones_dir = os.path.join(self.project_dir, "milestones")
            milestone_dir = os.path.join(milestones_dir, safe_title)
            
            if os.path.exists(milestone_dir) and os.path.isdir(milestone_dir):
                # Restore original milestone files
                milestone_json = os.path.join(milestone_dir, f"{safe_title}.json")
                milestone_yaml = os.path.join(milestone_dir, f"{safe_title}.yaml")
                
                if os.path.exists(milestone_json):
                    # Restore original JSON
                    with open(milestone_json, 'w', encoding='utf-8') as f:
                        json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                if os.path.exists(milestone_yaml):
                    # Restore original YAML
                    with open(milestone_yaml, 'w', encoding='utf-8') as f:
                        yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"Error reverting updated milestone: {str(e)}")
            return False
    
    def _restore_deleted_issue(self, item: Dict) -> bool:
        """Restores a deleted issue"""
        try:
            number = item.get("number")
            original_data = item.get("data")
            
            if not number or not original_data:
                return False
            
            # Determine milestone directory
            milestone = None
            if "milestone" in original_data and original_data["milestone"]:
                milestone_title = original_data["milestone"].get("title")
                if milestone_title:
                    milestone = milestone_title.replace(" ", "_").lower().replace(":", "_").replace("/", "_")
            
            milestones_dir = os.path.join(self.project_dir, "milestones")
            
            # If we have a milestone, save to that directory
            if milestone:
                milestone_dir = os.path.join(milestones_dir, milestone)
                if not os.path.exists(milestone_dir):
                    os.makedirs(milestone_dir)
                
                issue_json = os.path.join(milestone_dir, f"issue_{number}.json")
                issue_yaml = os.path.join(milestone_dir, f"issue_{number}.yaml")
                
                # Save as JSON
                with open(issue_json, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                # Save as YAML
                with open(issue_yaml, 'w', encoding='utf-8') as f:
                    yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            else:
                # No milestone, save to no_milestone directory
                no_milestone_dir = os.path.join(milestones_dir, "no_milestone")
                if not os.path.exists(no_milestone_dir):
                    os.makedirs(no_milestone_dir)
                
                issue_json = os.path.join(no_milestone_dir, f"issue_{number}.json")
                issue_yaml = os.path.join(no_milestone_dir, f"issue_{number}.yaml")
                
                # Save as JSON
                with open(issue_json, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                # Save as YAML
                with open(issue_yaml, 'w', encoding='utf-8') as f:
                    yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"Error restoring deleted issue: {str(e)}")
            return False
    
    def _restore_deleted_milestone(self, item: Dict) -> bool:
        """Restores a deleted milestone"""
        try:
            title = item.get("title")
            original_data = item.get("data")
            
            if not title or not original_data:
                return False
            
            # Convert title to safe filename
            safe_title = title.replace(" ", "_").lower().replace(":", "_").replace("/", "_")
            
            # Create milestone directory
            milestones_dir = os.path.join(self.project_dir, "milestones")
            milestone_dir = os.path.join(milestones_dir, safe_title)
            
            if not os.path.exists(milestone_dir):
                os.makedirs(milestone_dir)
            
            # Create milestone files
            milestone_json = os.path.join(milestone_dir, f"{safe_title}.json")
            milestone_yaml = os.path.join(milestone_dir, f"{safe_title}.yaml")
            
            # Save as JSON
            with open(milestone_json, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, indent=2, ensure_ascii=False)
            
            # Save as YAML
            with open(milestone_yaml, 'w', encoding='utf-8') as f:
                yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"Error restoring deleted milestone: {str(e)}")
            return False
    
    def has_approved_changes(self) -> bool:
        """
        Checks if there are any approved changes.
        
        Returns:
            Whether there are any approved changes
        """
        for type_name in ["created", "updated", "deleted"]:
            if self.approved_changes[type_name]:
                return True
        return False
    
    def is_change_approved(self, change_type: str, index: int) -> bool:
        """
        Checks if a specific change is approved.
        
        Args:
            change_type: The type of change ("created", "updated", or "deleted")
            index: The index of the change in the list
            
        Returns:
            Whether the change is approved
        """
        change = self.get_change_by_id(change_type, index)
        return change in self.approved_changes[change_type] if change else False
    
    def is_change_rejected(self, change_type: str, index: int) -> bool:
        """
        Checks if a specific change is rejected.
        
        Args:
            change_type: The type of change ("created", "updated", or "deleted")
            index: The index of the change in the list
            
        Returns:
            Whether the change is rejected
        """
        change = self.get_change_by_id(change_type, index)
        return change in self.rejected_changes[change_type] if change else False
    
    def review_changes(self, changes: Dict = None, operation_list=None) -> List:
        """
        Lets the user review and approve/reject changes.
        
        Args:
            changes: Dictionary of detected changes
            operation_list: Optional OperationList object to collect approved changes
            
        Returns:
            List of approved changes
        """
        if not changes:
            if hasattr(self.change_tracker, 'changes') and self.change_tracker.changes:
                changes = self.change_tracker.changes
            else:
                print("Hiç değişiklik bulunamadı. Önce değişiklikleri algılayın.")
                return []
        
        if not operation_list and self.operation_list:
            operation_list = self.operation_list
        
        # Initialize list of approved changes
        approved_changes = []
        
        num_created = len(changes.get("created", []))
        num_updated = len(changes.get("updated", []))
        num_deleted = len(changes.get("deleted", []))
        total_changes = num_created + num_updated + num_deleted
        
        if total_changes == 0:
            print("İncelenecek değişiklik yok.")
            return approved_changes
        
        print(f"\n*** DEĞİŞİKLİK İNCELEME ***")
        print(f"Toplam {total_changes} değişiklik bulundu:")
        print(f"- {num_created} yeni oluşturulan öğe")
        print(f"- {num_updated} güncellenen öğe")
        print(f"- {num_deleted} silinen öğe")
        print("\nHer değişikliği tek tek inceleyebilir ve GitHub'a göndermek üzere onaylayabilirsiniz.")
        
        # Process the changes by type
        for change_type in ["created", "updated", "deleted"]:
            if not changes.get(change_type):
                continue
                
            # Get the change display format based on the type
            if change_type == "created":
                change_display = "YENİ OLUŞTURULAN"
                color = "\033[92m"  # Green
            elif change_type == "updated":
                change_display = "GÜNCELLENEN"
                color = "\033[93m"  # Yellow
            elif change_type == "deleted":
                change_display = "SİLİNEN"
                color = "\033[91m"  # Red
            
            for i, change in enumerate(changes[change_type]):
                print(f"\n{color}{change_display} ÖĞE {i+1}/{len(changes[change_type])}\033[0m")
                
                # Get change item ID and type
                item_id = change.get("id", "Bilinmeyen ID")
                item_type = change.get("type", "unknown")
                item_title = change.get("title", "Başlık yok")
                item_path = change.get("file_path", "Dosya yolu bilinmiyor")
                
                # Improve item type display
                type_display = "Bilinmeyen"
                if item_type == "milestone":
                    type_display = "Milestone"
                elif item_type == "issue":
                    item_number = change.get("number", "")
                    type_display = f"Issue #{item_number}" if item_number else "Issue"
                
                # Display change information
                print(f"Tür: {type_display}")
                print(f"Başlık: {item_title}")
                print(f"ID: {item_id}")
                
                # For milestones, show more detailed information
                if item_type == "milestone":
                    # Show the file path for reference
                    print(f"Dosya: {item_path}")
                    
                    # Try to read the file to show more details
                    try:
                        if os.path.exists(item_path):
                            with open(item_path, 'r', encoding='utf-8') as f:
                                content = json.load(f)
                                
                                # Show milestone details if available
                                if isinstance(content, dict):
                                    # Show creation date if available
                                    created_at = content.get("created_at", "")
                                    if created_at:
                                        print(f"Oluşturulma Tarihi: {created_at}")
                                        
                                    # Show creator if available
                                    creator = content.get("creator", {})
                                    if isinstance(creator, dict) and "login" in creator:
                                        print(f"Oluşturan: {creator.get('login', '')}")
                                        
                                    # Show last update date if available
                                    updated_at = content.get("updated_at", "")
                                    if updated_at:
                                        print(f"Son Güncelleme: {updated_at}")
                                        
                                    # Show state if available
                                    state = content.get("state", "")
                                    if state:
                                        print(f"Durum: {state}")
                                        
                                    # Show description if available
                                    description = content.get("description", "")
                                    if description:
                                        # Truncate long descriptions
                                        if len(description) > 200:
                                            description = description[:197] + "..."
                                        print(f"Açıklama: {description}")
                                        
                                    # Show due date if available
                                    due_on = content.get("due_on", "")
                                    if due_on:
                                        print(f"Bitiş Tarihi: {due_on}")
                    except Exception as e:
                        print(f"Milestone detayları gösterilirken hata: {str(e)}")
                
                # For issues, extract and show important details
                if item_type == "issue":
                    # Show the file path for reference
                    print(f"Dosya: {item_path}")
                    
                    # For created and updated issues, show more details
                    if change_type in ["created", "updated"] and "is_initial_sync" not in change:
                        # Check if we can show the file content
                        try:
                            if os.path.exists(item_path):
                                with open(item_path, 'r', encoding='utf-8') as f:
                                    content = json.load(f)
                                    
                                    # Show issue contents
                                    if isinstance(content, dict):
                                        # Show creation date if available
                                        created_at = content.get("created_at", "")
                                        if created_at:
                                            print(f"Oluşturulma Tarihi: {created_at}")
                                            
                                        # Show creator if available
                                        user = content.get("user", {})
                                        if isinstance(user, dict) and "login" in user:
                                            print(f"Oluşturan: {user.get('login', '')}")
                                            
                                        # Show last update date if available
                                        updated_at = content.get("updated_at", "")
                                        if updated_at:
                                            print(f"Son Güncelleme: {updated_at}")
                                            
                                        # Show priority status
                                        state = content.get("state", "")
                                        if state:
                                            print(f"Durum: {state}")
                                            
                                        # Show assigned users
                                        assignees = content.get("assignees", [])
                                        if assignees and isinstance(assignees, list) and len(assignees) > 0:
                                            print(f"Atananlar: {', '.join([a.get('login', '') for a in assignees if isinstance(a, dict) and 'login' in a])}")
                                        
                                        # Show milestone
                                        milestone = content.get("milestone", {})
                                        if isinstance(milestone, dict) and "title" in milestone:
                                            print(f"Milestone: {milestone['title']}")
                                            
                                        # Show field values (skip duplicate Title field)
                                        field_values = content.get("field_values", [])
                                        if field_values and isinstance(field_values, list):
                                            print("Alan Değerleri:")
                                            for field in field_values:
                                                if isinstance(field, dict) and "field_name" in field and "value" in field:
                                                    # Skip showing Title field since it's already shown above
                                                    if field["field_name"] != "Title":
                                                        print(f"  - {field['field_name']}: {field['value']}")
                        except Exception as e:
                            print(f"Detaylar gösterilirken hata: {str(e)}")
                
                # For deleted items, just show a warning
                if change_type == "deleted":
                    print("UYARI: Bu öğe silinmiş olarak işaretlenmiştir.")
                
                # Display field changes for updated items
                if change_type == "updated" and "changes" in change:
                    print("\nDeğişiklikler:")
                    for field_name, change_data in change["changes"].items():
                        # Skip field_values.title field since we show content.title
                        if field_name == "field_values.title":
                            continue
                            
                        old_value = change_data.get("old", "")
                        new_value = change_data.get("new", "")
                        
                        # Truncate long values
                        if old_value and isinstance(old_value, str) and len(old_value) > 100:
                            old_value = old_value[:97] + "..."
                        if new_value and isinstance(new_value, str) and len(new_value) > 100:
                            new_value = new_value[:97] + "..."
                        
                        # Format the field name for better display
                        display_field = field_name
                        if field_name == "content.title":
                            display_field = "Başlık"
                        elif field_name == "content.body":
                            display_field = "İçerik"
                        elif field_name == "state":
                            display_field = "Durum"
                        
                        print(f"  - {display_field}:")
                        print(f"    Eski: {old_value}")
                        print(f"    Yeni: {new_value}")
                
                # Get user decision on the change
                decision = None
                while decision not in ['o', 'r', 's', 't', 'q']:
                    print("\nSeçenekler:")
                    print("(o) Onayla - Bu değişikliği GitHub'a gönderilecek işlem listesine ekle")
                    print("(r) Reddet - Bu değişikliği atla ve GitHub'a gönderme")
                    print("(s) Sonraki - Şimdilik karar vermeden sonraki değişikliğe geç")
                    print("(t) Tümünü onayla - Kalan tüm değişiklikleri otomatik onayla")
                    print("(q) Çık - İncelemeyi sonlandır")
                    
                    try:
                        decision = input("Kararınız [o/r/s/t/q]: ").lower()
                    except (KeyboardInterrupt, EOFError):
                        print("\nİşlem kullanıcı tarafından sonlandırıldı.")
                        return approved_changes
                
                if decision == 'o':
                    # Add to approved changes
                    approved_changes.append(change)
                    if operation_list:
                        operation_list.add_change(change, change_type)
                    print(f"{color}✓ Değişiklik onaylandı.\033[0m")
                    
                elif decision == 'r':
                    print(f"\033[91m✗ Değişiklik reddedildi.\033[0m")
                    
                elif decision == 's':
                    print("Sonraki değişikliğe geçiliyor...")
                    
                elif decision == 't':
                    # Auto-approve all remaining changes
                    print(f"{color}✓ Kalan tüm değişiklikler otomatik onaylanacak.\033[0m")
                    
                    # Add current change
                    approved_changes.append(change)
                    if operation_list:
                        operation_list.add_change(change, change_type)
                    
                    # Add all remaining changes of this type
                    remaining_same_type = changes[change_type][i+1:]
                    for remaining_change in remaining_same_type:
                        approved_changes.append(remaining_change)
                        if operation_list:
                            operation_list.add_change(remaining_change, change_type)
                    
                    # Add all changes of other types
                    for other_type in ["created", "updated", "deleted"]:
                        if other_type == change_type:
                            continue  # Skip current type as it's already handled
                        
                        for other_change in changes.get(other_type, []):
                            approved_changes.append(other_change)
                            if operation_list:
                                operation_list.add_change(other_change, other_type)
                    
                    # Break out of loop
                    return approved_changes
                    
                elif decision == 'q':
                    print("İşlem sonlandırılıyor...")
                    return approved_changes
        
        # Show summary
        num_approved = len(approved_changes)
        if num_approved > 0:
            print(f"\n\033[92m✓ Toplam {num_approved} değişiklik onaylandı.\033[0m")
            print("Bu değişiklikleri GitHub projenize göndermek için 'GitHub'a Gönder' seçeneğini kullanın.")
        else:
            print("\n\033[93mHiçbir değişiklik onaylanmadı.\033[0m")
        
        return approved_changes 