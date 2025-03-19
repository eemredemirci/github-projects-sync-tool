"""
GitHub API interaction service module.
"""
import os
import json
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
import re

from app.utils.language import get_text

# GitHub API endpoint
GITHUB_API_URL = "https://api.github.com"


class GitHubService:
    """Service class for interacting with the GitHub API."""
    
    def __init__(self, token: str, username: str = None):
        """
        Args:
            token: GitHub API token
            username: GitHub username (optional)
        """
        self.token = token
        self.username = username
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        # Rate limit tracking
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        
        # Debug token permissions
        self._debug_token_permissions()
    
    def _debug_token_permissions(self):
        """Debug token permissions to help diagnose access issues."""
        try:
            endpoint = "/user"
            response, status_code = self._make_request("GET", endpoint)
            
            if status_code == 200:
                # Token validation message removed
                # print(f"Token validated. User: {response.get('login', 'Unknown')}")
                
                # Check scopes from response headers
                if hasattr(response, 'headers') and 'X-OAuth-Scopes' in response.headers:
                    scopes = response.headers['X-OAuth-Scopes']
                    # print(f"Token permissions: {scopes}")
                    
                    if 'repo' not in scopes:
                        print(get_text('token_warning_repo'))
                    if 'project' not in scopes:
                        print(get_text('token_warning_project'))
        except Exception as e:
            print(get_text('token_permission_check_error').format(str(e)))
    
    def _check_rate_limit(self):
        """Check if we need to wait for rate limit reset."""
        if self.rate_limit_remaining < 10:
            current_time = time.time()
            if current_time < self.rate_limit_reset:
                wait_time = self.rate_limit_reset - current_time + 1
                print(get_text('rate_limit_warning').format(int(wait_time)))
                time.sleep(wait_time)
    
    def _update_rate_limit(self, response):
        """Update rate limit information from response headers."""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, custom_headers: Dict = None) -> Tuple[Dict, int]:
        """Make an API request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: URL parameters (optional)
            data: Request body (optional)
            custom_headers: Additional headers to merge with default headers (optional)
            
        Returns:
            Response data and HTTP status code
        """
        url = f"{GITHUB_API_URL}{endpoint}"
        self._check_rate_limit()
        
        # Use custom headers if provided
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {"error": "Invalid HTTP method"}, 400
            
            self._update_rate_limit(response)
            
            if response.status_code == 401:
                return {"error": "Authentication failed. Please check your GitHub token."}, response.status_code
            elif response.status_code == 403:
                if 'X-RateLimit-Remaining' in response.headers and int(response.headers['X-RateLimit-Remaining']) == 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = max(0, reset_time - int(time.time()))
                    return {"error": f"Rate limit exceeded. Resets in {wait_time} seconds."}, response.status_code
                return {"error": "Forbidden. You may not have permission to access this resource."}, response.status_code
            elif response.status_code == 404:
                return {"error": "Resource not found. Please check the URL and your permissions."}, response.status_code
            elif response.status_code >= 400:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", "API error")
                except:
                    error_msg = response.text or "API error"
                return {"error": error_msg}, response.status_code
            
            # Check for empty response
            if not response.text.strip():
                return {}, response.status_code
            
            return response.json(), response.status_code
        
        except requests.exceptions.RequestException as e:
            return {"error": f"Request error: {str(e)}"}, 500
        except json.JSONDecodeError:
            return {"error": "JSON parsing error"}, 500
    
    def validate_token(self) -> bool:
        """Validate token.
        
        Returns:
            Whether the token is valid
        """
        endpoint = "/user"
        try:
            response, status_code = self._make_request("GET", endpoint)
            
            if status_code == 401:
                print(get_text('token_validation_invalid'))
                return False
            elif status_code == 403:
                print(get_text('token_validation_permissions'))
                return False
            elif status_code >= 400:
                print(get_text('token_validation_error').format(response.get('error', 'Unknown error'), status_code))
                return False
            
            # Check user information
            if 'login' in response:
                print(get_text('token_validated').format(response['login']))
                if self.username and self.username != response['login']:
                    print(get_text('token_different_user_warning').format(response['login']))
                return True
            
            return status_code == 200
        except Exception as e:
            print(get_text('token_validation_error_generic').format(str(e)))
            return False
    
    def get_user(self) -> Dict[str, Any]:
        """Return user information.
        
        Returns:
            User information
        """
        endpoint = "/user"
        response, status_code = self._make_request("GET", endpoint)
        
        if status_code != 200:
            print(f"Failed to get user information: {response.get('error', 'Unknown error')}")
            return {}
        
        return response
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """Return the user's repositories with essential information for project operations.
        
        Returns:
            List of repositories with basic information
        """
        # Only fetch repositories owned by the user
        endpoint = "/user/repos"
        
        params = {
            "per_page": 100,
            "visibility": "all",  # Show both public and private repos
            "sort": "updated",
            "direction": "desc",
            "affiliation": "owner"  # Only repositories owned by the user
        }
        
        print(f"Fetching user repositories: {endpoint}")
        print(f"Parameters: {params}")
        
        response, status_code = self._make_request("GET", endpoint, params=params)
        
        if status_code != 200:
            print(f"Failed to fetch user repositories: {response.get('error', 'Unknown error')}")
            return []
        
        # Create a list of repositories with only essential information
        essential_repos = []
        for repo in response:
            essential_repo = {
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "description": repo.get("description"),
                "owner": {
                    "login": repo.get("owner", {}).get("login"),
                    "id": repo.get("owner", {}).get("id")
                }
            }
            essential_repos.append(essential_repo)
        
        print(f"Total {len(essential_repos)} repository found")
        
        return essential_repos
    
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Return the specified repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        endpoint = f"/repos/{owner}/{repo}"
        
        response, status_code = self._make_request("GET", endpoint)
        
        if status_code != 200:
            print(f"Failed to get repository information: {response.get('error', 'Unknown error')}")
            return {}
        
        return response
    
    def get_projects(self, owner: str = None, repo: str = None) -> List[Dict[str, Any]]:
        """Return projects.
        
        Args:
            owner: Repository owner (optional)
            repo: Repository name (optional)
            
        Returns:
            List of projects
        """
        # Repository projects
        if owner and repo:
            endpoint = f"/repos/{owner}/{repo}/projects"
        # User projects
        elif self.username:
            endpoint = f"/users/{self.username}/projects"
        # Authenticated user's projects
        else:
            endpoint = "/user/projects"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json,application/vnd.github.v3+json"
        }
        
        params = {
            "state": "all",
            "per_page": 100
        }
        
        print(f"Projects API endpoint: {endpoint}")
        response, status_code = self._make_request("GET", endpoint, params=params, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to get projects: {response.get('error', 'Unknown error')}")
            # Try organization projects as fallback
            if self.username and status_code == 404:
                print(f"Trying organization projects for {self.username}...")
                org_endpoint = f"/orgs/{self.username}/projects"
                org_response, org_status = self._make_request("GET", org_endpoint, params=params, custom_headers=custom_headers)
                if org_status == 200:
                    return org_response
            return []
        
        return response
    
    def get_repository_projects(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Return repository projects.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of projects
        """
        # Repository projects
        endpoint = f"/repos/{owner}/{repo}/projects"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json,application/vnd.github.v3+json"
        }
        
        params = {
            "state": "all",
            "per_page": 100
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to fetch repository projects: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_user_projects(self, username: str = None) -> List[Dict[str, Any]]:
        """Return user projects.
        
        Args:
            username: Username (optional)
            
        Returns:
            List of projects
        """
        # User projects
        if username:
            endpoint = f"/users/{username}/projects"
        # Authenticated user's projects
        else:
            endpoint = "/user/projects"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json,application/vnd.github.v3+json"
        }
        
        params = {
            "state": "all",
            "per_page": 100
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to fetch user projects: {response.get('error', 'Unknown error')}")
            # Try organization projects as fallback
            if username and status_code == 404:
                print(f"Trying organization projects for {username}...")
                org_endpoint = f"/orgs/{username}/projects"
                org_response, org_status = self._make_request("GET", org_endpoint, params=params, custom_headers=custom_headers)
                if org_status == 200:
                    return org_response
            return []
        
        return response
    
    def get_project(self, project_id: int) -> Dict[str, Any]:
        """Return the specified project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project information
        """
        endpoint = f"/projects/{project_id}"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json"
        }
        
        response, status_code = self._make_request("GET", endpoint, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to get project information: {response.get('error', 'Unknown error')}")
            return {}
        
        return response
    
    def get_project_columns(self, project_id: int) -> List[Dict[str, Any]]:
        """Return project columns.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of columns
        """
        endpoint = f"/projects/{project_id}/columns"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json"
        }
        
        response, status_code = self._make_request("GET", endpoint, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to get project columns: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_column_cards(self, column_id: int) -> List[Dict[str, Any]]:
        """Return column cards.
        
        Args:
            column_id: Column ID
            
        Returns:
            List of cards
        """
        endpoint = f"/projects/columns/{column_id}/cards"
        
        # Special header for Projects API
        custom_headers = {
            "Accept": "application/vnd.github.inertia-preview+json"
        }
        
        params = {
            "archived_state": "all"
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params, custom_headers=custom_headers)
        
        if status_code != 200:
            print(f"Failed to get column cards: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_card_content(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Return card content.
        
        Args:
            card: Card information
            
        Returns:
            Content information (issue or pull request)
        """
        content_url = card.get("content_url")
        
        if not content_url:
            return {}
        
        try:
            response = requests.get(content_url, headers=self.headers)
            
            if response.status_code != 200:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", "API error")
                except:
                    error_msg = response.text or "API error"
                print(f"Failed to get card content: {error_msg}")
                return {}
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return {}
        except json.JSONDecodeError:
            print("JSON parsing error")
            return {}
    
    def get_issues(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Return repository issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of issues
        """
        endpoint = f"/repos/{owner}/{repo}/issues"
        
        params = {
            "state": "all",
            "per_page": 100
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params)
        
        if status_code != 200:
            print(f"Failed to get issues: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_milestones(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Return repository milestones.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of milestones
        """
        endpoint = f"/repos/{owner}/{repo}/milestones"
        
        params = {
            "state": "all",
            "per_page": 100
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params)
        
        if status_code != 200:
            print(f"Failed to get milestones: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_labels(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Return repository labels.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of labels
        """
        endpoint = f"/repos/{owner}/{repo}/labels"
        
        params = {
            "per_page": 100
        }
        
        response, status_code = self._make_request("GET", endpoint, params=params)
        
        if status_code != 200:
            print(f"Failed to get labels: {response.get('error', 'Unknown error')}")
            return []
        
        return response
    
    def get_full_project_data(self, project_id: int) -> Dict[str, Any]:
        """Return complete project data.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data (including columns and cards)
        """
        # Get project information
        project = self.get_project(project_id)
        
        if not project:
            return {}
        
        # Get columns
        columns = self.get_project_columns(project_id)
        project_data = {
            **project,
            "columns": []
        }
        
        # Get cards for each column
        for column in columns:
            column_id = column["id"]
            cards = self.get_column_cards(column_id)
            
            column_data = {
                **column,
                "cards": []
            }
            
            # Get content for each card
            for card in cards:
                card_data = {**card}
                
                if card.get("content_url"):
                    content = self.get_card_content(card)
                    card_data["content"] = content
                
                column_data["cards"].append(card_data)
            
            project_data["columns"].append(column_data)
        
        return project_data
    
    def get_full_repository_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Return complete repository data.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data (including projects, issues, milestones, and labels)
        """
        # Get repository information
        repository = self.get_repository(owner, repo)
        
        if not repository:
            return {}
        
        # Get projects
        projects = self.get_projects(owner, repo)
        
        # Get issues
        issues = self.get_issues(owner, repo)
        
        # Get milestones
        milestones = self.get_milestones(owner, repo)
        
        # Get labels
        labels = self.get_labels(owner, repo)
        
        # Get complete data for each project
        full_projects = []
        for project in projects:
            project_id = project["id"]
            full_project = self.get_full_project_data(project_id)
            full_projects.append(full_project)
        
        repository_data = {
            **repository,
            "projects": full_projects,
            "issues": issues,
            "milestones": milestones,
            "labels": labels
        }
        
        return repository_data
    
    def get_projects_v2(self, owner: str = None, repo: str = None) -> List[Dict[str, Any]]:
        """Return projects using the v2 API.
        
        Args:
            owner: Repository owner (optional)
            repo: Repository name (optional)
            
        Returns:
            List of projects
        """
        # GraphQL endpoint for Projects v2
        endpoint = "/graphql"
        
        # Build GraphQL query based on parameters
        if owner and repo:
            # Repository projects query
            query = """
            query {
              repository(owner: "%s", name: "%s") {
                projectsV2(first: 20) {
                  nodes {
                    id
                    title
                    number
                    closed
                    updatedAt
                    url
                    createdAt
                    shortDescription
                  }
                }
              }
            }
            """ % (owner, repo)
        elif self.username:
            # User projects query
            query = """
            query {
              user(login: "%s") {
                projectsV2(first: 20) {
                  nodes {
                    id
                    title
                    number
                    closed
                    updatedAt
                    url
                    createdAt
                    shortDescription
                  }
                }
              }
            }
            """ % self.username
        else:
            # Viewer (authenticated user) projects query
            query = """
            query {
              viewer {
                projectsV2(first: 20) {
                  nodes {
                    id
                    title
                    number
                    closed
                    updatedAt
                    url
                    createdAt
                    shortDescription
                  }
                }
              }
            }
            """
        
        # Special header for GraphQL API
        custom_headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "query": query
        }
        
        print("Fetching Projects v2 using GraphQL API...")
        response, status_code = self._make_request("POST", endpoint, data=data, custom_headers=custom_headers)
        
        if status_code != 200 or "errors" in response:
            if "errors" in response:
                errors = response.get("errors", [])
                for error in errors:
                    print(f"GraphQL error: {error.get('message', 'Unknown error')}")
                    # More detailed error information
                    if 'type' in error:
                        print(f"Error type: {error.get('type')}")
                    if 'locations' in error:
                        print(f"Error locations: {error.get('locations')}")
            else:
                print(f"Failed to get projects v2: {response.get('error', 'Unknown error')}")
            
            print("GraphQL query for GitHub Projects v2 failed.")
            print("This may be due to token permissions or GitHub API changes.")
            return []
        
        # Extract projects from response
        projects = []
        data = response.get("data", {})
        
        if owner and repo:
            repository = data.get("repository", {})
            projects_data = repository.get("projectsV2", {}).get("nodes", [])
        elif self.username:
            user = data.get("user", {})
            projects_data = user.get("projectsV2", {}).get("nodes", [])
        else:
            viewer = data.get("viewer", {})
            projects_data = viewer.get("projectsV2", {}).get("nodes", [])
        
        # Convert to format similar to v1 API
        for project in projects_data:
            projects.append({
                "id": project.get("id"),
                "name": project.get("title"),
                "number": project.get("number"),
                "state": "closed" if project.get("closed") else "open",
                "created_at": project.get("createdAt"),
                "updated_at": project.get("updatedAt"),
                "html_url": project.get("url"),
                "description": project.get("shortDescription", ""),
                "is_v2": True
            })
        
        print(f"Total {len(projects)} GitHub Projects v2 found.")
        return projects
    
    def update_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Update GitHub Project.
        
        Args:
            project_id: GitHub Project ID
            project_data: GitHub Project data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"GitHub Project updating: {project_id}")
            
            # Get project information
            project_info = self.get_project_info(project_id)
            
            if not project_info:
                print(f"Failed to get GitHub Project information: {project_id}")
                return False
            
            # Update project name
            if "name" in project_data and project_data["name"] != project_info.get("name"):
                url = f"{self.api_url}/projects/{project_id}"
                payload = {"name": project_data["name"]}
                
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    print(f"Failed to update project name: {response.status_code} - {response.text}")
                    return False
                
                print(f"Project name updated: {project_data['name']}")
            
            # Update columns
            if "columns" in project_data:
                # Get existing columns
                existing_columns = self.get_project_columns(project_id)
                
                if existing_columns is None:
                    print("Failed to get existing columns.")
                    return False
                
                # Sütun eşleştirmesi yap
                # Match columns
                column_map = {column["name"]: column["id"] for column in existing_columns}
                
                # Yeni sütunları ekle
                # Add new columns
                for column_data in project_data["columns"]:
                    column_name = column_data["name"]
                    
                    if column_name in column_map:
                        # Mevcut sütunu güncelle
                        # Update existing column
                        column_id = column_map[column_name]
                        
                        # Kartları güncelle
                        # Update cards
                        if "cards" in column_data:
                            self._update_column_cards(column_id, column_data["cards"])
                    else:
                        # Yeni sütun ekle
                        # Add new column
                        column_id = self._create_column(project_id, column_name)
                        
                        if column_id:
                            # Kartları ekle
                            if "cards" in column_data:
                                self._update_column_cards(column_id, column_data["cards"])
            
            return True
        
        except Exception as e:
            print(f"{get_text('github_project_update_error').format(str(e))}")
            return False
    
    def _update_column_cards(self, column_id: str, cards_data: List[Dict[str, Any]]) -> bool:
        """Update column cards.
        
        Args:
            column_id: Column ID
            cards_data: Card data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get existing cards
            existing_cards = self.get_column_cards(column_id)
            
            if existing_cards is None:
                print(f"Failed to get existing cards: {column_id}")
                return False
            
            # Kart eşleştirmesi yap
            card_map = {}
            for card in existing_cards:
                # Match card by content
                if "content_url" in card:
                    card_map[card["content_url"]] = card["id"]
                else:
                    # Use note content for cards without content
                    note = card.get("note", "")
                    if note:
                        card_map[note] = card["id"]
            
            # Kartları güncelle
            for card_data in cards_data:
                # Determine card type
                if "content_url" in card_data:
                    # Content card
                    content_url = card_data["content_url"]
                    
                    if content_url in card_map:
                        # Update existing card
                        card_id = card_map[content_url]
                        self._update_card(card_id, card_data)
                    else:
                        # Yeni kart ekle
                        # Add new card
                        self._create_card(column_id, card_data)
                else:
                    # Not kartı
                    # Note card
                    note = card_data.get("note", "")
                    
                    if note and note in card_map:
                        # Update existing card
                        # Update existing card
                        card_id = card_map[note]
                        self._update_card(card_id, card_data)
                    else:
                        # Yeni kart ekle
                        # Add new card
                        self._create_card(column_id, card_data)
            
            return True
        
        except Exception as e:
            print(f"{get_text('column_cards_update_error').format(str(e))}")
            return False
    
    def _create_column(self, project_id: str, name: str) -> Optional[str]:
        """Create a new column.
        
        Args:
            project_id: Project ID
            name: Column name
            
        Returns:
            str: Column ID or None
        """
        try:
            url = f"{self.api_url}/projects/{project_id}/columns"
            payload = {"name": name}
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                column_data = response.json()
                print(f"{get_text('new_column_created').format(name, column_data['id'])}")
                return column_data["id"]
            else:
                print(f"{get_text('column_creation_error').format(response.status_code, response.text)}")
                return None
        
        except Exception as e:
            print(f"{get_text('column_creation_error_generic').format(str(e))}")
            return None
    
    def _update_card(self, card_id: str, card_data: Dict[str, Any]) -> bool:
        """Update a card.
        
        Args:
            card_id: Card ID
            card_data: Card data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/projects/columns/cards/{card_id}"
            payload = {}
            
            # Update note content
            if "note" in card_data:
                payload["note"] = card_data["note"]
            
            # Update archive status
            if "archived" in card_data:
                payload["archived"] = card_data["archived"]
            
            # If update is needed
            if payload:
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    print(f"{get_text('card_update_failed').format(response.status_code, response.text)}")
                    return False
            
            return True
        
        except Exception as e:
            print(f"{get_text('card_update_error').format(str(e))}")
            return False
    
    def _create_card(self, column_id: str, card_data: Dict[str, Any]) -> Optional[str]:
        """Create a new card.
        
        Args:
            column_id: Column ID
            card_data: Card data
            
        Returns:
            str: Card ID or None
        """
        try:
            url = f"{self.api_url}/projects/columns/{column_id}/cards"
            payload = {}
            
            # Determine card type
            if "content_url" in card_data:
                # Content card
                payload["content_id"] = card_data["content_id"]
                payload["content_type"] = card_data["content_type"]
            elif "note" in card_data:
                # Note card
                payload["note"] = card_data["note"]
            else:
                print(f"{get_text('invalid_card_data')}")
                return None
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                card_data = response.json()
                print(f"{get_text('new_card_created').format(card_data['id'])}")
                return card_data["id"]
            else:
                print(f"{get_text('card_creation_failed').format(response.status_code, response.text)}")
                return None
        
        except Exception as e:
            print(f"{get_text('card_creation_error').format(str(e))}")
            return None
    
    def update_project_v2(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Update GitHub Project v2.
        
        Args:
            project_id: GitHub Project ID
            project_data: GitHub Project data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"GitHub Project v2 updating: {project_id}")
            
            # Get project information
            project_info = self.get_project_info(project_id)
            
            if not project_info:
                print(f"Failed to get GitHub Project information: {project_id}")
                return False
            
            # Update project name
            if "name" in project_data and project_data["name"] != project_info.get("name"):
                # GraphQL query
                query = """
                mutation UpdateProjectV2($projectId: ID!, $input: UpdateProjectV2Input!) {
                    updateProjectV2(projectId: $projectId, input: $input) {
                        projectV2 {
                            id
                            title
                        }
                    }
                }
                """
                
                variables = {
                    "projectId": project_id,
                    "input": {
                        "title": project_data["name"]
                    }
                }
                
                response = requests.post(
                    "https://api.github.com/graphql",
                    headers=self.headers,
                    json={"query": query, "variables": variables}
                )
                
                if response.status_code != 200:
                    print(f"Failed to update project name: {response.status_code} - {response.text}")
                    return False
                
                print(f"Project name updated: {project_data['name']}")
            
            # Note: Full support for GitHub Projects v2 is not yet implemented.
            print("Note: Full support for GitHub Projects v2 is not yet implemented.")
            print("Only the project name was updated.")
            
            return True
        
        except Exception as e:
            print(f"{get_text('github_project_v2_update_error').format(str(e))}")
            return False
    
    def get_project_v2(self, project_id: str) -> Dict[str, Any]:
        """Return the specified project using v2 API.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project information
        """
        # GraphQL endpoint for Projects v2
        endpoint = "/graphql"
        
        # GraphQL query for a specific project
        query = """
        query {
          node(id: "%s") {
            ... on ProjectV2 {
              id
              title
              number
              closed
              updatedAt
              url
              createdAt
              shortDescription
              
              # Repository ilişkisi
              repositories(first: 10) {
                nodes {
                  name
                  owner { 
                    login 
                  }
                  url
                }
              }
              
              items(first: 100) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      id
                      title
                      number
                      state
                      url
                      
                      # Milestone ilişkisi
                      milestone {
                        title
                        dueOn
                        state
                      }
                      
                      # Assignee ilişkisi
                      assignees(first: 5) {
                        nodes {
                          login
                          avatarUrl
                        }
                      }
                      
                      # Parent issue field
                      parent {
                        title
                        number
                        url
                      }
                      
                      # Parent issues - issues this issue tracks
                      trackedIssues(first: 5) {
                        nodes {
                          title
                          number
                          url
                        }
                      }
                      
                      # Child issues - issues tracking this issue
                      trackedInIssues(first: 5) {
                        nodes {
                          title
                          number
                          url
                        }
                      }
                      
                      # Body içeriğinde ilişkili issue'ları çekebiliriz
                      body

                      # Relations via timeline
                      timelineItems(first: 20, itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT, CROSS_REFERENCED_EVENT]) {
                        nodes {
                          ... on ConnectedEvent {
                            subject {
                              ... on Issue {
                                id
                                title
                                number
                                url
                              }
                            }
                          }
                          ... on DisconnectedEvent {
                            subject {
                              ... on Issue {
                                id
                                title
                                number
                                url
                              }
                            }
                          }
                          ... on CrossReferencedEvent {
                            source {
                              ... on Issue {
                                id
                                title
                                number
                                url
                              }
                            }
                          }
                        }
                      }
                      
                      # Repository bilgisi
                      repository {
                        name
                        owner { 
                          login 
                        }
                      }
                    }
                    ... on PullRequest {
                      title
                      number
                      state
                      url
                      
                      # Milestone ilişkisi
                      milestone {
                        title
                        dueOn
                        state
                      }
                      
                      # Assignee ilişkisi
                      assignees(first: 5) {
                        nodes {
                          login
                          avatarUrl
                        }
                      }
                      
                      # Repository bilgisi
                      repository {
                        name
                        owner { 
                          login 
                        }
                      }
                    }
                    ... on DraftIssue {
                      title
                      body
                    }
                  }
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
              fields(first: 20) {
                nodes {
                  ... on ProjectV2FieldCommon {
                    id
                    name
                    dataType
                  }
                }
              }
            }
          }
        }
        """ % project_id
        
        # Special header for GraphQL API
        custom_headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "query": query
        }
        
        print(f"Fetching Project v2 data for ID: {project_id}")
        response, status_code = self._make_request("POST", endpoint, data=data, custom_headers=custom_headers)
        
        if status_code != 200 or "errors" in response:
            if "errors" in response:
                errors = response.get("errors", [])
                for error in errors:
                    print(f"GraphQL error: {error.get('message', 'Unknown error')}")
                    # More detailed error information
                    if 'type' in error:
                        print(f"Error type: {error.get('type')}")
                    if 'locations' in error:
                        print(f"Error locations: {error.get('locations')}")
            else:
                print(f"Failed to get project v2: {response.get('error', 'Unknown error')}")
            
            print("GraphQL query for GitHub Project v2 failed.")
            print("This may be due to token permissions or GitHub API changes.")
            return {}
        
        # Extract project from response
        data = response.get("data", {})
        node = data.get("node", {})
        
        if not node:
            print(f"Project v2 not found with ID: {project_id}")
            return {}
        
        # Convert to format similar to v1 API
        project = {
            "id": node.get("id"),
            "name": node.get("title"),
            "number": node.get("number"),
            "state": "closed" if node.get("closed") else "open",
            "created_at": node.get("createdAt"),
            "updated_at": node.get("updatedAt"),
            "html_url": node.get("url"),
            "description": node.get("shortDescription", ""),
            "is_v2": True,
            "fields": [],
            "items": [],
            "repositories": [],  # New field for related repositories
            "milestone": None,  # New field for milestone information
            "assignees": [],    # New field for assignee information
            "parent_issue": None, # New field for parent issue information
            "repository": None  # New field for repository information
        }
        
        # Extract repositories
        repositories_nodes = node.get("repositories", {}).get("nodes", [])
        for repo in repositories_nodes:
            project["repositories"].append({
                "name": repo.get("name"),
                "owner": repo.get("owner", {}).get("login"),
                "url": repo.get("url")
            })
        
        # Extract fields
        fields_nodes = node.get("fields", {}).get("nodes", [])
        for field in fields_nodes:
            project["fields"].append({
                "id": field.get("id"),
                "name": field.get("name"),
                "type": field.get("dataType")
            })
        
        # Extract items
        items_nodes = node.get("items", {}).get("nodes", [])
        for item in items_nodes:
            item_data = {
                "id": item.get("id"),
                "content": {},
                "field_values": [],
                "milestone": None,  # Milestone bilgisi için yeni alan
                "assignees": [],    # Assignee bilgileri için yeni alan
                "parent_issue": None, # Parent issue bilgisi için yeni alan
                "repository": None  # Repository bilgisi için yeni alan
            }
            
            # Extract content
            content = item.get("content", {})
            if content:
                item_data["content"] = {
                    "title": content.get("title"),
                    "number": content.get("number"),
                    "state": content.get("state"),
                    "url": content.get("url")
                }
                
                # Extract milestone
                if "milestone" in content and content["milestone"]:
                    item_data["milestone"] = {
                        "title": content["milestone"].get("title"),
                        "due_on": content["milestone"].get("dueOn"),
                        "state": content["milestone"].get("state")
                    }
                
                # Extract assignees
                if "assignees" in content:
                    assignees_nodes = content.get("assignees", {}).get("nodes", [])
                    for assignee in assignees_nodes:
                        item_data["assignees"].append({
                            "login": assignee.get("login"),
                            "avatar_url": assignee.get("avatarUrl")
                        })
                
                # Extract parent issue
                parent_issue = None
                
                # 1. Direct parent field - Sadece bu direkt ilişkiyi kullanalım
                if "parent" in content and content["parent"]:
                    parent = content.get("parent", {})
                    parent_issue = {
                        "title": parent.get("title"),
                        "number": parent.get("number"),
                        "url": parent.get("url"),
                        "source": "direct_parent"
                    }
                
                # Diğer kaynaklardan gelen parent ilişkilerini kullanmıyoruz:
                # 2. tracked issues - Bu kısım pasif
                # 3. timeline items - Bu kısım pasif
                # 4. Body analizi - Bu kısım pasif
                
                # İlişki bilgisini ekle - sadece direct_parent varsa
                if parent_issue and parent_issue.get("source") == "direct_parent":
                    item_data["parent_issue"] = parent_issue
                
                # Extract repository
                if "repository" in content:
                    repo = content.get("repository", {})
                    item_data["repository"] = {
                        "name": repo.get("name"),
                        "owner": repo.get("owner", {}).get("login")
                    }
            
            # Extract field values
            field_values = item.get("fieldValues", {}).get("nodes", [])
            for field_value in field_values:
                if "field" in field_value and "name" in field_value.get("field", {}):
                    field_name = field_value["field"]["name"]
                    
                    if "text" in field_value:
                        item_data["field_values"].append({
                            "field_name": field_name,
                            "value": field_value["text"],
                            "type": "text"
                        })
                    elif "date" in field_value:
                        item_data["field_values"].append({
                            "field_name": field_name,
                            "value": field_value["date"],
                            "type": "date"
                        })
                    elif "name" in field_value:
                        item_data["field_values"].append({
                            "field_name": field_name,
                            "value": field_value["name"],
                            "type": "single_select"
                        })
            
            project["items"].append(item_data)
        
        print(f"Project v2 data fetched successfully: {project['name']}")
        print(f"Fields: {len(project['fields'])}")
        print(f"Items: {len(project['items'])}")
        print(f"Related Repositories: {len(project['repositories'])}")
        
        return project
    
    def fetch_issue_with_parent(self, issue_id: str) -> Dict[str, Any]:
        """
        Doğrudan issue ID'si kullanarak parent issue bilgilerini getirir.
        
        Args:
            issue_id: Issue'nun ID'si
            
        Returns:
            Issue ve parent issue bilgileri
        """
        endpoint = "/graphql"
        
        query = """
        query($issueId: ID!) {
          node(id: $issueId) {
            ... on Issue {
              id
              title
              number
              state
              url
              body
              
              # Parent issue field - direct parent
              parent {
                id
                title
                number
                url
              }
              
              # Parent issues - issues this issue tracks
              trackedIssues(first: 5) {
                nodes {
                  id
                  title
                  number
                  url
                }
              }
              
              # Child issues - issues tracking this issue
              trackedInIssues(first: 5) {
                nodes {
                  id
                  title
                  number
                  url
                }
              }
              
              # Related issues - linked issues relationship
              linkedIssues: timelineItems(first: 20, itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT, CROSS_REFERENCED_EVENT]) {
                nodes {
                  ... on ConnectedEvent {
                    id
                    subject {
                      ... on Issue {
                        id
                        title
                        number
                        url
                      }
                    }
                  }
                  ... on DisconnectedEvent {
                    id
                    subject {
                      ... on Issue {
                        id
                        title
                        number
                        url
                      }
                    }
                  }
                  ... on CrossReferencedEvent {
                    source {
                      ... on Issue {
                        id
                        title
                        number
                        url
                      }
                    }
                  }
                }
              }
              
              milestone {
                id
                title
                dueOn
                state
              }
              assignees(first: 5) {
                nodes {
                  login
                  avatarUrl
                }
              }
              repository {
                name
                owner {
                  login
                }
              }
            }
          }
        }
        """
        
        variables = {"issueId": issue_id}
        
        # Special header for GraphQL API
        custom_headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "query": query,
            "variables": variables
        }
        
        print(f"Fetching issue data with parent information for ID: {issue_id}")
        response, status_code = self._make_request("POST", endpoint, data=data, custom_headers=custom_headers)
        
        if status_code != 200 or "errors" in response:
            if "errors" in response:
                errors = response.get("errors", [])
                for error in errors:
                    print(f"GraphQL error: {error.get('message', 'Unknown error')}")
                    if 'type' in error:
                        print(f"Error type: {error.get('type')}")
                    if 'locations' in error:
                        print(f"Error locations: {error.get('locations')}")
            else:
                print(f"Failed to get issue data: {response.get('error', 'Unknown error')}")
            
            return {}
        
        # Extract issue data
        data = response.get("data", {})
        node = data.get("node", {})
        
        if not node:
            print(f"Issue not found with ID: {issue_id}")
            return {}
        
        # Process and return issue data
        issue_data = {
            "id": node.get("id"),
            "title": node.get("title"),
            "number": node.get("number"),
            "state": node.get("state"),
            "url": node.get("url"),
            "body": node.get("body", ""),
            "parent_issues": [],
            "related_issues": [],
            "milestone": None,
            "assignees": [],
            "repository": None
        }
        
        # Extract parent issues - direct parent
        if "parent" in node and node["parent"]:
            parent = node.get("parent", {})
            issue_data["parent_issues"].append({
                "id": parent.get("id"),
                "title": parent.get("title"),
                "number": parent.get("number"),
                "url": parent.get("url"),
                "relationship": "direct_parent"
            })
                
        # Extract parent issues - tracked issues
        if "trackedIssues" in node:
            tracked = node.get("trackedIssues", {}).get("nodes", [])
            for parent in tracked:
                issue_data["parent_issues"].append({
                    "id": parent.get("id"),
                    "title": parent.get("title"),
                    "number": parent.get("number"),
                    "url": parent.get("url"),
                    "relationship": "tracked_issues"
                })
                
        # Extract child issues - tracked in issues
        if "trackedInIssues" in node:
            tracked_in = node.get("trackedInIssues", {}).get("nodes", [])
            for child in tracked_in:
                issue_data["related_issues"].append({
                    "id": child.get("id"),
                    "title": child.get("title"),
                    "number": child.get("number"),
                    "url": child.get("url"),
                    "relationship": "tracked_in"
                })
                
        # Extract related issues from timeline connections
        if "linkedIssues" in node:
            linked = node.get("linkedIssues", {}).get("nodes", [])
            for item in linked:
                # Check for ConnectedEvent or DisconnectedEvent
                if "subject" in item:
                    subject = item.get("subject", {})
                    if subject:
                        issue_data["related_issues"].append({
                            "id": subject.get("id"),
                            "title": subject.get("title"),
                            "number": subject.get("number"),
                            "url": subject.get("url"),
                            "relationship": "linked" 
                        })
                # Check for CrossReferencedEvent
                elif "source" in item:
                    source = item.get("source", {})
                    if source:
                        issue_data["related_issues"].append({
                            "id": source.get("id"),
                            "title": source.get("title"),
                            "number": source.get("number"),
                            "url": source.get("url"),
                            "relationship": "referenced"
                        })
        
        # Extract milestone
        if "milestone" in node and node["milestone"]:
            issue_data["milestone"] = {
                "id": node["milestone"].get("id"),
                "title": node["milestone"].get("title"),
                "due_on": node["milestone"].get("dueOn"),
                "state": node["milestone"].get("state")
            }
        
        # Extract assignees
        if "assignees" in node:
            assignees = node.get("assignees", {}).get("nodes", [])
            for assignee in assignees:
                issue_data["assignees"].append({
                    "login": assignee.get("login"),
                    "avatar_url": assignee.get("avatarUrl")
                })
        
        # Extract repository
        if "repository" in node:
            repo = node.get("repository", {})
            issue_data["repository"] = {
                "name": repo.get("name"),
                "owner": repo.get("owner", {}).get("login")
            }
        
        # Try to find parent issue references in the body
        body = node.get("body", "")
        if body:
            # Different parent-child reference patterns to look for
            parent_number = None
            
            # "Parent: #XX" or "Parent: XX" format
            parent_matches = re.findall(r"Parent:?\s+#?(\d+)", body, re.IGNORECASE)
            if parent_matches:
                parent_number = parent_matches[0]
            
            # "Child of #XX" format
            if not parent_number:
                child_matches = re.findall(r"Child of #?(\d+)", body, re.IGNORECASE)
                if child_matches:
                    parent_number = child_matches[0]
            
            # "Depends on #XX" format
            if not parent_number:
                depends_matches = re.findall(r"Depends on #?(\d+)", body, re.IGNORECASE)
                if depends_matches:
                    parent_number = depends_matches[0]
            
            # "Related to #XX" format
            if not parent_number:
                related_matches = re.findall(r"Related to #?(\d+)", body, re.IGNORECASE)
                if related_matches:
                    parent_number = related_matches[0]
            
            # Found a reference, create parent issue data
            if parent_number:
                repo_name = ""
                repo_owner = ""
                if "repository" in node:
                    repo = node.get("repository", {})
                    repo_name = repo.get("name", "")
                    repo_owner = repo.get("owner", {}).get("login", "")
                
                if repo_name and repo_owner:
                    parent_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{parent_number}"
                    issue_data["parent_issues"].append({
                        "title": f"Issue #{parent_number}",
                        "number": int(parent_number),
                        "url": parent_url,
                        "relationship": "mentioned_in_body"
                    })
        
        return issue_data
    
    def post_process_project_items(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proje verilerinde parent issue bilgisi null olan issue'lar için
        içerik analizine dayalı parent bilgisini günceller. Sadece doğrudan parent
        ilişkisi olan (direct_parent) işlemler için kullanılır.
        
        Args:
            project: Proje verileri
            
        Returns:
            Güncellenmiş proje verileri
        """
        if not project or "items" not in project:
            return project
        
        print("Post-processing project items to find parent issues...")
        
        # Tüm issue'ları bir sözlükte toplayalım (repo/number şeklinde)
        issue_by_identifier = {}
        for item in project["items"]:
            if "content" in item and item["content"].get("number"):
                content = item["content"]
                repo = item.get("repository", {})
                if repo:
                    repo_owner = repo.get("owner", "unknown")
                    repo_name = repo.get("name", "unknown")
                    issue_number = content.get("number")
                    
                    key = f"{repo_owner}/{repo_name}#{issue_number}"
                    issue_by_identifier[key] = item
        
        # Parent ilişkisi güncellenecek öğeleri kontrol edelim
        items_updated = 0
        items_filtered = 0
        
        # Sadece direkt ilişkisi olmayan parent bilgilerini temizleme
        for item in project["items"]:
            if item.get("parent_issue") and item["parent_issue"].get("source") != "direct_parent":
                # direct_parent dışında bir kaynak - temizle
                del item["parent_issue"]
                items_filtered += 1
                
        print(f"Post-processing completed. {items_filtered} non-direct parent relations filtered out.")
        return project 