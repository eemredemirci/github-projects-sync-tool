"""
Operation list module for GitHub Project Sync Tool.
This module provides classes for managing operations to be sent to GitHub.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class OperationList:
    """
    Manages a list of operations to be sent to GitHub.
    Operations are stored in a pending operations file and can be added, removed, and executed.
    """
    
    def __init__(self, project_dir: str):
        """
        Initialize the operation list.
        
        Args:
            project_dir: The project directory
        """
        self.project_dir = project_dir
        self.pending_dir = os.path.join(self.project_dir, ".pending")
        self.operations_file = os.path.join(self.pending_dir, "github_operations.json")
        
        # Ensure pending directory exists
        if not os.path.exists(self.pending_dir):
            os.makedirs(self.pending_dir)
        
        # Initialize operations list
        self.operations = []
        
        # Load existing operations
        self.load_operations()
    
    def add_operation(self, operation_type: str, item_type: str, item_id: str, 
                     data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Adds an operation to the list.
        
        Args:
            operation_type: The type of operation ("create", "update", or "delete")
            item_type: The type of item ("issue", "milestone", etc.)
            item_id: The ID of the item
            data: The data for the operation
            metadata: Additional metadata for the operation
            
        Returns:
            Whether the operation was successfully added
        """
        # Create the operation
        operation = {
            "id": f"{operation_type}_{item_type}_{item_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "item_type": item_type,
            "item_id": item_id,
            "data": data,
            "metadata": metadata or {},
            "status": "pending",
            "result": None
        }
        
        # Add to operations list
        self.operations.append(operation)
        
        # Save operations
        return self.save_operations()
    
    def add_create_issue_operation(self, repo_owner: str, repo_name: str, 
                                 title: str, body: str, milestone_id: Optional[str] = None,
                                 labels: Optional[List[str]] = None, 
                                 assignees: Optional[List[str]] = None) -> bool:
        """
        Adds an operation to create an issue.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            title: The title of the issue
            body: The body of the issue
            milestone_id: The ID of the milestone
            labels: The labels to apply
            assignees: The users to assign
            
        Returns:
            Whether the operation was successfully added
        """
        data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "title": title,
            "body": body,
            "milestone_id": milestone_id,
            "labels": labels or [],
            "assignees": assignees or []
        }
        
        return self.add_operation("create", "issue", "new", data)
    
    def add_update_issue_operation(self, repo_owner: str, repo_name: str, 
                                 issue_number: int, data: Dict[str, Any]) -> bool:
        """
        Adds an operation to update an issue.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            issue_number: The number of the issue
            data: The data to update
            
        Returns:
            Whether the operation was successfully added
        """
        operation_data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "issue_number": issue_number,
            "update_data": data
        }
        
        return self.add_operation("update", "issue", str(issue_number), operation_data)
    
    def add_delete_issue_operation(self, repo_owner: str, repo_name: str, 
                                 issue_number: int) -> bool:
        """
        Adds an operation to delete (close) an issue.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            issue_number: The number of the issue
            
        Returns:
            Whether the operation was successfully added
        """
        data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "issue_number": issue_number
        }
        
        return self.add_operation("delete", "issue", str(issue_number), data)
    
    def add_create_milestone_operation(self, repo_owner: str, repo_name: str, 
                                    title: str, description: Optional[str] = None,
                                    due_on: Optional[str] = None) -> bool:
        """
        Adds an operation to create a milestone.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            title: The title of the milestone
            description: The description of the milestone
            due_on: The due date of the milestone
            
        Returns:
            Whether the operation was successfully added
        """
        data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "title": title,
            "description": description,
            "due_on": due_on
        }
        
        return self.add_operation("create", "milestone", "new", data)
    
    def add_update_milestone_operation(self, repo_owner: str, repo_name: str, 
                                    milestone_number: int, data: Dict[str, Any]) -> bool:
        """
        Adds an operation to update a milestone.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            milestone_number: The number of the milestone
            data: The data to update
            
        Returns:
            Whether the operation was successfully added
        """
        operation_data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "milestone_number": milestone_number,
            "update_data": data
        }
        
        return self.add_operation("update", "milestone", str(milestone_number), operation_data)
    
    def add_delete_milestone_operation(self, repo_owner: str, repo_name: str, 
                                    milestone_number: int) -> bool:
        """
        Adds an operation to delete a milestone.
        
        Args:
            repo_owner: The owner of the repository
            repo_name: The name of the repository
            milestone_number: The number of the milestone
            
        Returns:
            Whether the operation was successfully added
        """
        data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "milestone_number": milestone_number
        }
        
        return self.add_operation("delete", "milestone", str(milestone_number), data)
    
    def remove_operation(self, operation_id: str) -> bool:
        """
        Removes an operation from the list.
        
        Args:
            operation_id: The ID of the operation to remove
            
        Returns:
            Whether the operation was successfully removed
        """
        # Find the operation
        for i, operation in enumerate(self.operations):
            if operation["id"] == operation_id:
                # Remove the operation
                self.operations.pop(i)
                
                # Save operations
                return self.save_operations()
        
        return False
    
    def update_operation_status(self, operation_id: str, status: str, result: Any = None) -> bool:
        """
        Updates the status of an operation.
        
        Args:
            operation_id: The ID of the operation to update
            status: The new status ("pending", "in_progress", "completed", "failed")
            result: The result of the operation
            
        Returns:
            Whether the operation was successfully updated
        """
        # Find the operation
        for operation in self.operations:
            if operation["id"] == operation_id:
                # Update the operation
                operation["status"] = status
                operation["result"] = result
                
                # Save operations
                return self.save_operations()
        
        return False
    
    def get_operations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Gets operations from the list.
        
        Args:
            status: The status of operations to get, or None for all operations
            
        Returns:
            A list of operations
        """
        if status:
            return [op for op in self.operations if op["status"] == status]
        else:
            return self.operations.copy()
    
    def get_operation_by_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets an operation by its ID.
        
        Args:
            operation_id: The ID of the operation
            
        Returns:
            The operation or None if not found
        """
        for operation in self.operations:
            if operation["id"] == operation_id:
                return operation
        
        return None
    
    def get_pending_operations_count(self) -> int:
        """
        Gets the number of pending operations.
        
        Returns:
            Number of pending operations
        """
        return len([op for op in self.operations if op["status"] == "pending"])
    
    def clear_operations(self) -> bool:
        """
        Clears all operations from the list.
        
        Returns:
            Whether the operation was successful
        """
        self.operations = []
        return self.save_operations()
    
    def save_operations(self) -> bool:
        """
        Saves operations to a file.
        
        Returns:
            Whether the operations were successfully saved
        """
        try:
            operations_data = {
                "timestamp": datetime.now().isoformat(),
                "operations": self.operations
            }
            
            with open(self.operations_file, 'w', encoding='utf-8') as f:
                json.dump(operations_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving operations: {str(e)}")
            return False
    
    def load_operations(self) -> bool:
        """
        Loads operations from a file.
        
        Returns:
            Whether the operations were successfully loaded
        """
        try:
            if os.path.exists(self.operations_file):
                with open(self.operations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "operations" in data and isinstance(data["operations"], list):
                    self.operations = data["operations"]
                    return True
            
            # File doesn't exist or is invalid
            self.operations = []
            return False
        except Exception as e:
            print(f"Error loading operations: {str(e)}")
            self.operations = []
            return False
    
    def group_operations_by_type(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Groups operations by type and item type.
        
        Returns:
            Dictionary of operations grouped by type and item type
        """
        result = {
            "create": {"issue": [], "milestone": []},
            "update": {"issue": [], "milestone": []},
            "delete": {"issue": [], "milestone": []}
        }
        
        for operation in self.operations:
            op_type = operation["operation_type"]
            item_type = operation["item_type"]
            
            if op_type in result and item_type in result[op_type]:
                result[op_type][item_type].append(operation)
        
        return result 