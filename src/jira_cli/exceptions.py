"""Exception classes for Jira CLI."""


class JiraCliError(Exception):
    """Base exception for Jira CLI."""
    pass


class AuthenticationError(JiraCliError):
    """Authentication failed."""
    pass


class JiraApiError(JiraCliError):
    """Jira API error."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ConfigurationError(JiraCliError):
    """Configuration error."""
    pass


class ValidationError(JiraCliError):
    """Data validation error."""
    pass