"""
CapabilityRegistry - Discovers and catalogs all available tools in RFFL Tools.

Discovers:
- CLI commands (rffl core, rffl recipe, rffl live, etc.)
- Scripts in /scripts/*.py
- Recipes in /recipes/**/*.yaml
- Key data files
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class CapabilityType(Enum):
    """Type of capability."""
    CLI_COMMAND = "cli_command"
    SCRIPT = "script"
    RECIPE = "recipe"
    DATA_FILE = "data_file"


@dataclass
class Capability:
    """A single capability (command, script, recipe, or data file)."""
    name: str
    capability_type: CapabilityType
    description: str
    path: str | None = None  # For scripts/recipes/data files
    command_template: str | None = None  # For CLI commands
    keywords: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        type_label = self.capability_type.value.replace("_", " ").title()
        return f"[{type_label}] {self.name}: {self.description}"


class CapabilityRegistry:
    """
    Registry of all available capabilities in RFFL Tools.

    Discovers CLI commands, scripts, recipes, and key data files
    to provide a complete picture of available tools.
    """

    def __init__(self, repo_root: Path | None = None):
        """Initialize registry with optional repo root path."""
        self._capabilities: dict[str, Capability] = {}
        self._repo_root = repo_root or self._find_repo_root()
        self._discovered = False

    def _find_repo_root(self) -> Path:
        """Find repository root by looking for pyproject.toml."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return current

    def discover_all(self) -> None:
        """Discover all capabilities."""
        self._discover_cli_commands()
        self._discover_scripts()
        self._discover_recipes()
        self._discover_data_files()
        self._discovered = True

    def _discover_cli_commands(self) -> None:
        """Register known CLI commands with their metadata."""
        # Core commands
        cli_commands = [
            Capability(
                name="core export",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export ESPN fantasy football boxscores to CSV format",
                command_template="rffl core export --year {year}",
                keywords=["export", "boxscores", "boxscore", "csv", "data", "download"],
                options={
                    "year": {"type": "int", "required": True, "help": "Season year"},
                    "week": {"type": "int", "help": "Specific week"},
                    "start_week": {"type": "int", "help": "Start week"},
                    "end_week": {"type": "int", "help": "End week"},
                    "out": {"type": "str", "help": "Output CSV path"},
                },
            ),
            Capability(
                name="core h2h",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export simplified head-to-head matchup results",
                command_template="rffl core h2h --year {year}",
                keywords=["h2h", "head-to-head", "matchups", "standings", "results"],
                options={
                    "year": {"type": "int", "required": True},
                    "start_week": {"type": "int"},
                    "end_week": {"type": "int"},
                },
            ),
            Capability(
                name="core draft",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export season draft results to CSV",
                command_template="rffl core draft --year {year}",
                keywords=["draft", "auction", "picks", "selections"],
                options={"year": {"type": "int", "required": True}},
            ),
            Capability(
                name="core transactions",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export transaction history",
                command_template="rffl core transactions --year {year}",
                keywords=["transactions", "trades", "waivers", "adds", "drops", "moves"],
                options={"year": {"type": "int", "required": True}},
            ),
            Capability(
                name="core stat-corrections",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export stat corrections history (requires authentication)",
                command_template="rffl core stat-corrections --year {year}",
                keywords=["stat", "corrections", "scoring", "changes", "adjustments"],
                options={"year": {"type": "int", "required": True}, "week": {"type": "int"}},
            ),
            Capability(
                name="core historical-rosters",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Export end-of-season roster compositions for historical seasons (2011-2018)",
                command_template="rffl core historical-rosters --year {year}",
                keywords=["rosters", "historical", "legacy", "old", "players"],
                options={"year": {"type": "int", "required": True}},
            ),
            Capability(
                name="core validate",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Validate exported boxscore data for consistency",
                command_template="rffl core validate {csv_path}",
                keywords=["validate", "check", "verify", "consistency", "quality"],
                options={"csv_path": {"type": "str", "required": True}},
            ),
            Capability(
                name="core validate-lineup",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Validate RFFL lineup compliance",
                command_template="rffl core validate-lineup {csv_path}",
                keywords=["lineup", "validate", "compliance", "roster", "slots"],
                options={"csv_path": {"type": "str", "required": True}},
            ),
            # Recipe commands
            Capability(
                name="recipe run",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Execute a recipe",
                command_template="rffl recipe run {recipe_path}",
                keywords=["recipe", "run", "execute", "workflow", "pipeline"],
                options={"recipe_path": {"type": "str", "required": True}},
            ),
            Capability(
                name="recipe wizard",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Interactive wizard for creating recipes",
                command_template="rffl recipe wizard",
                keywords=["wizard", "create", "new", "recipe", "interactive"],
                options={"baseline": {"type": "str"}, "profile": {"type": "str"}},
            ),
            Capability(
                name="recipe list",
                capability_type=CapabilityType.CLI_COMMAND,
                description="List available recipes",
                command_template="rffl recipe list",
                keywords=["list", "recipes", "available", "show"],
                options={"all": {"type": "bool"}},
            ),
            Capability(
                name="recipe validate",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Validate a recipe file",
                command_template="rffl recipe validate {recipe_path}",
                keywords=["validate", "recipe", "check"],
                options={"recipe_path": {"type": "str", "required": True}},
            ),
            # Live commands
            Capability(
                name="live scores",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Fetch live scores",
                command_template="rffl live scores --season {season}",
                keywords=["live", "scores", "current", "now", "real-time", "scoreboard"],
                options={"season": {"type": "int", "required": True}, "scoring_period": {"type": "int"}},
            ),
            Capability(
                name="live report",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Generate live matchup report",
                command_template="rffl live report --season {season}",
                keywords=["live", "report", "matchup", "status"],
                options={"season": {"type": "int", "required": True}},
            ),
            Capability(
                name="live korm",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Generate KORM live update report",
                command_template="rffl live korm {week} --season {season}",
                keywords=["korm", "live", "king", "red", "marks", "standings"],
                options={"week": {"type": "int", "required": True}, "season": {"type": "int", "required": True}},
            ),
            # KORM commands
            Capability(
                name="korm generate",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Generate KORM results for a single season",
                command_template="rffl korm generate {year}",
                keywords=["korm", "generate", "process", "calculate", "results"],
                options={"year": {"type": "int", "required": True}},
            ),
            Capability(
                name="korm generate-all",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Generate KORM results for all seasons",
                command_template="rffl korm generate-all",
                keywords=["korm", "generate", "all", "batch", "bulk"],
                options={"start_year": {"type": "int"}, "end_year": {"type": "int"}},
            ),
            Capability(
                name="korm standings",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Show KORM standings for a season",
                command_template="rffl korm standings {year}",
                keywords=["korm", "standings", "leaderboard", "rankings"],
                options={"year": {"type": "int", "required": True}, "week": {"type": "int"}},
            ),
            # Forensic commands
            Capability(
                name="forensic investigate",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Execute a forensic investigation",
                command_template="rffl forensic investigate {case_id}",
                keywords=["forensic", "investigate", "analysis", "inquiry", "case"],
                options={"case_id": {"type": "str", "required": True}},
            ),
            Capability(
                name="forensic list",
                capability_type=CapabilityType.CLI_COMMAND,
                description="List all investigations",
                command_template="rffl forensic list",
                keywords=["forensic", "list", "investigations", "cases"],
                options={},
            ),
            Capability(
                name="forensic approve",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Mark an investigation as commissioner-approved",
                command_template="rffl forensic approve {case_id}",
                keywords=["forensic", "approve", "authorize"],
                options={"case_id": {"type": "str", "required": True}},
            ),
            # Utils commands
            Capability(
                name="utils read-inbox",
                capability_type=CapabilityType.CLI_COMMAND,
                description="List files in the inbox folder",
                command_template="rffl utils read-inbox",
                keywords=["inbox", "files", "pending", "queue"],
                options={"preview": {"type": "bool"}},
            ),
            Capability(
                name="utils clean-inbox",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Clean up the inbox folder",
                command_template="rffl utils clean-inbox",
                keywords=["inbox", "clean", "cleanup", "delete", "move"],
                options={},
            ),
            Capability(
                name="utils inbox-status",
                capability_type=CapabilityType.CLI_COMMAND,
                description="Check the status of the inbox folder",
                command_template="rffl utils inbox-status",
                keywords=["inbox", "status"],
                options={},
            ),
        ]

        for cap in cli_commands:
            self._capabilities[cap.name] = cap

    def _discover_scripts(self) -> None:
        """Discover Python scripts in /scripts directory."""
        scripts_dir = self._repo_root / "scripts"
        if not scripts_dir.exists():
            return

        for script_path in scripts_dir.glob("*.py"):
            if script_path.name.startswith("_"):
                continue

            # Parse script docstring for description
            description = self._extract_script_description(script_path)
            name = script_path.stem

            # Generate keywords from filename
            keywords = name.replace("_", " ").split()

            cap = Capability(
                name=f"script:{name}",
                capability_type=CapabilityType.SCRIPT,
                description=description,
                path=str(script_path.relative_to(self._repo_root)),
                command_template=f"python scripts/{script_path.name}",
                keywords=keywords,
            )
            self._capabilities[cap.name] = cap

    def _extract_script_description(self, script_path: Path) -> str:
        """Extract description from script docstring."""
        try:
            content = script_path.read_text()
            # Look for module docstring
            if content.startswith('"""'):
                end = content.find('"""', 3)
                if end > 0:
                    docstring = content[3:end].strip()
                    # Return first line
                    return docstring.split("\n")[0]
            elif content.startswith("'''"):
                end = content.find("'''", 3)
                if end > 0:
                    docstring = content[3:end].strip()
                    return docstring.split("\n")[0]
        except Exception:
            pass
        return f"Script: {script_path.name}"

    def _discover_recipes(self) -> None:
        """Discover recipe YAML files."""
        recipes_dir = self._repo_root / "recipes"
        if not recipes_dir.exists():
            return

        for recipe_path in recipes_dir.glob("**/*.yaml"):
            name = recipe_path.stem
            category = recipe_path.parent.name  # e.g., "baselines" or "local"

            # Try to parse recipe for description
            description = self._extract_recipe_description(recipe_path)

            # Generate keywords
            keywords = [name.replace("-", " ").replace("_", " ")]
            keywords.extend(name.replace("-", " ").replace("_", " ").split())
            keywords.append(category)

            rel_path = str(recipe_path.relative_to(self._repo_root))
            cap = Capability(
                name=f"recipe:{category}/{name}",
                capability_type=CapabilityType.RECIPE,
                description=description,
                path=rel_path,
                command_template=f"rffl recipe run {rel_path}",
                keywords=keywords,
            )
            self._capabilities[cap.name] = cap

    def _extract_recipe_description(self, recipe_path: Path) -> str:
        """Extract description from recipe YAML."""
        try:
            content = yaml.safe_load(recipe_path.read_text())
            if isinstance(content, dict):
                if "description" in content:
                    return content["description"]
                if "name" in content:
                    return f"Recipe: {content['name']}"
        except Exception:
            pass
        return f"Recipe: {recipe_path.name}"

    def _discover_data_files(self) -> None:
        """Register key data files."""
        data_files = [
            ("data/teams.csv", "Team registry with codes and ESPN IDs", ["teams", "registry", "team", "codes"]),
            ("data/seasons", "Season data directory", ["seasons", "historical", "data"]),
            ("data/korm_history", "KORM historical results", ["korm", "history", "results"]),
        ]

        for rel_path, description, keywords in data_files:
            full_path = self._repo_root / rel_path
            if full_path.exists():
                cap = Capability(
                    name=f"data:{rel_path}",
                    capability_type=CapabilityType.DATA_FILE,
                    description=description,
                    path=rel_path,
                    keywords=keywords,
                )
                self._capabilities[cap.name] = cap

    @property
    def capabilities(self) -> dict[str, Capability]:
        """Get all registered capabilities."""
        if not self._discovered:
            self.discover_all()
        return self._capabilities

    def get(self, name: str) -> Capability | None:
        """Get a capability by name."""
        return self.capabilities.get(name)

    def search(self, query: str) -> list[Capability]:
        """Search capabilities by keyword."""
        query_lower = query.lower()
        query_words = query_lower.split()

        results: list[tuple[int, Capability]] = []

        for cap in self.capabilities.values():
            score = 0
            # Check name match
            if query_lower in cap.name.lower():
                score += 10
            # Check description match
            if query_lower in cap.description.lower():
                score += 5
            # Check keyword matches
            for keyword in cap.keywords:
                if keyword.lower() in query_lower or query_lower in keyword.lower():
                    score += 3
                for qword in query_words:
                    if qword in keyword.lower():
                        score += 1

            if score > 0:
                results.append((score, cap))

        # Sort by score descending
        results.sort(key=lambda x: -x[0])
        return [cap for _, cap in results]

    def list_by_type(self, capability_type: CapabilityType) -> list[Capability]:
        """List all capabilities of a specific type."""
        return [
            cap for cap in self.capabilities.values()
            if cap.capability_type == capability_type
        ]

    def format_capabilities_list(self) -> str:
        """Format all capabilities as a readable list."""
        if not self._discovered:
            self.discover_all()

        lines = ["Available Capabilities:", "=" * 50, ""]

        # Group by type
        for cap_type in CapabilityType:
            caps = self.list_by_type(cap_type)
            if caps:
                type_name = cap_type.value.replace("_", " ").title()
                lines.append(f"## {type_name}s ({len(caps)})")
                lines.append("")
                for cap in sorted(caps, key=lambda c: c.name):
                    lines.append(f"  - {cap.name}")
                    lines.append(f"    {cap.description}")
                    if cap.command_template:
                        lines.append(f"    Command: {cap.command_template}")
                lines.append("")

        return "\n".join(lines)
