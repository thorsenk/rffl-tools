"""
SessionContext - Tracks session state and recent operations.

Maintains:
- Current working season (default: 2025)
- Last command executed
- Recent outputs/results
- Session metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OperationResult:
    """Result of a single operation."""
    timestamp: datetime
    request: str
    resolved_command: str
    success: bool
    output_summary: str | None = None
    error: str | None = None
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "request": self.request,
            "resolved_command": self.resolved_command,
            "success": self.success,
            "output_summary": self.output_summary,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SessionContext:
    """
    Tracks session state for the MOA dispatcher.

    Maintains context across multiple operations within a session,
    including the default season, recent operations, and session metadata.
    """

    current_season: int = 2025
    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    started_at: datetime = field(default_factory=datetime.now)
    operations: list[OperationResult] = field(default_factory=list)
    max_history: int = 100  # Maximum operations to keep in memory

    @property
    def last_operation(self) -> OperationResult | None:
        """Get the most recent operation."""
        return self.operations[-1] if self.operations else None

    @property
    def operation_count(self) -> int:
        """Get total number of operations in this session."""
        return len(self.operations)

    def record_operation(
        self,
        request: str,
        resolved_command: str,
        success: bool,
        output_summary: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> OperationResult:
        """Record a new operation result."""
        result = OperationResult(
            timestamp=datetime.now(),
            request=request,
            resolved_command=resolved_command,
            success=success,
            output_summary=output_summary,
            error=error,
            duration_ms=duration_ms,
        )
        self.operations.append(result)

        # Trim history if needed
        if len(self.operations) > self.max_history:
            self.operations = self.operations[-self.max_history:]

        return result

    def get_recent_operations(self, n: int = 5) -> list[OperationResult]:
        """Get the N most recent operations."""
        return self.operations[-n:] if self.operations else []

    def set_season(self, year: int) -> None:
        """Set the current working season."""
        if 2010 <= year <= 2030:
            self.current_season = year
        else:
            raise ValueError(f"Invalid season year: {year}")

    def format_recent_history(self, n: int = 5) -> str:
        """Format recent operations as readable text."""
        recent = self.get_recent_operations(n)
        if not recent:
            return "No operations in this session yet."

        lines = [f"Last {len(recent)} operations:", ""]
        for i, op in enumerate(reversed(recent), 1):
            status = "OK" if op.success else "FAILED"
            time_str = op.timestamp.strftime("%H:%M:%S")
            lines.append(f"{i}. [{time_str}] {status}")
            lines.append(f"   Request: {op.request}")
            lines.append(f"   Command: {op.resolved_command}")
            if op.output_summary:
                lines.append(f"   Result: {op.output_summary}")
            if op.error:
                lines.append(f"   Error: {op.error}")
            lines.append("")

        return "\n".join(lines)

    def format_session_info(self) -> str:
        """Format session information as readable text."""
        duration = datetime.now() - self.started_at
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)

        successful = sum(1 for op in self.operations if op.success)
        failed = len(self.operations) - successful

        lines = [
            "Session Information",
            "=" * 40,
            f"Session ID: {self.session_id}",
            f"Started: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {minutes}m {seconds}s",
            f"Current Season: {self.current_season}",
            f"Operations: {len(self.operations)} ({successful} successful, {failed} failed)",
        ]

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert session context to dictionary."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "current_season": self.current_season,
            "operation_count": len(self.operations),
            "operations": [op.to_dict() for op in self.operations],
        }
