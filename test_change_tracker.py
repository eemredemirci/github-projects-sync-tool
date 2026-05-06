import os
import json
import shutil
import unittest
import tempfile
import time
from app.utils.change_tracker import ChangeTracker

class TestChangeTracker(unittest.TestCase):
    """Test ChangeTracker class functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Create project structure
        self.milestones_dir = os.path.join(self.test_dir, "milestones")
        self.cache_dir = os.path.join(self.test_dir, ".cache")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        self.sync_history_dir = os.path.join(self.test_dir, "sync_history")
        self.pending_dir = os.path.join(self.test_dir, ".pending")
        
        # Create required directories
        for directory in [self.milestones_dir, self.cache_dir, 
                          self.logs_dir, self.sync_history_dir, 
                          self.pending_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Create project.json
        self.project_data = {
            "id": "test_project_id",
            "name": "Test Project",
            "items": [
                {
                    "id": "issue_1_id",
                    "content": {
                        "title": "Issue 1 Title",
                        "number": 1,
                        "state": "OPEN"
                    },
                    "milestone": {
                        "id": "milestone_1_id",
                        "title": "Sprint 1: Test Milestone",
                        "state": "OPEN",
                        "due_on": "2023-12-31T00:00:00Z"
                    }
                }
            ]
        }
        
        with open(os.path.join(self.test_dir, "project.json"), "w") as f:
            json.dump(self.project_data, f)
        
        with open(os.path.join(self.test_dir, "project.yaml"), "w") as f:
            f.write("name: Test Project")
        
        # Create milestone directory and issue file
        self.milestone_dir = os.path.join(self.milestones_dir, "sprint_1__test_milestone")
        os.makedirs(self.milestone_dir, exist_ok=True)
        
        # Create milestone file
        milestone_data = {
            "id": "milestone_1_id",
            "title": "Sprint 1: Test Milestone",
            "state": "OPEN",
            "due_on": "2023-12-31T00:00:00Z"
        }
        with open(os.path.join(self.milestone_dir, "sprint_1__test_milestone.json"), "w") as f:
            json.dump(milestone_data, f)
        
        # Create issue file
        issue_data = {
            "id": "issue_1_id",
            "content": {
                "title": "Issue 1 Title",
                "number": 1,
                "state": "OPEN"
            },
            "milestone": milestone_data
        }
        with open(os.path.join(self.milestone_dir, "issue_1.json"), "w") as f:
            json.dump(issue_data, f)
            
        # Initialize ChangeTracker
        self.tracker = ChangeTracker(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_initial_capture(self):
        """Test initial state capture."""
        # Capture original state
        result = self.tracker.capture_original_state(self.project_data)
        self.assertTrue(result, "Failed to capture original state")
        
        # Verify original state file exists
        self.assertTrue(os.path.exists(os.path.join(self.cache_dir, "original_state.json")))
        
        # Load the original state
        with open(os.path.join(self.cache_dir, "original_state.json"), "r") as f:
            state = json.load(f)
        
        # Verify milestone and issue are captured
        self.assertIn("issue_1", state["items"], "Issue 1 not found in items")
        milestone_key = "milestone_sprint_1__test_milestone"
        self.assertIn(milestone_key, state["items"], f"Milestone '{milestone_key}' not found in items: {list(state['items'].keys())}")
    
    def test_change_detection(self):
        """Test change detection."""
        # Capture original state
        self.tracker.capture_original_state(self.project_data)
        
        # Print original state for debugging
        print("Original State:")
        with open(os.path.join(self.cache_dir, "original_state.json"), "r") as f:
            original_state = json.load(f)
            print(json.dumps(original_state, indent=2))
        
        # Modify issue file
        with open(os.path.join(self.milestone_dir, "issue_1.json"), "r") as f:
            issue_data = json.load(f)
        
        # Change the title in the content section
        issue_data["content"]["title"] = "Modified Issue Title"
        
        # Save the modified issue back
        with open(os.path.join(self.milestone_dir, "issue_1.json"), "w") as f:
            json.dump(issue_data, f)
        
        # Scan current state
        self.tracker.scan_current_state()
        
        # Print current state for debugging
        print("\nCurrent State:")
        print(json.dumps(self.tracker.current_state, indent=2))
        
        # Detect changes
        changes = self.tracker.detect_changes()
        
        # Print detected changes for debugging
        print("\nDetected Changes:")
        print(json.dumps(changes, indent=2))
        
        # Verify changes
        self.assertEqual(len(changes["updated"]), 1, "Failed to detect one updated item")
        self.assertEqual(len(changes["created"]), 0, "Incorrectly detected created items")
        self.assertEqual(len(changes["deleted"]), 0, "Incorrectly detected deleted items")
        
        # Verify the change details
        updated_item = changes["updated"][0]
        self.assertEqual(updated_item["type"], "issue")
        self.assertEqual(updated_item["number"], 1)
        
        # Check if field changes are properly detected
        self.assertIn("field_changes", updated_item)
        found_title_change = False
        for change in updated_item["field_changes"]:
            if change["field"] == "title":
                found_title_change = True
                self.assertEqual(change["new_value"], "Modified Issue Title")
        self.assertTrue(found_title_change, "Failed to detect title change")
    
    def test_milestone_change_detection(self):
        """Test milestone change detection does not report false positives."""
        # Capture original state
        self.tracker.capture_original_state(self.project_data)
        
        # Don't modify anything
        
        # Scan current state
        self.tracker.scan_current_state()
        
        # Detect changes
        changes = self.tracker.detect_changes()
        
        # Verify no changes should be detected
        self.assertEqual(len(changes["updated"]), 0, "Incorrectly detected updated items")
        self.assertEqual(len(changes["created"]), 0, "Incorrectly detected created items")
        self.assertEqual(len(changes["deleted"]), 0, "Incorrectly detected deleted items")

if __name__ == "__main__":
    unittest.main() 