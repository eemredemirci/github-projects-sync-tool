import os
import sys
import json
from pprint import pprint

# Ana dizini Python yoluna ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# GitHub service'i import et
from app.services.github_service import GitHubService

def test_parent_issue_fetch():
    """
    Belirli bir issue ID için parent issue ilişkilerini test eder.
    """
    # GitHub token'ı güvenli bir şekilde al
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        token = input("GitHub API token'ınızı girin: ")
    
    if not token:
        print("GitHub token belirtilmedi. Test iptal ediliyor.")
        return
    
    # GitHub service oluştur
    github_service = GitHubService(token)
    
    # Test edilecek issue ID'si
    issue_id = "PVTI_lAHOAQtKyM4AyQUbzgX3Olg"  # Test için örnek bir issue ID - #37 numaralı issue
    
    # Issue bilgilerini getir
    print(f"Fetching issue with ID: {issue_id}")
    issue_data = github_service.fetch_issue_with_parent(issue_id)
    
    # Sonuçları göster
    if not issue_data:
        print("Issue bulunamadı veya hata oluştu.")
        return
    
    print("\nFetched issue information:")
    print(f"Title: {issue_data.get('title')}")
    print(f"Number: {issue_data.get('number')}")
    print(f"URL: {issue_data.get('url')}")
    
    # Parent issue bilgilerini göster
    parent_issues = issue_data.get('parent_issues', [])
    if parent_issues:
        print(f"\nFound {len(parent_issues)} parent issues:")
        for i, parent in enumerate(parent_issues, 1):
            print(f"  {i}. {parent.get('title')} (#{parent.get('number')}) - Relationship: {parent.get('relationship')}")
    else:
        print("\nNo parent issues found.")
    
    # Related issues bilgilerini göster
    related_issues = issue_data.get('related_issues', [])
    if related_issues:
        print(f"\nFound {len(related_issues)} related issues:")
        for i, related in enumerate(related_issues, 1):
            print(f"  {i}. {related.get('title')} (#{related.get('number')}) - Relationship: {related.get('relationship')}")
    else:
        print("\nNo related issues found.")
    
    # Body içeriğini göster
    print("\nIssue body:")
    print(issue_data.get('body', 'No body content'))
    
    # JSON olarak kaydet
    output_file = os.path.join(current_dir, "issue_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(issue_data, f, indent=2, ensure_ascii=False)
    print(f"\nIssue data saved to {output_file}")

if __name__ == "__main__":
    test_parent_issue_fetch() 