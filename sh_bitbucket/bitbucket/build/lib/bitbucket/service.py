import json
import requests
from atlassian import Bitbucket
from typing import Dict, Optional, Any, List

class BitbucketService:
    """Base service class for Bitbucket OAuth and API operations"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_base_url = "https://bitbucket.org/site/oauth2"
        self.api_base_url = "https://api.bitbucket.org/2.0"
        
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Get the authorization URL for OAuth flow"""
        scopes = "repository account pullrequest:write webhook"
        return (
            f"{self.oauth_base_url}/authorize?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"state={state}&"
            f"scope={scopes}&"
            f"redirect_uri={redirect_uri}"
        )
    
    def get_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_url = f"{self.oauth_base_url}/access_token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(
            token_url,
            auth=(self.client_id, self.client_secret),
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")
            
        return response.json()
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token"""
        token_url = f"{self.oauth_base_url}/access_token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(
            token_url,
            auth=(self.client_id, self.client_secret),
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.text}")
            
        return response.json()

    def get_workspaces(self, access_token: str) -> List[Dict[str, Any]]:
        """List all workspaces the authenticated user is a member of."""
        print("\nFetching workspaces from /2.0/workspaces...")
        response_data = self._make_request('GET', 'workspaces', access_token)
        
        if 'values' in response_data and isinstance(response_data['values'], list):
            print(f"Successfully fetched {len(response_data['values'])} workspace(s).")
            # For debugging, print the slugs of fetched workspaces
            # for ws in response_data['values']:
            #    print(f"  - Found workspace slug: {ws.get('slug')}, name: {ws.get('name')}")
            return response_data['values']
        
        print(f"Warning: Could not parse workspaces from API response or no workspaces found. Response: {response_data}")
        return []

    def _make_request(self, method: str, endpoint: str, access_token: str, **kwargs) -> Dict:
        """Make an authenticated request to Bitbucket API"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        url = f"{self.api_base_url}/{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code not in (200, 201):
            raise Exception(f"API request failed: {response.text}")
            
        return response.json()

class BitbucketAccount:
    """Class to manage Bitbucket account operations"""
    
    def __init__(self, access_token: str, service: BitbucketService):
        self.access_token = access_token
        self.service = service
        self._user_info = None
        
    @property
    def user_info(self) -> Dict[str, Any]:
        """Get cached or fetch user information"""
        if not self._user_info:
            self._user_info = self.service._make_request('GET', 'user', self.access_token)
            print("\nDebug - Full User Info Response:", json.dumps(self._user_info, indent=2))
        return self._user_info
    
    @property
    def username(self) -> str:
        """Get the username of the authenticated user"""
        return self.user_info['username']
    
    @property
    def workspace(self) -> str:
        """Get the workspace identifier for the authenticated user"""
        return self.username  # Always use username as the workspace identifier
    
    def get_repositories(self) -> 'BitbucketRepositories':
        """Get repositories manager for this account"""
        return BitbucketRepositories(self.access_token, self.service, self)

    def get_user_emails(self) -> List[Dict[str, Any]]:
        """Get email addresses for the authenticated user."""
        print("\nFetching user emails from /2.0/user/emails...")
        response_data = self.service._make_request('GET', 'user/emails', self.access_token)
        emails = response_data.get('values', [])
        if emails:
            print(f"Successfully fetched {len(emails)} email address(es).")
        else:
            print("No email addresses returned by the API. Check scopes or user email visibility.")
        return emails

class BitbucketRepositories:
    """Class to manage Bitbucket repositories"""
    
    def __init__(self, access_token: str, service: BitbucketService, account: BitbucketAccount):
        self.access_token = access_token
        self.service = service
        self.account = account
        
    def list(self, workspace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List repositories for the account or specific workspace"""
        account_username = self.account.username
        resolved_workspace = workspace or account_username

        # --- BEGIN DEBUG BLOCK ---
        print(f"\n--- Debugging BitbucketRepositories.list ---")
        print(f"Passed 'workspace' argument: {workspace}")
        print(f"Value from self.account.username: '{account_username}' (Type: {type(account_username)})")
        print(f"Final 'resolved_workspace' for API call: '{resolved_workspace}' (Type: {type(resolved_workspace)})")
        endpoint = f"repositories/{resolved_workspace}"
        print(f"Constructed API endpoint: '{endpoint}'")
        print(f"--- End Debugging BitbucketRepositories.list ---\n")
        # --- END DEBUG BLOCK ---
        
        response = self.service._make_request('GET', endpoint, self.access_token)
        return response['values']
    
    def get(self, repo_slug: str, workspace: Optional[str] = None) -> Dict[str, Any]:
        """Get specific repository information"""
        workspace = workspace or self.account.username
        endpoint = f"repositories/{workspace}/{repo_slug}"
        return self.service._make_request('GET', endpoint, self.access_token)
    
    def get_branches(self, repo_slug: str, workspace: Optional[str] = None) -> 'BitbucketBranches':
        """Get branches manager for a specific repository"""
        workspace = workspace or self.account.username
        return BitbucketBranches(self.access_token, self.service, repo_slug, workspace)

class BitbucketBranches:
    """Class to manage repository branches"""
    
    def __init__(self, access_token: str, service: BitbucketService, repo_slug: str, workspace: str):
        self.access_token = access_token
        self.service = service
        self.repo_slug = repo_slug
        self.workspace = workspace
        
    def list(self) -> List[Dict[str, Any]]:
        """List all branches in the repository"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/refs/branches"
        response = self.service._make_request('GET', endpoint, self.access_token)
        return response['values']
    
    def get(self, branch_name: str) -> Dict[str, Any]:
        """Get specific branch information"""
        endpoint = f"repositories/{self.workspace}/{self.repo_slug}/refs/branches/{branch_name}"
        return self.service._make_request('GET', endpoint, self.access_token)