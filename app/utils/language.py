"""
Language support module for GitHub Project Sync Tool.
"""
import os
import json
from typing import Dict, Any

# Default language
DEFAULT_LANGUAGE = "en"

# Available languages
LANGUAGES = {
    "en": "English",
    "tr": "Türkçe"
}

# Path to store language preference
LANGUAGE_FILE = os.path.join("data", "language.json")

# Current language
current_language = DEFAULT_LANGUAGE

# Translations
translations = {
    # Main Menu
    "main_menu_title": {
        "en": "GitHub Project Sync Tool",
        "tr": "GitHub Proje Senkronizasyon Aracı"
    },
    "main_menu_login": {
        "en": "User Login",
        "tr": "Kullanıcı Girişi"
    },
    "main_menu_list_users": {
        "en": "List Users",
        "tr": "Kullanıcıları Listele"
    },
    "main_menu_about": {
        "en": "About",
        "tr": "Hakkında"
    },
    "main_menu_language": {
        "en": "Change Language",
        "tr": "Dil Değiştir"
    },
    "main_menu_exit": {
        "en": "Exit",
        "tr": "Çıkış"
    },
    "main_menu_back": {
        "en": "Back",
        "tr": "Geri"
    },
    
    # Language Menu
    "language_menu_title": {
        "en": "Select Language",
        "tr": "Dil Seçin"
    },
    "language_changed": {
        "en": "Language changed to English",
        "tr": "Dil Türkçe olarak değiştirildi"
    },
    
    # User Menu
    "user_menu_title": {
        "en": "User Menu",
        "tr": "Kullanıcı Menüsü"
    },
    "user_menu_repositories": {
        "en": "Repositories",
        "tr": "Repolar"
    },
    "user_menu_github_projects": {
        "en": "GitHub Projects",
        "tr": "GitHub Projeleri"
    },
    "user_menu_local_projects": {
        "en": "Local Projects",
        "tr": "Yerel Projeler"
    },
    "user_menu_update_from_github": {
        "en": "Update from GitHub",
        "tr": "GitHub'dan Güncelle"
    },
    "user_menu_update_token": {
        "en": "Update Token",
        "tr": "Token Güncelle"
    },
    
    # User Actions
    "user_actions_title": {
        "en": "User Actions",
        "tr": "Kullanıcı İşlemleri"
    },
    "user_actions_login": {
        "en": "Login",
        "tr": "Giriş Yap"
    },
    "user_actions_set_default": {
        "en": "Set as Default",
        "tr": "Varsayılan Olarak Ayarla"
    },
    "user_actions_update_token": {
        "en": "Update Token",
        "tr": "Token Güncelle"
    },
    "user_actions_delete": {
        "en": "Delete User",
        "tr": "Kullanıcıyı Sil"
    },
    
    # Repository Menu
    "repository_menu_title": {
        "en": "Repository Menu",
        "tr": "Repo Menüsü"
    },
    "repository_menu_list_projects": {
        "en": "List GitHub Projects",
        "tr": "GitHub Projelerini Listele"
    },
    "repository_menu_update": {
        "en": "Update Repository",
        "tr": "Repoyu Güncelle"
    },
    "repository_menu_open_browser": {
        "en": "Open in Browser",
        "tr": "Tarayıcıda Aç"
    },
    
    # Project Menu
    "project_menu_title": {
        "en": "Project Menu",
        "tr": "Proje Menüsü"
    },
    "project_menu_fetch": {
        "en": "Fetch Project Data",
        "tr": "Proje Verilerini İndir"
    },
    "project_menu_send_to_github": {
        "en": "Send Latest to GitHub",
        "tr": "Son Değişiklikleri GitHub'a Gönder"
    },
    "project_menu_sync_yaml": {
        "en": "Sync YAML to GitHub",
        "tr": "YAML'ı GitHub'a Senkronize Et"
    },
    "project_menu_sync_json": {
        "en": "Sync JSON to GitHub",
        "tr": "JSON'ı GitHub'a Senkronize Et"
    },
    "project_menu_view_yaml": {
        "en": "View YAML Content",
        "tr": "YAML İçeriğini Görüntüle"
    },
    "project_menu_open_location": {
        "en": "Open File Location",
        "tr": "Dosya Konumunu Aç"
    },
    
    # Messages
    "enter_choice": {
        "en": "Enter your choice",
        "tr": "Seçiminizi girin"
    },
    "invalid_choice": {
        "en": "Invalid choice. Please try again.",
        "tr": "Geçersiz seçim. Lütfen tekrar deneyin."
    },
    "press_enter": {
        "en": "Press Enter to continue...",
        "tr": "Devam etmek için Enter'a basın..."
    },
    "loading": {
        "en": "Loading...",
        "tr": "Yükleniyor..."
    },
    "success": {
        "en": "Success!",
        "tr": "Başarılı!"
    },
    "error": {
        "en": "Error!",
        "tr": "Hata!"
    },
    "warning": {
        "en": "Warning!",
        "tr": "Uyarı!"
    },
    "info": {
        "en": "Info",
        "tr": "Bilgi"
    },
    "confirm": {
        "en": "Are you sure? (y/n)",
        "tr": "Emin misiniz? (e/h)"
    },
    "yes": {
        "en": "y",
        "tr": "e"
    },
    "no": {
        "en": "n",
        "tr": "h"
    },
    
    # User Management
    "enter_username": {
        "en": "Enter GitHub username",
        "tr": "GitHub kullanıcı adını girin"
    },
    "enter_token": {
        "en": "Enter GitHub token",
        "tr": "GitHub token'ını girin"
    },
    "token_validation_success": {
        "en": "Token validated successfully!",
        "tr": "Token başarıyla doğrulandı!"
    },
    "token_validation_error": {
        "en": "Token validation failed!",
        "tr": "Token doğrulaması başarısız!"
    },
    "user_added": {
        "en": "User added successfully!",
        "tr": "Kullanıcı başarıyla eklendi!"
    },
    "user_deleted": {
        "en": "User deleted successfully!",
        "tr": "Kullanıcı başarıyla silindi!"
    },
    "user_set_default": {
        "en": "User set as default successfully!",
        "tr": "Kullanıcı başarıyla varsayılan olarak ayarlandı!"
    },
    "user_not_found": {
        "en": "User not found!",
        "tr": "Kullanıcı bulunamadı!"
    },
    "no_users": {
        "en": "No users found. Please add a user first.",
        "tr": "Kullanıcı bulunamadı. Lütfen önce bir kullanıcı ekleyin."
    },
    "default_user": {
        "en": "Default User",
        "tr": "Varsayılan Kullanıcı"
    },
    
    # Repository Management
    "fetching_repositories": {
        "en": "Fetching repositories from GitHub...",
        "tr": "GitHub'dan repolar alınıyor..."
    },
    "no_repositories": {
        "en": "No repositories found.",
        "tr": "Repo bulunamadı."
    },
    "repository_updated": {
        "en": "Repository updated successfully!",
        "tr": "Repo başarıyla güncellendi!"
    },
    "loading_from_cache": {
        "en": "Loading {} repositories from cache...",
        "tr": "Önbellekten {} repo yükleniyor..."
    },
    
    # Project Management
    "fetching_projects": {
        "en": "Fetching projects from GitHub...",
        "tr": "GitHub'dan projeler alınıyor..."
    },
    "no_projects": {
        "en": "No projects found.",
        "tr": "Proje bulunamadı."
    },
    "project_fetched": {
        "en": "Project data fetched successfully!",
        "tr": "Proje verileri başarıyla indirildi!"
    },
    "project_sent": {
        "en": "Project sent to GitHub successfully!",
        "tr": "Proje başarıyla GitHub'a gönderildi!"
    },
    "loading_projects_from_cache": {
        "en": "Loading {} projects from cache...",
        "tr": "Önbellekten {} proje yükleniyor..."
    },
    "confirm_send_to_github": {
        "en": "Are you sure you want to send this project to GitHub? This will overwrite the project on GitHub. (y/n)",
        "tr": "Bu projeyi GitHub'a göndermek istediğinizden emin misiniz? Bu, GitHub'daki projenin üzerine yazacaktır. (e/h)"
    },
    
    # Cache Management
    "cache_updated": {
        "en": "Cache updated successfully!",
        "tr": "Önbellek başarıyla güncellendi!"
    },
    "cache_cleared": {
        "en": "Cache cleared successfully!",
        "tr": "Önbellek başarıyla temizlendi!"
    },
    
    # About
    "about_title": {
        "en": "About GitHub Project Sync Tool",
        "tr": "GitHub Proje Senkronizasyon Aracı Hakkında"
    },
    "about_description": {
        "en": "GitHub Project Sync Tool is a command-line tool that allows you to manage and synchronize GitHub Projects locally. With this tool, you can download GitHub projects in JSON and YAML formats, edit them locally, and send changes back to GitHub.",
        "tr": "GitHub Proje Senkronizasyon Aracı, GitHub Projects'i yerel olarak yönetmenize ve senkronize etmenize olanak tanıyan bir komut satırı aracıdır. Bu araç sayesinde GitHub projelerinizi JSON ve YAML formatında indirebilir, düzenleyebilir ve değişiklikleri GitHub'a gönderebilirsiniz."
    },
    "about_version": {
        "en": "Version: 1.0.0",
        "tr": "Sürüm: 1.0.0"
    },
    "about_author": {
        "en": "Author: GitHub Project Sync Tool Team",
        "tr": "Yazar: GitHub Proje Senkronizasyon Aracı Ekibi"
    },
    "about_license": {
        "en": "License: MIT",
        "tr": "Lisans: MIT"
    },
    
    # Navigation
    "navigation_main_menu": {
        "en": "Main Menu",
        "tr": "Ana Menü"
    },
    "navigation_user_menu": {
        "en": "User Menu",
        "tr": "Kullanıcı Menüsü"
    },
    "navigation_repository_menu": {
        "en": "Repository Menu",
        "tr": "Repo Menüsü"
    },
    "navigation_project_menu": {
        "en": "Project Menu",
        "tr": "Proje Menüsü"
    },
    "navigation_local_projects": {
        "en": "Local Projects",
        "tr": "Yerel Projeler"
    },
    "navigation_github_projects": {
        "en": "GitHub Projects",
        "tr": "GitHub Projeleri"
    },
    "navigation_repositories": {
        "en": "Repositories",
        "tr": "Repolar"
    },
    "navigation_users": {
        "en": "Users",
        "tr": "Kullanıcılar"
    },
    
    # UI Elements
    "options": {
        "en": "Options:",
        "tr": "Seçenekler:"
    },
    "disabled": {
        "en": "disabled",
        "tr": "devre dışı"
    },
    "local_files": {
        "en": "Local Files:",
        "tr": "Yerel Dosyalar:"
    },
    "menu_options": {
        "en": "Menu Options:",
        "tr": "Menü Seçenekleri:"
    },
    "navigation": {
        "en": "Navigation",
        "tr": "Navigasyon"
    },
    
    # User List
    "users_title": {
        "en": "Users",
        "tr": "Kullanıcılar"
    },
    "total_users_found": {
        "en": "Total {} users found:",
        "tr": "Toplam {} kullanıcı bulundu:"
    },
    "username_column": {
        "en": "Username",
        "tr": "Kullanıcı Adı"
    },
    "added_date_column": {
        "en": "Added Date",
        "tr": "Eklenme Tarihi"
    },
    "default_column": {
        "en": "Default",
        "tr": "Varsayılan"
    },
    
    # Repository List
    "repositories_title": {
        "en": "Repositories",
        "tr": "Repolar"
    },
    "total_repos_found": {
        "en": "Total {} repositories found:",
        "tr": "Toplam {} repo bulundu:"
    },
    "repo_name_column": {
        "en": "Repository Name",
        "tr": "Repo Adı"
    },
    "description_column": {
        "en": "Description",
        "tr": "Açıklama"
    },
    
    # Project List
    "projects_title": {
        "en": "GitHub Projects",
        "tr": "GitHub Projeleri"
    },
    "total_projects_found": {
        "en": "Total {} projects found:",
        "tr": "Toplam {} proje bulundu:"
    },
    "project_name_column": {
        "en": "Project Name",
        "tr": "Proje Adı"
    },
    "status_column": {
        "en": "Status",
        "tr": "Durum"
    },
    "last_update_column": {
        "en": "Last Update",
        "tr": "Son Güncelleme"
    },
    
    # Local Projects
    "local_projects_title": {
        "en": "Local Projects",
        "tr": "Yerel Projeler"
    },
    "no_local_projects": {
        "en": "No local projects found!",
        "tr": "Hiç yerel proje bulunamadı!"
    },
    "fetch_projects_hint": {
        "en": "You can use the 'GitHub Projects' menu to fetch projects from GitHub.",
        "tr": "GitHub'dan proje çekmek için 'GitHub Projeleri' menüsünü kullanabilirsiniz."
    },
    
    # Project Details
    "id_label": {
        "en": "ID",
        "tr": "ID"
    },
    "url_label": {
        "en": "URL",
        "tr": "URL"
    },
    "state_label": {
        "en": "State",
        "tr": "Durum"
    },
    "number_label": {
        "en": "Number",
        "tr": "Numara"
    },
    
    # Login
    "login_title": {
        "en": "GitHub Token Login",
        "tr": "GitHub Token ile Giriş"
    },
    "token_info": {
        "en": "Log in with your GitHub token.",
        "tr": "GitHub token ile giriş yapın."
    },
    "token_create_info": {
        "en": "To create a token: https://github.com/settings/tokens",
        "tr": "Token oluşturmak için: https://github.com/settings/tokens"
    },
    "token_permissions_info": {
        "en": "The token needs the following permissions:",
        "tr": "Token'ın şu izinlere sahip olması gerekir:"
    },
    "token_permission_repo": {
        "en": "- repo (all sub-permissions)",
        "tr": "- repo (tüm alt izinler)"
    },
    "token_permission_org": {
        "en": "- admin:org (read:org)",
        "tr": "- admin:org (read:org)"
    },
    "token_permission_project": {
        "en": "- project",
        "tr": "- project"
    },
    "token_empty_error": {
        "en": "Token cannot be empty!",
        "tr": "Token boş olamaz!"
    },
    "token_invalid_error": {
        "en": "Invalid token or insufficient permissions!",
        "tr": "Token geçersiz veya yetkileri yetersiz!"
    },
    "username_not_found_error": {
        "en": "Username could not be retrieved!",
        "tr": "Kullanıcı adı alınamadı!"
    },
    
    # Update Token
    "update_token_title": {
        "en": "Update Token",
        "tr": "Token Güncelle"
    },
    "current_token": {
        "en": "Current Token: {}",
        "tr": "Mevcut Token: {}"
    },
    "new_token_prompt": {
        "en": "Enter new token (leave empty to keep current):",
        "tr": "Yeni token girin (değiştirmemek için boş bırakın):"
    },
    "token_not_changed": {
        "en": "Token not changed.",
        "tr": "Token değiştirilmedi."
    },
    "token_different_user": {
        "en": "Token belongs to a different user: {}",
        "tr": "Token farklı bir kullanıcıya ait: {}"
    },
    "expected_user": {
        "en": "Expected user: {}",
        "tr": "Beklenen kullanıcı: {}"
    },
    "token_updated": {
        "en": "Token updated.",
        "tr": "Token güncellendi."
    },
    "cache_file_deleted": {
        "en": "Cache file deleted: {}",
        "tr": "Cache dosyası silindi: {}"
    },
    "all_cache_deleted": {
        "en": "All cache files deleted.",
        "tr": "Tüm cache dosyaları silindi."
    },
    
    # Update from GitHub
    "update_from_github_title": {
        "en": "Update from GitHub",
        "tr": "GitHub'dan Güncelle"
    },
    "updating_all_data": {
        "en": "Updating all data from GitHub...",
        "tr": "GitHub'dan tüm veriler güncelleniyor..."
    },
    "updating_repositories": {
        "en": "Updating repositories...",
        "tr": "Repolar güncelleniyor..."
    },
    "repositories_cache_created": {
        "en": "Repositories cache created: {}",
        "tr": "Repolar cache oluşturuldu: {}"
    },
    "total_repos_found_info": {
        "en": "Total {} repositories found.",
        "tr": "Toplam {} repo bulundu."
    },
    "updating_projects": {
        "en": "Updating projects...",
        "tr": "Projeler güncelleniyor..."
    },
    "projects_v1_found": {
        "en": "GitHub Projects v1: {} projects found.",
        "tr": "GitHub Projects v1: {} proje bulundu."
    },
    "projects_v2_found": {
        "en": "GitHub Projects v2: {} projects found.",
        "tr": "GitHub Projects v2: {} proje bulundu."
    },
    "projects_cache_created": {
        "en": "Projects cache created: {}",
        "tr": "Projeler cache oluşturuldu: {}"
    },
    "total_projects_found_info": {
        "en": "Total {} projects found.",
        "tr": "Toplam {} proje bulundu."
    },
    "all_data_updated": {
        "en": "All data successfully updated!",
        "tr": "Tüm veriler başarıyla güncellendi!"
    },
    
    # Fetch Project Data
    "fetching_project_data": {
        "en": "Fetching project data from GitHub: {}",
        "tr": "GitHub'dan proje verileri çekiliyor: {}"
    },
    "project_data_fetch_error": {
        "en": "Could not fetch project data: {}",
        "tr": "Proje verileri çekilemedi: {}"
    },
    "project_access_error": {
        "en": "Project may have been deleted or you may not have access.",
        "tr": "Proje silinmiş veya erişim izniniz olmayabilir."
    },
    "json_file_saved": {
        "en": "JSON file saved: {}",
        "tr": "JSON dosyası kaydedildi: {}"
    },
    "latest_json_updated": {
        "en": "Latest JSON file updated: {}",
        "tr": "En son JSON dosyası güncellendi: {}"
    },
    "yaml_file_saved": {
        "en": "YAML file saved: {}",
        "tr": "YAML dosyası kaydedildi: {}"
    },
    "latest_yaml_updated": {
        "en": "Latest YAML file updated: {}",
        "tr": "En son YAML dosyası güncellendi: {}"
    },
    "project_name_changed": {
        "en": "Project name changed: {} -> {}",
        "tr": "Proje adı değişmiş: {} -> {}"
    },
    
    # Sync to GitHub
    "sending_latest_to_github": {
        "en": "Sending latest file to GitHub: {}",
        "tr": "En son değiştirilen dosya GitHub'a gönderiliyor: {}"
    },
    "no_files_found": {
        "en": "No files found!",
        "tr": "Hiçbir dosya bulunamadı!"
    },
    "fetch_data_first": {
        "en": "Use the 'Fetch Project Data' option first to download data.",
        "tr": "Önce 'Proje Verilerini İndir' seçeneğini kullanarak verileri çekmelisiniz."
    },
    "json_more_recent": {
        "en": "JSON file is more recent. Last update: {}",
        "tr": "JSON dosyası daha güncel. Son güncelleme: {}"
    },
    "yaml_more_recent": {
        "en": "YAML file is more recent. Last update: {}",
        "tr": "YAML dosyası daha güncel. Son güncelleme: {}"
    },
    "yaml_file_not_found": {
        "en": "YAML file not found!",
        "tr": "YAML dosyası bulunamadı!"
    },
    "json_file_not_found": {
        "en": "JSON file not found!",
        "tr": "JSON dosyası bulunamadı!"
    },
    "project_found_on_github": {
        "en": "Project found on GitHub: {}",
        "tr": "GitHub'da proje bulundu: {}"
    },
    "local_project_info": {
        "en": "Local project: {}",
        "tr": "Lokal proje: {}"
    },
    "confirm_send_data": {
        "en": "Confirm sending data (y/n)?",
        "tr": "Verilerin gönderilmesi için onaylayın (e/h)?"
    },
    "operation_cancelled": {
        "en": "Operation cancelled.",
        "tr": "İşlem iptal edildi."
    },
    "yaml_synced_to_github": {
        "en": "YAML file synced to GitHub.",
        "tr": "YAML dosyası GitHub'a senkronize edildi."
    },
    "json_updated": {
        "en": "JSON file updated.",
        "tr": "JSON dosyası güncellendi."
    },
    "yaml_sync_failed": {
        "en": "Failed to sync YAML file to GitHub.",
        "tr": "YAML dosyası GitHub'a senkronize edilemedi."
    },
    "json_synced_to_github": {
        "en": "JSON file synced to GitHub.",
        "tr": "JSON dosyası GitHub'a senkronize edildi."
    },
    "yaml_updated": {
        "en": "YAML file updated.",
        "tr": "YAML dosyası güncellendi."
    },
    "json_sync_failed": {
        "en": "Failed to sync JSON file to GitHub.",
        "tr": "JSON dosyası GitHub'a senkronize edilemedi."
    },
    
    # View YAML Content
    "yaml_content": {
        "en": "YAML Content:",
        "tr": "YAML İçeriği:"
    },
    
    # Table Headers
    "table_header_number": {
        "en": "#",
        "tr": "#"
    },
    "table_header_username": {
        "en": "Username",
        "tr": "Kullanıcı Adı"
    },
    "table_header_added_date": {
        "en": "Added Date",
        "tr": "Eklenme Tarihi"
    },
    "table_header_default": {
        "en": "Default",
        "tr": "Varsayılan"
    },
    "table_header_repo_name": {
        "en": "Repository Name",
        "tr": "Repo Adı"
    },
    "table_header_description": {
        "en": "Description",
        "tr": "Açıklama"
    },
    "table_header_project_name": {
        "en": "Project Name",
        "tr": "Proje Adı"
    },
    "table_header_status": {
        "en": "Status",
        "tr": "Durum"
    },
    "table_header_last_update": {
        "en": "Last Update",
        "tr": "Son Güncelleme"
    },
    
    # Back Option
    "back_option": {
        "en": "0: Back",
        "tr": "0: Geri"
    },
    
    # Error Messages
    "directory_creation_error": {
        "en": "Error creating directory: {}",
        "tr": "Dizin oluşturulurken hata: {}"
    },
    "user_file_corrupt_error": {
        "en": "Error: User file is corrupt. Creating a new file.",
        "tr": "Hata: Kullanıcı dosyası bozuk. Yeni bir dosya oluşturuluyor."
    },
    "user_load_error": {
        "en": "Error loading user information: {}",
        "tr": "Kullanıcı bilgileri yüklenirken hata: {}"
    },
    "user_save_error": {
        "en": "Error saving user information: {}",
        "tr": "Kullanıcı bilgileri kaydedilirken hata: {}"
    },
    "user_validation_error": {
        "en": "Error validating user: {}",
        "tr": "Kullanıcı doğrulanırken hata: {}"
    },
    "user_not_found": {
        "en": "User not found.",
        "tr": "Kullanıcı bulunamadı."
    },
    
    # GitHub Service Messages
    "token_warning_repo": {
        "en": "WARNING: Token does not have 'repo' permission. Some operations may not work.",
        "tr": "UYARI: Token 'repo' iznine sahip değil. Bazı işlemler çalışmayabilir."
    },
    "token_warning_project": {
        "en": "WARNING: Token does not have 'project' permission. Project operations may not work.",
        "tr": "UYARI: Token 'project' iznine sahip değil. Proje işlemleri çalışmayabilir."
    },
    "token_permission_check_error": {
        "en": "Error checking token permissions: {}",
        "tr": "Token izinleri kontrol edilirken hata oluştu: {}"
    },
    "rate_limit_warning": {
        "en": "Rate limit almost reached. Waiting {} seconds...",
        "tr": "Rate limit almost reached. Waiting {} seconds..."
    },
    "token_validation_invalid": {
        "en": "Token validation error: Invalid or expired token.",
        "tr": "Token doğrulama hatası: Geçersiz veya süresi dolmuş token."
    },
    "token_validation_permissions": {
        "en": "Token validation error: Insufficient permissions. Make sure the token has 'repo' and 'project' permissions.",
        "tr": "Token doğrulama hatası: Yetersiz izinler. Token'ın 'repo' ve 'project' izinlerine sahip olduğundan emin olun."
    },
    "token_validation_error": {
        "en": "Token validation error: {} (Code: {})",
        "tr": "Token doğrulama hatası: {} (Kod: {})"
    },
    "token_validated": {
        "en": "Token validated. User: {}",
        "tr": "Token doğrulandı. Kullanıcı: {}"
    },
    "token_different_user_warning": {
        "en": "Warning: Token belongs to a different user ({}), but can still be used.",
        "tr": "Uyarı: Token farklı bir kullanıcıya ait ({}), ancak yine de kullanılabilir."
    },
    "token_validation_error_generic": {
        "en": "Error validating token: {}",
        "tr": "Token doğrulanırken hata oluştu: {}"
    },
    
    # Sync Service Messages
    "directory_created": {
        "en": "Created directory: {}",
        "tr": "Dizin oluşturuldu: {}"
    },
    "json_file_saved": {
        "en": "Saved JSON file: {}",
        "tr": "JSON dosyası kaydedildi: {}"
    },
    "json_file_save_error": {
        "en": "Error saving JSON file: {}",
        "tr": "JSON dosyası kaydedilirken hata: {}"
    },
    "json_file_not_found": {
        "en": "JSON file not found: {}",
        "tr": "JSON dosyası bulunamadı: {}"
    },
    "json_file_loaded": {
        "en": "Loaded JSON file: {}",
        "tr": "JSON dosyası yüklendi: {}"
    },
    "json_file_load_error": {
        "en": "Error loading JSON file: {}",
        "tr": "JSON dosyası yüklenirken hata: {}"
    },
    "yaml_file_saved": {
        "en": "Saved YAML file: {}",
        "tr": "YAML dosyası kaydedildi: {}"
    },
    "yaml_file_save_error": {
        "en": "Error saving YAML file: {}",
        "tr": "YAML dosyası kaydedilirken hata: {}"
    },
    "yaml_file_not_found": {
        "en": "YAML file not found: {}",
        "tr": "YAML dosyası bulunamadı: {}"
    },
    "yaml_file_loaded": {
        "en": "Loaded YAML file: {}",
        "tr": "YAML dosyası yüklendi: {}"
    },
    "yaml_file_load_error": {
        "en": "Error loading YAML file: {}",
        "tr": "YAML dosyası yüklenirken hata: {}"
    },
    "fetching_repository_data": {
        "en": "Fetching repository data: {}/{}",
        "tr": "Repository verilerini çekiliyor: {}/{}"
    },
    "repository_data_fetch_error": {
        "en": "Could not fetch repository data: {}/{}",
        "tr": "Repository verileri alınamadı: {}/{}"
    },
    "repository_data_saved": {
        "en": "Repository data successfully saved: {}/{}",
        "tr": "Repository verileri başarıyla kaydedildi: {}/{}"
    },
    "fetching_project_data": {
        "en": "Fetching project data: {}",
        "tr": "Proje verilerini çekiliyor: {}"
    },
    "project_data_fetch_error": {
        "en": "Could not fetch project data: {}",
        "tr": "Proje verileri alınamadı: {}"
    },
    "project_data_saved": {
        "en": "Project data successfully saved: {}",
        "tr": "Proje verileri başarıyla kaydedildi: {}"
    },
    "yaml_to_json_sync": {
        "en": "Syncing from YAML to JSON: {}",
        "tr": "YAML'dan JSON'a senkronizasyon yapılıyor: {}"
    },
    "yaml_to_json_sync_completed": {
        "en": "YAML to JSON synchronization completed: {}",
        "tr": "YAML'dan JSON'a senkronizasyon tamamlandı: {}"
    },
    "json_to_yaml_sync": {
        "en": "Syncing from JSON to YAML: {}",
        "tr": "JSON'dan YAML'a senkronizasyon yapılıyor: {}"
    },
    "json_to_yaml_sync_completed": {
        "en": "JSON to YAML synchronization completed: {}",
        "tr": "JSON'dan YAML'a senkronizasyon tamamlandı: {}"
    },
    "checking_project_changes": {
        "en": "Checking project changes: {}",
        "tr": "Proje değişiklikleri kontrol ediliyor: {}"
    },
    "no_changes_found": {
        "en": "No changes found: {}",
        "tr": "Değişiklik bulunamadı: {}"
    },
    "changes_found": {
        "en": "Changes found: {}",
        "tr": "Değişiklikler bulundu: {}"
    },
    "checking_github_changes": {
        "en": "Checking GitHub changes: {}",
        "tr": "GitHub değişiklikleri kontrol ediliyor: {}"
    },
    "no_github_changes": {
        "en": "No GitHub changes found: {}",
        "tr": "GitHub değişikliği bulunamadı: {}"
    },
    "github_changes_found": {
        "en": "GitHub changes found: {}",
        "tr": "GitHub değişiklikleri bulundu: {}"
    },
    "sending_project_data": {
        "en": "Sending project data to GitHub: {}",
        "tr": "Proje verileri GitHub'a gönderiliyor: {}"
    },
    "project_data_sent": {
        "en": "Project data sent to GitHub (simulation): {}",
        "tr": "Proje verileri GitHub'a gönderildi (simülasyon): {}"
    },
    
    # User Manager Functions
    "default_project": {
        "en": "Default project",
        "tr": "Varsayılan proje"
    },
    "update_user": {
        "en": "Update user information",
        "tr": "Kullanıcı bilgilerini güncelle"
    },
    
    # GraphQL Messages
    "fetching_projects_v2": {
        "en": "Fetching Projects v2 using GraphQL API...",
        "tr": "GraphQL API kullanarak Projects v2 çekiliyor..."
    },
    "graphql_error": {
        "en": "GraphQL error: {}",
        "tr": "GraphQL hatası: {}"
    },
    "graphql_error_type": {
        "en": "Error type: {}",
        "tr": "Hata tipi: {}"
    },
    "graphql_error_locations": {
        "en": "Error locations: {}",
        "tr": "Hata konumları: {}"
    },
    "graphql_query_failed": {
        "en": "GraphQL query for GitHub Projects v2 failed.",
        "tr": "GitHub Projects v2 için GraphQL sorgusu başarısız oldu."
    },
    "graphql_query_failed_reason": {
        "en": "This may be due to token permissions or GitHub API changes.",
        "tr": "Bu, token izinleri veya GitHub API değişiklikleri nedeniyle olabilir."
    },
    "total_projects_v2_found": {
        "en": "Total {} GitHub Projects v2 found.",
        "tr": "Toplam {} GitHub Projects v2 bulundu."
    },
    "updating_github_project": {
        "en": "Updating GitHub Project: {}",
        "tr": "GitHub Project güncelleniyor: {}"
    },
    "github_project_info_error": {
        "en": "Could not get GitHub Project information: {}",
        "tr": "GitHub Project bilgileri alınamadı: {}"
    },
    "project_name_update_error": {
        "en": "Could not update project name: {} - {}",
        "tr": "Proje adı güncellenemedi: {} - {}"
    },
    "project_name_updated": {
        "en": "Project name updated: {}",
        "tr": "Proje adı güncellendi: {}"
    },
    "columns_fetch_error": {
        "en": "Could not get existing columns.",
        "tr": "Mevcut sütunlar alınamadı."
    },
    "github_project_update_error": {
        "en": "GitHub Project update error: {}",
        "tr": "GitHub Project güncelleme hatası: {}"
    },
    "cards_fetch_error": {
        "en": "Could not get existing cards: {}",
        "tr": "Mevcut kartlar alınamadı: {}"
    },
    "column_cards_update_error": {
        "en": "Column cards update error: {}",
        "tr": "Sütun kartları güncelleme hatası: {}"
    },
    "new_column_created": {
        "en": "New column created: {} ({})",
        "tr": "Yeni sütun oluşturuldu: {} ({})"
    },
    "column_creation_error": {
        "en": "Could not create column: {} - {}",
        "tr": "Sütun oluşturulamadı: {} - {}"
    },
    "column_creation_generic_error": {
        "en": "Column creation error: {}",
        "tr": "Sütun oluşturma hatası: {}"
    },
    "card_update_error": {
        "en": "Could not update card: {} - {}",
        "tr": "Kart güncellenemedi: {} - {}"
    },
    "card_update_generic_error": {
        "en": "Card update error: {}",
        "tr": "Kart güncelleme hatası: {}"
    },
    "invalid_card_data": {
        "en": "Invalid card data: Content or note required",
        "tr": "Geçersiz kart verisi: İçerik veya not gerekli"
    },
    "new_card_created": {
        "en": "New card created: {}",
        "tr": "Yeni kart oluşturuldu: {}"
    }
}

def get_text(key: str) -> str:
    """
    Get the translated text for the given key.
    
    Args:
        key: The translation key
        
    Returns:
        The translated text
    """
    if key not in translations:
        return key
    
    if current_language not in translations[key]:
        return translations[key][DEFAULT_LANGUAGE]
    
    return translations[key][current_language]

def set_language(language: str) -> bool:
    """
    Set the current language.
    
    Args:
        language: The language code (e.g., 'en', 'tr')
        
    Returns:
        True if the language was set successfully, False otherwise
    """
    global current_language
    
    if language not in LANGUAGES:
        return False
    
    current_language = language
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(LANGUAGE_FILE), exist_ok=True)
    
    # Save language preference
    with open(LANGUAGE_FILE, "w") as f:
        json.dump({"language": language}, f)
    
    return True

def load_language() -> None:
    """
    Load the language preference from the language file.
    """
    global current_language
    
    if not os.path.exists(LANGUAGE_FILE):
        return
    
    try:
        with open(LANGUAGE_FILE, "r") as f:
            data = json.load(f)
            if "language" in data and data["language"] in LANGUAGES:
                current_language = data["language"]
    except Exception:
        pass

def language_menu() -> None:
    """
    Display the language selection menu.
    """
    from app.interactive_cli import clear_screen, print_header, print_menu, get_user_choice, wait_for_enter, print_success
    
    clear_screen()
    print_header(get_text("language_menu_title"))
    
    options = []
    for code, name in LANGUAGES.items():
        options.append({
            "name": f"{name} ({code})",
            "value": code,
            "selected": code == current_language
        })
    
    print_menu(options)
    
    choice = get_user_choice(len(options))
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        language = options[int(choice) - 1]["value"]
        set_language(language)
        print_success(get_text("language_changed"))
        wait_for_enter()
        return

# Load language preference on module import
load_language() 