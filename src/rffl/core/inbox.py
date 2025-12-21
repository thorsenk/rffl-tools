"""
Utility functions for processing files from the inbox folder.

⚠️ CRITICAL: When processing files from the inbox, you MUST clean up after completion.
Files should be moved to their proper destination OR deleted. Never leave files in the inbox.

Use `ensure_inbox_clean()` to verify cleanup before completing your task.
"""

from pathlib import Path
from typing import Callable, Optional
import shutil
from rich.console import Console

console = Console()


def get_inbox_path(repo_root: Optional[Path] = None) -> Path:
    """
    Get the path to the inbox folder.
    
    Args:
        repo_root: Optional repository root path (auto-detected if None)
    
    Returns:
        Path to the inbox folder
    """
    if repo_root is None:
        # Find repo root
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                repo_root = parent
                break
        
        if repo_root is None:
            raise ValueError("Could not find repository root")
    
    return repo_root / "inbox"


def list_inbox_files(repo_root: Optional[Path] = None) -> list[Path]:
    """
    List all files in the inbox folder (excluding README.md and .gitkeep).
    
    Args:
        repo_root: Optional repository root path (auto-detected if None)
    
    Returns:
        List of file paths in the inbox
    """
    inbox_path = get_inbox_path(repo_root)
    
    if not inbox_path.exists():
        return []
    
    files = []
    for item in inbox_path.iterdir():
        if item.is_file() and item.name not in ["README.md", ".gitkeep"]:
            files.append(item)
    
    return files


def process_inbox_files(
    processor: Callable[[Path], None],
    repo_root: Optional[Path] = None,
    auto_cleanup: bool = True,
) -> list[Path]:
    """
    Process all files in the inbox folder and optionally clean up.
    
    This is a helper function to ensure agents remember to clean up after processing.
    
    Args:
        processor: Function that takes a file path and processes it
        repo_root: Optional repository root path (auto-detected if None)
        auto_cleanup: If True, automatically delete files after processing
    
    Returns:
        List of processed file paths
    
    Example:
        ```python
        def process_file(file_path: Path):
            # Your processing logic here
            # Move file to destination or delete it
            shutil.move(file_path, destination)
        
        processed = process_inbox_files(process_file, auto_cleanup=False)
        ```
    """
    inbox_path = get_inbox_path(repo_root)
    files = list_inbox_files(repo_root)
    
    if not files:
        console.print("[yellow]No files found in inbox[/yellow]")
        return []
    
    console.print(f"[cyan]Found {len(files)} file(s) in inbox[/cyan]")
    
    processed = []
    for file_path in files:
        try:
            console.print(f"[cyan]Processing: {file_path.name}[/cyan]")
            processor(file_path)
            processed.append(file_path)
        except Exception as e:
            console.print(f"[red]Error processing {file_path.name}: {e}[/red]")
            raise
    
    if auto_cleanup:
        remaining = list_inbox_files(repo_root)
        if remaining:
            console.print(
                f"[yellow]Warning: {len(remaining)} file(s) still in inbox after processing[/yellow]"
            )
            console.print(
                "[yellow]Files should be moved to their destination or deleted![/yellow]"
            )
        else:
            console.print("[green]✅ Inbox cleaned up successfully[/green]")
    
    return processed


def ensure_inbox_clean(repo_root: Optional[Path] = None) -> bool:
    """
    Verify that the inbox folder is clean (only README.md and .gitkeep remain).
    
    Args:
        repo_root: Optional repository root path (auto-detected if None)
    
    Returns:
        True if inbox is clean, False otherwise
    """
    files = list_inbox_files(repo_root)
    
    if files:
        console.print(f"[red]❌ Inbox is not clean: {len(files)} file(s) remaining[/red]")
        for file_path in files:
            console.print(f"  - {file_path.name}")
        return False
    
    console.print("[green]✅ Inbox is clean[/green]")
    return True


def move_inbox_file(
    source_file: Path,
    destination: Path,
    repo_root: Optional[Path] = None,
) -> Path:
    """
    Move a file from the inbox to a destination.
    
    This is a convenience function that ensures the file is moved (not copied)
    and provides feedback.
    
    Args:
        source_file: Path to file in inbox (can be relative or absolute)
        destination: Destination path (can be file or directory)
        repo_root: Optional repository root path (auto-detected if None)
    
    Returns:
        Path to the moved file
    """
    inbox_path = get_inbox_path(repo_root)
    
    # If source_file is relative, assume it's in inbox
    if not source_file.is_absolute():
        source_file = inbox_path / source_file
    
    # Ensure destination directory exists
    if destination.is_dir() or not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_dir():
            destination = destination / source_file.name
    
    shutil.move(str(source_file), str(destination))
    console.print(f"[green]Moved: {source_file.name} → {destination}[/green]")
    
    return destination

