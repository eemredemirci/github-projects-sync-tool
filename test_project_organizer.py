#!/usr/bin/env python
"""
Test script for ProjectOrganizer functionality.
This script tests the new structured data organization system.
"""
import os
import sys
import json
import yaml
import shutil
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.project_organizer import ProjectOrganizer


def test_project_organizer():
    """Test ProjectOrganizer functionality"""
    print("Starting ProjectOrganizer test...")
    
    # Create a test directory
    test_dir = os.path.join("data", "test_project")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create some mock data files including date-stamped versions
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create mock project.json
    mock_project = {
        "id": "TEST_PROJECT",
        "name": "Test Project",
        "number": 1,
        "state": "open",
        "description": "Test project for organizing data",
        "fields": [
            {"id": "FIELD1", "name": "Status", "type": "SINGLE_SELECT"},
            {"id": "FIELD2", "name": "Priority", "type": "SINGLE_SELECT"}
        ],
        "items": [
            {
                "id": "ITEM1",
                "content": {
                    "title": "Test Issue 1",
                    "number": 1,
                    "state": "OPEN"
                },
                "milestone": {
                    "title": "Sprint 1",
                    "due_on": "2025-03-16T00:00:00Z",
                    "state": "OPEN"
                }
            },
            {
                "id": "ITEM2",
                "content": {
                    "title": "Test Issue 2",
                    "number": 2,
                    "state": "CLOSED"
                },
                "milestone": {
                    "title": "Sprint 1",
                    "due_on": "2025-03-16T00:00:00Z",
                    "state": "OPEN"
                }
            }
        ]
    }
    
    # Write mock project data
    with open(os.path.join(test_dir, f"project_{current_date}.json"), "w") as f:
        json.dump(mock_project, f, indent=2)
    
    with open(os.path.join(test_dir, f"project_{current_date}.yaml"), "w") as f:
        yaml.dump(mock_project, f, default_flow_style=False)
    
    # Create main files
    with open(os.path.join(test_dir, "project.json"), "w") as f:
        json.dump(mock_project, f, indent=2)
    
    with open(os.path.join(test_dir, "project.yaml"), "w") as f:
        yaml.dump(mock_project, f, default_flow_style=False)
    
    # Test ProjectOrganizer
    print("Initializing ProjectOrganizer...")
    organizer = ProjectOrganizer(test_dir)
    
    print("Organizing project data...")
    success = organizer.organize(mock_project)
    if success:
        print("Successfully organized project data")
    else:
        print("Failed to organize project data")
        return
    
    # Verify the structure
    verify_structure(test_dir)
    
    # Test cleanup
    print("Cleaning up old versions...")
    removed_count = organizer.cleanup_old_versions()
    print(f"Removed {removed_count} old version files")
    
    # Verify the cleanup
    if os.path.exists(os.path.join(test_dir, f"project_{current_date}.json")):
        print("ERROR: Date-stamped JSON file still exists")
    else:
        print("Date-stamped JSON file successfully removed")
    
    if os.path.exists(os.path.join(test_dir, f"project_{current_date}.yaml")):
        print("ERROR: Date-stamped YAML file still exists")
    else:
        print("Date-stamped YAML file successfully removed")
    
    print("Test completed successfully!")


def verify_structure(test_dir):
    """Verify the directory structure created by ProjectOrganizer"""
    # Check main project files
    if not os.path.exists(os.path.join(test_dir, "project.json")):
        print("ERROR: project.json does not exist")
        return
    
    if not os.path.exists(os.path.join(test_dir, "project.yaml")):
        print("ERROR: project.yaml does not exist")
        return
    
    # Check subdirectories
    subdirs = ["details", "fields", "issues", "milestones"]
    for subdir in subdirs:
        if not os.path.exists(os.path.join(test_dir, subdir)):
            print(f"ERROR: {subdir} directory does not exist")
            return
        else:
            print(f"Found {subdir} directory")
    
    # Check details
    if not os.path.exists(os.path.join(test_dir, "details", "project_info.json")):
        print("ERROR: project_info.json does not exist")
    else:
        print("Found project_info.json")
    
    if not os.path.exists(os.path.join(test_dir, "details", "project_info.yaml")):
        print("ERROR: project_info.yaml does not exist")
    else:
        print("Found project_info.yaml")
    
    # Check fields
    if not os.path.exists(os.path.join(test_dir, "fields", "all_fields.json")):
        print("ERROR: all_fields.json does not exist")
    else:
        print("Found all_fields.json")
    
    # Check issues
    if not os.path.exists(os.path.join(test_dir, "issues", "all_issues.json")):
        print("ERROR: all_issues.json does not exist")
    else:
        print("Found all_issues.json")
    
    # Check milestones
    if not os.path.exists(os.path.join(test_dir, "milestones", "all_milestones.json")):
        print("ERROR: all_milestones.json does not exist")
    else:
        print("Found all_milestones.json")


if __name__ == "__main__":
    test_project_organizer() 