import os
import shutil
import glob
import json
from typing import List, Dict, Any

def clean_milestone_files():
    """
    Clean up old milestone files in the project directories.
    Removes:
    - *_items.json/yaml
    - *_with_items.json/yaml
    - no_milestone_items.json/yaml
    - no_milestone_summary.json/yaml
    
    Keeps:
    - all_milestones.json/yaml
    - {milestone_id}.json/yaml
    """
    print("🧹 Cleaning up old milestone files...")
    
    # Get all project directories
    base_dir = os.path.join("data", "projects")
    if not os.path.exists(base_dir):
        print(f"❌ Directory '{base_dir}' not found")
        return
    
    project_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    for project_dir in project_dirs:
        full_project_dir = os.path.join(base_dir, project_dir)
        milestones_dir = os.path.join(full_project_dir, "milestones")
        
        if not os.path.exists(milestones_dir):
            continue
        
        print(f"\nProcessing project: {project_dir}")
        
        # Files to remove
        patterns_to_remove = [
            "*_items.json",
            "*_items.yaml",
            "*_with_items.json",
            "*_with_items.yaml",
            "no_milestone_items.json",
            "no_milestone_items.yaml",
            "no_milestone_summary.json",
            "no_milestone_summary.yaml"
        ]
        
        # Get all files that match patterns to remove
        files_to_remove = []
        for pattern in patterns_to_remove:
            files_to_remove.extend(glob.glob(os.path.join(milestones_dir, pattern)))
        
        # Remove files
        removed_count = 0
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                removed_count += 1
                print(f"  Removed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"  ❌ Failed to remove {os.path.basename(file_path)}: {str(e)}")
        
        print(f"  ✅ Removed {removed_count} old milestone files")

def test_directory_structure():
    """
    Test function to examine and display the new directory structure.
    """
    print("\n🔍 Testing new directory structure...")
    
    # Get all project directories
    base_dir = os.path.join("data", "projects")
    if not os.path.exists(base_dir):
        print(f"❌ Directory '{base_dir}' not found")
        return
    
    project_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    for project_dir in project_dirs:
        full_project_dir = os.path.join(base_dir, project_dir)
        
        print(f"\n📁 Project: {project_dir}")
        
        # Check for repository directories
        repo_dirs = [d for d in os.listdir(full_project_dir) 
                    if os.path.isdir(os.path.join(full_project_dir, d)) 
                    and d not in ["milestones", "issues", "fields", "details"]]
        
        if not repo_dirs:
            print("  ❌ No repository directories found")
            continue
        
        for repo_dir in repo_dirs:
            repo_path = os.path.join(full_project_dir, repo_dir)
            print(f"  📁 Repository: {repo_dir}")
            
            # Check for milestones directory
            milestones_dir = os.path.join(repo_path, "milestones")
            if not os.path.exists(milestones_dir):
                print("    ❌ No milestones directory found")
                continue
            
            # Get milestone directories
            milestone_dirs = [d for d in os.listdir(milestones_dir) 
                             if os.path.isdir(os.path.join(milestones_dir, d))]
            
            print(f"    📋 Found {len(milestone_dirs)} milestone directories")
            
            # Check milestone directories
            for milestone_dir in milestone_dirs:
                milestone_path = os.path.join(milestones_dir, milestone_dir)
                
                # Get issue files in the milestone directory
                issue_files = [f for f in os.listdir(milestone_path) 
                              if os.path.isfile(os.path.join(milestone_path, f)) 
                              and f.startswith("issue_") 
                              and (f.endswith(".json") or f.endswith(".yaml"))]
                
                # Count unique issues (ignoring .json/.yaml duplicates)
                unique_issues = set()
                for issue_file in issue_files:
                    # Extract issue number from filename (issue_XX.json/yaml)
                    issue_num = issue_file.split(".")[0].replace("issue_", "")
                    unique_issues.add(issue_num)
                
                print(f"    📁 Milestone: {milestone_dir} - {len(unique_issues)} issues")
                
                # Print details for no_milestone directory
                if milestone_dir == "no_milestone":
                    summary_file = os.path.join(milestone_path, "summary.json")
                    if os.path.exists(summary_file):
                        try:
                            with open(summary_file, 'r', encoding='utf-8') as f:
                                summary_data = json.load(f)
                                print(f"      🔍 Issues without milestone: {summary_data.get('count', 0)}")
                                
                                # Print sample of issues without milestone
                                if 'items' in summary_data and summary_data['items']:
                                    print("      📋 Sample issues:")
                                    for item in summary_data['items'][:5]:  # Show first 5
                                        print(f"        - {item.get('title', 'Unknown')}")
                                    
                                    if len(summary_data['items']) > 5:
                                        print(f"        - ... and {len(summary_data['items']) - 5} more")
                        except Exception as e:
                            print(f"      ❌ Error reading summary file: {str(e)}")

if __name__ == "__main__":
    # Clean up old milestone files
    clean_milestone_files()
    
    # Test and show the new directory structure
    test_directory_structure() 