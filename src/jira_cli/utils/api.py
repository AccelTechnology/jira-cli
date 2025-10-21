"""API utilities for Jira CLI."""

import json
from typing import Dict, Any, Optional, List
import requests
from requests.exceptions import RequestException, Timeout

from ..exceptions import JiraApiError, AuthenticationError
from .auth import get_jira_credentials, get_auth_headers


class JiraApiClient:
    """Jira API client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        """Initialize Jira API client.

        Args:
            base_url: Jira base URL (defaults to env var JIRA_URL)
            email: Jira user email (defaults to env var JIRA_EMAIL)
            api_token: Jira API token (defaults to env var JIRA_API_TOKEN)
        """
        if not all([base_url, email, api_token]):
            base_url, email, api_token = get_jira_credentials()

        self.base_url = base_url.rstrip("/")
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
                    error_parts = []

                    # Handle errorMessages array
                    if "errorMessages" in error_data and error_data["errorMessages"]:
                        error_parts.extend(error_data["errorMessages"])

                    # Handle errors object (field-specific errors)
                    if "errors" in error_data and error_data["errors"]:
                        for field, message in error_data["errors"].items():
                            error_parts.append(f"{field}: {message}")

                    # Handle single message field
                    if "message" in error_data:
                        error_parts.append(error_data["message"])

                    if error_parts:
                        error_msg = "; ".join(error_parts)
                    else:
                        error_msg = response.text or error_msg
                except:
                    error_msg = response.text or error_msg

                raise JiraApiError(error_msg, response.status_code)

            if response.content:
                return response.json()
            return {}

        except RequestException as e:
            raise JiraApiError(f"Request failed: {str(e)}")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", endpoint, json=data)

    def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, json=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint)

    def search_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> Dict[str, Any]:
        """Search for issues using JQL.

        Args:
            jql: JQL query string
            fields: List of fields to return
            max_results: Maximum number of results
            start_at: Starting index for pagination

        Returns:
            Search results
        """
        params = {"jql": jql, "maxResults": max_results, "startAt": start_at}

        if fields:
            params["fields"] = ",".join(fields)

        return self.get("search/jql", params)

    def get_issue(
        self, issue_key: str, fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get issue by key.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: List of fields to return

        Returns:
            Issue data
        """
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        return self.get(f"issue/{issue_key}", params)

    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new issue.

        Args:
            issue_data: Issue creation data

        Returns:
            Created issue data
        """
        return self.post("issue", issue_data)

    def update_issue(
        self, issue_key: str, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing issue.

        Args:
            issue_key: Issue key
            issue_data: Update data

        Returns:
            Empty response
        """
        return self.put(f"issue/{issue_key}", issue_data)

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        return self.get("project")

    def get_issue_types(self) -> List[Dict[str, Any]]:
        """Get all issue types."""
        return self.get("issuetype")

    def get_project_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get issue types available for a specific project.

        Args:
            project_key: Project key (e.g., 'PD')

        Returns:
            List of issue types available in the project
        """
        try:
            project_data = self.get(f"project/{project_key}")
            if "issueTypes" in project_data:
                return project_data["issueTypes"]
            else:
                # Fallback to project creation meta to get issue types
                creation_meta = self.get(
                    f"issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes"
                )
                if creation_meta.get("projects"):
                    return creation_meta["projects"][0].get("issueTypes", [])
                return []
        except Exception:
            # If project-specific lookup fails, return global issue types
            return self.get_issue_types()

    def get_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for issue.

        Args:
            issue_key: Issue key

        Returns:
            Transitions data
        """
        return self.get(f"issue/{issue_key}/transitions")

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transition issue to new status.

        Args:
            issue_key: Issue key
            transition_id: ID of transition to perform
            fields: Additional fields to update

        Returns:
            Empty response
        """
        data = {"transition": {"id": transition_id}}
        if fields:
            data["fields"] = fields

        return self.post(f"issue/{issue_key}/transitions", data)

    def search_users(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for users by email, name, or account ID.

        Args:
            query: Search query (email, display name, or account ID)
            max_results: Maximum number of results

        Returns:
            List of user data
        """
        params = {"query": query, "maxResults": max_results}
        return self.get("user/search", params)

    def get_user_by_account_id(self, account_id: str) -> Dict[str, Any]:
        """Get user details by account ID.

        Args:
            account_id: User account ID

        Returns:
            User data
        """
        params = {"accountId": account_id}
        return self.get("user", params)

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
        mention_pattern = r"@(?:accountid:([a-f0-9\-]{36})|([a-zA-Z0-9._-]+(?:@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?|[a-zA-Z0-9._-]+))"

        for match in re.finditer(mention_pattern, text):
            start, end = match.span()

            # Add text before mention
            if start > last_end:
                content_nodes.append({"type": "text", "text": text[last_end:start]})

            # Extract account ID or search query
            account_id = match.group(1)  # accountid:xxx format
            search_query = match.group(2)  # username or email format

            if account_id:
                # Direct account ID provided
                try:
                    user = self.get_user_by_account_id(account_id)
                    content_nodes.append(
                        {
                            "type": "mention",
                            "attrs": {
                                "id": account_id,
                                "text": f"@{user.get('displayName', 'User')}",
                            },
                        }
                    )
                except:
                    # If user lookup fails, treat as regular text
                    content_nodes.append({"type": "text", "text": match.group(0)})
            elif search_query:
                # Search for user by email or username
                try:
                    users = self.search_users(search_query, max_results=1)
                    if users:
                        user = users[0]
                        content_nodes.append(
                            {
                                "type": "mention",
                                "attrs": {
                                    "id": user["accountId"],
                                    "text": f"@{user.get('displayName', search_query)}",
                                },
                            }
                        )
                    else:
                        # No user found, treat as regular text
                        content_nodes.append({"type": "text", "text": match.group(0)})
                except:
                    # If search fails, treat as regular text
                    content_nodes.append({"type": "text", "text": match.group(0)})

            last_end = end

        # Add remaining text
        if last_end < len(text):
            content_nodes.append({"type": "text", "text": text[last_end:]})

        return content_nodes

    def _process_mentions_in_adf(self, adf_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process @mentions in an ADF document structure.

        Recursively walks through the ADF document and replaces text nodes
        containing @mentions with proper mention nodes.

        Args:
            adf_doc: ADF document structure

        Returns:
            Updated ADF document with mentions processed
        """
        import re
        from copy import deepcopy

        doc = deepcopy(adf_doc)

        def process_content_list(content_list):
            """Process a list of content nodes."""
            new_content = []

            for node in content_list:
                if node.get("type") == "text" and "text" in node:
                    # Check if this text node contains mentions
                    text = node["text"]
                    mention_pattern = r"@(?:accountid:([a-f0-9\-]{36})|([a-zA-Z0-9._-]+(?:@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?|[a-zA-Z0-9._-]+))"

                    if re.search(mention_pattern, text):
                        # Parse mentions and split into multiple nodes
                        parsed_nodes = self._parse_mentions_in_text(text)
                        # Preserve marks from original node
                        if "marks" in node:
                            for parsed_node in parsed_nodes:
                                if parsed_node.get("type") == "text":
                                    parsed_node["marks"] = node["marks"]
                        new_content.extend(parsed_nodes)
                    else:
                        new_content.append(node)
                elif "content" in node:
                    # Recursively process child content
                    node["content"] = process_content_list(node["content"])
                    new_content.append(node)
                else:
                    new_content.append(node)

            return new_content

        if "content" in doc:
            doc["content"] = process_content_list(doc["content"])

        return doc

    def add_comment(
        self,
        issue_key: str,
        body: str,
        parse_mentions: bool = True,
        is_markdown: bool = True,
    ) -> Dict[str, Any]:
        """Add comment to issue with optional mention support and markdown parsing.

        Args:
            issue_key: Issue key
            body: Comment text (may contain mentions like @username or @email@domain.com and markdown)
            parse_mentions: Whether to parse and convert mentions to ADF format
            is_markdown: Whether to parse body as markdown

        Returns:
            Created comment data
        """
        if is_markdown:
            # Use full markdown parsing
            from .markdown_to_adf import markdown_to_adf
            adf_body = markdown_to_adf(body)

            # If mention parsing is enabled, process mentions in the ADF structure
            if parse_mentions:
                adf_body = self._process_mentions_in_adf(adf_body)
        elif parse_mentions:
            # Parse mentions only (no markdown)
            content_nodes = self._parse_mentions_in_text(body)
            adf_body = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": content_nodes}],
            }
        else:
            # Simple text without mention or markdown parsing
            content_nodes = [{"text": body, "type": "text"}]
            adf_body = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": content_nodes}],
            }

        return self.post(f"issue/{issue_key}/comment", {"body": adf_body})

    def add_comment_with_mentions(
        self, issue_key: str, body: str, mentions: List[str]
    ) -> Dict[str, Any]:
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
            content_nodes.append({"type": "text", "text": body})

        # Add mentions
        for mention in mentions:
            if body:  # Add space before mentions if there's body text
                content_nodes.append({"type": "text", "text": " "})

            # Check if mention is already an account ID (UUID format)
            if len(mention) == 36 and "-" in mention:
                # Direct account ID
                try:
                    user = self.get_user_by_account_id(mention)
                    content_nodes.extend(
                        [
                            {
                                "type": "mention",
                                "attrs": {
                                    "id": mention,
                                    "text": f"@{user.get('displayName', 'User')}",
                                },
                            }
                        ]
                    )
                except:
                    content_nodes.append({"type": "text", "text": f"@{mention}"})
            else:
                # Search for user
                try:
                    users = self.search_users(mention, max_results=1)
                    if users:
                        user = users[0]
                        content_nodes.append(
                            {
                                "type": "mention",
                                "attrs": {
                                    "id": user["accountId"],
                                    "text": f"@{user.get('displayName', mention)}",
                                },
                            }
                        )
                    else:
                        content_nodes.append({"type": "text", "text": f"@{mention}"})
                except:
                    content_nodes.append({"type": "text", "text": f"@{mention}"})

        # Create ADF document
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": content_nodes}],
        }

        return self.post(f"issue/{issue_key}/comment", {"body": adf_body})

    def delete_issue(self, issue_key: str) -> Dict[str, Any]:
        """Delete an issue.

        Args:
            issue_key: Issue key

        Returns:
            Empty response
        """
        return self.delete(f"issue/{issue_key}")

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        return self.get("myself")

    def get_subtasks(self, parent_issue_key: str) -> Dict[str, Any]:
        """Get subtasks of a parent issue.

        Args:
            parent_issue_key: Parent issue key

        Returns:
            Search results containing subtasks
        """
        jql = f"parent = {parent_issue_key}"
        fields = [
            "summary",
            "issuetype",
            "status",
            "assignee",
            "reporter",
            "priority",
            "duedate",
            "created",
            "updated",
        ]
        return self.search_issues(jql, fields)

    def create_subtask(
        self, parent_issue_key: str, subtask_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a subtask under a parent issue.

        Args:
            parent_issue_key: Parent issue key
            subtask_data: Subtask creation data

        Returns:
            Created subtask data
        """
        # Add parent reference to the subtask data
        subtask_data["fields"]["parent"] = {"key": parent_issue_key}

        # Dynamically resolve subtask issue type to handle project-specific configurations
        if "issuetype" not in subtask_data["fields"]:
            try:
                # First, get the parent issue to determine the project
                parent_issue = self.get_issue(parent_issue_key, fields=["project"])
                project_key = parent_issue["fields"]["project"]["key"]

                # Get project-specific issue types
                issue_types = self.get_project_issue_types(project_key)

                # Look for subtask types that match - check both 'subtask' field and common names
                subtask_types = []
                for it in issue_types:
                    if it.get("subtask") == True or it["name"].lower() in [
                        "subtask",
                        "sub-task",
                        "sub task",
                    ]:
                        subtask_types.append(it)

                if subtask_types:
                    # Use the first available subtask type ID for better reliability
                    subtask_type_id = subtask_types[0]["id"]
                    subtask_data["fields"]["issuetype"] = {"id": subtask_type_id}

                    # Debug info to help troubleshooting
                    print(
                        f"ℹ Using subtask type: {subtask_types[0]['name']} (ID: {subtask_type_id})"
                    )
                else:
                    # If no subtask types found in project, try global fallback
                    global_issue_types = self.get_issue_types()
                    global_subtask_types = [
                        it
                        for it in global_issue_types
                        if it.get("subtask")
                        and it["name"].lower() in ["subtask", "sub-task", "sub task"]
                    ]

                    if global_subtask_types:
                        subtask_type_id = global_subtask_types[0]["id"]
                        subtask_data["fields"]["issuetype"] = {"id": subtask_type_id}
                        print(
                            f"ℹ Using global subtask type: {global_subtask_types[0]['name']} (ID: {subtask_type_id})"
                        )
                    else:
                        # Final fallback to name-based approach
                        subtask_data["fields"]["issuetype"] = {"name": "Sub-task"}
                        print("ℹ Using fallback subtask type name: Sub-task")

            except Exception as e:
                # Final fallback to standard name
                subtask_data["fields"]["issuetype"] = {"name": "Sub-task"}
                print(f"ℹ Using fallback due to error: {e}")

        return self.create_issue(subtask_data)

    def link_subtask_to_parent(
        self, subtask_key: str, parent_key: str
    ) -> Dict[str, Any]:
        """Link an existing issue as a subtask to a parent.

        Args:
            subtask_key: Subtask issue key
            parent_key: Parent issue key

        Returns:
            Empty response
        """
        update_data = {"fields": {"parent": {"key": parent_key}}}
        return self.update_issue(subtask_key, update_data)

    def get_watchers(self, issue_key: str) -> Dict[str, Any]:
        """Get watchers for an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')

        Returns:
            Watchers data
        """
        return self.get(f"issue/{issue_key}/watchers")

    def add_watcher(
        self, issue_key: str, account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a watcher to an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            account_id: Account ID of user to add as watcher (optional, defaults to current user)

        Returns:
            Empty response
        """
        data = account_id if account_id else None
        return self.post(f"issue/{issue_key}/watchers", data)

    def remove_watcher(
        self, issue_key: str, account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove a watcher from an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            account_id: Account ID of user to remove as watcher

        Returns:
            Empty response
        """
        params = {"accountId": account_id} if account_id else {}
        return self._make_request(
            "DELETE", f"issue/{issue_key}/watchers", params=params
        )

    def get_worklogs(
        self, issue_key: str, start_at: int = 0, max_results: int = 50
    ) -> Dict[str, Any]:
        """Get worklogs for an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            start_at: Starting index for pagination
            max_results: Maximum number of results

        Returns:
            Worklogs data
        """
        params = {"startAt": start_at, "maxResults": max_results}
        return self.get(f"issue/{issue_key}/worklog", params)

    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        comment: Optional[str] = None,
        started: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a worklog to an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            time_spent: Time spent (e.g., '1h 30m', '2d', '4h')
            comment: Optional comment for the worklog
            started: Optional start time (ISO 8601 format, defaults to now)

        Returns:
            Created worklog data
        """
        data = {"timeSpent": time_spent}

        if comment:
            data["comment"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"text": comment, "type": "text"}],
                    }
                ],
            }

        if started:
            data["started"] = started

        return self.post(f"issue/{issue_key}/worklog", data)

    def update_worklog(
        self,
        issue_key: str,
        worklog_id: str,
        time_spent: Optional[str] = None,
        comment: Optional[str] = None,
        started: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a worklog.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            worklog_id: Worklog ID
            time_spent: Time spent (e.g., '1h 30m', '2d', '4h')
            comment: Optional comment for the worklog
            started: Optional start time (ISO 8601 format)

        Returns:
            Updated worklog data
        """
        data = {}

        if time_spent:
            data["timeSpent"] = time_spent

        if comment:
            data["comment"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"text": comment, "type": "text"}],
                    }
                ],
            }

        if started:
            data["started"] = started

        return self.put(f"issue/{issue_key}/worklog/{worklog_id}", data)

    def delete_worklog(self, issue_key: str, worklog_id: str) -> Dict[str, Any]:
        """Delete a worklog.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            worklog_id: Worklog ID

        Returns:
            Empty response
        """
        return self._make_request("DELETE", f"issue/{issue_key}/worklog/{worklog_id}")

    def get_attachment(self, attachment_id: str) -> Dict[str, Any]:
        """Get attachment metadata.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment metadata
        """
        return self.get(f"attachment/{attachment_id}")

    def download_attachment(self, attachment_id: str) -> bytes:
        """Download attachment content.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment content as bytes
        """
        url = f"{self.base_url}/rest/api/3/attachment/content/{attachment_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    def upload_attachment(self, issue_key: str, file_path: str) -> List[Dict[str, Any]]:
        """Upload an attachment to an issue.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            file_path: Path to the file to upload

        Returns:
            List of uploaded attachment data
        """
        import os

        if not os.path.exists(file_path):
            raise JiraApiError(f"File not found: {file_path}")

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"

        # Special headers required for attachments
        headers = self.headers.copy()
        headers["X-Atlassian-Token"] = "no-check"
        del headers["Content-Type"]  # Let requests set this for multipart

        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            }
            response = self.session.post(url, files=files, headers=headers)

        if response.status_code not in [200, 201]:
            raise JiraApiError(f"Upload failed: {response.status_code} {response.text}")

        return response.json()

    def delete_attachment(self, attachment_id: str) -> Dict[str, Any]:
        """Delete an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            Empty response
        """
        return self._make_request("DELETE", f"attachment/{attachment_id}")

    def bulk_transition_issues(
        self, transitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk transition multiple issues.

        Args:
            transitions: List of transition requests, each containing:
                - issueIds: List of issue IDs or keys
                - transition: Dict with 'id' field for transition ID

        Returns:
            Bulk operation result
        """
        data = {"transitions": transitions}
        return self.post("bulk/issues/transition", data)

    def bulk_edit_issues(
        self, issue_ids: List[str], fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk edit multiple issues.

        Args:
            issue_ids: List of issue IDs or keys
            fields: Dictionary of fields to update

        Returns:
            Bulk operation result
        """
        data = {"issueIds": issue_ids, "fields": fields}
        return self.post("bulk/issues/fields", data)

    def bulk_watch_issues(self, issue_ids: List[str]) -> Dict[str, Any]:
        """Bulk watch multiple issues.

        Args:
            issue_ids: List of issue IDs or keys

        Returns:
            Bulk operation result
        """
        data = {"issueIds": issue_ids}
        return self.post("bulk/issues/watch", data)

    def bulk_unwatch_issues(self, issue_ids: List[str]) -> Dict[str, Any]:
        """Bulk unwatch multiple issues.

        Args:
            issue_ids: List of issue IDs or keys

        Returns:
            Bulk operation result
        """
        data = {"issueIds": issue_ids}
        return self.post("bulk/issues/unwatch", data)
