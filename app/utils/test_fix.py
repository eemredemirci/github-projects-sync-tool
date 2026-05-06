#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the ChangeTracker fix.
This will load project data, analyze it, and try to capture state.
"""

import os
import sys
import json
import pprint
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.utils.change_tracker import ChangeTracker

def analyze_structure(data, prefix="", max_depth=3, current_depth=0):
    """Recursively analyze and print out structure of data"""
    if current_depth >= max_depth:
        return
    
    if isinstance(data, dict):
        for key, value in list(data.items())[:10]:  # Limit to first 10 keys
            value_type = type(value).__name__
            if isinstance(value, (dict, list)):
                size = len(value)
                print(f"{prefix}{key} ({value_type}, {size} items)")
                analyze_structure(value, prefix + "  ", max_depth, current_depth + 1)
            else:
                value_repr = repr(value)
                if len(value_repr) > 50:
                    value_repr = value_repr[:47] + "..."
                print(f"{prefix}{key}: {value_repr} ({value_type})")
    
    elif isinstance(data, list) and len(data) > 0:
        print(f"{prefix}Liste ({len(data)} öğe):")
        if len(data) > 0:
            # Show first item structure
            first_item = data[0]
            print(f"{prefix}  İlk öğe ({type(first_item).__name__}):")
            analyze_structure(first_item, prefix + "    ", max_depth, current_depth + 1)
            
            # Show if there are different types in the list
            types = {type(item).__name__ for item in data[:10]}
            if len(types) > 1:
                print(f"{prefix}  Listedeki diğer türler: {types}")

def main():
    """Test the ChangeTracker fixed functionality"""
    
    # Define project path
    project_dir = "./data/projects/PVT_kwHOAQtKyM4AyQUb_Modern_E-Commerce_Development"
    
    # Check if project exists
    if not os.path.exists(project_dir):
        print(f"Proje dizini bulunamadı: {project_dir}")
        return
    
    print(f"Proje dizini bulundu: {project_dir}")
    
    # Project JSON path
    project_json = os.path.join(project_dir, "project.json")
    
    # Check if project JSON exists
    if not os.path.exists(project_json):
        print(f"Proje JSON dosyası bulunamadı: {project_json}")
        return
    
    print(f"Proje JSON dosyası bulundu: {project_json}")
    
    # Load project data
    try:
        with open(project_json, "r", encoding="utf-8") as f:
            project_data = json.load(f)
    except Exception as e:
        print(f"Proje JSON dosyası okunamadı: {e}")
        return
    
    # Analyze project data
    print("\nProje verileri analizi:")
    print(f"Veri türü: {type(project_data)}")
    
    print("\nProje veri yapısı detaylı analizi:")
    analyze_structure(project_data)
    
    # "items" alanı var ise, daha detaylı analiz yapalım
    if isinstance(project_data, dict) and "items" in project_data:
        items = project_data["items"]
        print(f"\n'items' alanının türü: {type(items)}")
        
        if isinstance(items, list):
            print(f"Liste uzunluğu: {len(items)}")
            if len(items) > 0:
                print("İlk öğe örneği:")
                pprint.pprint(items[0])
        elif isinstance(items, dict):
            print(f"Sözlük anahtar sayısı: {len(items)}")
            if len(items) > 0:
                print("İlk anahtar-değer örneği:")
                first_key = list(items.keys())[0]
                print(f"Anahtar: {first_key}")
                pprint.pprint(items[first_key])
    
    print("\n-------------------------------------------------------------------")
    
    # DEMO: İşlenmiş Veri Oluştur
    print("\nİşlenmiş veri oluşturuluyor...")
    
    # Milestones ve issues için yeni formatta veri oluştur
    processed_data = {}
    
    # Eğer items dict ise, listlenmiş öğeler
    if isinstance(project_data, dict) and "items" in project_data:
        items = project_data["items"]
        if isinstance(items, dict):
            # İşle ve ekle
            for item_id, item in items.items():
                if isinstance(item, dict):
                    if "type" in item and item["type"] == "milestone":
                        # Milestone işle
                        processed_data[item_id] = {
                            "id": item.get("id", ""),
                            "type": "milestone",
                            "title": item.get("title", ""),
                            "state": item.get("state", "OPEN"),
                            "description": item.get("description", ""),
                            "due_on": item.get("due_on")
                        }
                    elif "type" in item and item["type"] == "issue" or "content" in item:
                        # Issue işle
                        issue_number = 0
                        if "content" in item and isinstance(item["content"], dict):
                            issue_number = item["content"].get("number", 0)
                        
                        if issue_number:
                            processed_data[f"issue_{issue_number}"] = {
                                "id": item.get("id", ""),
                                "type": "issue",
                                "number": issue_number,
                                "content": item.get("content", {}),
                                "milestone": item.get("milestone"),
                                "parent_issue": item.get("parent_issue"),
                                "field_values": item.get("field_values", [])
                            }
        elif isinstance(items, list):
            # Liste öğelerini işle
            for idx, item in enumerate(items):
                if isinstance(item, dict):
                    # Milestone kontrolü
                    if "type" in item and item["type"] == "milestone":
                        title = item.get("title", "")
                        if title:
                            milestone_id = f"milestone_{idx}"
                            processed_data[milestone_id] = {
                                "id": item.get("id", ""),
                                "type": "milestone",
                                "title": title,
                                "state": item.get("state", "OPEN"),
                                "description": item.get("description", ""),
                                "due_on": item.get("due_on")
                            }
                    # Issue kontrolü
                    elif "content" in item and isinstance(item["content"], dict):
                        issue_number = item["content"].get("number", 0)
                        if issue_number:
                            processed_data[f"issue_{issue_number}"] = {
                                "id": item.get("id", ""),
                                "type": "issue",
                                "number": issue_number,
                                "content": item.get("content", {}),
                                "milestone": item.get("milestone"),
                                "parent_issue": item.get("parent_issue"),
                                "field_values": item.get("field_values", [])
                            }
    
    # Ana proje alanlarında öğeleri doğrudan ara
    if len(processed_data) == 0:
        # Milestone'ları ara
        if "milestones" in project_data and isinstance(project_data["milestones"], list):
            for idx, milestone in enumerate(project_data["milestones"]):
                if isinstance(milestone, dict):
                    title = milestone.get("title", "")
                    if title:
                        milestone_id = f"milestone_{idx}"
                        processed_data[milestone_id] = {
                            "id": milestone.get("id", ""),
                            "type": "milestone",
                            "title": title,
                            "state": milestone.get("state", "OPEN"),
                            "description": milestone.get("description", ""),
                            "due_on": milestone.get("due_on")
                        }
        
        # Issue'ları ara
        for issue_source in ["issues", "pull_requests"]:
            if issue_source in project_data and isinstance(project_data[issue_source], list):
                for item in project_data[issue_source]:
                    if isinstance(item, dict) and "content" in item and isinstance(item["content"], dict):
                        issue_number = item["content"].get("number", 0)
                        if issue_number:
                            processed_data[f"issue_{issue_number}"] = {
                                "id": item.get("id", ""),
                                "type": "issue",
                                "number": issue_number,
                                "content": item.get("content", {}),
                                "milestone": item.get("milestone"),
                                "parent_issue": item.get("parent_issue"),
                                "field_values": item.get("field_values", [])
                            }
    
    print(f"İşlenmiş veri oluşturuldu, toplam öğe sayısı: {len(processed_data)}")
    print(f"Milestone: {sum(1 for k in processed_data if k.startswith('milestone_'))}")
    print(f"Issue: {sum(1 for k in processed_data if k.startswith('issue_'))}")
    
    # İşlenmiş veriyi yazdır
    if len(processed_data) > 0:
        print("\nİşlenmiş veri örnekleri:")
        # İlk milestone örneği
        for k in processed_data:
            if k.startswith("milestone_"):
                print(f"\nMilestone örneği: {k}")
                pprint.pprint(processed_data[k])
                break
        
        # İlk issue örneği
        for k in processed_data:
            if k.startswith("issue_"):
                print(f"\nIssue örneği: {k}")
                # Sadece bazı alanları göster
                issue = processed_data[k]
                print(f"Number: {issue.get('number')}")
                if "content" in issue and isinstance(issue["content"], dict):
                    print(f"Title: {issue['content'].get('title')}")
                print(f"Milestone: {issue.get('milestone')}")
                break
    
    print("\n-------------------------------------------------------------------")
    
    # Create ChangeTracker
    try:
        change_tracker = ChangeTracker(project_dir)
        print("\nChangeTracker başarıyla oluşturuldu.")
    except Exception as e:
        print(f"ChangeTracker oluşturulamadı: {e}")
        return
    
    # Try to capture original state
    print("\nOrijinal durumu yakalamayı deniyoruz:")
    
    # İşlenmiş veriyi kullan, eğer öğe sayısı yeterli ise
    if len(processed_data) > 0:
        try:
            result = change_tracker.capture_original_state(processed_data)
            print(f"İşlenmiş veri ile sonuç: {'Başarılı' if result else 'Başarısız'}")
        except Exception as e:
            print(f"İşlenmiş veri ile orijinal durum yakalanırken hata: {e}")
    else:
        # Orijinal veri ile deneyelim
        try:
            result = change_tracker.capture_original_state(project_data)
            print(f"Orijinal veri ile sonuç: {'Başarılı' if result else 'Başarısız'}")
        except Exception as e:
            print(f"Orijinal veri ile orijinal durum yakalanırken hata: {e}")

# Run the test
if __name__ == "__main__":
    main() 