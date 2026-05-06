"""
GitHub Proje Yönetim Aracı için etkileşimli komut satırı arayüzü.
"""
import os
import re
import sys
import json
import yaml
import uuid
import time
import shutil
import copy
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import webbrowser
import subprocess
import getpass

from app.utils.user_manager import (
    get_default_user, get_all_users, add_user, remove_user, 
    set_default_user, get_user, get_user_repositories, get_repository_projects,
    get_default_project, update_user
)
from app.services.github_service import GitHubService
from app.services.sync_service import SyncService
from app.utils.language import get_text, language_menu


# Color codes for terminal output
class Colors:
    """Terminal color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Main colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Special colors
    HEADER = BOLD + MAGENTA
    ERROR = RED
    SUCCESS = GREEN
    INFO = CYAN
    WARNING = YELLOW
    GITHUB = BLUE
    LOCAL = GREEN
    NAV = YELLOW
    DISABLED = "\03.90m"  # Gray color
    MILESTONE = GREEN
    ISSUE = RED


def print_info(message: str) -> None:
    """Bilgi mesajı yazdırır.
    
    Args:
        message: Yazdırılacak mesaj
    """
    print(f"{Colors.INFO}{message}{Colors.RESET}")


def print_success(message: str) -> None:
    """Başarı mesajı yazdırır.
    
    Args:
        message: Yazdırılacak mesaj
    """
    print(f"{Colors.SUCCESS}{message}{Colors.RESET}")


def print_warning(message: str):
    """Uyarı mesajı yazdırır.
    
    Args:
        message: Mesaj metni
    """
    print(f"{Colors.WARNING}⚠ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.ERROR}{message}{Colors.RESET}")


def print_github_info(message: str) -> None:
    """GitHub bilgi mesajı yazdırır.
    
    Args:
        message: Yazdırılacak mesaj
    """
    print(f"{Colors.GITHUB}{message}{Colors.RESET}")


def print_local_info(message: str):
    """Lokal işlemlerle ilgili bilgi mesajı yazdırır.
    
    Args:
        message: Mesaj metni
    """
    print(f"{Colors.LOCAL}⊙ {message}{Colors.RESET}")


def clear_screen():
    """Clear the screen."""
    # Ekranı temizleme işlemi devre dışı bırakıldı
    # os.system('cls' if os.name == 'nt' else 'clear')
    pass


def print_header(title: str) -> None:
    """Başlık yazdırır.
    
    Args:
        title: Başlık metni
    """
    print("\n" + "=" * 80)
    print(f"{Colors.HEADER}{title}{Colors.RESET}")
    print("=" * 80)


def print_navigation(breadcrumbs: List[str]) -> None:
    """Navigasyon bilgisini yazdırır.
    
    Args:
        breadcrumbs: Navigasyon yolu
    """
    nav_text = " > ".join(breadcrumbs)
    print(f"{Colors.NAV}{get_text('navigation')}: {nav_text}{Colors.RESET}")


def print_menu(options: List[Dict[str, Any]]) -> None:
    """
    Menü seçeneklerini yazdırır.
    
    Args:
        options: Menü seçenekleri listesi. Her seçenek bir sözlük olmalı ve şu anahtarları içerebilir:
            - name: Seçenek metni
            - value: Seçenek değeri
            - disabled: Seçeneğin devre dışı olup olmadığı
            - selected: Seçeneğin seçili olup olmadığı
    """
    print(f"\n{get_text('options')}")
    
    for i, option in enumerate(options, 1):
        option_text = option.get("name", option.get("text", ""))  # Geriye dönük uyumluluk için
        option_value = option.get("value", "")
        disabled = option.get("disabled", False)
        selected = option.get("selected", False)
        
        # Seçenek durumuna göre renk belirle
        if disabled:
            color = Colors.DISABLED
        elif selected:
            color = Colors.SUCCESS
        else:
            color = Colors.RESET
        
        # Seçenek numarası ve metni yazdır
        if disabled:
            print(f"  {Colors.DISABLED}{i}. {option_text}{Colors.RESET} ({get_text('disabled')})")
        else:
            print(f"  {Colors.BOLD}{i}.{Colors.RESET} {color}{option_text}{Colors.RESET}")
    
    # "Back" ve "Exit" seçeneklerini menüde gösterme, sadece kullanıcı giriş kısmında kullan
    # print(f"  {Colors.BOLD}b.{Colors.RESET} {get_text('main_menu_back')}")
    # print(f"  {Colors.BOLD}q.{Colors.RESET} {get_text('main_menu_exit')}")


def shorten_path(path: str, max_length: int = 50) -> str:
    """Dosya yolunu kısaltır.
    
    Args:
        path: Kısaltılacak dosya yolu
        max_length: Maksimum uzunluk
        
    Returns:
        str: Kısaltılmış dosya yolu
    """
    if len(path) <= max_length:
        return path
    
    # Dosya adını ve uzantısını al
    basename = os.path.basename(path)
    
    # Dizin yolunu al
    dirname = os.path.dirname(path)
    
    # Dizin yolunu kısalt
    if len(dirname) > max_length - len(basename) - 5:
        dirname = dirname[:max_length - len(basename) - 5] + "..."
    
    # Kısaltılmış yolu döndür
    return os.path.join(dirname, basename)


def get_user_choice(max_choice: int) -> str:
    """
    Kullanıcıdan bir seçim alır.
    
    Args:
        max_choice: Maksimum seçim numarası
        
    Returns:
        Kullanıcının seçimi
    """
    while True:
        try:
            choice = input(f"\n{Colors.BOLD}{get_text('enter_choice')} (1-{max_choice}): {Colors.RESET}")
            if choice.lower() == "q" or choice.lower() == "exit":
                clear_screen()
                sys.exit(0)
            if choice.lower() == "b" or choice.lower() == "back":
                return "back"
            if not choice.isdigit() or int(choice) < 1 or int(choice) > max_choice:
                print_error(get_text("invalid_choice"))
                continue
            return choice
        except KeyboardInterrupt:
            clear_screen()
            sys.exit(0)
        except Exception:
            print_error(get_text("invalid_choice"))


def wait_for_enter(clear_screen_after: bool = False) -> None:
    """
    Kullanıcının Enter tuşuna basmasını bekler.
    
    Args:
        clear_screen_after: Enter'a basıldıktan sonra ekranı temizle
    """
    try:
        input(f"\n{Colors.BOLD}{get_text('press_enter')}{Colors.RESET}")
        if clear_screen_after:
            clear_screen()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)


def login_menu() -> None:
    """Giriş menüsü."""
    while True:
        # Navigasyon
        print_header("Kullanıcı Girişi")
        print_navigation(["Ana Menü", "Kullanıcı Girişi"])
        
        # Menü seçenekleri
        options = [
            {"text": "GitHub Token ile Giriş", "type": "github"},
            {"text": "Kullanıcıları Listele", "type": "local"}
        ]
        
        print_menu(options)
        
        choice = input("\nSeçiminiz: ").strip()
        
        if choice == "1":
            login_user()
        elif choice == "2":
            list_users()
        elif choice == "0":
            return
        else:
            print_error("Geçersiz seçim!")
            wait_for_enter(True)


def login_user() -> None:
    """GitHub token ile giriş yapar."""
    # Navigasyon
    print_header("GitHub Token ile Giriş")
    print_navigation(["Ana Menü", "Kullanıcı Girişi", "Token ile Giriş"])
    
    print_info("GitHub token ile giriş yapın.")
    print_info("Token oluşturmak için: https://github.com/settings/tokens")
    print_info("Token'ın şu izinlere sahip olması gerekir:")
    print_info("- repo (tüm alt izinler)")
    print_info("- admin:org (read:org)")
    print_info("- project")
    
    token = getpass.getpass("\nGitHub Token: ")
    
    if not token:
        print_error("Token boş olamaz!")
        wait_for_enter(True)
        return
    
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(token)
        
        # Token'ı doğrula
        user_info = github_service.get_user()
        
        if not user_info:
            print_error("Token geçersiz veya yetkileri yetersiz!")
            wait_for_enter(True)
            return
        
        # Kullanıcı bilgilerini al
        username = user_info.get("login")
        
        if not username:
            print_error("Kullanıcı adı alınamadı!")
            wait_for_enter(True)
            return
        
        # Kullanıcıyı ekle
        add_user(username, token)
        
        # Kullanıcı menüsüne git
        user = {"username": username, "token": token}
        user_menu(user)
    except Exception as e:
        print_error(f"Giriş yapılırken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter(True)


def add_new_user():
    """Add a new user."""
    # Breadcrumb navigation
    breadcrumb = f"{get_text('navigation_main_menu')} > {get_text('user_actions_login')}"
    print_header(get_text('user_actions_login'))
    print_info(f"{get_text('navigation')}: {breadcrumb}")
    
    # Kullanıcı bilgilerini al
    print_info("\nGitHub kullanıcı adınızı girin:")
    username = input("> ").strip()
    
    if not username:
        print_error("Kullanıcı adı boş olamaz!")
        wait_for_enter()
        return
    
    # Kullanıcının zaten var olup olmadığını kontrol et
    users = get_all_users()
    for user in users:
        if user["username"].lower() == username.lower():
            print_error(f"Bu kullanıcı adı zaten kayıtlı: {username}")
            wait_for_enter()
            return
    
    print_info("\nGitHub token'ınızı girin:")
    token = input("> ").strip()
    
    if not token:
        print_error("Token boş olamaz!")
        wait_for_enter()
        return
    
    # Token'ı doğrula
    print_info("Token doğrulanıyor...")
    
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(token, username)
        
        # Kullanıcı bilgilerini doğrula
        user_info = github_service.get_user()
        
        if not user_info:
            print_error("Token geçersiz! Kullanıcı bilgileri alınamadı.")
            wait_for_enter()
            return
        
        # Kullanıcı adını doğrula
        if user_info.get("login", "").lower() != username.lower():
            print_error(f"Token, {username} kullanıcısına ait değil! Gerçek kullanıcı: {user_info.get('login', '')}")
            wait_for_enter()
            return
        
        # Kullanıcıyı ekle
        user = {
            "username": username,
            "token": token,
            "email": user_info.get("email", ""),
            "name": user_info.get("name", ""),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        add_user(user)
        
        print_success(f"Kullanıcı başarıyla eklendi: {username}")
        
        # Varsayılan kullanıcı olarak ayarla
        if not get_default_user():
            set_default_user(username)
            print_success(f"Varsayılan kullanıcı olarak ayarlandı: {username}")
    except Exception as e:
        print_error(f"Kullanıcı eklenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
    
    wait_for_enter()


def list_users() -> None:
    """Kullanıcıları listeler."""
    # Navigasyon
    print_header("Kullanıcılar")
    print_navigation(["Ana Menü", "Kullanıcılar"])
    
    # Kullanıcıları al
    users = get_all_users()
    
    if not users:
        print_error(get_text('no_users'))
        print_info(get_text('token_info'))
        wait_for_enter(True)
        return
    
    # Varsayılan kullanıcıyı al
    default_user = get_default_user()
    default_username = default_user["username"] if default_user else ""
    
    # Kullanıcıları listele
    print_info(f"\nToplam {len(users)} kullanıcı bulundu:")
    print("\n{:<5} {:<30} {:<20} {:<10}".format("#", "Kullanıcı Adı", "Eklenme Tarihi", "Varsayılan"))
    print("-" * 70)
    
    for i, user in enumerate(users, 1):
        username = user["username"]
        added_at = user.get("added_at", "")
        is_default = "✓" if username == default_username else ""
        
        print("{:<5} {:<30} {:<20} {:<10}".format(i, username, added_at, is_default))
    
    print("\n0: Geri")
    
    choice = get_user_choice(len(users))
    
    if choice == "0":
        return
    
    selected_user = users[int(choice) - 1]
    
    # Kullanıcı işlemleri
    user_actions(selected_user)


def browse_local_projects(user: Dict[str, Any]):
    """Yerel GitHub Projelerini listeler.
    
    Args:
        user: Kullanıcı bilgileri
    """
    try:
        # Navigasyon
        print_header("Yerel Projeler")
        print_navigation(["Ana Menü", user['username'], "Yerel Projeler"])
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Senkronizasyon servisini oluştur
        sync_service = SyncService(github_service)
        
        # Proje dizinini kontrol et
        projects_dir = sync_service.projects_dir
        
        # Proje dizinlerini listele
        project_dirs = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
        
        if not project_dirs:
            print_error("Hiç yerel proje bulunamadı!")
            print_info("GitHub'dan proje çekmek için 'GitHub Projeleri' menüsünü kullanabilirsiniz.")
            wait_for_enter(True)
            return
        
        # Proje bilgilerini topla
        projects = []
        
        for dir_name in project_dirs:
            try:
                # Proje ID ve adını dizin adından çıkar
                parts = dir_name.split("_", 1)
                if len(parts) < 2:
                    continue
                
                project_id = parts[0]
                project_name = parts[1].replace("_", " ")
                
                # Proje dizini
                project_dir = os.path.join(projects_dir, dir_name)
                
                # JSON ve YAML dosyalarını kontrol et
                json_file = os.path.join(project_dir, "project.json")
                yaml_file = os.path.join(project_dir, "project.yaml")
                
                # Dosya durumlarını belirle
                json_exists = os.path.exists(json_file)
                yaml_exists = os.path.exists(yaml_file)
                
                if not json_exists and not yaml_exists:
                    continue
                
                # Proje bilgilerini oku
                project_data = {}
                
                if json_exists:
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            project_data = json.load(f)
                    except Exception as e:
                        print_error(f"JSON dosyası okunamadı: {json_file} - {str(e)}")
                
                # Proje bilgilerini oluştur
                project = {
                    "id": project_id,
                    "title": project_data.get("name", project_name),
                    "state": project_data.get("state", ""),
                    "html_url": project_data.get("html_url", ""),
                    "json_exists": json_exists,
                    "yaml_exists": yaml_exists
                }
                
                # Dosya zamanlarını belirle
                if json_exists:
                    project["json_time"] = datetime.fromtimestamp(os.path.getmtime(json_file)).strftime('%Y-%m-%d %H:%M:%S')
                
                if yaml_exists:
                    project["yaml_time"] = datetime.fromtimestamp(os.path.getmtime(yaml_file)).strftime('%Y-%m-%d %H:%M:%S')
                
                projects.append(project)
            except Exception as e:
                print_error(f"Proje bilgileri alınırken hata oluştu: {dir_name} - {str(e)}")
        
        if not projects:
            print_error("Hiç geçerli yerel proje bulunamadı!")
            print_info("GitHub'dan proje çekmek için 'GitHub Projeleri' menüsünü kullanabilirsiniz.")
            wait_for_enter(True)
            return
        
        # Projeleri listele
        print_info(f"\nToplam {len(projects)} yerel proje bulundu:")
        print("\n{:<5} {:<60} {:<20}".format("#", "Proje Adı", "Son Güncelleme"))
        print("-" * 85)
        
        for i, project in enumerate(projects, 1):
            project_name = project["title"]
            
            # Son güncelleme zamanını belirle
            last_update = ""
            if project.get("json_time") and project.get("yaml_time"):
                # En son güncellenen dosyanın zamanını al
                json_time = datetime.strptime(project["json_time"], '%Y-%m-%d %H:%M:%S')
                yaml_time = datetime.strptime(project["yaml_time"], '%Y-%m-%d %H:%M:%S')
                last_update = project["json_time"] if json_time > yaml_time else project["yaml_time"]
            elif project.get("json_time"):
                last_update = project["json_time"]
            elif project.get("yaml_time"):
                last_update = project["yaml_time"]
            
            if len(project_name) > 58:
                project_name = project_name[:55] + "..."
            
            print("{:<5} {:<60} {:<20}".format(i, project_name, last_update))
        
        print("\n0: Geri")
        
        choice = get_user_choice(len(projects))
        
        if choice == "0":
            return
        
        selected_project = projects[int(choice) - 1]
        
        # Proje menüsüne git
        project_menu(user, selected_project)
    except Exception as e:
        print_error(f"Yerel projeler listelenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter(True)


def update_all_from_github(user: Dict[str, Any]) -> bool:
    """GitHub'dan tüm verileri günceller.
    
    Args:
        user: Kullanıcı bilgileri
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # Navigasyon
        print_header("GitHub'dan Güncelle")
        print_navigation(["Ana Menü", user['username'], "GitHub'dan Güncelle"])
        
        print_github_info("GitHub'dan tüm veriler güncelleniyor...")
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Cache dizinlerini oluştur
        repo_cache_dir = os.path.join("data", "repositories")
        project_cache_dir = os.path.join("data", "projects")
        old_repo_projects_cache_dir = os.path.join("data", "repositories", "projects")
        
        os.makedirs(repo_cache_dir, exist_ok=True)
        os.makedirs(project_cache_dir, exist_ok=True)
        
        # Eski cache yapısını temizle
        if os.path.exists(old_repo_projects_cache_dir):
            try:
                # Eski repository project cache dosyalarını sil
                for file in os.listdir(old_repo_projects_cache_dir):
                    if file.endswith("_projects_cache.json"):
                        os.remove(os.path.join(old_repo_projects_cache_dir, file))
                        print_info(f"Eski cache dosyası silindi: {file}")
            except Exception as e:
                print_warning(f"Eski cache dosyaları silinirken hata oluştu: {str(e)}")
        
        # Repoları güncelle
        print_github_info("\nRepolar güncelleniyor...")
        
        # GitHub'dan repoları çek
        repositories = github_service.get_repositories()
        
        # Cache'e kaydet
        repo_cache_file = os.path.join(repo_cache_dir, f"{user['username']}-repos-cache.json")
        with open(repo_cache_file, "w", encoding="utf-8") as f:
            json.dump(repositories, f, indent=2, ensure_ascii=False)
        print_success(f"Repolar cache oluşturuldu: {shorten_path(repo_cache_file)}")
        print_info(f"Toplam {len(repositories)} repo bulundu.")
        
        # Projeleri güncelle
        print_github_info("\nProjeler güncelleniyor...")
        
        # GitHub'dan projeleri çek (v1 API)
        projects_v1 = github_service.get_user_projects(user["username"])
        print_info(f"GitHub Projects v1: {len(projects_v1)} proje bulundu.")
        
        # GitHub'dan projeleri çek (v2 API)
        projects_v2 = github_service.get_projects_v2(user["username"])
        print_info(f"GitHub Projects v2: {len(projects_v2)} proje bulundu.")
        
        # Tüm projeleri birleştir
        all_projects = projects_v1 + projects_v2
        
        # Cache'e kaydet
        project_cache_file = os.path.join(project_cache_dir, f"{user['username']}-projects-cache.json")
        with open(project_cache_file, "w", encoding="utf-8") as f:
            json.dump(all_projects, f, indent=2, ensure_ascii=False)
        print_success(f"Projeler cache oluşturuldu: {shorten_path(project_cache_file)}")
        print_info(f"Toplam {len(all_projects)} proje bulundu.")
        
        print_success("\nTüm veriler başarıyla güncellendi!")
        wait_for_enter(True)
        return True
    except Exception as e:
        print_error(f"Veriler güncellenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter(True)
        return False


def update_token(user: Dict[str, Any]) -> bool:
    """GitHub API tokenını günceller.
    
    Args:
        user: Kullanıcı bilgileri
        
    Returns:
        İşlemin başarılı olup olmadığı
    """
    clear_screen()
    print_header("GitHub Token Güncelleme")
    print_navigation(["Ana Menü", user['username'], "Token Güncelleme"])
    
    print_info("GitHub Personal Access Token, GitHub API'sine erişmek için gereklidir.")
    print_info("GitHub Projects v2 API için token oluşturma seçenekleri:")
    print(f"\n{Colors.BOLD}1. Classic Token (Eski stil){Colors.RESET}")
    print("Token oluşturma: https://github.com/settings/tokens")
    print("Gerekli izinler:")
    print("- repo (tüm alt izinler dahil)")
    print("- project (tüm alt izinler dahil)")
    print("- Yüksek rate limitleri sağlar")
    
    print(f"\n{Colors.BOLD}2. Fine-grained Token (Önerilen){Colors.RESET}")
    print("Token oluşturma: https://github.com/settings/tokens?type=beta")
    print("Gerekli izinler:")
    print("- Repository permissions:")
    print("  - Contents: Read and write")
    print("  - Issues: Read and write")
    print("  - Pull requests: Read and write") 
    print("  - Projects: Read and write")
    print("- Account permissions: ")
    print("  - Project: Read and write")
    print("")
    print_info("Lütfen GitHub token'ınızı doğru ayarladığınızdan emin olun.")
    
    current_token = user.get('token', '')
    if current_token:
        masked_token = current_token[:4] + "*" * (len(current_token) - 8) + current_token[-4:]
        print_info(f"Mevcut token: {masked_token}")
        
    print_info("Yeni GitHub tokenını girin (Eski tokenı kullanmak için boş bırakın):")
    new_token = input().strip()
    
    if not new_token:
        print_info("Token değiştirilmedi.")
        wait_for_enter()
        return False
    
    # Token geçerliliğini kontrol et
    print_info("Token doğrulanıyor...")
    from app.services.github_service import GitHubService
    
    gh_service = GitHubService(user.get('username', ''), new_token)
    if gh_service.validate_token():
        # Token geçerli, kaydet
        user['token'] = new_token
        
        # Kullanıcı bilgilerini kaydet
        from app.services.user_service import UserService
        if UserService.save_user(user):
            print_success("GitHub token başarıyla güncellendi.")
            
            # GraphQL API'si için özel izinleri kontrol et
            print_info("GitHub Projects v2 API izinleri kontrol ediliyor...")
            try:
                # Test GraphQL sorgusu
                test_query = """
                query {
                  viewer {
                    login
                  }
                }
                """
                endpoint = "/graphql"
                data = {"query": test_query}
                custom_headers = {"Accept": "application/vnd.github.v3+json"}
                
                response, status_code = gh_service._make_request("POST", endpoint, data=data, custom_headers=custom_headers)
                
                if status_code == 200 and "data" in response and "viewer" in response["data"]:
                    print_success("Token, GraphQL API'si için gerekli izinlere sahip.")
                else:
                    print_warning("Token, GraphQL API'si için gerekli tüm izinlere sahip olmayabilir.")
                    print_info("GitHub Projects v2 API'si için 'project' izninin açık olduğundan emin olun.")
            except Exception as e:
                print_warning(f"GraphQL API izin kontrolü sırasında hata: {str(e)}")
                print_info("Token çalışıyor ancak GitHub Projects v2 için ek izinler gerekebilir.")
            
            wait_for_enter()
            return True
        else:
            print_error("Kullanıcı bilgileri kaydedilirken hata oluştu!")
            wait_for_enter()
            return False
    else:
        print_error("Geçersiz GitHub token! Token doğrulanamadı.")
        print_info("Token'ınızın doğru olduğundan veya süresi dolmadığından emin olun.")
        print_info("GitHub'ın API servislerinin çalıştığından emin olun.")
        wait_for_enter()
        return False


def user_actions(user: Dict[str, Any]) -> None:
    """
    Kullanıcı işlemleri menüsünü gösterir.
    
    Args:
        user: Kullanıcı bilgileri
    """
    clear_screen()
    print_header(f"{get_text('user_actions_title')}: {Colors.GITHUB}{user['username']}{Colors.RESET}")
    
    # Varsayılan kullanıcıyı kontrol et
    default_user = get_default_user()
    is_default = default_user and default_user.get("username") == user["username"]
    
    options = [
        {"name": get_text("user_actions_login"), "value": "login"},
        {"name": get_text("user_actions_set_default"), "value": "set_default", "disabled": is_default},
        {"name": get_text("user_actions_update_token"), "value": "update_token"},
        {"name": get_text("user_actions_delete"), "value": "delete"},
        {"name": get_text("main_menu_back"), "value": "back"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        # Kullanıcı menüsüne git
        user_menu(user)
    elif choice == "2" and not is_default:
        # Varsayılan olarak ayarla
        set_default_user(user["username"])
        print_success(get_text("user_set_default"))
        wait_for_enter()
    elif choice == "3":
        # Token güncelle
        update_token(user)
    elif choice == "4":
        # Kullanıcıyı sil
        confirm = input(f"\n{Colors.WARNING}{get_text('confirm')}{Colors.RESET} ")
        if confirm.lower() == get_text("yes").lower():
            remove_user(user["username"])
            print_success(get_text("user_deleted"))
            wait_for_enter()
            return
    elif choice == "5" or choice == "back":
        return
    
    user_actions(user)


def user_menu(user: Dict[str, Any]) -> None:
    """
    Kullanıcı menüsünü gösterir.
    
    Args:
        user: Kullanıcı bilgileri
    """
    clear_screen()
    print_header(f"{get_text('user_menu_title')}: {Colors.GITHUB}{user['username']}{Colors.RESET}")
    
    # GitHub token'ı doğrula
    github_service = GitHubService(user["token"], user["username"])
    if not github_service.validate_token():
        print_error(get_text("token_validation_error"))
        if update_token(user):
            print_success(get_text("token_validation_success"))
        else:
            wait_for_enter()
            return
    
    options = [
        {"name": get_text("user_menu_repositories"), "value": "repositories"},
        {"name": get_text("user_menu_github_projects"), "value": "github_projects"},
        {"name": get_text("user_menu_local_projects"), "value": "local_projects"},
        {"name": get_text("user_menu_update_from_github"), "value": "update_from_github"},
        {"name": get_text("user_menu_update_token"), "value": "update_token"},
        {"name": get_text("main_menu_back"), "value": "back"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        browse_repositories(user)
    elif choice == "2":
        list_github_projects(user)
    elif choice == "3":
        browse_local_projects(user)
    elif choice == "4":
        update_all_from_github(user)
        wait_for_enter()
    elif choice == "5":
        update_token(user)
    elif choice == "6" or choice == "back":
        return
    
    user_menu(user)


def browse_repositories(user: Dict[str, Any]):
    """List user repositories.
    
    Args:
        user: User information
    """
    try:
        # Navigasyon
        print_header("Repolar")
        print_navigation(["Ana Menü", user['username'], "Repolar"])
        
        print_github_info("GitHub'dan repolar alınıyor...")
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Repoları al
        repositories = get_user_repositories(user)
        
        if not repositories:
            print_error("Hiç repo bulunamadı!")
            wait_for_enter(True)
            return
        
        # Repoları listele
        print_info(f"\nToplam {len(repositories)} repo bulundu:")
        print("\n{:<5} {:<60} {:<20}".format("#", "Repo Adı", "Açıklama"))
        print("-" * 85)
        
        for i, repo in enumerate(repositories, 1):
            repo_name = repo["name"]
            
            # Açıklama
            description = repo.get("description", "") or ""
            if description and len(description) > 18:
                description = description[:15] + "..."
            
            if len(repo_name) > 58:
                repo_name = repo_name[:55] + "..."
            
            print("{:<5} {:<60} {:<20}".format(i, repo_name, description))
        
        print("\n0: Geri")
        
        choice = get_user_choice(len(repositories))
        
        if choice == "0":
            return
        
        selected_repo = repositories[int(choice) - 1]
        
        # Repo menüsüne git
        repository_menu(user, selected_repo)
    except Exception as e:
        print_error(f"Repolar listelenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter(True)


def repository_menu(user: Dict[str, Any], repository: Dict[str, Any]):
    """
    Repository menüsünü gösterir.
    
    Args:
        user: Kullanıcı bilgileri
        repository: Repository bilgileri
    """
    clear_screen()
    print_header(f"{get_text('repository_menu_title')}: {Colors.GITHUB}{repository['name']}{Colors.RESET}")
    
    options = [
        {"name": get_text("repository_menu_list_projects"), "value": "list_projects"},
        {"name": get_text("repository_menu_update"), "value": "update"},
        {"name": get_text("repository_menu_open_browser"), "value": "open_browser"},
        {"name": get_text("main_menu_back"), "value": "back"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        list_github_projects(user, repository)
    elif choice == "2":
        updated_repo = update_repository(user, repository)
        if updated_repo:
            repository = updated_repo
            print_success(get_text("repository_updated"))
        wait_for_enter()
    elif choice == "3":
        webbrowser.open(repository["html_url"])
        wait_for_enter()
    elif choice == "4" or choice == "back":
        return
    
    repository_menu(user, repository)


def list_repository_github_projects(user: Dict[str, Any], repository: Dict[str, Any]):
    """Bir reponun GitHub projelerini listeler.
    
    Args:
        user: Kullanıcı bilgileri
        repository: Repo bilgileri
    """
    try:
        # Navigasyon
        print_header(f"GitHub Projeleri: {repository['name']}")
        print_navigation(["Ana Menü", user['username'], "Repolar", repository['name'], "GitHub Projeleri"])
        
        # Cache dizinini oluştur
        cache_dir = os.path.join("data", "repositories", "projects")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache dosyası
        repo_id = repository.get("id", "")
        repo_name = repository.get("name", "")
        cache_file = os.path.join(cache_dir, f"{repo_id}_{repo_name}_projects_cache.json")
        
        # Önce cache'den projeleri yüklemeyi dene
        projects = []
        cache_used = False
        
        if os.path.exists(cache_file):
            try:
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 3600:  # 1 saat = 3600 saniye
                    with open(cache_file, "r", encoding="utf-8") as f:
                        projects = json.load(f)
                        print_github_info(f"Cache'den {len(projects)} proje yüklendi.")
                        cache_used = True
            except Exception as e:
                print_warning(f"Cache okuma hatası: {str(e)}")
        
        # Cache yoksa veya eskiyse GitHub'dan projeleri çek
        if not cache_used:
            print_github_info("GitHub'dan projeler alınıyor...")
            
            # GitHub servisini oluştur
            github_service = GitHubService(user["token"], user["username"])
            
            # Projeleri al (v1 API)
            projects = github_service.get_repository_projects(repository["owner"]["login"], repository["name"])
            
            # Projects v2 API'sini de dene
            projects_v2 = github_service.get_projects_v2(repository["owner"]["login"], repository["name"])
            
            # İki listeyi birleştir
            all_projects = projects + projects_v2
            
            # Cache'e kaydet
            if all_projects:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(all_projects, f, indent=2, ensure_ascii=False)
                    print_github_info(f"Projeler cache'e kaydedildi: {cache_file}")
                except Exception as e:
                    print_warning(f"Cache yazma hatası: {str(e)}")
            
            projects = all_projects
        
        if not projects:
            print_error("Bu repoda hiç proje bulunamadı!")
            wait_for_enter(True)
            return
        
        # Projeleri listele
        print_info(f"\nToplam {len(projects)} proje bulundu:")
        print("\n{:<5} {:<60} {:<20}".format("#", "Proje Adı", "Durum"))
        print("-" * 85)
        
        for i, project in enumerate(projects, 1):
            # API versiyonuna göre alan isimlerini kontrol et
            if "title" in project:
                project_name = project["title"]
            elif "name" in project:
                project_name = project["name"]
            else:
                project_name = "İsimsiz Proje"
            
            # Durum bilgisini kontrol et
            if "state" in project:
                project_state = project.get("state", "")
            else:
                project_state = "open" if not project.get("closed", False) else "closed"
            
            # Proje tipini belirt
            project_type = "v2" if project.get("is_v2", False) else "v1"
            
            if len(project_name) > 58:
                project_name = project_name[:55] + "..."
            
            print("{:<5} {:<60} {:<20}".format(i, project_name, f"{project_state} ({project_type})"))
        
        print("\n0: Geri")
        
        choice = get_user_choice(len(projects))
        
        if choice == "0":
            return
        
        # Seçilen projeyi al
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(projects):
            selected_project = projects[selected_index]
            project_menu(user, selected_project)
        else:
            print_error("Geçersiz seçim!")
            wait_for_enter()
    except Exception as e:
        print_error(f"Projeler listelenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter()
        return


def list_github_projects(user: Dict[str, Any], repository: Dict[str, Any] = None):
    """Kullanıcının tüm GitHub projelerini listeler.
    
    Args:
        user: Kullanıcı bilgileri
        repository: Repository bilgileri (opsiyonel, repository menüsünden çağrıldığında kullanılır)
    """
    try:
        # Navigasyon - Repository menüsünden mi yoksa kullanıcı menüsünden mi çağrıldığını kontrol et
        if repository:
            print_header(f"GitHub Projeleri: {repository['name']}")
            print_navigation(["Ana Menü", user['username'], "Repolar", repository['name'], "GitHub Projeleri"])
        else:
            print_header("GitHub Projeleri")
            print_navigation(["Ana Menü", user['username'], "GitHub Projeleri"])
        
        # Cache dizinini oluştur
        cache_dir = os.path.join("data", "projects")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache dosyası - Tek bir cache yapısı kullan
        cache_file = os.path.join(cache_dir, f"{user['username']}-projects-cache.json")
        
        # Önce cache'den projeleri yüklemeyi dene
        projects = []
        cache_used = False
        
        if os.path.exists(cache_file):
            try:
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 3600:  # 1 saat = 3600 saniye
                    with open(cache_file, "r", encoding="utf-8") as f:
                        projects = json.load(f)
                        print_github_info(f"Cache'den {len(projects)} proje yüklendi.")
                        cache_used = True
            except Exception as e:
                print_warning(f"Cache okuma hatası: {str(e)}")
        
        # Cache yoksa veya eskiyse GitHub'dan projeleri çek
        if not cache_used:
            print_github_info("GitHub'dan projeler alınıyor...")
            
            # GitHub servisini oluştur
            github_service = GitHubService(user["token"], user["username"])
            
            # GitHub'dan projeleri çek (v1 API)
            projects_v1 = github_service.get_user_projects(user["username"])
            print_info(f"GitHub Projects v1: {len(projects_v1)} proje bulundu.")
            
            # GitHub'dan projeleri çek (v2 API)
            projects_v2 = github_service.get_projects_v2(user["username"])
            print_info(f"GitHub Projects v2: {len(projects_v2)} proje bulundu.")
            
            # Tüm projeleri birleştir
            projects = projects_v1 + projects_v2
            
            # Cache'e kaydet
            if projects:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(projects, f, indent=2, ensure_ascii=False)
                    print_github_info(f"Projeler cache'e kaydedildi: {cache_file}")
                except Exception as e:
                    print_warning(f"Cache yazma hatası: {str(e)}")
        
        # Eğer repository belirtilmişse ve repository'ye ait projeler isteniyorsa, filtreleme yap
        if repository:
            # Repository ID'sini al
            repo_id = repository.get("id")
            repo_name = repository.get("name")
            
            # Projeleri filtrele (v2 projeleri için repository bağlantısı farklı olabilir)
            # Bu kısım GitHub API'sine göre güncellenebilir
            # Şimdilik tüm projeleri gösteriyoruz
            print_info(f"Not: GitHub Projects v2, repository'den bağımsız olarak çalışır.")
            print_info(f"Tüm projeleriniz gösteriliyor.")
        
        if not projects:
            print_error("Hiç proje bulunamadı!")
            wait_for_enter(True)
            return
        
        # Projeleri listele
        print_info(f"\nToplam {len(projects)} proje bulundu:")
        print("\n{:<5} {:<60} {:<20}".format("#", "Proje Adı", "Durum"))
        print("-" * 85)
        
        for i, project in enumerate(projects, 1):
            # API versiyonuna göre alan isimlerini kontrol et
            if "title" in project:
                project_name = project["title"]
            elif "name" in project:
                project_name = project["name"]
            else:
                project_name = "İsimsiz Proje"
            
            # Durum bilgisini kontrol et
            if "state" in project:
                project_state = project.get("state", "")
            else:
                project_state = "open" if not project.get("closed", False) else "closed"
            
            # Proje tipini belirt
            project_type = "v2" if project.get("is_v2", False) else "v1"
            
            if len(project_name) > 58:
                project_name = project_name[:55] + "..."
            
            print("{:<5} {:<60} {:<20}".format(i, project_name, f"{project_state} ({project_type})"))
        
        print("\n0: Geri")
        
        choice = get_user_choice(len(projects))
        
        if choice == "0":
            return
        
        # Seçilen projeyi al
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(projects):
            selected_project = projects[selected_index]
            project_menu(user, selected_project)
        else:
            print_error("Geçersiz seçim!")
            wait_for_enter()
    except Exception as e:
        print_error(f"Projeler listelenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter()
        return


def project_menu(user: Dict[str, Any], project: Dict[str, Any]):
    """
    Proje menüsünü gösterir.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
    """
    clear_screen()
    # Fix the KeyError by safely accessing the title or name
    project_title = project.get('title', project.get('name', 'Unknown Project'))
    print_header(f"{get_text('project_menu_title')}: {Colors.GITHUB}{project_title}{Colors.RESET}")
    
    # Proje bilgilerini göster
    print(f"\n{Colors.BOLD}ID:{Colors.RESET} {project['id']}")
    print(f"{Colors.BOLD}URL:{Colors.RESET} {project['html_url']}")
    print(f"{Colors.BOLD}State:{Colors.RESET} {project['state']}")
    print(f"{Colors.BOLD}Number:{Colors.RESET} {project['number']}")
    
    # Proje dosyalarını kontrol et - birden fazla format için kontrol yap
    project_id = project['id']
    
    # İsim seçeneklerini hazırla
    name_options = []
    if 'name' in project:
        name_options.append(project['name'].replace(' ', '_').replace('/', '_'))
    if 'title' in project:
        name_options.append(project['title'].replace(' ', '_').replace('/', '_'))
    
    # Projelerin temel dizini
    projects_dir = os.path.join("data", "projects")
    
    # Proje dizinini bul
    project_dir = None
    json_file = None
    yaml_file = None
    
    # Doğrudan tam isimle dizini bulmaya çalış
    for name in name_options:
        potential_dir = os.path.join(projects_dir, f"{project_id}_{name}")
        if os.path.exists(potential_dir):
            project_dir = potential_dir
            json_file = os.path.join(project_dir, "project.json")
            yaml_file = os.path.join(project_dir, "project.yaml")
            break
    
    # Doğrudan bulunamadıysa, dizinde arayarak bul
    if project_dir is None and os.path.exists(projects_dir):
        for dir_name in os.listdir(projects_dir):
            if dir_name.startswith(f"{project_id}_"):
                project_dir = os.path.join(projects_dir, dir_name)
                json_file = os.path.join(project_dir, "project.json")
                yaml_file = os.path.join(project_dir, "project.yaml")
                break
    
    has_json = json_file and os.path.exists(json_file)
    has_yaml = yaml_file and os.path.exists(yaml_file)
    
    if has_json or has_yaml:
        print(f"\n{Colors.BOLD}{get_text('local_files')}{Colors.RESET}")
        if has_json:
            print(f"{Colors.LOCAL}JSON:{Colors.RESET} {json_file}")
        if has_yaml:
            print(f"{Colors.LOCAL}YAML:{Colors.RESET} {yaml_file}")
    
    options = [
        {"name": get_text("project_menu_fetch"), "value": "fetch"},
        {"name": get_text("project_menu_track_changes"), "value": "track_changes", "disabled": not (has_json or has_yaml)},
        {"name": get_text("project_menu_view_yaml"), "value": "view_yaml", "disabled": not has_yaml},
        {"name": get_text("project_menu_open_location"), "value": "open_location", "disabled": not (has_json or has_yaml)},
        {"name": get_text("main_menu_back"), "value": "back"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        fetch_project_data(user, project)
        # Verileri indirdikten sonra tekrar menüyü göster ki seçenekler aktif olsun
        project_menu(user, project)
        return
    elif choice == "2" and not options[1]["disabled"]:
        change_tracking_menu(user, project, project_dir)
    elif choice == "3" and not options[2]["disabled"]:
        view_yaml_content(yaml_file)
    elif choice == "4" and not options[3]["disabled"]:
        open_file_location(project_dir)
    elif choice == "5" or choice == "back":
        return
    
    project_menu(user, project)


def fetch_project_data(user: Dict[str, Any], project: Dict[str, Any]) -> bool:
    """
    GitHub'dan proje verilerini indirir ve yapılandırılmış JSON/YAML dosyalarına kaydeder.
    Ayrıca issue içeriklerini analiz ederek parent-child ilişkilerini belirler.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        
    Returns:
        İşlemin başarılı olup olmadığı
    """
    from app.services.github_service import GitHubService
    from app.utils.project_organizer import ProjectOrganizer
    from app.utils.change_tracker import ChangeTracker
    import re
    
    # İşlem başlangıcını göster
    clear_screen()
    print_header(f"Proje Verilerini İndirme: {Colors.GITHUB}{project.get('name', '')}{Colors.RESET}")
    print_navigation(["Ana Menü", user['username'], project.get('name', ''), "Veri İndirme"])
    
    # GitHub servisini oluştur - PARAMETRELERIN SIRASI ÖNEMLİ, token ilk parametre
    gh_service = GitHubService(user["token"], user["username"])
    
    # Proje ID'sini al
    project_id = project.get("id", "")
    project_name = project.get("name", "")
    
    if not project_id:
        print_error("Geçersiz proje ID'si!")
        wait_for_enter()
        return False
    
    # Proje dizinini belirle
    projects_dir = os.path.join("data", "projects")
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir)
    
    # Proje adını klasör adına dönüştür
    safe_project_name = project_id
    if project_name:
        # Dosya sisteminde güvenli bir isim oluştur
        safe_name = project_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_project_name = f"{project_id}_{safe_name}"
    
    # Proje dizinini oluştur
    project_dir = os.path.join(projects_dir, safe_project_name)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    
    print_info(f"İndirilen veriler {project_dir} dizinine kaydedilecek")
    
    # Proje verilerini indir - ana akış başlıyor
    print_info(f"GitHub'dan proje verilerini indiriliyor: {project_name} (ID: {project_id})")
    
    try:
        # 1. GitHub token'ı kontrol et
        is_validated = gh_service.validate_token()
        
        if not is_validated:
            print_error("GitHub token doğrulanamadı. Token geçersiz olabilir veya süresi dolmuş olabilir.")
            print_info("Yeni bir token oluşturmak için: https://github.com/settings/tokens")
            print_info("Token'ı güncellemek ister misiniz? (E/H)")
            
            choice = input().strip().lower()
            if choice in ["e", "evet"]:
                update_token(user)
                print_info("Lütfen 'Proje Verilerini İndir' seçeneğini tekrar deneyin.")
                wait_for_enter()
                return False
            else:
                print_info("Token güncellenmedi. İşlem iptal edildi.")
                wait_for_enter()
                return False
        
        # 2. GraphQL API ile proje verilerini çek
        print_info("GraphQL API ile proje verileri çekiliyor...")
        project_data = gh_service.get_project_v2(project_id)
        
        # Hata kontrolü
        if isinstance(project_data, dict) and "error" in project_data:
            error_msg = project_data["error"]
            print_error(f"GitHub'dan veri alınırken hata: {error_msg}")
            
            # OAuth token hatası kontrolü
            if "authentication" in error_msg.lower() or "token" in error_msg.lower() or "failed" in error_msg.lower() or "oauth" in error_msg.lower():
                print_error("GitHub token hatası! GitHub API erişimi için yeterli izinler gereklidir.")
                # Token maskeli göster - sadece ilk 4 ve son 4 karakter
                masked_token = f"{user['token'][:4]}...{user['token'][-4:]}" if len(user['token']) > 8 else "****"
                print_info(f"Kullanılan token: {masked_token}")
                print_info("GraphQL API ve Projects v2 için özel izinler gereklidir:")
                print_info("1. Tokeni GitHub'da oluştururken 'repo' ve 'project' izinlerini seçtiğinizden emin olun")
                print_info("2. Klasik token (classic) seçeneğini kullanın")
                print_info("")
                print_info("Tokenınızı güncellemek ister misiniz? (E/H)")
                choice = input().strip().lower()
                
                if choice == "e" or choice == "evet":
                    # Token güncelleme fonksiyonunu çağır
                    print_info("Token güncelleme ekranına yönlendiriliyorsunuz...")
                    update_token(user)
                    
                    # Mevcut fonksiyondan çık
                    return False
            
            wait_for_enter()
            return False
        
        # Empty data check
        if not project_data or not isinstance(project_data, dict) or not project_data:
            print_error("Proje verileri indirilemedi. Boş veya geçersiz veri alındı.")
            wait_for_enter()
            return False
        
        # Parent issue ilişkilerini analiz et
        try:
            print_info("Issue içeriklerini analiz ederek parent ilişkileri tespit ediliyor...")
            project_data = gh_service.post_process_project_items(project_data)
        except Exception as e:
            print_warning(f"Issue ilişkileri analiz edilirken hata oluştu: {str(e)}")
        
        print_success(f"Proje verileri başarıyla indirildi: {len(project_data.get('items', []))} öğe")
        
        # Project Organizer ile verileri düzenli bir yapıya dönüştür
        print_info("Proje verileri düzenli bir yapıya dönüştürülüyor...")
        organizer = ProjectOrganizer(project_dir)
        if not organizer.organize(project_data):
            print_error("Proje verilerini düzenli yapıya dönüştürme başarısız oldu!")
            wait_for_enter()
            return False
        
        # İndirilen verileri orijinal durum olarak kaydediyoruz (referans durumu)
        # Bu, ilk indirmeden sonra değişiklik olarak algılanmasını önler
        print_info("Referans durumu için orijinal verileri kaydediyoruz...")
        
        # ChangeTracker oluştur ve orijinal durumu kaydet
        tracker = ChangeTracker(project_dir)
        if tracker.capture_original_state(project_data):
            print_success("Orijinal durum kaydedildi. Değişiklik tespiti artık doğru çalışacak.")
        else:
            print_warning("Orijinal durum kaydedilemedi. Değişiklik takibi etkilenebilir.")
        
        print_success("İşlem tamamlandı. Proje verileri başarıyla indirildi ve düzenlendi.")
        if not project.get("local_path"):
            # Yerel yolu güncelle
            project["local_path"] = project_dir
            
            # Kullanıcının projelerini güncelle
            for i, p in enumerate(user.get("projects", [])):
                if p.get("id") == project_id:
                    user["projects"][i] = project
                    break
                
            # Kullanıcı bilgilerini kaydet
            from app.services.user_service import UserService
            UserService.save_user(user)
            
        print_info(f"Proje verileri yerel diskten kullanılabilir: {project_dir}")
        print_info("Ana menüye döndüğünüzde tüm proje seçenekleri aktif olacaktır.")
        wait_for_enter()
        return True
        
    except Exception as e:
        print_error(f"Proje verileri indirilirken hata oluştu: {str(e)}")
        wait_for_enter()
        return False


def send_latest_to_github(user: Dict[str, Any], project: Dict[str, Any]):
    """En son değiştirilen dosyayı GitHub'a gönderir.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
    """
    print_info(f"En son değiştirilen dosya GitHub'a gönderiliyor: {project['name']}")
    
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Senkronizasyon servisini oluştur
        sync_service = SyncService(github_service)
        
        # Proje dizinini al
        project_id = project["id"]
        project_name = project["name"]
        project_dir = os.path.join(sync_service.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        
        # JSON ve YAML dosyalarını kontrol et
        json_file = os.path.join(project_dir, "project.json")
        yaml_file = os.path.join(project_dir, "project.yaml")
        
        json_exists = os.path.exists(json_file)
        yaml_exists = os.path.exists(yaml_file)
        
        if not json_exists and not yaml_exists:
            print_error("Hiçbir dosya bulunamadı!")
            print_info("Önce 'GitHub'dan Çek' seçeneğini kullanarak verileri çekmelisiniz.")
            return False
        
        # Dosyaların son değiştirilme zamanlarını kontrol et
        json_time = os.path.getmtime(json_file) if json_exists else 0
        yaml_time = os.path.getmtime(yaml_file) if yaml_exists else 0
        
        # En son değiştirilen dosyayı belirle
        if json_time > yaml_time:
            print_info(f"JSON dosyası daha güncel. Son güncelleme: {datetime.fromtimestamp(json_time).strftime('%Y-%m-%d %H:%M:%S')}")
            return sync_json_to_github(user, project)
        else:
            print_info(f"YAML dosyası daha güncel. Son güncelleme: {datetime.fromtimestamp(yaml_time).strftime('%Y-%m-%d %H:%M:%S')}")
            return sync_yaml_to_github(user, project)
    except Exception as e:
        print_error(f"En son değiştirilen dosya GitHub'a gönderilirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        return False


def sync_yaml_to_github(user: Dict[str, Any], project: Dict[str, Any], yaml_file: str) -> bool:
    """YAML dosyasını GitHub'a senkronize eder.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        yaml_file: YAML dosya yolu
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # YAML dosyasını kontrol et
        if not os.path.exists(yaml_file):
            print_error("YAML dosyası bulunamadı!")
            return False
        
        # YAML dosyasını oku
        with open(yaml_file, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        
        # YAML'ı JSON'a dönüştür
        from app.utils.yaml_converter import yaml_to_json
        json_data = yaml_to_json(yaml_content)
        
        # GitHub'dan proje bilgilerini kontrol et
        project_id = project["id"]
        
        # API versiyonuna göre proje bilgilerini al
        if project.get("is_v2", False):
            github_project = github_service.get_project_v2(project_id)
        else:
            github_project = github_service.get_project(project_id)
        
        if not github_project:
            print_error(f"GitHub'da proje bulunamadı: {project_id}")
            print_info("Proje silinmiş veya erişim izniniz olmayabilir.")
            return False
        
        # Proje adını kontrol et
        github_project_name = github_project.get("title", github_project.get("name", ""))
        local_project_name = project.get("title", project.get("name", ""))
        
        print_info(f"GitHub'da proje bulundu: {github_project_name}")
        print_info(f"Lokal proje: {local_project_name}")
        
        # Kullanıcıya onay sor
        print_info("\nVerilerin gönderilmesi için onaylayın (e/h)?")
        confirm = input("> ").strip().lower()
        
        if confirm != "e":
            print_info("İşlem iptal edildi.")
            return False
        
        # GitHub'a gönder
        success = github_service.update_project_v2(project_id, json_data)
        
        if success:
            print_success("YAML dosyası GitHub'a senkronize edildi.")
            
            # JSON dosyasını da güncelle
            json_file = os.path.join(os.path.dirname(yaml_file), "project.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print_success("JSON dosyası güncellendi.")
            
            return True
        else:
            print_error("YAML dosyası GitHub'a senkronize edilemedi.")
            return False
    except Exception as e:
        print_error(f"YAML dosyası GitHub'a senkronize edilirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        return False


def sync_json_to_github(user: Dict[str, Any], project: Dict[str, Any], json_file: str) -> bool:
    """JSON dosyasını GitHub'a senkronize eder.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        json_file: JSON dosya yolu
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # JSON dosyasını kontrol et
        if not os.path.exists(json_file):
            print_error("JSON dosyası bulunamadı!")
            return False
        
        # JSON dosyasını oku
        with open(json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        # GitHub'dan proje bilgilerini kontrol et
        project_id = project["id"]
        
        # API versiyonuna göre proje bilgilerini al
        if project.get("is_v2", False):
            github_project = github_service.get_project_v2(project_id)
        else:
            github_project = github_service.get_project(project_id)
        
        if not github_project:
            print_error(f"GitHub'da proje bulunamadı: {project_id}")
            print_info("Proje silinmiş veya erişim izniniz olmayabilir.")
            return False
        
        # Proje adını kontrol et
        github_project_name = github_project.get("title", github_project.get("name", ""))
        local_project_name = project.get("title", project.get("name", ""))
        
        print_info(f"GitHub'da proje bulundu: {github_project_name}")
        print_info(f"Lokal proje: {local_project_name}")
        
        # Kullanıcıya onay sor
        print_info("\nVerilerin gönderilmesi için onaylayın (e/h)?")
        confirm = input("> ").strip().lower()
        
        if confirm != "e":
            print_info("İşlem iptal edildi.")
            return False
        
        # GitHub'a gönder
        success = github_service.update_project_v2(project_id, json_data)
        
        if success:
            print_success("JSON dosyası GitHub'a senkronize edildi.")
            
            # YAML dosyasını da güncelle
            yaml_file = os.path.join(os.path.dirname(json_file), "project.yaml")
            from app.utils.yaml_converter import json_to_yaml
            yaml_content = json_to_yaml(json_data)
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            print_success("YAML dosyası güncellendi.")
            
            return True
        else:
            print_error("JSON dosyası GitHub'a senkronize edilemedi.")
            return False
    except Exception as e:
        print_error(f"JSON dosyası GitHub'a senkronize edilirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        return False


def view_yaml_content(yaml_file: str) -> bool:
    """YAML içeriğini görüntüler.
    
    Args:
        yaml_file: YAML dosya yolu
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # YAML dosyasını kontrol et
        if not os.path.exists(yaml_file):
            print_error("YAML dosyası bulunamadı!")
            return False
        
        # YAML dosyasını oku
        with open(yaml_file, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        
        print_info("\nYAML İçeriği:")
        print(yaml_content)
        
        return True
    except Exception as e:
        print_error(f"YAML içeriği görüntülenirken hata oluştu: {str(e)}")
        return False


def open_file_location(path: str) -> bool:
    """Dosya konumunu açar.
    
    Args:
        path: Açılacak dosya veya dizin yolu
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # Linux, macOS
            if sys.platform == 'darwin':  # macOS
                subprocess.call(['open', path])
            else:  # Linux
                subprocess.call(['xdg-open', path])
        else:
            print_error(f"İşletim sistemi desteklenmiyor: {os.name}")
            return False
        
        return True
    except Exception as e:
        print_error(f"Dosya konumu açılırken hata oluştu: {str(e)}")
        return False


def get_user_repositories(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get user repositories from GitHub or cache.
    
    Args:
        user: User information
        
    Returns:
        List of repositories
    """
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Cache dizinini oluştur
        cache_dir = os.path.join("data", "repositories")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache dosyası
        cache_file = os.path.join(cache_dir, f"{user['username']}-repos-cache.json")
        
        # If cache file exists and is less than 1 hour old, read from cache
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600:  # 1 hour = 3600 seconds
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        repositories = json.load(f)
                        print_github_info(f"Cache'den {len(repositories)} repo yüklendi.")
                        return repositories
                except Exception as e:
                    print_warning(f"Cache okuma hatası: {str(e)}")
        
        # GitHub'dan repoları al
        print_github_info("GitHub'dan repolar alınıyor...")
        repositories = github_service.get_repositories()
        
        # Repoları cache'e kaydet
        if repositories:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(repositories, f, ensure_ascii=False, indent=2)
                print_github_info(f"Repolar cache'e kaydedildi: {cache_file}")
            except Exception as e:
                print_warning(f"Cache yazma hatası: {str(e)}")
        
        return repositories
    except Exception as e:
        print_error(f"Repolar alınırken hata oluştu: {str(e)}")
        return []


def update_repository(user: Dict[str, Any], repository: Dict[str, Any]) -> Dict[str, Any]:
    """Repository bilgilerini GitHub'dan günceller.
    
    Args:
        user: Kullanıcı bilgileri
        repository: Repository bilgileri
        
    Returns:
        Güncellenmiş repository bilgileri
    """
    try:
        print_github_info(f"Repository bilgileri güncelleniyor: {repository['name']}...")
        
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Repository bilgilerini al
        repo_owner = repository["owner"]["login"]
        repo_name = repository["name"]
        
        # GitHub'dan repository bilgilerini çek
        updated_repo = github_service.get_repository(repo_owner, repo_name)
        
        if not updated_repo:
            print_error(f"Repository bilgileri alınamadı: {repo_name}")
            return repository
        
        print_success(f"Repository bilgileri güncellendi: {repo_name}")
        
        # Cache dosyasını güncelle
        try:
            cache_dir = os.path.join("data", "repositories")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Cache dosyası
            cache_file = os.path.join(cache_dir, f"{user['username']}-repos-cache.json")
            
            # Cache dosyası varsa, içindeki repository'yi güncelle
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    repositories = json.load(f)
                
                # Repository'yi güncelle
                for i, repo in enumerate(repositories):
                    if repo.get("id") == repository.get("id"):
                        repositories[i] = updated_repo
                        break
                
                # Cache'i güncelle
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(repositories, f, ensure_ascii=False, indent=2)
                
                print_github_info(f"Repository cache güncellendi: {cache_file}")
        except Exception as e:
            print_warning(f"Cache güncellenirken hata oluştu: {str(e)}")
        
        return updated_repo
    except Exception as e:
        print_error(f"Repository güncellenirken hata oluştu: {str(e)}")
        return repository


def change_tracking_menu(user, project, project_dir):
    """
    Değişiklik yönetimi menüsünü görüntüler ve değişikliklerle ilgili işlemleri yönetir.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        project_dir: Proje dizini
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Başlığı ve gezinme yolunu göster
    print("=" * 80)
    print("Değişiklik Takip: " + project.get("title", ""))
    print("=" * 80)
    print(f"Navigasyon: Ana Menü > {user['username']} > {project.get('title', '')} > Değişiklik Takip")
    
    # Değişiklikleri algıla
    print("Yerel dosyalar taranıyor...")
    
    from app.utils.change_tracker import ChangeTracker
    
    tracker = ChangeTracker(
        project_dir=project_dir,
        project_id=project.get("id", ""),
        project_name=project.get("title", ""),
        auto_save=True  # Değişiklikleri otomatik kaydet
    )
    
    # Yerel dosyaları tara
    print("Yerel dosyaları taranıyor...")
    tracker.scan_current_state()
    
    # Değişiklikleri algıla
    print("Değişiklikler tespit ediliyor...")
    changes = tracker.detect_changes()
    
    # Değişiklikleri göster
    total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Başlığı ve gezinme yolunu göster
        print("=" * 80)
        print("Değişiklik Takip: " + project.get("title", ""))
        print("=" * 80)
        print(f"Navigasyon: Ana Menü > {user['username']} > {project.get('title', '')} > Değişiklik Takip")
        
        print(f"\nToplam değişiklik sayısı: {total_changes}")
        print(f"- Eklenen: {len(changes['created'])}")
        print(f"- Güncellenen: {len(changes['updated'])}")
        print(f"- Silinen: {len(changes['deleted'])}")
        
        if total_changes == 0:
            print("\nSeçenekler:")
            print("  1. Yerel değişiklikleri tekrar algıla")
            print("  2. GitHub'dan değişiklikleri kontrol et")
            print("  3. Geri")
            
            choice = input("\nSeçiminizi girin (1-3): ")
            
            if choice == "1":
                # Değişiklikleri yeniden algıla
                print("Yerel dosyaları taranıyor...")
                tracker.scan_current_state()
                
                print("Değişiklikler tespit ediliyor...")
                changes = tracker.detect_changes()
                
                total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
                input("\nDevam etmek için Enter'a basın...")
            elif choice == "2":
                # GitHub'dan değişiklikleri kontrol et (henüz uygulanmadı)
                print("\nBu özellik henüz uygulanmadı.")
                input("\nDevam etmek için Enter'a basın...")
            elif choice == "3":
                # Projeye geri dön
                return
            else:
                print("\nGeçersiz seçim. Lütfen tekrar deneyin.")
                input("\nDevam etmek için Enter'a basın...")
        else:
            # Değişiklikler varsa farklı bir menü göster
            print("\nSeçenekler:")
            print("  1. Değişiklikleri görüntüle")
            print("  2. Değişiklikleri GitHub'a gönder")
            print("  3. Değişiklikleri yok say")
            print("  4. Başlık tutarsızlıklarını düzelt")
            print("  5. Geri")
            
            choice = input("\nSeçiminizi girin (1-5): ")
            
            if choice == "1":
                # Değişiklikleri görüntüle
                view_changes(changes)
                input("\nDevam etmek için Enter'a basın...")
            elif choice == "2":
                # Değişiklikleri GitHub'a gönder
                send_changes_menu(user, project, tracker, changes)
                # Değişiklikler gönderildikten sonra yeniden algıla
                print("Değişiklikler yeniden taranıyor...")
                tracker.scan_current_state()
                changes = tracker.detect_changes()
                total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
            elif choice == "3":
                # Değişiklikleri yok say
                print("\nDeğişiklikler yok sayılacak ve mevcut durum yeni başlangıç noktası olarak kaydedilecek.")
                confirm = input("Emin misiniz? (E/H): ")
                
                if confirm.upper() == "E":
                    tracker.save_current_as_original()
                    print("\nDeğişiklikler başarıyla yok sayıldı.")
                    # Değişiklikleri yeniden algıla (artık 0 olmalı)
                    changes = tracker.detect_changes()
                    total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
                
                input("\nDevam etmek için Enter'a basın...")
            elif choice == "4":
                # Başlık tutarsızlıklarını düzelt
                print("\nTüm sorun dosyalarındaki başlık tutarsızlıkları kontrol ediliyor...")
                updated_count = tracker.sync_all_issue_titles()
                print(f"\nToplam {updated_count} dosyada başlık tutarsızlığı düzeltildi.")
                
                if updated_count > 0:
                    # Değişiklikleri yeniden algıla
                    print("Değişiklikler yeniden taranıyor...")
                    tracker.scan_current_state()
                    changes = tracker.detect_changes()
                    total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
                
                input("\nDevam etmek için Enter'a basın...")
            elif choice == "5":
                # Projeye geri dön
                return
            else:
                print("\nGeçersiz seçim. Lütfen tekrar deneyin.")
                input("\nDevam etmek için Enter'a basın...")
    

def view_operation_list(user: Dict[str, Any], project: Dict[str, Any], project_dir: str):
    """
    Operasyon listesini görüntüler.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        project_dir: Proje dizini
    """
    from app.utils.operation_list import OperationList
    
    clear_screen()
    project_title = project.get('title', project.get('name', 'Unknown Project'))
    print_header(f"Operasyon Listesi: {Colors.GITHUB}{project_title}{Colors.RESET}")
    print_navigation(["Ana Menü", user['username'], project_title, "Değişiklik Takip", "Operasyon Listesi"])
    
    # Operasyon listesi nesnesi oluştur
    op_list = OperationList(project_dir)
    
    # Operasyonları al
    operations = op_list.get_operations()
    
    if not operations:
        print_info("Operasyon listesi boş.")
        print_info("Değişiklikleri onayladıktan sonra operasyon listesi otomatik olarak oluşturulacaktır.")
        wait_for_enter()
        return
    
    # Operasyonları listele
    print_info(f"\nToplam {len(operations)} operasyon bulundu:")
    print("\n{:<5} {:<15} {:<15} {:<50}".format("#", "Operasyon", "Durum", "Açıklama"))
    print("-" * 85)
    
    for i, op in enumerate(operations, 1):
        op_type = op["operation_type"]
        item_type = op["item_type"]
        status = op["status"]
        
        # Açıklama oluştur
        description = ""
        if item_type == "issue":
            if op_type == "create":
                description = f"Yeni issue oluşturulacak: {op['data'].get('title', '')}"
            elif op_type == "update":
                description = f"Issue #{op['data'].get('issue_number', '')} güncellenecek"
            elif op_type == "delete":
                description = f"Issue #{op['data'].get('issue_number', '')} silinecek"
        elif item_type == "milestone":
            if op_type == "create":
                description = f"Yeni milestone oluşturulacak: {op['data'].get('title', '')}"
            elif op_type == "update":
                description = f"Milestone #{op['data'].get('milestone_number', '')} güncellenecek"
            elif op_type == "delete":
                description = f"Milestone #{op['data'].get('milestone_number', '')} silinecek"
        
        # Durum rengini belirle
        if status == "pending":
            status_color = Colors.WARNING
        elif status == "completed":
            status_color = Colors.SUCCESS
        elif status == "failed":
            status_color = Colors.ERROR
        else:
            status_color = Colors.RESET
        
        print("{:<5} {:<15} {}{:<15}{} {:<50}".format(
            i, f"{op_type}_{item_type}", status_color, status, Colors.RESET, description[:50]))
    
    # Menü seçenekleri
    print(f"\n{Colors.BOLD}Seçenekler:{Colors.RESET}")
    print(f"  {Colors.BOLD}1.{Colors.RESET} Operasyon Listesini Temizle")
    print(f"  {Colors.BOLD}2.{Colors.RESET} Geri Dön")
    
    choice = input(f"\n{Colors.BOLD}Seçiminiz:{Colors.RESET} ").strip()
    
    if choice == "1":
        # Operasyon listesini temizle
        confirm = input(f"{Colors.WARNING}Tüm operasyonlar silinecek. Onaylıyor musunuz? (e/h):{Colors.RESET} ").strip().lower()
        if confirm == "e":
            op_list.clear_operations()
            print_success("Operasyon listesi temizlendi.")
    
    wait_for_enter()


def send_changes_to_github(user: Dict[str, Any], project: Dict[str, Any], project_dir: str):
    """
    Onaylanan değişiklikleri GitHub'a gönderir.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        project_dir: Proje dizini
    """
    from app.utils.operation_list import OperationList
    from app.utils.github_synchronizer import GitHubSynchronizer
    from app.services.github_service import GitHubService
    
    clear_screen()
    project_title = project.get('title', project.get('name', 'Unknown Project'))
    print_header(f"GitHub'a Gönder: {Colors.GITHUB}{project_title}{Colors.RESET}")
    print_navigation(["Ana Menü", user['username'], project_title, "Değişiklik Takip", "GitHub'a Gönder"])
    
    # Operasyon listesi nesnesi oluştur
    op_list = OperationList(project_dir)
    
    # Operasyonları al
    operations = op_list.get_operations(status="pending")
    
    if not operations:
        print_info("Gönderilecek değişiklik yok. Önce değişiklikleri onaylamalısınız.")
        wait_for_enter()
        return
    
    # Operasyonları listele
    print_info(f"\nToplam {len(operations)} operasyon GitHub'a gönderilecek:")
    print("\n{:<5} {:<15} {:<50}".format("#", "Operasyon", "Açıklama"))
    print("-" * 70)
    
    for i, op in enumerate(operations, 1):
        op_type = op["operation_type"]
        item_type = op["item_type"]
        
        # Açıklama oluştur
        description = ""
        if item_type == "issue":
            if op_type == "create":
                description = f"Yeni issue oluşturulacak: {op['data'].get('title', '')}"
            elif op_type == "update":
                description = f"Issue #{op['data'].get('issue_number', '')} güncellenecek"
            elif op_type == "delete":
                description = f"Issue #{op['data'].get('issue_number', '')} silinecek"
        elif item_type == "milestone":
            if op_type == "create":
                description = f"Yeni milestone oluşturulacak: {op['data'].get('title', '')}"
            elif op_type == "update":
                description = f"Milestone #{op['data'].get('milestone_number', '')} güncellenecek"
            elif op_type == "delete":
                description = f"Milestone #{op['data'].get('milestone_number', '')} silinecek"
        
        print("{:<5} {:<15} {:<50}".format(i, f"{op_type}_{item_type}", description[:50]))
    
    # Onay iste
    print(f"\n{Colors.WARNING}Uyarı: Bu işlem GitHub üzerinde gerçek değişiklikler yapacaktır.{Colors.RESET}")
    confirm = input(f"{Colors.BOLD}Değişiklikleri GitHub'a göndermek istiyor musunuz? (e/h):{Colors.RESET} ").strip().lower()
    
    if confirm != "e":
        print_info("İşlem iptal edildi.")
        wait_for_enter()
        return
    
    # GitHub servisini ve senkronizasyon nesnesini oluştur
    github_service = GitHubService(user["token"], user["username"])
    synchronizer = GitHubSynchronizer(project_dir, github_service)
    
    # İşlemleri gerçekleştir
    print_info("\nGitHub'a değişiklikler gönderiliyor...")
    results = synchronizer.execute_operations(operations)
    
    # Sonuçları göster
    print_info(f"\nToplam: {results['total_operations']}, Başarılı: {results['successful_operations']}, Başarısız: {results['failed_operations']}")
    
    if results['failed_operations'] > 0:
        print_error("Başarısız işlemler:")
        for op in results['operations']:
            if not op['success']:
                print(f"  {Colors.ERROR}- {op['operation_type']} {op['item_type']}: {op['result']}{Colors.RESET}")
    
    # İşlem başarılıysa, projenin en son halini tekrar indir
    if results['successful_operations'] > 0:
        print_info("\nProje verilerini GitHub'dan yeniden çekiyoruz...")
        fetch_project_data(user, project)
    
    wait_for_enter()


def main_menu() -> None:
    """Ana menüyü gösterir."""
    clear_screen()
    print_header(get_text("main_menu_title"))
    
    options = [
        {"name": get_text("main_menu_login"), "value": "login"},
        {"name": get_text("main_menu_list_users"), "value": "list_users"},
        {"name": get_text("main_menu_language"), "value": "language"},
        {"name": get_text("main_menu_about"), "value": "about"},
        {"name": get_text("main_menu_exit"), "value": "exit"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        login_user()
    elif choice == "2":
        list_users()
    elif choice == "3":
        language_menu()
    elif choice == "4":
        about()
    elif choice == "5":
        clear_screen()
        sys.exit(0)
    else:
        print_error(get_text("invalid_choice"))
        wait_for_enter()
    
    main_menu()


def about() -> None:
    """Uygulama hakkında bilgi gösterir."""
    clear_screen()
    print_header(get_text("about_title"))
    
    print(f"\n{Colors.BOLD}{get_text('about_description')}{Colors.RESET}\n")
    print(f"{Colors.BOLD}{get_text('about_version')}{Colors.RESET}")
    print(f"{Colors.BOLD}{get_text('about_author')}{Colors.RESET}")
    print(f"{Colors.BOLD}{get_text('about_license')}{Colors.RESET}")
    
    wait_for_enter()


def main():
    """Ana fonksiyon."""
    try:
        # Gerekli dizinleri oluştur
        os.makedirs("data", exist_ok=True)
        os.makedirs(os.path.join("data", "users"), exist_ok=True)
        os.makedirs(os.path.join("data", "repositories"), exist_ok=True)
        os.makedirs(os.path.join("data", "projects"), exist_ok=True)
        
        # Giriş menüsünü başlat
        main_menu()
    except KeyboardInterrupt:
        print_info("\nProgram kullanıcı tarafından sonlandırıldı.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Beklenmeyen bir hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        sys.exit(1)


def view_changes(changes):
    """
    Algılanan değişiklikleri görüntüler.
    
    Args:
        changes: Değişiklik bilgileri içeren sözlük
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Başlığı göster
    print("=" * 80)
    print("Değişiklik Görüntüleme")
    print("=" * 80)
    
    # Eklenen öğeleri göster
    if changes["created"]:
        print("\nEKLENEN ÖĞELER:")
        print("-" * 40)
        for i, item in enumerate(changes["created"], 1):
            print(f"{i}. {item.get('type', 'Bilinmeyen')} - {item.get('title', 'Başlık yok')}")
            if "file_path" in item:
                print(f"   Dosya: {item['file_path']}")
            print()
    
    # Güncellenen öğeleri göster
    if changes["updated"]:
        print("\nGÜNCELLENEN ÖĞELER:")
        print("-" * 40)
        for i, item in enumerate(changes["updated"], 1):
            print(f"{i}. {item.get('type', 'Bilinmeyen')} - {item.get('title', 'Başlık yok')}")
            if "file_path" in item:
                print(f"   Dosya: {item['file_path']}")
            
            # Değişen alanları göster
            if "changes" in item:
                print("   Değişen alanlar:")
                for field, change in item["changes"].items():
                    old_val = change.get("old", "")
                    new_val = change.get("new", "")
                    
                    # Uzun değerleri kısalt
                    if isinstance(old_val, str) and len(old_val) > 50:
                        old_val = old_val[:47] + "..."
                    if isinstance(new_val, str) and len(new_val) > 50:
                        new_val = new_val[:47] + "..."
                        
                    print(f"   - {field}: '{old_val}' -> '{new_val}'")
            print()
    
    # Silinen öğeleri göster
    if changes["deleted"]:
        print("\nSİLİNEN ÖĞELER:")
        print("-" * 40)
        for i, item in enumerate(changes["deleted"], 1):
            print(f"{i}. {item.get('type', 'Bilinmeyen')} - {item.get('title', 'Başlık yok')}")
            print()

def send_changes_menu(user, project, tracker, changes):
    """
    Değişiklikleri GitHub'a gönderme menüsünü gösterir.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        tracker: ChangeTracker nesnesi
        changes: Değişiklik bilgileri içeren sözlük
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Başlığı göster
    print("=" * 80)
    print("Değişiklikleri GitHub'a Gönder")
    print("=" * 80)
    
    total_changes = len(changes["created"]) + len(changes["updated"]) + len(changes["deleted"])
    print(f"\nToplam {total_changes} değişiklik tespit edildi:")
    print(f"- {len(changes['created'])} eklenen öğe")
    print(f"- {len(changes['updated'])} güncellenen öğe")
    print(f"- {len(changes['deleted'])} silinen öğe")
    
    print("\nBu fonksiyon henüz uygulanmadı. GitHub API entegrasyonu geliştirilmektedir.")
    print("Değişiklikler şu anda yalnızca yerel olarak izlenebilir.")
    
    input("\nDevam etmek için Enter'a basın...")


if __name__ == "__main__":
    main() 