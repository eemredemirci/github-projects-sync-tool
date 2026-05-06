"""
GitHub synchronizer module for GitHub Project Sync Tool.
This module provides classes for synchronizing local changes with GitHub.
"""
import os
import json
import shutil
import requests
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from app.utils.operation_list import OperationList
from app.services.github_service import GitHubService

class GitHubSynchronizer:
    """
    Synchronizes local changes with GitHub.
    Executes operations on GitHub based on the operation list.
    """
    
    def __init__(self, project_dir: str, github_service: GitHubService):
        """
        Initialize the GitHub synchronizer.
        
        Args:
            project_dir: The project directory
            github_service: The GitHub service
        """
        self.project_dir = project_dir
        self.github_service = github_service
        self.operation_list = OperationList(project_dir)
        
        # Paths for history and logs
        self.sync_history_dir = os.path.join(self.project_dir, "sync_history")
        self.logs_dir = os.path.join(self.project_dir, "logs")
        
        # Ensure directories exist
        for directory in [self.sync_history_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Setup logging
        self.log_dir = os.path.join(self.project_dir, "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.log_file = os.path.join(self.log_dir, f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.logger = self._setup_logger()
        
        # Current sync results
        self.current_sync_results = {
            "timestamp": datetime.now().isoformat(),
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operations": []
        }
    
    def _setup_logger(self) -> logging.Logger:
        """
        Sets up logging.
        
        Returns:
            Logger instance
        """
        logger = logging.getLogger("github_synchronizer")
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _remove_duplicate_title_fields(self, issue_data: Dict) -> Dict:
        """
        Remove duplicate title fields from field_values to prevent display issues.
        
        Args:
            issue_data: Issue data dictionary
            
        Returns:
            Dict: Updated issue data with Title field removed from field_values
        """
        if not isinstance(issue_data, dict):
            return issue_data
            
        # If field_values exists and is a list
        if "field_values" in issue_data and isinstance(issue_data["field_values"], list):
            # Filter out any field with field_name "Title"
            issue_data["field_values"] = [
                field for field in issue_data["field_values"] 
                if not (isinstance(field, dict) and field.get("field_name") == "Title")
            ]
            
        return issue_data
    
    def _normalize_milestone_value(self, value: str) -> str:
        """Normalize a milestone value to use as a filesystem-friendly name."""
        if not value:
            return "unknown"
        
        # Replace invalid characters
        safe_value = value.replace('/', '_').replace('\\', '_')
        
        # Truncate if too long
        if len(safe_value) > 100:
            safe_value = safe_value[:97] + "..."
            
        return safe_value
    
    def execute_operations(self, operations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute operations on GitHub.
        This method will create, update, or delete items on GitHub based on the provided list of operations.
        
        Args:
            operations: List of operations to execute, each being a dictionary with operation details
                If None, will use all operations from the operation list
                
        Returns:
            Dictionary with results of operations execution
        """
        if operations is None:
            # Get all operations from the operation list
            operations = self.operation_list.get_all_operations()
        
        if not operations:
            self.logger.info("No operations to execute.")
            return {"success": False, "message": "No operations to execute.", "results": []}
        
        self.logger.info(f"Executing {len(operations)} operations on GitHub...")
        
        # Initialize results
        results = []
        success_count = 0
        
        # Start timing
        start_time = datetime.now()
        
        # Execute operations
        for operation in operations:
            operation_id = operation.get("id", "unknown")
            operation_type = operation.get("type", "unknown")
            operation_action = operation.get("action", "unknown")
            
            self.logger.info(f"Executing operation {operation_id}: {operation_action} {operation_type}")
            
            # Execute operation
            success, result = self._execute_operation(operation)
            
            # Record result
            operation_result = {
                "id": operation_id,
                "type": operation_type,
                "action": operation_action,
                "success": success,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(operation_result)
            
            if success:
                success_count += 1
                self.logger.info(f"Operation {operation_id} executed successfully.")
            else:
                self.logger.error(f"Operation {operation_id} failed: {result}")
        
        # End timing
        end_time = datetime.now()
        
        # Save sync history
        self._save_sync_history(operations, results, start_time, end_time)
        
        # Return results
        return {
            "success": success_count > 0,
            "message": f"{success_count}/{len(operations)} operations executed successfully.",
            "results": results
        }
    
    def _execute_operation(self, operation: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Execute a single operation on GitHub.
        
        Args:
            operation: Dictionary with operation details
            
        Returns:
            Tuple with success status and result details
        """
        if not operation:
            return False, "Operation is empty."
        
        operation_type = operation.get("type", "")
        operation_action = operation.get("action", "")
        
        # Process issue operations
        if operation_type == "issue":
            if operation_action == "create":
                return self._create_issue(operation)
            elif operation_action == "update":
                return self._update_issue(operation)
            elif operation_action == "delete":
                return self._delete_issue(operation)
                
        # Process milestone operations
        elif operation_type == "milestone":
            if operation_action == "create":
                return self._create_milestone(operation)
            elif operation_action == "update":
                return self._update_milestone(operation)
            elif operation_action == "delete":
                return self._delete_milestone(operation)
        
        return False, f"Unsupported operation: {operation_type} - {operation_action}"
    
    def _create_issue(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Create an issue on GitHub.
        
        Args:
            data: Dictionary with issue data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Prepare issue data
            issue_data = data.get("data", {})
            
            # Remove duplicate title fields
            issue_data = self._remove_duplicate_title_fields(issue_data)
            
            # Create issue with the GitHub service
            result = self.github_service.create_issue(issue_data)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error creating issue")
            return False, str(e)
    
    def _update_issue(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Update an issue on GitHub.
        
        Args:
            data: Dictionary with issue data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Prepare issue data
            issue_data = data.get("data", {})
            issue_id = data.get("id", "")
            
            # Remove duplicate title fields
            issue_data = self._remove_duplicate_title_fields(issue_data)
            
            # Update issue with the GitHub service
            result = self.github_service.update_issue(issue_id, issue_data)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error updating issue")
            return False, str(e)
    
    def _delete_issue(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Delete an issue on GitHub.
        
        Args:
            data: Dictionary with issue data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Get issue ID
            issue_id = data.get("id", "")
            
            # Delete issue with the GitHub service
            result = self.github_service.delete_issue(issue_id)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error deleting issue")
            return False, str(e)
    
    def _create_milestone(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Create a milestone on GitHub.
        
        Args:
            data: Dictionary with milestone data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Prepare milestone data
            milestone_data = data.get("data", {})
            
            # Create milestone with the GitHub service
            result = self.github_service.create_milestone(milestone_data)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error creating milestone")
            return False, str(e)
    
    def _update_milestone(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Update a milestone on GitHub.
        
        Args:
            data: Dictionary with milestone data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Prepare milestone data
            milestone_data = data.get("data", {})
            milestone_id = data.get("id", "")
            
            # Update milestone with the GitHub service
            result = self.github_service.update_milestone(milestone_id, milestone_data)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error updating milestone")
            return False, str(e)
    
    def _delete_milestone(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Delete a milestone on GitHub.
        
        Args:
            data: Dictionary with milestone data
            
        Returns:
            Tuple with success status and result details
        """
        try:
            # Get milestone ID
            milestone_id = data.get("id", "")
            
            # Delete milestone with the GitHub service
            result = self.github_service.delete_milestone(milestone_id)
            
            if not result or "error" in result:
                error_message = result.get("error", "Unknown error") if result else "No result from GitHub"
                return False, error_message
            
            return True, result
        except Exception as e:
            self.logger.exception("Error deleting milestone")
            return False, str(e)
    
    def _save_sync_results(self) -> bool:
        """
        Save the current sync results to a file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sync_results_{timestamp}.json"
            filepath = os.path.join(self.sync_history_dir, filename)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_sync_results, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.exception("Error saving sync results")
            return False
    
    def get_sync_history(self) -> List[Dict[str, Any]]:
        """
        Get the sync history from the sync history directory.
        
        Returns:
            List of dictionaries with sync history information
        """
        history = []
        
        if not os.path.exists(self.sync_history_dir):
            return history
        
        # Get all JSON files in the sync history directory
        files = [f for f in os.listdir(self.sync_history_dir) if f.endswith('.json')]
        
        for file in files:
            try:
                filepath = os.path.join(self.sync_history_dir, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract basic info
                history.append({
                    "filename": file,
                    "timestamp": data.get("timestamp", ""),
                    "total_operations": data.get("total_operations", 0),
                    "successful_operations": data.get("successful_operations", 0),
                    "failed_operations": data.get("failed_operations", 0)
                })
            except Exception as e:
                self.logger.exception(f"Error reading sync history file: {file}")
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return history
    
    def get_sync_details(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get the details of a specific sync operation.
        
        Args:
            filename: The name of the sync results file
            
        Returns:
            Dictionary with sync details or None if not found
        """
        if not filename:
            return None
        
        filepath = os.path.join(self.sync_history_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.exception(f"Error reading sync details file: {filename}")
            return None
    
    def generate_sync_report(self, sync_results: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a human-readable report of sync results.
        
        Args:
            sync_results: Dictionary with sync results, if None will use current results
            
        Returns:
            String with sync report
        """
        if sync_results is None:
            sync_results = self.current_sync_results
        
        if not sync_results:
            return "No sync results available."
        
        # Basic info
        timestamp = sync_results.get("timestamp", "")
        total_ops = sync_results.get("total_operations", 0)
        success_ops = sync_results.get("successful_operations", 0)
        failed_ops = sync_results.get("failed_operations", 0)
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_timestamp = timestamp
        
        # Build report
        report = [
            "GitHub Sync Report",
            "=================",
            f"Timestamp: {formatted_timestamp}",
            f"Total Operations: {total_ops}",
            f"Successful: {success_ops}",
            f"Failed: {failed_ops}",
            ""
        ]
        
        # Add operation details
        if "operations" in sync_results and sync_results["operations"]:
            report.append("Operation Details:")
            report.append("------------------")
            
            for i, op in enumerate(sync_results["operations"], 1):
                op_id = op.get("id", "unknown")
                op_type = op.get("type", "unknown")
                op_action = op.get("action", "unknown")
                op_success = op.get("success", False)
                op_result = op.get("result", "")
                
                status = "✓ Success" if op_success else "✗ Failed"
                
                report.append(f"{i}. {op_action.capitalize()} {op_type} ({op_id}): {status}")
                
                if not op_success and op_result:
                    report.append(f"   Error: {op_result}")
                
                report.append("")
        
        return "\n".join(report)
    
    def get_pending_operations_count(self) -> int:
        """
        Get the count of pending operations.
        
        Returns:
            Number of pending operations
        """
        if not self.operation_list:
            return 0
        
        return self.operation_list.get_operation_count()
    
    def clear_completed_operations(self) -> bool:
        """
        Clear all completed operations from the operation list.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.operation_list:
            return False
        
        return self.operation_list.clear_completed_operations()
    
    def _save_sync_history(self, operations: List[Dict[str, Any]], results: List[Dict[str, Any]], 
                          start_time: datetime, end_time: datetime):
        """
        Save sync history to a file.
        
        Args:
            operations: List of operations executed
            results: List of operation results
            start_time: Start time of sync
            end_time: End time of sync
        """
        try:
            # Calculate stats
            total_ops = len(operations)
            success_ops = sum(1 for r in results if r.get("success", False))
            failed_ops = total_ops - success_ops
            
            # Create sync results object
            sync_results = {
                "timestamp": datetime.now().isoformat(),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "total_operations": total_ops,
                "successful_operations": success_ops,
                "failed_operations": failed_ops,
                "operations": results
            }
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sync_results_{timestamp}.json"
            filepath = os.path.join(self.sync_history_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sync_results, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Sync history saved to: {filepath}")
            
            # Update current sync results
            self.current_sync_results = sync_results
            
        except Exception as e:
            self.logger.exception("Error saving sync history") 