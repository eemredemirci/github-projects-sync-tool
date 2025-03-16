"""
User management module.
"""
import os
import json
import sys
from typing import Dict, List, Optional, Any

from app.services.github_service import GitHubService
from app.utils.language import get_text


# File to store user information
USER_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "users")
USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "users.json")

# Default user structure
DEFAULT_USER_STRUCTURE = {
    "users": [],
    "active_user": None
}


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    if not os.path.exists(USER_CONFIG_DIR):
        try:
            os.makedirs(USER_CONFIG_DIR)
        except Exception as e:
            print(f"{get_text('directory_creation_error').format(str(e))}")


def load_users() -> Dict[str, Any]:
    """Load user information.
    
    Returns:
        Dictionary of user information
    """
    ensure_config_dir()
    
    if not os.path.exists(USER_CONFIG_FILE):
        return DEFAULT_USER_STRUCTURE
    
    try:
        with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"{get_text('user_file_corrupt_error')}")
        return DEFAULT_USER_STRUCTURE
    except Exception as e:
        print(f"{get_text('user_load_error').format(str(e))}")
        return DEFAULT_USER_STRUCTURE


def save_users(users_data: Dict[str, Any]) -> None:
    """Save user information.
    
    Args:
        users_data: Dictionary of user information
    """
    ensure_config_dir()
    
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"{get_text('user_save_error').format(str(e))}")


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Return the specified user.
    
    Args:
        username: Username
        
    Returns:
        Dictionary of user information or None
    """
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == username:
            return user
    
    return None


def get_all_users() -> List[Dict[str, Any]]:
    """Return all users.
    
    Returns:
        List of user information
    """
    users_data = load_users()
    return users_data["users"]


def add_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new user.
    
    Args:
        user: User information
        
    Returns:
        Added user information
    """
    users_data = load_users()
    
    # Check if the user already exists
    for i, existing_user in enumerate(users_data["users"]):
        if existing_user["username"] == user["username"]:
            # Update existing user
            users_data["users"][i] = user
            save_users(users_data)
            return users_data["users"][i]
    
    # Add new user
    users_data["users"].append(user)
    
    # If there's no default user, set this user as default
    if not users_data["active_user"]:
        users_data["active_user"] = user["username"]
    
    save_users(users_data)
    
    return user


def remove_user(username: str) -> bool:
    """Remove a user.
    
    Args:
        username: Username
        
    Returns:
        Whether the user was removed
    """
    users_data = load_users()
    
    # Find user
    for i, user in enumerate(users_data["users"]):
        if user["username"] == username:
            # Remove user
            users_data["users"].pop(i)
            
            # Update active user if needed
            if users_data["active_user"] == username:
                users_data["active_user"] = users_data["users"][0]["username"] if users_data["users"] else None
            
            save_users(users_data)
            return True
    
    return False


def set_default_user(username: str) -> bool:
    """Set the default user.
    
    Args:
        username: Username
        
    Returns:
        Whether the default user was set
    """
    users_data = load_users()
    
    # Find user
    for user in users_data["users"]:
        if user["username"] == username:
            # Set as default user
            users_data["active_user"] = username
            save_users(users_data)
            return True
    
    return False


def get_default_user() -> Optional[Dict[str, Any]]:
    """Return the default user.
    
    Returns:
        Dictionary of user information or None
    """
    users_data = load_users()
    
    if not users_data["active_user"]:
        return None
    
    return get_user(users_data["active_user"])


def validate_user(username: str, token: str) -> bool:
    """Validate user credentials.
    
    Args:
        username: Username
        token: GitHub token
        
    Returns:
        Whether the credentials are valid
    """
    try:
        # Create GitHub service
        github_service = GitHubService(token, username)
        
        # Validate token
        return github_service.validate_token()
    except Exception as e:
        print(f"{get_text('user_validation_error').format(str(e))}")
        return False


def get_user_repositories(username: str = None) -> List[Dict[str, Any]]:
    """Return user repositories.
    
    Args:
        username: Username (optional)
        
    Returns:
        List of repositories
    """
    # Get user
    user = get_user(username) if username else get_default_user()
    
    if not user:
        print(get_text('user_not_found'))
        return []
    
    # Create GitHub service
    github_service = GitHubService(user["token"], user["username"])
    
    # Get repositories
    return github_service.get_repositories()


def get_repository_projects(username: str = None, repo: str = None) -> List[Dict[str, Any]]:
    """Return repository projects.
    
    Args:
        username: Username (optional)
        repo: Repository name (optional)
        
    Returns:
        List of projects
    """
    # Get user
    user = get_user(username) if username else get_default_user()
    
    if not user:
        print(get_text('user_not_found'))
        return []
    
    # Create GitHub service
    github_service = GitHubService(user["token"], user["username"])
    
    # Get projects
    return github_service.get_projects(user["username"], repo)


def get_user_projects(username: str = None) -> List[Dict[str, Any]]:
    """Return user projects.
    
    Args:
        username: Username (optional)
        
    Returns:
        List of projects
    """
    # Get user
    user = get_user(username) if username else get_default_user()
    
    if not user:
        print(get_text('user_not_found'))
        return []
    
    # Create GitHub service
    github_service = GitHubService(user["token"], user["username"])
    
    # Get projects
    return github_service.get_projects()


def get_default_project() -> Optional[Dict[str, Any]]:
    """Return the default project.
    
    Returns:
        Default project information or None
    """
    config_dir = os.path.join("data", "config")
    config_file = os.path.join(config_dir, "default_project.json")
    
    if not os.path.exists(config_file):
        return None
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def update_user(user: Dict[str, Any]) -> bool:
    """Update user information.
    
    Args:
        user: User information
        
    Returns:
        Whether the update was successful
    """
    users_data = load_users()
    
    # Find user
    for i, existing_user in enumerate(users_data["users"]):
        if existing_user["username"] == user["username"]:
            # Update user
            users_data["users"][i] = user
            save_users(users_data)
            return True
    
    return False 