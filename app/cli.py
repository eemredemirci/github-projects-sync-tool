"""
GitHub Proje Yönetim Aracı için komut satırı arayüzü.
"""
import os
import sys
import argparse
import json
from typing import Dict, List, Any, Optional

from app.utils.user_manager import (
    get_default_user, get_all_users, add_user, remove_user, 
    set_default_user, get_user, get_user_repositories, get_repository_projects
)
from app.services.github_service import GitHubService
from app.services.sync_service import SyncService


def setup_parser() -> argparse.ArgumentParser:
    """Komut satırı argüman ayrıştırıcısını oluşturur.
    
    Returns:
        Argüman ayrıştırıcı
    """
    parser = argparse.ArgumentParser(
        description="GitHub Proje Yönetim Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Komutlar")
    
    # Kullanıcı komutları
    user_parser = subparsers.add_parser("user", help="Kullanıcı yönetimi")
    user_subparsers = user_parser.add_subparsers(dest="user_command", help="Kullanıcı komutları")
    
    # Kullanıcı listeleme
    user_list_parser = user_subparsers.add_parser("list", help="Kullanıcıları listele")
    
    # Kullanıcı ekleme
    user_add_parser = user_subparsers.add_parser("add", help="Kullanıcı ekle")
    user_add_parser.add_argument("username", help="GitHub kullanıcı adı")
    user_add_parser.add_argument("token", help="GitHub API token")
    user_add_parser.add_argument("--email", help="E-posta adresi")
    user_add_parser.add_argument("--name", help="Ad Soyad")
    
    # Kullanıcı silme
    user_remove_parser = user_subparsers.add_parser("remove", help="Kullanıcı sil")
    user_remove_parser.add_argument("username", help="GitHub kullanıcı adı")
    
    # Varsayılan kullanıcı ayarlama
    user_default_parser = user_subparsers.add_parser("default", help="Varsayılan kullanıcıyı ayarla")
    user_default_parser.add_argument("username", help="GitHub kullanıcı adı")
    
    # Repository komutları
    repo_parser = subparsers.add_parser("repo", help="Repository yönetimi")
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command", help="Repository komutları")
    
    # Repository listeleme
    repo_list_parser = repo_subparsers.add_parser("list", help="Repositoryleri listele")
    repo_list_parser.add_argument("--username", help="GitHub kullanıcı adı (opsiyonel)")
    
    # Repository çekme
    repo_fetch_parser = repo_subparsers.add_parser("fetch", help="Repository verilerini çek")
    repo_fetch_parser.add_argument("owner", help="Repository sahibi")
    repo_fetch_parser.add_argument("repo", help="Repository adı")
    
    # GitHub Project komutları
    project_parser = subparsers.add_parser("project", help="GitHub Project yönetimi")
    project_subparsers = project_parser.add_subparsers(dest="project_command", help="GitHub Project komutları")
    
    # GitHub Project listeleme
    project_list_parser = project_subparsers.add_parser("list", help="GitHub Projects listele")
    project_list_parser.add_argument("--username", help="GitHub kullanıcı adı (opsiyonel)")
    project_list_parser.add_argument("--repo", help="Repository adı (opsiyonel)")
    
    # GitHub Project çekme
    project_fetch_parser = project_subparsers.add_parser("fetch", help="GitHub Project verilerini çek")
    project_fetch_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    
    # Senkronizasyon komutları
    sync_parser = subparsers.add_parser("sync", help="Senkronizasyon yönetimi")
    sync_subparsers = sync_parser.add_subparsers(dest="sync_command", help="Senkronizasyon komutları")
    
    # Yerel GitHub Projects listeleme
    sync_list_parser = sync_subparsers.add_parser("list", help="Yerel GitHub Projects listele")
    
    # YAML'dan JSON'a senkronizasyon
    sync_yaml_to_json_parser = sync_subparsers.add_parser("yaml2json", help="YAML'dan JSON'a senkronize et")
    sync_yaml_to_json_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    sync_yaml_to_json_parser.add_argument("project_name", help="GitHub Project adı")
    
    # JSON'dan YAML'a senkronizasyon
    sync_json_to_yaml_parser = sync_subparsers.add_parser("json2yaml", help="JSON'dan YAML'a senkronize et")
    sync_json_to_yaml_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    sync_json_to_yaml_parser.add_argument("project_name", help="GitHub Project adı")
    
    # GitHub Project değişikliklerini kontrol etme
    sync_check_parser = sync_subparsers.add_parser("check", help="GitHub Project değişikliklerini kontrol et")
    sync_check_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    sync_check_parser.add_argument("project_name", help="GitHub Project adı")
    
    # GitHub değişikliklerini kontrol etme
    sync_check_github_parser = sync_subparsers.add_parser("check-github", help="GitHub değişikliklerini kontrol et")
    sync_check_github_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    sync_check_github_parser.add_argument("project_name", help="GitHub Project adı")
    
    # GitHub Project'i GitHub'a gönderme
    sync_push_parser = sync_subparsers.add_parser("push", help="GitHub Project'i GitHub'a gönder")
    sync_push_parser.add_argument("project_id", type=int, help="GitHub Project ID")
    sync_push_parser.add_argument("project_name", help="GitHub Project adı")
    
    return parser


def handle_user_commands(args: argparse.Namespace) -> None:
    """Kullanıcı komutlarını işler.
    
    Args:
        args: Komut satırı argümanları
    """
    if args.user_command == "list":
        users = get_all_users()
        default_user = get_default_user()
        
        if not users:
            print("Kayıtlı kullanıcı bulunamadı.")
            return
        
        print("\nKayıtlı Kullanıcılar:")
        print("-" * 80)
        print(f"{'Kullanıcı Adı':<20} {'Token':<40} {'E-posta':<30} {'Ad Soyad':<30}")
        print("-" * 80)
        
        for user in users:
            is_default = " (Varsayılan)" if default_user and user["username"] == default_user["username"] else ""
            token_masked = user["token"][:4] + "*" * (len(user["token"]) - 8) + user["token"][-4:] if len(user["token"]) > 8 else "****"
            print(f"{user['username'] + is_default:<20} {token_masked:<40} {user.get('email', ''):<30} {user.get('name', ''):<30}")
        
        print("-" * 80)
    
    elif args.user_command == "add":
        user = add_user(args.username, args.token, args.email or "", args.name or "")
        print(f"Kullanıcı eklendi: {user['username']}")
    
    elif args.user_command == "remove":
        success = remove_user(args.username)
        if success:
            print(f"Kullanıcı silindi: {args.username}")
        else:
            print(f"Kullanıcı bulunamadı: {args.username}")
    
    elif args.user_command == "default":
        success = set_default_user(args.username)
        if success:
            print(f"Varsayılan kullanıcı ayarlandı: {args.username}")
        else:
            print(f"Kullanıcı bulunamadı: {args.username}")
    
    else:
        print("Geçersiz kullanıcı komutu. Yardım için 'user -h' komutunu kullanın.")


def handle_repo_commands(args: argparse.Namespace) -> None:
    """Repository komutlarını işler.
    
    Args:
        args: Komut satırı argümanları
    """
    if args.repo_command == "list":
        user = get_default_user() if not args.username else get_user(args.username)
        
        if not user:
            print("Kullanıcı bulunamadı.")
            return
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Repositoryleri al
        repositories = github_service.get_repositories()
        
        if not repositories:
            print("Repository bulunamadı.")
            return
        
        print("\nRepositoryler:")
        print("-" * 100)
        print(f"{'Ad':<30} {'Açıklama':<50} {'Güncellenme Tarihi':<20}")
        print("-" * 100)
        
        for repo in repositories:
            name = repo.get("name", "")
            description = repo.get("description", "") or ""
            updated_at = repo.get("updated_at", "")
            
            if len(description) > 47:
                description = description[:47] + "..."
            
            print(f"{name:<30} {description:<50} {updated_at:<20}")
        
        print("-" * 100)
    
    elif args.repo_command == "fetch":
        user = get_default_user()
        
        if not user:
            print("Varsayılan kullanıcı bulunamadı.")
            return
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Senkronizasyon servisini oluştur
        sync_service = SyncService(github_service)
        
        # Repository verilerini çek
        repo_data = sync_service.fetch_repository(args.owner, args.repo)
        
        if not repo_data:
            print(f"Repository verileri alınamadı: {args.owner}/{args.repo}")
            return
        
        print(f"Repository verileri başarıyla alındı: {args.owner}/{args.repo}")
        print(f"Toplam GitHub Project sayısı: {len(repo_data.get('projects', []))}")
        print(f"Toplam issue sayısı: {len(repo_data.get('issues', []))}")
        print(f"Toplam milestone sayısı: {len(repo_data.get('milestones', []))}")
        print(f"Toplam etiket sayısı: {len(repo_data.get('labels', []))}")
    
    else:
        print("Geçersiz repository komutu. Yardım için 'repo -h' komutunu kullanın.")


def handle_project_commands(args: argparse.Namespace) -> None:
    """GitHub Project komutlarını işler.
    
    Args:
        args: Komut satırı argümanları
    """
    if args.project_command == "list":
        user = get_default_user() if not args.username else get_user(args.username)
        
        if not user:
            print("Kullanıcı bulunamadı.")
            return
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # GitHub Projects al
        if args.repo:
            # Repository GitHub Projects al
            projects = github_service.get_projects(user["username"], args.repo)
        else:
            # Kullanıcı GitHub Projects al
            projects = github_service.get_projects()
        
        if not projects:
            print("GitHub Project bulunamadı.")
            return
        
        print("\nGitHub Projects:")
        print("-" * 100)
        print(f"{'ID':<10} {'Ad':<30} {'Durum':<10} {'Güncellenme Tarihi':<20}")
        print("-" * 100)
        
        for project in projects:
            project_id = project.get("id", 0)
            name = project.get("name", "")
            state = project.get("state", "")
            updated_at = project.get("updated_at", "")
            
            print(f"{project_id:<10} {name:<30} {state:<10} {updated_at:<20}")
        
        print("-" * 100)
    
    elif args.project_command == "fetch":
        user = get_default_user()
        
        if not user:
            print("Varsayılan kullanıcı bulunamadı.")
            return
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Senkronizasyon servisini oluştur
        sync_service = SyncService(github_service)
        
        # GitHub Project verilerini çek
        project_data = sync_service.fetch_project(args.project_id)
        
        if not project_data:
            print(f"GitHub Project verileri alınamadı: {args.project_id}")
            return
        
        print(f"GitHub Project verileri başarıyla alındı: {project_data.get('name', '')}")
        print(f"Toplam sütun sayısı: {len(project_data.get('columns', []))}")
        
        # Sütun ve kart sayılarını göster
        for column in project_data.get("columns", []):
            column_name = column.get("name", "")
            card_count = len(column.get("cards", []))
            print(f"  - {column_name}: {card_count} kart")
    
    else:
        print("Geçersiz GitHub Project komutu. Yardım için 'project -h' komutunu kullanın.")


def handle_sync_commands(args: argparse.Namespace) -> None:
    """Senkronizasyon komutlarını işler.
    
    Args:
        args: Komut satırı argümanları
    """
    user = get_default_user()
    
    if not user:
        print("Varsayılan kullanıcı bulunamadı.")
        return
    
    # GitHub servisini oluştur
    github_service = GitHubService(user["token"], user["username"])
    
    # Senkronizasyon servisini oluştur
    sync_service = SyncService(github_service)
    
    if args.sync_command == "list":
        # Yerel GitHub Projects listele
        projects = sync_service.list_projects()
        
        if not projects:
            print("Yerel GitHub Project bulunamadı.")
            return
        
        print("\nYerel GitHub Projects:")
        print("-" * 100)
        print(f"{'ID':<10} {'Ad':<30} {'Durum':<10} {'Güncellenme Tarihi':<20} {'Yerel Güncellenme':<20}")
        print("-" * 100)
        
        for project in projects:
            project_id = project.get("id", 0)
            name = project.get("name", "")
            state = project.get("state", "")
            updated_at = project.get("updated_at", "")
            local_updated_at = project.get("local_updated_at", "")
            
            print(f"{project_id:<10} {name:<30} {state:<10} {updated_at:<20} {local_updated_at:<20}")
        
        print("-" * 100)
    
    elif args.sync_command == "yaml2json":
        # YAML'dan JSON'a senkronize et
        success, messages = sync_service.sync_project_yaml_to_json(args.project_id, args.project_name)
        
        if success:
            print(f"YAML'dan JSON'a senkronizasyon başarılı: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
        else:
            print(f"YAML'dan JSON'a senkronizasyon başarısız: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
    
    elif args.sync_command == "json2yaml":
        # JSON'dan YAML'a senkronize et
        success, messages = sync_service.sync_project_json_to_yaml(args.project_id, args.project_name)
        
        if success:
            print(f"JSON'dan YAML'a senkronizasyon başarılı: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
        else:
            print(f"JSON'dan YAML'a senkronizasyon başarısız: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
    
    elif args.sync_command == "check":
        # GitHub Project değişikliklerini kontrol et
        has_changes, changes = sync_service.check_project_changes(args.project_id, args.project_name)
        
        if has_changes:
            print(f"GitHub Project değişiklikleri bulundu: {args.project_id}")
            for i, change in enumerate(changes[:10]):  # İlk 10 değişikliği göster
                print(f"  {change}")
            
            if len(changes) > 10:
                print(f"  ... ve {len(changes) - 10} değişiklik daha")
        else:
            print(f"GitHub Project değişikliği bulunamadı: {args.project_id}")
            for message in changes:
                print(f"  - {message}")
    
    elif args.sync_command == "check-github":
        # GitHub değişikliklerini kontrol et
        has_changes, changes = sync_service.check_github_changes(args.project_id, args.project_name)
        
        if has_changes:
            print(f"GitHub değişiklikleri bulundu: {args.project_id}")
            for i, change in enumerate(changes[:10]):  # İlk 10 değişikliği göster
                print(f"  {change}")
            
            if len(changes) > 10:
                print(f"  ... ve {len(changes) - 10} değişiklik daha")
        else:
            print(f"GitHub değişikliği bulunamadı: {args.project_id}")
            for message in changes:
                print(f"  - {message}")
    
    elif args.sync_command == "push":
        # GitHub Project'i GitHub'a gönder
        success, messages = sync_service.push_project_to_github(args.project_id, args.project_name)
        
        if success:
            print(f"GitHub Project GitHub'a gönderildi: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
        else:
            print(f"GitHub Project GitHub'a gönderilemedi: {args.project_id}")
            for message in messages:
                print(f"  - {message}")
    
    else:
        print("Geçersiz senkronizasyon komutu. Yardım için 'sync -h' komutunu kullanın.")


def main():
    """Ana fonksiyon."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "user":
        handle_user_commands(args)
    elif args.command == "repo":
        handle_repo_commands(args)
    elif args.command == "project":
        handle_project_commands(args)
    elif args.command == "sync":
        handle_sync_commands(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 