"""Data models for Jira CLI."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class JiraUser(BaseModel):
    """Jira user model."""
    
    account_id: str
    display_name: str
    email_address: Optional[str] = None
    active: bool = True


class JiraStatus(BaseModel):
    """Jira issue status model."""
    
    id: str
    name: str
    category: Optional[str] = None


class JiraPriority(BaseModel):
    """Jira issue priority model."""
    
    id: str
    name: str


class JiraIssueType(BaseModel):
    """Jira issue type model."""
    
    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None


class JiraProject(BaseModel):
    """Jira project model."""
    
    id: str
    key: str
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    lead: Optional[JiraUser] = None


class JiraIssue(BaseModel):
    """Jira issue model."""
    
    id: str
    key: str
    summary: str
    description: Optional[str] = None
    status: JiraStatus
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    priority: Optional[JiraPriority] = None
    issue_type: JiraIssueType
    project: JiraProject
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    resolution: Optional[str] = None
    labels: List[str] = []
    fix_versions: List[str] = []
    components: List[str] = []


class JiraSearchResult(BaseModel):
    """Jira search result model."""
    
    start_at: int
    max_results: int
    total: int
    issues: List[JiraIssue]


class JiraComment(BaseModel):
    """Jira comment model."""
    
    id: str
    body: str
    author: JiraUser
    created: datetime
    updated: Optional[datetime] = None


class JiraTransition(BaseModel):
    """Jira transition model."""
    
    id: str
    name: str
    to: JiraStatus
    fields: Dict[str, Any] = {}