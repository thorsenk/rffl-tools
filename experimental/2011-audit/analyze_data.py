#!/usr/bin/env python3
"""Analyze the extracted 2011 JSON data to understand structure."""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()
data_dir = Path(__file__).parent

# Load the most comprehensive file
combined_file = data_dir / "league_history_combined_views.json"

if not combined_file.exists():
    console.print("[red]❌ Combined views file not found[/red]")
    exit(1)

with open(combined_file) as f:
    data = json.load(f)

league = data[0] if isinstance(data, list) else data

console.print("\n[bold blue]📊 2011 Season Data Structure Analysis[/bold blue]\n")

# Top-level structure
console.print("[bold]Top-Level Keys:[/bold]")
for key in sorted(league.keys()):
    val = league[key]
    if isinstance(val, list):
        console.print(f"  • {key}: list ({len(val)} items)")
    elif isinstance(val, dict):
        console.print(f"  • {key}: dict ({len(val)} keys)")
    else:
        console.print(f"  • {key}: {type(val).__name__}")

# Teams analysis
if "teams" in league:
    teams = league["teams"]
    console.print(f"\n[bold]Teams:[/bold] {len(teams)} teams found")
    if teams:
        team = teams[0]
        console.print(f"  Sample team keys: {', '.join(list(team.keys())[:15])}")
        if "roster" in team:
            roster = team["roster"]
            console.print(f"  Roster type: {type(roster).__name__}")
            if isinstance(roster, dict):
                console.print(f"  Roster keys: {', '.join(list(roster.keys())[:10])}")

# Draft analysis
if "draftDetail" in league:
    draft = league["draftDetail"]
    console.print(f"\n[bold]Draft:[/bold]")
    console.print(f"  Draft keys: {', '.join(list(draft.keys())[:10])}")
    picks = draft.get("picks", [])
    console.print(f"  Total picks: {len(picks)}")
    if picks:
        console.print(f"  Sample pick keys: {', '.join(list(picks[0].keys())[:10])}")

# Schedule analysis
if "schedule" in league:
    schedule = league["schedule"]
    console.print(f"\n[bold]Schedule:[/bold]")
    if isinstance(schedule, list):
        console.print(f"  Matchups: {len(schedule)}")
        if schedule:
            matchup = schedule[0]
            console.print(f"  Sample matchup keys: {', '.join(list(matchup.keys())[:10])}")

# Settings analysis
if "settings" in league:
    settings = league["settings"]
    console.print(f"\n[bold]Settings:[/bold]")
    console.print(f"  Settings keys: {', '.join(list(settings.keys())[:15])}")

# Transactions analysis
trans_file = data_dir / "league_history_with_transactions.json"
if trans_file.exists():
    with open(trans_file) as f:
        trans_data = json.load(f)
    trans_league = trans_data[0] if isinstance(trans_data, list) else trans_data
    console.print(f"\n[bold]Transactions:[/bold]")
    console.print(f"  Transaction-related keys: {', '.join([k for k in trans_league.keys() if 'trans' in k.lower() or 'activity' in k.lower()])}")
    # Check for transactions in various possible locations
    for key in ["transactions", "recentTransactions", "activity", "recentActivity"]:
        if key in trans_league:
            val = trans_league[key]
            if isinstance(val, list):
                console.print(f"  {key}: {len(val)} transactions found")
            elif isinstance(val, dict):
                console.print(f"  {key}: dict with {len(val)} keys")

console.print("\n[bold green]✅ Analysis complete![/bold green]")

