"""
MOADispatcher - Routes natural language requests to specific tools.

The main orchestrator that:
1. Parses natural language requests
2. Matches requests to capabilities using keyword matching
3. Resolves command parameters from context
4. Executes commands and tracks results
"""

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context import SessionContext
from .logger import StructuredLogger
from .registry import CapabilityRegistry, Capability, CapabilityType


@dataclass
class DispatchResult:
    """Result of dispatching a request."""
    success: bool
    command: str
    output: str
    error: str | None = None
    duration_ms: int | None = None
    capability: Capability | None = None


class MOADispatcher:
    """
    Master Orchestrator Agent - Intelligent command dispatcher.

    Routes natural language requests to appropriate RFFL tools by:
    1. Parsing the request for intent and parameters
    2. Matching to known capabilities via keyword matching
    3. Resolving parameters from context or request
    4. Executing and logging the result
    """

    # Built-in commands that MOA handles directly
    BUILTIN_COMMANDS = {
        "list capabilities": "list_capabilities",
        "list commands": "list_capabilities",
        "show capabilities": "list_capabilities",
        "what can you do": "list_capabilities",
        "help": "list_capabilities",
        "what did i just do": "show_last_operation",
        "last operation": "show_last_operation",
        "show history": "show_history",
        "recent operations": "show_history",
        "session info": "show_session_info",
        "session status": "show_session_info",
        "set season": "set_season",
    }

    def __init__(
        self,
        repo_root: Path | None = None,
        context: SessionContext | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize the dispatcher.

        Args:
            repo_root: Repository root path
            context: Optional existing session context
            dry_run: If True, don't execute commands, just show what would run
        """
        self._repo_root = repo_root or self._find_repo_root()
        self._registry = CapabilityRegistry(self._repo_root)
        self._context = context or SessionContext()
        self._logger = StructuredLogger(repo_root=self._repo_root)
        self._dry_run = dry_run

    def _find_repo_root(self) -> Path:
        """Find repository root by looking for pyproject.toml."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return current

    def dispatch(self, request: str) -> DispatchResult:
        """
        Dispatch a natural language request to the appropriate tool.

        Args:
            request: Natural language request string

        Returns:
            DispatchResult with the outcome
        """
        start_time = time.time()
        request_lower = request.lower().strip()

        # Check for built-in commands first
        for pattern, handler_name in self.BUILTIN_COMMANDS.items():
            if pattern in request_lower or request_lower.startswith(pattern.split()[0]):
                handler = getattr(self, f"_handle_{handler_name}")
                result = handler(request)
                duration_ms = int((time.time() - start_time) * 1000)
                result.duration_ms = duration_ms
                self._log_result(request, result)
                return result

        # Try to match to a capability
        capability, params = self._match_capability(request)

        if capability is None:
            result = DispatchResult(
                success=False,
                command="",
                output="",
                error=f"Could not understand request: '{request}'. Try 'list capabilities' to see available commands.",
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms
            self._log_result(request, result)
            return result

        # Build the command
        command = self._build_command(capability, params)

        if self._dry_run:
            result = DispatchResult(
                success=True,
                command=command,
                output=f"[DRY RUN] Would execute: {command}",
                capability=capability,
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms
            return result

        # Execute the command
        result = self._execute_command(command, capability)
        duration_ms = int((time.time() - start_time) * 1000)
        result.duration_ms = duration_ms

        # Log the result
        self._log_result(request, result)

        return result

    def _match_capability(self, request: str) -> tuple[Capability | None, dict[str, Any]]:
        """
        Match a request to a capability and extract parameters.

        Returns:
            Tuple of (matched capability or None, extracted parameters)
        """
        request_lower = request.lower()

        # Search for matching capabilities
        matches = self._registry.search(request)

        if not matches:
            return None, {}

        # Use the best match
        capability = matches[0]

        # Extract parameters from the request
        params = self._extract_params(request, capability)

        return capability, params

    def _extract_params(self, request: str, capability: Capability) -> dict[str, Any]:
        """Extract parameters from the request based on capability options."""
        params: dict[str, Any] = {}
        request_lower = request.lower()

        # Extract year from request (e.g., "2024", "2023")
        year_match = re.search(r"\b(20\d{2})\b", request)
        if year_match:
            params["year"] = int(year_match.group(1))
            params["season"] = int(year_match.group(1))
        else:
            # Use context default
            params["year"] = self._context.current_season
            params["season"] = self._context.current_season

        # Extract week from request (e.g., "week 16", "wk 5")
        week_match = re.search(r"\b(?:week|wk)\s*(\d+)\b", request_lower)
        if week_match:
            params["week"] = int(week_match.group(1))

        # Extract file paths (quoted or .csv/.yaml extensions)
        path_match = re.search(r'["\']([^"\']+)["\']|(\S+\.(?:csv|yaml|json))', request)
        if path_match:
            params["path"] = path_match.group(1) or path_match.group(2)
            params["csv_path"] = params["path"]
            params["recipe_path"] = params["path"]

        # Extract case ID for forensic commands
        case_match = re.search(r"(RFFL-INQ-\d{4}-\d+)", request)
        if case_match:
            params["case_id"] = case_match.group(1)

        return params

    def _build_command(self, capability: Capability, params: dict[str, Any]) -> str:
        """Build an executable command from capability and parameters."""
        if not capability.command_template:
            return f"# No command template for {capability.name}"

        command = capability.command_template

        # Replace template placeholders
        for key, value in params.items():
            placeholder = "{" + key + "}"
            if placeholder in command:
                command = command.replace(placeholder, str(value))

        # Remove any remaining unreplaced placeholders for optional params
        command = re.sub(r"\s*\{[^}]+\}", "", command)

        return command.strip()

    def _execute_command(self, command: str, capability: Capability) -> DispatchResult:
        """Execute a command and capture the result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self._repo_root),
            )

            if result.returncode == 0:
                return DispatchResult(
                    success=True,
                    command=command,
                    output=result.stdout or "Command completed successfully.",
                    capability=capability,
                )
            else:
                return DispatchResult(
                    success=False,
                    command=command,
                    output=result.stdout,
                    error=result.stderr or f"Command failed with exit code {result.returncode}",
                    capability=capability,
                )

        except subprocess.TimeoutExpired:
            return DispatchResult(
                success=False,
                command=command,
                output="",
                error="Command timed out after 5 minutes",
                capability=capability,
            )
        except Exception as e:
            return DispatchResult(
                success=False,
                command=command,
                output="",
                error=str(e),
                capability=capability,
            )

    def _log_result(self, request: str, result: DispatchResult) -> None:
        """Log the dispatch result."""
        # Record in session context
        self._context.record_operation(
            request=request,
            resolved_command=result.command,
            success=result.success,
            output_summary=result.output[:200] if result.output else None,
            error=result.error,
            duration_ms=result.duration_ms,
        )

        # Log to JSONL file
        self._logger.log(
            session_id=self._context.session_id,
            request=request,
            resolved_command=result.command,
            success=result.success,
            result_summary=result.output[:200] if result.output else None,
            error=result.error,
            duration_ms=result.duration_ms,
            metadata={
                "capability": result.capability.name if result.capability else None,
                "current_season": self._context.current_season,
            },
        )

    # Built-in command handlers

    def _handle_list_capabilities(self, request: str) -> DispatchResult:
        """Handle request to list all capabilities."""
        output = self._registry.format_capabilities_list()
        return DispatchResult(
            success=True,
            command="moa:list_capabilities",
            output=output,
        )

    def _handle_show_last_operation(self, request: str) -> DispatchResult:
        """Handle request to show last operation."""
        last = self._context.last_operation
        if last:
            output = (
                f"Last operation:\n"
                f"  Time: {last.timestamp.strftime('%H:%M:%S')}\n"
                f"  Request: {last.request}\n"
                f"  Command: {last.resolved_command}\n"
                f"  Status: {'OK' if last.success else 'FAILED'}\n"
            )
            if last.output_summary:
                output += f"  Result: {last.output_summary}\n"
            if last.error:
                output += f"  Error: {last.error}\n"
        else:
            output = "No operations in this session yet."

        return DispatchResult(
            success=True,
            command="moa:show_last_operation",
            output=output,
        )

    def _handle_show_history(self, request: str) -> DispatchResult:
        """Handle request to show operation history."""
        # Extract count if specified (e.g., "last 10 operations")
        count_match = re.search(r"(\d+)", request)
        count = int(count_match.group(1)) if count_match else 5

        output = self._context.format_recent_history(count)
        return DispatchResult(
            success=True,
            command="moa:show_history",
            output=output,
        )

    def _handle_show_session_info(self, request: str) -> DispatchResult:
        """Handle request to show session information."""
        output = self._context.format_session_info()
        return DispatchResult(
            success=True,
            command="moa:show_session_info",
            output=output,
        )

    def _handle_set_season(self, request: str) -> DispatchResult:
        """Handle request to set the current season."""
        year_match = re.search(r"(20\d{2})", request)
        if year_match:
            year = int(year_match.group(1))
            try:
                self._context.set_season(year)
                return DispatchResult(
                    success=True,
                    command=f"moa:set_season {year}",
                    output=f"Current season set to {year}",
                )
            except ValueError as e:
                return DispatchResult(
                    success=False,
                    command="moa:set_season",
                    output="",
                    error=str(e),
                )
        else:
            return DispatchResult(
                success=False,
                command="moa:set_season",
                output="",
                error="Please specify a year (e.g., 'set season 2024')",
            )

    @property
    def context(self) -> SessionContext:
        """Get the session context."""
        return self._context

    @property
    def registry(self) -> CapabilityRegistry:
        """Get the capability registry."""
        return self._registry
