#!/usr/bin/env python3
"""Extract transactions for all seasons 2019-2025."""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Seasons to process
SEASONS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

# League ID
LEAGUE_ID = os.getenv("LEAGUE", "323196")

# Check for credentials
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

if not ESPN_S2 or not SWID:
    console.print(
        "[red]❌ Missing ESPN_S2 or SWID credentials[/red]"
    )
    console.print(
        "[yellow]Set them with:[/yellow]"
    )
    console.print(
        "[dim]  export ESPN_S2='your_espn_s2_value'[/dim]"
    )
    console.print(
        "[dim]  export SWID='your_swid_value'[/dim]"
    )
    sys.exit(1)

# Find repo root
repo_root = Path(__file__).parent.parent
os.chdir(repo_root)

console.print(f"[bold]Extracting transactions for seasons {min(SEASONS)}-{max(SEASONS)}[/bold]")
console.print(f"[dim]League ID: {LEAGUE_ID}[/dim]")
console.print(f"[dim]Output directory: data/seasons/{{YEAR}}/transactions.csv[/dim]\n")

results = {}

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    for year in SEASONS:
        task = progress.add_task(f"Processing {year}...", total=None)
        
        output_path = repo_root / "data" / "seasons" / str(year) / "transactions.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run rffl command
        cmd = [
            "rffl",
            "core",
            "transactions",
            "--year",
            str(year),
            "--league",
            str(LEAGUE_ID),
            "--out",
            str(output_path),
        ]
        
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per season
            )
            
            if result.returncode == 0:
                # Count transactions
                if output_path.exists():
                    with open(output_path) as f:
                        line_count = sum(1 for _ in f) - 1  # Subtract header
                    results[year] = {
                        "status": "success",
                        "transactions": line_count,
                        "path": str(output_path),
                    }
                    progress.update(
                        task,
                        description=f"[green]✅ {year}: {line_count} transactions[/green]",
                    )
                else:
                    results[year] = {
                        "status": "error",
                        "error": "File not created",
                    }
                    progress.update(
                        task,
                        description=f"[red]❌ {year}: File not created[/red]",
                    )
            else:
                error_msg = result.stderr.split("\n")[-2] if result.stderr else "Unknown error"
                results[year] = {
                    "status": "error",
                    "error": error_msg,
                }
                progress.update(
                    task,
                    description=f"[red]❌ {year}: {error_msg[:50]}[/red]",
                )
        except subprocess.TimeoutExpired:
            results[year] = {
                "status": "error",
                "error": "Timeout (exceeded 5 minutes)",
            }
            progress.update(
                task,
                description=f"[red]❌ {year}: Timeout[/red]",
            )
        except Exception as e:
            results[year] = {
                "status": "error",
                "error": str(e),
            }
            progress.update(
                task,
                description=f"[red]❌ {year}: {str(e)[:50]}[/red]",
            )

console.print("\n[bold]Summary:[/bold]\n")

total_transactions = 0
success_count = 0
error_count = 0

for year in SEASONS:
    result = results.get(year, {})
    if result.get("status") == "success":
        count = result.get("transactions", 0)
        total_transactions += count
        success_count += 1
        console.print(
            f"  [green]✅ {year}:[/green] {count:,} transactions → {result['path']}"
        )
    else:
        error_count += 1
        error = result.get("error", "Unknown error")
        console.print(f"  [red]❌ {year}:[/red] {error}")

console.print(f"\n[bold]Total:[/bold] {success_count} successful, {error_count} errors")
if total_transactions > 0:
    console.print(f"[bold]Total transactions extracted:[/bold] {total_transactions:,}")

