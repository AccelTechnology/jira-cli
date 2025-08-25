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
    
    def search_users(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for users by email, name, or account ID.
        
        Args:
            query: Search query (email, display name, or account ID)
            max_results: Maximum number of results
            
        Returns:
            List of user data
        """
        params = {
            'query': query,
            'maxResults': max_results
        }
        return self.get('user/search', params)
    
    def get_user_by_account_id(self, account_id: str) -> Dict[str, Any]:
        """Get user details by account ID.
        
        Args:
            account_id: User account ID
            
        Returns:
            User data
        """
        params = {'accountId': account_id}
        return self.get('user', params)
    
    def _parse_mentions_in_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse mentions in text and create ADF content nodes.
        
        Args:
            text: Text that may contain mentions like @username or @email@domain.com
            
        Returns:
            List of ADF content nodes
        """
        import re
        
        content_nodes = []
        last_end = 0
        
        # Pattern to match @username, @email@domain.com, or @accountid:ACCOUNT_ID
        mention_pattern = r'@(?:accountid:([a-f0-9\-]{36})|([a-zA-Z0-9._-]+(?:@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?|[a-zA-Z0-9._-]+))'
        
        for match in re.finditer(mention_pattern, text):
            start, end = match.span()
            
            # Add text before mention
            if start > last_end:
                content_nodes.append({
                    "type": "text",
                    "text": text[last_end:start]
                })
            
            # Extract account ID or search query
            account_id = match.group(1)  # accountid:xxx format
            search_query = match.group(2)  # username or email format
            
            if account_id:
                # Direct account ID provided
                try:
                    user = self.get_user_by_account_id(account_id)
                    content_nodes.append({
                        "type": "mention",
                        "attrs": {
                            "id": account_id,
                            "text": f"@{user.get('displayName', 'User')}"
                        }
                    })
                except:
                    # If user lookup fails, treat as regular text
                    content_nodes.append({
                        "type": "text",
                        "text": match.group(0)
                    })
            elif search_query:
                # Search for user by email or username
                try:
                    users = self.search_users(search_query, max_results=1)
                    if users:
                        user = users[0]
                        content_nodes.append({
                            "type": "mention",
                            "attrs": {
                                "id": user['accountId'],
                                "text": f"@{user.get('displayName', search_query)}"
                            }
                        })
                    else:
                        # No user found, treat as regular text
                        content_nodes.append({
                            "type": "text",
                            "text": match.group(0)
                        })
                except:
                    # If search fails, treat as regular text
                    content_nodes.append({
                        "type": "text",
                        "text": match.group(0)
                    })
            
            last_end = end
        
        # Add remaining text
        if last_end < len(text):
            content_nodes.append({
                "type": "text",
                "text": text[last_end:]
            })
        
        return content_nodes

    def add_comment(self, issue_key: str, body: str, parse_mentions: bool = True, is_markdown: bool = True) -> Dict[str, Any]:
        """Add comment to issue with optional mention support and markdown parsing.
        
        Args:
            issue_key: Issue key
            body: Comment text (may contain mentions like @username or @email@domain.com and markdown)
            parse_mentions: Whether to parse and convert mentions to ADF format
            is_markdown: Whether to parse body as markdown
            
        Returns:
            Created comment data
        """
        if is_markdown and not parse_mentions:
            # Use full markdown parsing (without mention support)
            from .markdown_to_adf import markdown_to_adf
            adf_body = markdown_to_adf(body)
        elif parse_mentions:
            # Parse mentions in text (existing behavior)
            content_nodes = self._parse_mentions_in_text(body)
            adf_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": content_nodes
                    }
                ]
            }
        else:
            # Simple text without mention or markdown parsing
            content_nodes = [{
                "text": body,
                "type": "text"
            }]
            adf_body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": content_nodes
                    }
                ]
            }
        
        return self.post(f'issue/{issue_key}/comment', {'body': adf_body})
    
    def add_comment_with_mentions(self, issue_key: str, body: str, mentions: List[str]) -> Dict[str, Any]:
        """Add comment to issue with explicit mentions.
        
        Args:
            issue_key: Issue key
            body: Comment text
            mentions: List of account IDs, emails, or usernames to mention
            
        Returns:
            Created comment data
        """
        content_nodes = []
        
        # Add main comment text
        if body:
            content_nodes.append({
                "type": "text",
                "text": body
            })
        
        # Add mentions
        for mention in mentions:
            if body:  # Add space before mentions if there's body text
                content_nodes.append({
                    "type": "text", 
                    "text": " "
                })
            
            # Check if mention is already an account ID (UUID format)
            if len(mention) == 36 and '-' in mention:
                # Direct account ID
                try:
                    user = self.get_user_by_account_id(mention)
                    content_nodes.extend([
                        {
                            "type": "mention",
                            "attrs": {
                                "id": mention,
                                "text": f"@{user.get('displayName', 'User')}"
                            }
                        }
                    ])
                except:
                    content_nodes.append({
                        "type": "text",
                        "text": f"@{mention}"
                    })
            else:
                # Search for user
                try:
                    users = self.search_users(mention, max_results=1)
                    if users:
                        user = users[0]
                        content_nodes.append({
                            "type": "mention",
                            "attrs": {
                                "id": user['accountId'],
                                "text": f"@{user.get('displayName', mention)}"
                            }
                        })
                    else:
                        content_nodes.append({
                            "type": "text",
                            "text": f"@{mention}"
                        })
                except:
                    content_nodes.append({
                        "type": "text",
                        "text": f"@{mention}"
                    })
        
        # Create ADF document
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": content_nodes
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
    
    def get_subtasks(self, parent_issue_key: str) -> Dict[str, Any]:
        """Get subtasks of a parent issue.
        
        Args:
            parent_issue_key: Parent issue key
            
        Returns:
            Search results containing subtasks
        """
        jql = f'parent = {parent_issue_key}'
        return self.search_issues(jql)
    
    def create_subtask(self, parent_issue_key: str, subtask_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a subtask under a parent issue.
        
        Args:
            parent_issue_key: Parent issue key
            subtask_data: Subtask creation data
            
        Returns:
            Created subtask data
        """
        # Add parent reference to the subtask data
        subtask_data['fields']['parent'] = {'key': parent_issue_key}
        # Set issue type to Subtask
        subtask_data['fields']['issuetype'] = {'name': 'Subtask'}
        
        return self.create_issue(subtask_data)
    
    def link_subtask_to_parent(self, subtask_key: str, parent_key: str) -> Dict[str, Any]:
        """Link an existing issue as a subtask to a parent.
        
        Args:
            subtask_key: Subtask issue key
            parent_key: Parent issue key
            
        Returns:
            Empty response
        """
        update_data = {
            'fields': {
                'parent': {'key': parent_key}
            }
        }
        return self.update_issue(subtask_key, update_data)