"""
MOA (Master Orchestrator Agent) - Intelligent command dispatcher for RFFL Tools.

This module provides a unified entry point that knows all available tools
and routes natural language requests to the appropriate commands.

Phase 1 Components:
- CapabilityRegistry: Discovers all available CLI commands, scripts, and recipes
- SessionContext: Tracks session state and recent operations
- StructuredLogger: JSONL audit trail for all operations
- MOADispatcher: Routes natural language requests to specific tools
"""

from .registry import CapabilityRegistry, Capability, CapabilityType
from .context import SessionContext
from .logger import StructuredLogger
from .dispatcher import MOADispatcher

__all__ = [
    "CapabilityRegistry",
    "Capability",
    "CapabilityType",
    "SessionContext",
    "StructuredLogger",
    "MOADispatcher",
]
