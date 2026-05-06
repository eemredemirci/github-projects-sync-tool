#!/usr/bin/env python
"""
Test script for milestone organization functionality.
"""
import os
import sys
import json
import yaml
from pprint import pprint
from typing import Dict, Any, List, Optional

# Add the app directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.project_organizer import ProjectOrganizer

def test_directory_structure():
    """
    Test function to examine and display the new directory structure.
    """
    print("\n🔍 Testing new directory structure...\n")
    
    # Doğrudan proje dizinini belirtelim
    base_dir = os.path.join("data", "projects")
    if not os.path.exists(base_dir):
        print(f"❌ Directory '{base_dir}' not found")
        return
    
    # Mevcut projeleri kontrol et
    project_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    if not project_dirs:
        print("❌ No project directories found!")
        return
    
    print(f"Mevcut projeler: {', '.join(project_dirs)}")
    
    # Doğrudan proje ID'sini kullanalım
    project_dir = "PVT_kwHOAQtKyM4AyQUb_Modern_E-Commerce_Development"
    full_project_dir = os.path.join(base_dir, project_dir)
    
    if not os.path.exists(full_project_dir):
        print(f"❌ Project with ID {project_dir} not found")
        return
    
    print(f"\n📁 Project: {project_dir}")
    
    # Check for repository directories
    repo_dirs = [d for d in os.listdir(full_project_dir) 
                if os.path.isdir(os.path.join(full_project_dir, d)) 
                and d not in ["milestones", "issues", "fields", "details"]]
    
    if not repo_dirs:
        print("  ❌ No repository directories found")
        return
    
    for repo_dir in repo_dirs:
        repo_path = os.path.join(full_project_dir, repo_dir)
        print(f"\n  📁 Repository: {repo_dir}")
        
        # Check for milestones directory
        milestones_dir = os.path.join(repo_path, "milestones")
        if not os.path.exists(milestones_dir):
            print("    ❌ No milestones directory found")
            continue
        
        # Get milestone directories
        milestone_dirs = [d for d in os.listdir(milestones_dir) 
                         if os.path.isdir(os.path.join(milestones_dir, d))]
        
        print(f"\n    📋 Found {len(milestone_dirs)} milestone directories")
        
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
            
            print(f"\n    📁 Milestone: {milestone_dir} - {len(unique_issues)} issues")
            
            # Get sample issues
            sample_issues = []
            for issue_num in list(unique_issues)[:3]:  # Get first 3 unique issue numbers
                issue_file = os.path.join(milestone_path, f"issue_{issue_num}.json")
                if os.path.exists(issue_file):
                    try:
                        with open(issue_file, 'r', encoding='utf-8') as f:
                            issue_data = json.load(f)
                            title = issue_data.get("content", {}).get("title", "Unknown")
                            state = issue_data.get("content", {}).get("state", "Unknown")
                            # Check parent_issue
                            parent_issue = issue_data.get("parent_issue", None)
                            parent_info = f", Parent: {parent_issue['title']}" if parent_issue else ", No Parent"
                            sample_issues.append(f"#{issue_num} - {title} ({state}{parent_info})")
                    except Exception as e:
                        sample_issues.append(f"#{issue_num} - Error: {str(e)}")
            
            # Print sample issues
            if sample_issues:
                print("      Sample issues:")
                for sample in sample_issues:
                    print(f"        - {sample}")
                
                if len(unique_issues) > 3:
                    print(f"        - ... and {len(unique_issues) - 3} more")
            
            # Print details for no_milestone directory
            if milestone_dir == "no_milestone":
                summary_file = os.path.join(milestone_path, "summary.json")
                if os.path.exists(summary_file):
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)
                            print(f"\n      🔍 Issues without milestone: {summary_data.get('count', 0)}")
                            
                            # Print sample of issues without milestone
                            if 'items' in summary_data and summary_data['items']:
                                print("      📋 Sample issues without milestone:")
                                for item in summary_data['items'][:5]:  # Show first 5
                                    print(f"        - #{item.get('number', '?')} - {item.get('title', 'Unknown')}")
                                
                                if len(summary_data['items']) > 5:
                                    print(f"        - ... and {len(summary_data['items']) - 5} more")
                    except Exception as e:
                        print(f"      ❌ Error reading summary file: {str(e)}")
    
    print("\n✅ Directory structure test completed!")

if __name__ == "__main__":
    test_directory_structure() 