"""Validation decorators and utilities for Jira CLI commands."""

import functools
from typing import Any, Callable, List, Optional, Union

from .error_handling import InputValidator, ValidationError, handle_api_error
from ..exceptions import JiraCliError


def validate_issue_key(param_name: str = "issue_key", command_context: str = ""):
    """Decorator to validate issue key parameter.

    Args:
        param_name: Name of the parameter containing the issue key
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs:
                    kwargs[param_name] = InputValidator.validate_issue_key(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_project_key(param_name: str = "project_key", command_context: str = ""):
    """Decorator to validate project key parameter.

    Args:
        param_name: Name of the parameter containing the project key
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs:
                    kwargs[param_name] = InputValidator.validate_project_key(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_email(param_name: str = "email", command_context: str = ""):
    """Decorator to validate email parameter.

    Args:
        param_name: Name of the parameter containing the email
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs and kwargs[param_name]:
                    kwargs[param_name] = InputValidator.validate_email(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_date(param_name: str = "date", command_context: str = ""):
    """Decorator to validate date parameter.

    Args:
        param_name: Name of the parameter containing the date
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs and kwargs[param_name]:
                    kwargs[param_name] = InputValidator.validate_date_format(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_time_spent(param_name: str = "time_spent", command_context: str = ""):
    """Decorator to validate time spent parameter.

    Args:
        param_name: Name of the parameter containing the time spent
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs and kwargs[param_name]:
                    kwargs[param_name] = InputValidator.validate_time_format(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_jql(param_name: str = "jql", command_context: str = ""):
    """Decorator to validate JQL query parameter.

    Args:
        param_name: Name of the parameter containing the JQL query
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs:
                    kwargs[param_name] = InputValidator.validate_jql_query(
                        kwargs[param_name],
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_required(param_names: Union[str, List[str]], command_context: str = ""):
    """Decorator to validate required parameters.

    Args:
        param_names: Name or list of names of required parameters
        command_context: Command context for error messages
    """
    if isinstance(param_names, str):
        param_names = [param_names]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                for param_name in param_names:
                    if param_name in kwargs:
                        kwargs[param_name] = InputValidator.validate_required_parameter(
                            kwargs[param_name],
                            param_name,
                            command_context
                            or f"{func.__module__.split('.')[-1]} {func.__name__}",
                        )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_choice(
    param_name: str, valid_choices: List[str], command_context: str = ""
):
    """Decorator to validate choice parameter.

    Args:
        param_name: Name of the parameter to validate
        valid_choices: List of valid choice values
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if param_name in kwargs and kwargs[param_name]:
                    kwargs[param_name] = InputValidator.validate_choice_parameter(
                        kwargs[param_name],
                        valid_choices,
                        param_name,
                        command_context
                        or f"{func.__module__.split('.')[-1]} {func.__name__}",
                    )
                return func(*args, **kwargs)
            except ValidationError:
                raise JiraCliError("Validation failed")

        return wrapper

    return decorator


def validate_project_issue_type(
    project_key: str, issue_type: str, command_context: str = ""
) -> str:
    """Validate that an issue type exists in the specified project.

    Args:
        project_key: Project key to validate against
        issue_type: Issue type name or ID to validate
        command_context: Command context for error messages

    Returns:
        Validated issue type (may return ID if name was provided)

    Raises:
        ValidationError: If issue type is not valid for the project
    """
    try:
        from ..utils.api import JiraApiClient
        from .error_handling import ErrorFormatter

        client = JiraApiClient()

        # Get project details to access issue types
        project = client.get_project(project_key)
        available_types = project.get("issueTypes", [])

        if not available_types:
            # Fallback to global issue types if project doesn't provide them
            available_types = client.get_issue_types()

        # Check if issue_type matches by name or ID
        matching_type = None
        for issue_type_info in available_types:
            if (
                issue_type.lower() == issue_type_info["name"].lower()
                or issue_type == issue_type_info["id"]
                or str(issue_type) == str(issue_type_info["id"])
            ):
                matching_type = issue_type_info
                break

        if not matching_type:
            # Generate helpful suggestions
            type_names = [it["name"] for it in available_types]
            subtask_types = [it["name"] for it in available_types if it.get("subtask")]
            regular_types = [
                it["name"] for it in available_types if not it.get("subtask")
            ]

            suggestions = [
                f"Use one of the available issue types for project {project_key}",
                "Check project configuration for issue type restrictions",
            ]

            if subtask_types and issue_type.lower() in ["subtask", "sub-task"]:
                suggestions.append(f"For subtasks, use: {', '.join(subtask_types)}")

            ErrorFormatter.print_formatted_error(
                "Invalid Issue Type",
                f"Issue type '{issue_type}' is not available in project '{project_key}'.",
                received=f"Issue type: '{issue_type}'",
                expected=f"One of the available issue types for project {project_key}",
                examples=type_names[:5],  # Show first 5 available types
                suggestions=suggestions,
                command_context=command_context,
            )
            raise ValidationError(
                f"Invalid issue type '{issue_type}' for project '{project_key}'"
            )

        return matching_type["name"]  # Return the canonical name

    except ValidationError:
        raise
    except Exception as e:
        # If we can't validate (API error, etc.), allow it to proceed
        # The actual API call will handle the final validation
        return issue_type


def handle_errors(command_context: str = ""):
    """Decorator to handle and format errors consistently.

    Args:
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except JiraCliError as e:
                # JiraCliError includes ValidationError - these are already formatted
                if str(e) != "Validation failed":
                    handle_api_error(
                        e, command_context or f"{func.__module__.split('.')[-1]}"
                    )
                import typer

                raise typer.Exit(1)
            except Exception as e:
                handle_api_error(
                    e, command_context or f"{func.__module__.split('.')[-1]}"
                )
                import typer

                raise typer.Exit(1)

        return wrapper

    return decorator


def validate_command(
    issue_key_params: Optional[List[str]] = None,
    project_key_params: Optional[List[str]] = None,
    email_params: Optional[List[str]] = None,
    date_params: Optional[List[str]] = None,
    time_params: Optional[List[str]] = None,
    jql_params: Optional[List[str]] = None,
    required_params: Optional[List[str]] = None,
    choice_params: Optional[
        List[tuple]
    ] = None,  # List of (param_name, valid_choices) tuples
    command_context: str = "",
):
    """Combined decorator to validate multiple parameter types.

    Args:
        issue_key_params: List of parameter names that should be issue keys
        project_key_params: List of parameter names that should be project keys
        email_params: List of parameter names that should be emails
        date_params: List of parameter names that should be dates
        time_params: List of parameter names that should be time values
        jql_params: List of parameter names that should be JQL queries
        required_params: List of parameter names that are required
        choice_params: List of (param_name, valid_choices) tuples for choice validation
        command_context: Command context for error messages
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                context = (
                    command_context
                    or f"{func.__module__.split('.')[-1]} {func.__name__}"
                )

                # Validate issue keys
                if issue_key_params:
                    for param in issue_key_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_issue_key(
                                kwargs[param], context
                            )

                # Validate project keys
                if project_key_params:
                    for param in project_key_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_project_key(
                                kwargs[param], context
                            )

                # Validate emails
                if email_params:
                    for param in email_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_email(
                                kwargs[param], context
                            )

                # Validate dates
                if date_params:
                    for param in date_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_date_format(
                                kwargs[param], context
                            )

                # Validate time values
                if time_params:
                    for param in time_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_time_format(
                                kwargs[param], context
                            )

                # Validate JQL queries
                if jql_params:
                    for param in jql_params:
                        if param in kwargs and kwargs[param]:
                            kwargs[param] = InputValidator.validate_jql_query(
                                kwargs[param], context
                            )

                # Validate required parameters
                if required_params:
                    for param in required_params:
                        if param in kwargs:
                            kwargs[param] = InputValidator.validate_required_parameter(
                                kwargs[param], param, context
                            )

                # Validate choice parameters
                if choice_params:
                    for param_name, valid_choices in choice_params:
                        if param_name in kwargs and kwargs[param_name]:
                            kwargs[param_name] = (
                                InputValidator.validate_choice_parameter(
                                    kwargs[param_name],
                                    valid_choices,
                                    param_name,
                                    context,
                                )
                            )

                return func(*args, **kwargs)

            except ValidationError:
                import typer

                raise typer.Exit(1)
            except JiraCliError as e:
                if str(e) != "Validation failed":
                    handle_api_error(e, context)
                import typer

                raise typer.Exit(1)
            except Exception as e:
                handle_api_error(e, context)
                import typer

                raise typer.Exit(1)

        return wrapper

    return decorator
