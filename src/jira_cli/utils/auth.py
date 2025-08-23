"""Authentication utilities for Jira CLI."""

import os
from typing import Optional, Tuple
from ..exceptions import AuthenticationError, ConfigurationError


def get_jira_credentials() -> Tuple[str, str, str]:
    """Get Jira credentials from environment variables.
    
    Returns:
        Tuple of (base_url, email, api_token)
        
    Raises:
        ConfigurationError: If required environment variables are not set
    """
    base_url = os.getenv('JIRA_URL', 'https://acceldevs.atlassian.net')
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    if not email:
        raise ConfigurationError(
            "JIRA_EMAIL environment variable is required. "
            "Set it with: export JIRA_EMAIL=your.email@example.com"
        )
    
    if not api_token:
        raise ConfigurationError(
            "JIRA_API_TOKEN environment variable is required. "
            "Create an API token at: https://id.atlassian.com/manage-profile/security/api-tokens"
        )
    
    return base_url, email, api_token


def get_auth_headers(email: str, api_token: str) -> dict:
    """Get authentication headers for Jira API requests.
    
    Args:
        email: Jira user email
        api_token: Jira API token
        
    Returns:
        Dictionary with authentication headers
    """
    import base64
    
    credentials = f"{email}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }