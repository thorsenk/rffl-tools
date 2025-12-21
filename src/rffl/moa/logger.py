"""
StructuredLogger - JSONL audit trail for MOA operations.

Provides persistent logging of all MOA operations to:
- data/moa/session_log.jsonl

Each log entry includes:
- Timestamp
- Session ID
- Request (natural language input)
- Resolved command
- Result summary
- Success/failure status
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class StructuredLogger:
    """
    JSONL logger for MOA operations.

    Writes structured log entries to data/moa/session_log.jsonl for
    audit trail and debugging purposes.
    """

    def __init__(self, log_path: Path | None = None, repo_root: Path | None = None):
        """Initialize logger with optional custom log path."""
        if log_path:
            self._log_path = log_path
        else:
            root = repo_root or self._find_repo_root()
            self._log_path = root / "data" / "moa" / "session_log.jsonl"

        # Ensure directory exists
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _find_repo_root(self) -> Path:
        """Find repository root by looking for pyproject.toml."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return current

    def log(
        self,
        session_id: str,
        request: str,
        resolved_command: str,
        success: bool,
        result_summary: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an operation to the JSONL file.

        Args:
            session_id: Unique session identifier
            request: Original natural language request
            resolved_command: The command that was executed
            success: Whether the operation succeeded
            result_summary: Brief summary of the result
            error: Error message if failed
            duration_ms: Execution time in milliseconds
            metadata: Additional metadata to include
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "request": request,
            "resolved_command": resolved_command,
            "success": success,
        }

        if result_summary:
            entry["result_summary"] = result_summary
        if error:
            entry["error"] = error
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if metadata:
            entry["metadata"] = metadata

        self._write_entry(entry)

    def _write_entry(self, entry: dict[str, Any]) -> None:
        """Write a single entry to the log file."""
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def read_recent(self, n: int = 10, session_id: str | None = None) -> list[dict[str, Any]]:
        """
        Read recent log entries.

        Args:
            n: Number of entries to return
            session_id: Optional filter by session ID

        Returns:
            List of log entries (most recent last)
        """
        if not self._log_path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if session_id is None or entry.get("session_id") == session_id:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries[-n:]

    def read_all(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """
        Read all log entries.

        Args:
            session_id: Optional filter by session ID

        Returns:
            List of all log entries
        """
        if not self._log_path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if session_id is None or entry.get("session_id") == session_id:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries

    def format_recent(self, n: int = 5, session_id: str | None = None) -> str:
        """Format recent entries as readable text."""
        entries = self.read_recent(n, session_id)
        if not entries:
            return "No log entries found."

        lines = [f"Recent {len(entries)} operations:", ""]
        for i, entry in enumerate(reversed(entries), 1):
            timestamp = entry.get("timestamp", "unknown")
            if "T" in timestamp:
                # Parse ISO format and show just time
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except ValueError:
                    time_str = timestamp
            else:
                time_str = timestamp

            status = "OK" if entry.get("success") else "FAILED"
            lines.append(f"{i}. [{time_str}] {status}")
            lines.append(f"   Request: {entry.get('request', 'N/A')}")
            lines.append(f"   Command: {entry.get('resolved_command', 'N/A')}")
            if entry.get("result_summary"):
                lines.append(f"   Result: {entry['result_summary']}")
            if entry.get("error"):
                lines.append(f"   Error: {entry['error']}")
            lines.append("")

        return "\n".join(lines)

    def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a specific session."""
        entries = self.read_all(session_id)
        if not entries:
            return {
                "session_id": session_id,
                "total_operations": 0,
                "successful": 0,
                "failed": 0,
            }

        successful = sum(1 for e in entries if e.get("success"))
        failed = len(entries) - successful

        # Calculate average duration if available
        durations = [e.get("duration_ms") for e in entries if e.get("duration_ms") is not None]
        avg_duration = sum(durations) / len(durations) if durations else None

        return {
            "session_id": session_id,
            "total_operations": len(entries),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(entries) if entries else 0,
            "avg_duration_ms": avg_duration,
        }

    @property
    def log_path(self) -> Path:
        """Get the path to the log file."""
        return self._log_path

    def clear(self) -> None:
        """Clear the log file (use with caution)."""
        if self._log_path.exists():
            self._log_path.unlink()
