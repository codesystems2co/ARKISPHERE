#!/usr/bin/env python3
import os
import sys
import secrets
from urllib.parse import quote
from bitbucket.service import BitbucketService, BitbucketAccount # Assuming this is the desired import
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    # Bitbucket OAuth app credentials
    CLIENT_ID = "YVW7qCHyF5YhERyfdh"
    CLIENT_SECRET = "ynJp4KVEBMPyuPk5rHrpZqJFs7H9EHZd"
    REDIRECT_URI = "https://arkiphere.cloud/en/bitbucket/callback"
    
    # Initialize the Bitbucket service
    service = BitbucketService(CLIENT_ID, CLIENT_SECRET)
    
    # Generate a secure state token to prevent CSRF
    state = secrets.token_urlsafe(32)
    
    # Step 1: Get the authorization URL with corrected scopes
    auth_url = (
        f"{service.oauth_base_url}/authorize?"
        f"client_id={service.client_id}&"
        f"response_type=code&"
        f"state={state}&"
        f"scope=repository account pullrequest:write webhook email&" # email scope included
        f"redirect_uri={quote(REDIRECT_URI)}"
    )
    print("\n=== Step 1: Authorization URL ===")
    print(f"Open this URL in your browser:\n{auth_url}")
    
    # Step 2: Get the authorization code from user input
    print("\n=== Step 2: Enter Authorization Code ===")
    auth_code = input("After authorizing, enter the code from the redirect URL: ")
    
    try:
        # Step 3: Exchange the code for access token
        print("\n=== Step 3: Getting Access Token ===")
        token_info = service.get_access_token(auth_code, REDIRECT_URI)
        access_token = token_info['access_token']
        print("Access token obtained successfully!")
        
        # --- BEGIN DYNAMIC WORKSPACE FETCHING ---
        print("\nFetching workspace information...")
        workspaces = service.get_workspaces(access_token)
        target_workspace_slug = None
        if workspaces:
            first_workspace = workspaces[0]
            target_workspace_slug = first_workspace.get('slug')
            print(f"Using workspace slug: '{target_workspace_slug}' (Name: '{first_workspace.get('name')}')")
        
        if not target_workspace_slug:
            print("Error: Could not dynamically determine workspace slug. Please check API permissions or workspace membership.")
            print("Falling back to previously hardcoded 'arkiphere' for now, but this should be fixed.")
            target_workspace_slug = "arkiphere"
        # --- END DYNAMIC WORKSPACE FETCHING ---
        
        # Step 4: Initialize account and get user info
        print("\n=== Step 4: Getting User Info ===")
        account = BitbucketAccount(access_token, service)
        user_info = account.user_info
        print("Debug - Full user info response:", json.dumps(user_info, indent=2))
        print(f"Logged in as: {user_info['username']}")

        # Step 4.5: Get User Emails
        print("\n=== Step 4.5: Getting User Emails ===")
        try:
            user_emails_list = account.get_user_emails()
            if user_emails_list:
                print("User email addresses:")
                for email_info in user_emails_list:
                    email_address = email_info.get('email', 'N/A')
                    is_primary = email_info.get('is_primary', False)
                    is_confirmed = email_info.get('is_confirmed', False)
                    print(f"  - Email: {email_address} (Primary: {is_primary}, Confirmed: {is_confirmed})")
            else:
                print("No email addresses found for the user. This could be due to privacy settings or missing 'email' scope during authorization.")
        except Exception as e:
            print(f"Error fetching user emails: {str(e)}")
            
        # Step 5: List repositories
        print("\n=== Step 5: Listing Repositories ===")
        print(f"Attempting to list repositories for workspace: '{target_workspace_slug}'")
        repos = account.get_repositories().list(workspace=target_workspace_slug)
        print("\nYour repositories:")
        for repo in repos:
            print(f"- {repo['name']}: {repo['description'] or 'No description'}")
            
            # Step 6: List branches for each repository
            print(f"\nBranches in {repo['name']}:")
            branches = account.get_repositories().get_branches(
                repo_slug=repo['slug'],
                workspace=target_workspace_slug 
            ).list()
            for branch in branches:
                print(f"  - {branch['name']}")
            print()
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
