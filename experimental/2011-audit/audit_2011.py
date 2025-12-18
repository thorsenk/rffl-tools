#!/usr/bin/env python3
"""Complete data audit for 2011 season using ESPN API with authentication."""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

import requests
from rich.console import Console
from rich.table import Table

console = Console()

# ESPN API base URLs
BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
LEAGUE_ID = 323196
YEAR = 2011

# Get credentials from environment
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

if not ESPN_S2 or not SWID:
    console.print("[red]❌ Missing ESPN_S2 or SWID credentials[/red]")
    console.print("[yellow]Set ESPN_S2 and SWID environment variables[/yellow]")
    sys.exit(1)

cookies = {
    "espn_s2": ESPN_S2,
    "SWID": SWID,
}

output_dir = Path(__file__).parent
output_dir.mkdir(parents=True, exist_ok=True)

results = {
    "timestamp": datetime.now().isoformat(),
    "league_id": LEAGUE_ID,
    "year": YEAR,
    "endpoints_tested": [],
    "successful": [],
    "failed": [],
}


def test_endpoint(name: str, url: str, description: str = "") -> dict:
    """Test an ESPN API endpoint and save results."""
    console.print(f"\n[cyan]Testing: {name}[/cyan]")
    if description:
        console.print(f"[dim]{description}[/dim]")
    
    try:
        response = requests.get(url, cookies=cookies, timeout=15)
        status = response.status_code
        
        result = {
            "name": name,
            "url": url,
            "status_code": status,
            "success": False,
            "data_size": 0,
            "error": None,
        }
        
        if status == 200:
            try:
                data = response.json()
                result["success"] = True
                result["data_size"] = len(json.dumps(data))
                
                # Save response
                output_file = output_dir / f"{name.replace(' ', '_').lower()}.json"
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
                
                console.print(f"[green]✅ Success[/green] - Saved to {output_file.name}")
                console.print(f"[dim]   Data size: {result['data_size']:,} bytes[/dim]")
                
                # Try to extract useful info
                if isinstance(data, list) and data:
                    console.print(f"[dim]   Response is array with {len(data)} items[/dim]")
                    if isinstance(data[0], dict):
                        console.print(f"[dim]   Keys: {', '.join(list(data[0].keys())[:5])}...[/dim]")
                elif isinstance(data, dict):
                    console.print(f"[dim]   Top-level keys: {', '.join(list(data.keys())[:10])}[/dim]")
                
                results["successful"].append(result)
                
            except json.JSONDecodeError as e:
                result["error"] = f"Invalid JSON: {e}"
                console.print(f"[red]❌ Invalid JSON response[/red]")
                results["failed"].append(result)
        else:
            result["error"] = f"HTTP {status}: {response.text[:200]}"
            console.print(f"[red]❌ Failed: HTTP {status}[/red]")
            if status == 401:
                console.print("[yellow]   Authentication required or invalid[/yellow]")
            elif status == 404:
                console.print("[yellow]   Endpoint not found or data not available[/yellow]")
            results["failed"].append(result)
        
        results["endpoints_tested"].append(result)
        return result
        
    except requests.exceptions.RequestException as e:
        result = {
            "name": name,
            "url": url,
            "status_code": None,
            "success": False,
            "data_size": 0,
            "error": str(e),
        }
        console.print(f"[red]❌ Request failed: {e}[/red]")
        results["failed"].append(result)
        results["endpoints_tested"].append(result)
        return result


def main():
    """Run complete audit of 2011 season data."""
    console.print(f"\n[bold blue]🔍 Complete Data Audit: Season {YEAR}[/bold blue]")
    console.print(f"🏈 League ID: {LEAGUE_ID}\n")
    
    # Test various endpoints
    endpoints = [
        # Legacy leagueHistory endpoint
        (
            "League History Basic",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}",
            "Basic league info via legacy endpoint"
        ),
        (
            "League History with Teams",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mTeam",
            "Team data via legacy endpoint"
        ),
        (
            "League History with Rosters",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mRoster",
            "Roster data via legacy endpoint"
        ),
        (
            "League History with Transactions",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mTransactions",
            "Transaction data via legacy endpoint"
        ),
        (
            "League History with Schedule",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mSchedule",
            "Schedule/matchup data via legacy endpoint"
        ),
        (
            "League History with Settings",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mSettings",
            "League settings via legacy endpoint"
        ),
        (
            "League History with Standings",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mStandings",
            "Standings data via legacy endpoint"
        ),
        (
            "League History with Draft",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mDraftDetail",
            "Draft data via legacy endpoint"
        ),
        (
            "League History Combined Views",
            f"{BASE_URL}/leagueHistory/{LEAGUE_ID}?seasonId={YEAR}&view=mTeam&view=mRoster&view=mSchedule&view=mSettings",
            "Multiple views combined"
        ),
        # Modern endpoint (may not work for 2011)
        (
            "Modern Season Endpoint",
            f"{BASE_URL}/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}",
            "Modern API endpoint (may not support 2011)"
        ),
        (
            "Modern with Teams",
            f"{BASE_URL}/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}?view=mTeam",
            "Modern endpoint with team view"
        ),
    ]
    
    for name, url, desc in endpoints:
        test_endpoint(name, url, desc)
    
    # Save summary
    summary_file = output_dir / "audit_summary.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary table
    console.print("\n[bold]📊 Audit Summary[/bold]\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Endpoint", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Notes")
    
    for endpoint in results["endpoints_tested"]:
        status = "✅" if endpoint["success"] else "❌"
        size = f"{endpoint['data_size']:,}" if endpoint["success"] else "-"
        notes = endpoint.get("error", "")[:50] if not endpoint["success"] else "Success"
        table.add_row(
            endpoint["name"],
            status,
            size,
            notes
        )
    
    console.print(table)
    
    console.print(f"\n[bold green]✅ Audit complete![/bold green]")
    console.print(f"📁 Results saved to: {output_dir}")
    console.print(f"📄 Summary: {summary_file.name}")
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  ✅ Successful: {len(results['successful'])}")
    console.print(f"  ❌ Failed: {len(results['failed'])}")
    console.print(f"  📊 Total tested: {len(results['endpoints_tested'])}")


if __name__ == "__main__":
    main()

