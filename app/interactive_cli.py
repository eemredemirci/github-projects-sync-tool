"""
GitHub Proje Yönetim Aracı için etkileşimli komut satırı arayüzü.
"""
import os
import sys
import time
import json
import yaml
import shutil
import copy
from typing import Dict, List, Any, Optional, Callable
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
    DISABLED = "\033[90m"  # Gray color


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
    """Token günceller.
    
    Args:
        user: Kullanıcı bilgileri
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # Navigasyon
        print_header("Token Güncelle")
        print_navigation(["Ana Menü", user['username'], "Token Güncelle"])
        
        # Show current token (masked)
        current_token = user["token"]
        masked_token = current_token[:4] + "*" * (len(current_token) - 8) + current_token[-4:]
        print_info(get_text('current_token').format(masked_token))
        
        # Get new token
        print_info("\n" + get_text('new_token_prompt'))
        new_token = getpass.getpass(get_text('new_token_prompt') + ": ")
        
        if not new_token:
            print_info(get_text('token_not_changed'))
            wait_for_enter(True)
            return False
        
        # Validate token
        github_service = GitHubService(new_token)
        user_info = github_service.get_user()
        
        if not user_info:
            print_error(get_text('token_invalid_error'))
            wait_for_enter(True)
            return False
        
        # Kullanıcı adını kontrol et
        username = user_info.get("login")
        
        if username != user["username"]:
            print_error(f"Token farklı bir kullanıcıya ait: {username}")
            print_error(f"Beklenen kullanıcı: {user['username']}")
            wait_for_enter(True)
            return False
        
        # Token'ı güncelle
        user["token"] = new_token
        
        # Kullanıcı dosyasını güncelle
        users_dir = os.path.join("data", "users")
        user_file = os.path.join(users_dir, f"{user['username']}.json")
        
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(user, f, indent=2, ensure_ascii=False)
        
        print_success("Token güncellendi.")
        
        # Cache dosyalarını sil
        try:
            # Repo cache dosyalarını sil
            repo_cache_dir = os.path.join("data", "repositories")
            if os.path.exists(repo_cache_dir):
                repo_cache_files = [f for f in os.listdir(repo_cache_dir) if f.startswith(f"{user['username']}-repos-")]
                for cache_file in repo_cache_files:
                    os.remove(os.path.join(repo_cache_dir, cache_file))
                    print_info(f"Repo cache dosyası silindi: {cache_file}")
            
            # Eski repository project cache dosyalarını sil
            old_repo_projects_cache_dir = os.path.join("data", "repositories", "projects")
            if os.path.exists(old_repo_projects_cache_dir):
                for file in os.listdir(old_repo_projects_cache_dir):
                    if file.endswith("_projects_cache.json"):
                        os.remove(os.path.join(old_repo_projects_cache_dir, file))
                        print_info(f"Eski proje cache dosyası silindi: {file}")
            
            # Proje cache dosyalarını sil
            project_cache_dir = os.path.join("data", "projects")
            if os.path.exists(project_cache_dir):
                project_cache_files = [f for f in os.listdir(project_cache_dir) if f.startswith(f"{user['username']}-")]
                for cache_file in project_cache_files:
                    os.remove(os.path.join(project_cache_dir, cache_file))
                    print_info(f"Proje cache dosyası silindi: {cache_file}")
            
            print_info("Tüm cache dosyaları silindi.")
        except Exception as e:
            print_error(f"Cache dosyaları silinirken hata oluştu: {str(e)}")
        
        wait_for_enter(True)
        return True
    except Exception as e:
        print_error(f"Token güncellenirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
        wait_for_enter(True)
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
    
    # Proje dosyalarını kontrol et
    project_dir = os.path.join("data", "projects", f"{project['id']}_{project['name']}")
    json_file = os.path.join(project_dir, "project.json")
    yaml_file = os.path.join(project_dir, "project.yaml")
    
    has_json = os.path.exists(json_file)
    has_yaml = os.path.exists(yaml_file)
    
    if has_json or has_yaml:
        print(f"\n{Colors.BOLD}{get_text('local_files')}{Colors.RESET}")
        if has_json:
            print(f"{Colors.LOCAL}JSON:{Colors.RESET} {json_file}")
        if has_yaml:
            print(f"{Colors.LOCAL}YAML:{Colors.RESET} {yaml_file}")
    
    options = [
        {"name": get_text("project_menu_fetch"), "value": "fetch"},
        {"name": get_text("project_menu_send_to_github"), "value": "send_to_github", "disabled": not (has_json or has_yaml)},
        {"name": get_text("project_menu_sync_yaml"), "value": "sync_yaml", "disabled": not has_yaml},
        {"name": get_text("project_menu_sync_json"), "value": "sync_json", "disabled": not has_json},
        {"name": get_text("project_menu_view_yaml"), "value": "view_yaml", "disabled": not has_yaml},
        {"name": get_text("project_menu_open_location"), "value": "open_location", "disabled": not (has_json or has_yaml)},
        {"name": get_text("main_menu_back"), "value": "back"}
    ]
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice == "1":
        fetch_project_data(user, project)
    elif choice == "2" and (has_json or has_yaml):
        send_latest_to_github(user, project)
    elif choice == "3" and has_yaml:
        sync_yaml_to_github(user, project, yaml_file)
    elif choice == "4" and has_json:
        sync_json_to_github(user, project, json_file)
    elif choice == "5" and has_yaml:
        view_yaml_content(yaml_file)
    elif choice == "6" and (has_json or has_yaml):
        open_file_location(project_dir)
    elif choice == "7" or choice == "back":
        return
    
    project_menu(user, project)


def fetch_project_data(user: Dict[str, Any], project: Dict[str, Any]) -> bool:
    """GitHub'dan proje verilerini çeker ve JSON/YAML olarak kaydeder.
    
    Args:
        user: Kullanıcı bilgileri
        project: Proje bilgileri
        
    Returns:
        bool: İşlem başarılı mı
    """
    try:
        # GitHub servisini oluştur
        github_service = GitHubService(user["token"], user["username"])
        
        # Senkronizasyon servisini oluştur
        sync_service = SyncService(github_service)
        
        # Proje verilerini çek
        project_id = project["id"]
        project_name = project.get("title", project.get("name", ""))
        
        print_github_info(f"GitHub'dan proje verileri çekiliyor: {project_name}")
        
        # GitHub'dan proje verilerini al
        github_data = github_service.get_project_v2(project_id)
        
        if not github_data:
            print_error(f"Proje verileri çekilemedi: {project_name}")
            print_info("Proje silinmiş veya erişim izniniz olmayabilir.")
            return False
        
        # Proje dizinini oluştur
        project_dir = os.path.join(sync_service.projects_dir, f"{project_id}_{project_name.replace(' ', '_').replace('/', '_')}")
        os.makedirs(project_dir, exist_ok=True)
        
        # Tarih bilgisini al
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON olarak kaydet
        json_file = os.path.join(project_dir, f"project_{current_date}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)
        print_success(f"JSON dosyası kaydedildi: {shorten_path(json_file)}")
        
        # Sembolik link oluştur (her zaman en son dosyayı gösterecek)
        latest_json_file = os.path.join(project_dir, "project.json")
        if os.path.exists(latest_json_file):
            os.remove(latest_json_file)
        
        # Dosyayı kopyala
        shutil.copy2(json_file, latest_json_file)
        print_info(f"En son JSON dosyası güncellendi: {shorten_path(latest_json_file)}")
        
        # YAML olarak kaydet
        yaml_file = os.path.join(project_dir, f"project_{current_date}.yaml")
        
        # JSON'ı YAML'a dönüştür
        import yaml
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(github_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print_success(f"YAML dosyası kaydedildi: {shorten_path(yaml_file)}")
        
        # Sembolik link oluştur (her zaman en son dosyayı gösterecek)
        latest_yaml_file = os.path.join(project_dir, "project.yaml")
        if os.path.exists(latest_yaml_file):
            os.remove(latest_yaml_file)
        
        # Dosyayı kopyala
        shutil.copy2(yaml_file, latest_yaml_file)
        print_info(f"En son YAML dosyası güncellendi: {shorten_path(latest_yaml_file)}")
        
        # Proje adı değişmiş mi kontrol et
        github_project_name = github_data.get("title", github_data.get("name", ""))
        if github_project_name and github_project_name != project_name:
            print_info(f"Proje adı değişmiş: {project_name} -> {github_project_name}")
            if "title" in project:
                project["title"] = github_project_name
            if "name" in project:
                project["name"] = github_project_name
        
        return True
    except Exception as e:
        print_error(f"Proje verileri çekilirken hata oluştu: {str(e)}")
        import traceback
        print_error(f"Hata detayı: {traceback.format_exc()}")
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


if __name__ == "__main__":
    main() 