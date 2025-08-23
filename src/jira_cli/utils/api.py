"""API utilities for Jira CLI."""

import json
from typing import Dict, Any, Optional, List
import requests
from requests.exceptions import RequestException, Timeout

from ..exceptions import JiraApiError, AuthenticationError
from .auth import get_jira_credentials, get_auth_headers


class JiraApiClient:
    """Jira API client."""
    
    def __init__(self, base_url: Optional[str] = None, email: Optional[str] = None, api_token: Optional[str] = None):
        """Initialize Jira API client.
        
        Args:
            base_url: Jira base URL (defaults to env var JIRA_URL)
            email: Jira user email (defaults to env var JIRA_EMAIL)
            api_token: Jira API token (defaults to env var JIRA_API_TOKEN)
        """
        if not all([base_url, email, api_token]):
            base_url, email, api_token = get_jira_credentials()
        
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.headers = get_auth_headers(email, api_token)
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Jira API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments passed to requests
            
        Returns:
            JSON response data
            
        Raises:
            JiraApiError: If API request fails
            AuthenticationError: If authentication fails
        """
        url = f"{self.base_url}/rest/api/3/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid Jira credentials")
            elif response.status_code == 403:
                raise JiraApiError("Insufficient permissions", response.status_code)
            elif response.status_code == 404:
                raise JiraApiError("Resource not found", response.status_code)
            elif response.status_code >= 400:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'errorMessages' in error_data:
                        error_msg = '; '.join(error_data['errorMessages'])
                    elif 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    error_msg = response.text or error_msg
                
                raise JiraApiError(error_msg, response.status_code)
            
            if response.content:
                return response.json()
            return {}
            
        except RequestException as e:
            raise JiraApiError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request('PUT', endpoint, json=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request('DELETE', endpoint)
    
    def search_issues(self, jql: str, fields: Optional[List[str]] = None, max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """Search for issues using JQL.
        
        Args:
            jql: JQL query string
            fields: List of fields to return
            max_results: Maximum number of results
            start_at: Starting index for pagination
            
        Returns:
            Search results
        """
        params = {
            'jql': jql,
            'maxResults': max_results,
            'startAt': start_at
        }
        
        if fields:
            params['fields'] = ','.join(fields)
        
        return self.get('search', params)
    
    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get issue by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: List of fields to return
            
        Returns:
            Issue data
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        return self.get(f'issue/{issue_key}', params)
    
    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new issue.
        
        Args:
            issue_data: Issue creation data
            
        Returns:
            Created issue data
        """
        return self.post('issue', issue_data)
    
    def update_issue(self, issue_key: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing issue.
        
        Args:
            issue_key: Issue key
            issue_data: Update data
            
        Returns:
            Empty response
        """
        return self.put(f'issue/{issue_key}', issue_data)
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        return self.get('project')
    
    def get_issue_types(self) -> List[Dict[str, Any]]:
        """Get all issue types."""
        return self.get('issuetype')
    
    def get_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for issue.
        
        Args:
            issue_key: Issue key
            
        Returns:
            Transitions data
        """
        return self.get(f'issue/{issue_key}/transitions')
    
    def transition_issue(self, issue_key: str, transition_id: str, fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transition issue to new status.
        
        Args:
            issue_key: Issue key
            transition_id: ID of transition to perform
            fields: Additional fields to update
            
        Returns:
            Empty response
        """
        data = {'transition': {'id': transition_id}}
        if fields:
            data['fields'] = fields
        
        return self.post(f'issue/{issue_key}/transitions', data)
    
    def add_comment(self, issue_key: str, body: str) -> Dict[str, Any]:
        """Add comment to issue.
        
        Args:
            issue_key: Issue key
            body: Comment text
            
        Returns:
            Created comment data
        """
        # Convert plain text to Atlassian Document Format (ADF)
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": body,
                            "type": "text"
                        }
                    ]
                }
            ]
        }
        return self.post(f'issue/{issue_key}/comment', {'body': adf_body})
    
    def delete_issue(self, issue_key: str) -> Dict[str, Any]:
        """Delete an issue.
        
        Args:
            issue_key: Issue key
            
        Returns:
            Empty response
        """
        return self.delete(f'issue/{issue_key}')
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        return self.get('myself')