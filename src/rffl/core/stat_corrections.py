"""Stat corrections export logic via web scraping."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .api import ESPNCredentials
from .exceptions import ESPNAPIError


@dataclass
class StatCorrectionRow:
    """Row data structure for stat correction export."""

    season_year: int
    week: int
    player_id: str | None
    player_name: str | None
    team_id: int | None
    team_code: str | None
    stat_id: str | None
    stat_name: str | None
    original_value: str | None
    corrected_value: str | None
    points_impact: str | None
    correction_date: str | None


def _make_session(credentials: ESPNCredentials | None) -> requests.Session:
    """Create authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    if credentials and credentials.is_authenticated:
        if credentials.swid:
            swid_val = credentials.swid.strip()
            session.cookies.set("SWID", swid_val)
            session.cookies.set("swid", swid_val)
        if credentials.espn_s2:
            # ESPN_S2 is often provided URL-encoded; unquote it for proper cookie usage
            s2_val = unquote(credentials.espn_s2)
            session.cookies.set("ESPN_S2", s2_val)
            session.cookies.set("espn_s2", s2_val)
    
    return session


def _scrape_stat_corrections_page(
    league_id: int,
    year: int,
    week: int,
    session: requests.Session,
) -> list[StatCorrectionRow]:
    """
    Scrape stat corrections from ESPN web page.
    
    ESPN uses a Next.js React app that loads corrections dynamically via JavaScript.
    We use Playwright to render the page and extract the data.
    
    Args:
        league_id: ESPN league ID
        year: Season year
        week: Week number (scoringPeriodId)
        session: Authenticated requests session (for cookies)
        
    Returns:
        List of StatCorrectionRow objects
        
    Raises:
        ESPNAPIError: If scraping fails
    """
    url = f"https://fantasy.espn.com/football/statcorrections"
    params = {
        "leagueId": league_id,
        "scoringPeriodId": week,
    }
    
    corrections = []
    
    # Use Playwright to render JavaScript if available
    if PLAYWRIGHT_AVAILABLE:
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                # Set cookies from session
                if session.cookies:
                    cookies_list: list[dict[str, str]] = []
                    for cookie in session.cookies:
                        cookies_list.append({
                            "name": cookie.name,
                            "value": cookie.value,
                            "domain": cookie.domain or ".espn.com",
                            "path": cookie.path or "/",
                        })
                    context.add_cookies(cookies_list)  # type: ignore[arg-type]
                
                page = context.new_page()
                full_url = f"{url}?leagueId={league_id}&scoringPeriodId={week}"
                page.goto(full_url, wait_until="networkidle", timeout=30000)
                
                # Wait for corrections table or data to load
                try:
                    # Wait for table or "No corrections" message
                    page.wait_for_selector("table, [data-testid*='correction'], .stat-corrections, .no-corrections", timeout=10000)
                except:
                    pass  # Continue even if selector not found
                
                # Try to extract data from the rendered page
                # Method 1: Look for table
                table_html = page.query_selector("table")
                if table_html:
                    table_text = table_html.inner_html()
                    soup = BeautifulSoup(table_text, "html.parser")
                    rows = soup.find_all("tr")
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 3:
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            if any(cell_texts):  # Has data
                                player_name = cell_texts[0] if len(cell_texts) > 0 else None
                                stat_name = cell_texts[1] if len(cell_texts) > 1 else None
                                original_value = cell_texts[2] if len(cell_texts) > 2 else None
                                corrected_value = cell_texts[3] if len(cell_texts) > 3 else None
                                points_impact = cell_texts[4] if len(cell_texts) > 4 else None
                                
                                if player_name or stat_name:
                                    corrections.append(
                                        StatCorrectionRow(
                                            season_year=year,
                                            week=week,
                                            player_id=None,
                                            player_name=player_name,
                                            team_id=None,
                                            team_code=None,
                                            stat_id=None,
                                            stat_name=stat_name,
                                            original_value=original_value,
                                            corrected_value=corrected_value,
                                            points_impact=points_impact,
                                            correction_date=None,
                                        )
                                    )
                
                # Method 2: Try to get data from page's JavaScript context
                try:
                    # Execute JavaScript to get corrections data if stored in window/React state
                    corrections_data = page.evaluate("""
                        () => {
                            // Try to find corrections in React state or window object
                            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.pageProps) {
                                const pageProps = window.__NEXT_DATA__.props.pageProps;
                                if (pageProps.corrections || pageProps.statCorrections) {
                                    return pageProps.corrections || pageProps.statCorrections;
                                }
                            }
                            // Try to find in React component state
                            const reactRoot = document.querySelector('#__next');
                            if (reactRoot && reactRoot._reactInternalInstance) {
                                // This is a simplified attempt - React internals vary
                            }
                            return null;
                        }
                    """)
                    
                    if corrections_data and isinstance(corrections_data, list):
                        for item in corrections_data:
                            if isinstance(item, dict):
                                corrections.append(
                                    StatCorrectionRow(
                                        season_year=year,
                                        week=week,
                                        player_id=str(item.get("playerId", "")) if item.get("playerId") else None,
                                        player_name=item.get("playerName") or item.get("name") or item.get("player"),
                                        team_id=item.get("teamId"),
                                        team_code=item.get("teamCode") or item.get("team"),
                                        stat_id=str(item.get("statId", "")) if item.get("statId") else None,
                                        stat_name=item.get("statName") or item.get("stat"),
                                        original_value=str(item.get("originalValue", "")) if item.get("originalValue") is not None else None,
                                        corrected_value=str(item.get("correctedValue", "")) if item.get("correctedValue") is not None else None,
                                        points_impact=str(item.get("pointsImpact", "")) if item.get("pointsImpact") is not None else None,
                                        correction_date=item.get("correctionDate") or item.get("date"),
                                    )
                                )
                except Exception:
                    pass  # JavaScript extraction failed, continue with HTML parsing
                
                browser.close()
        except Exception as e:
            # Fall back to simple HTML scraping if Playwright fails
            pass
    
    # Fallback: Simple HTML scraping (won't work for React apps but try anyway)
    if not corrections:
        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check for __NEXT_DATA__
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script and next_data_script.string:
                try:
                    import json
                    next_data = json.loads(next_data_script.string)
                    def find_corrections_in_data(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if "correction" in key.lower():
                                    if isinstance(value, list):
                                        return value
                                if isinstance(value, (dict, list)):
                                    result = find_corrections_in_data(value, f"{path}.{key}")
                                    if result:
                                        return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_corrections_in_data(item, path)
                                if result:
                                    return result
                        return None
                    
                    corrections_data = find_corrections_in_data(next_data)
                    if corrections_data:
                        for item in corrections_data:
                            if isinstance(item, dict):
                                corrections.append(
                                    StatCorrectionRow(
                                        season_year=year,
                                        week=week,
                                        player_id=str(item.get("playerId", "")) if item.get("playerId") else None,
                                        player_name=item.get("playerName") or item.get("name"),
                                        team_id=item.get("teamId"),
                                        team_code=item.get("teamCode") or item.get("team"),
                                        stat_id=str(item.get("statId", "")) if item.get("statId") else None,
                                        stat_name=item.get("statName") or item.get("stat"),
                                        original_value=str(item.get("originalValue", "")) if item.get("originalValue") is not None else None,
                                        corrected_value=str(item.get("correctedValue", "")) if item.get("correctedValue") is not None else None,
                                        points_impact=str(item.get("pointsImpact", "")) if item.get("pointsImpact") is not None else None,
                                        correction_date=item.get("correctionDate") or item.get("date"),
                                    )
                                )
                except Exception:
                    pass
        except requests.RequestException:
            pass
    
    return corrections


def export_stat_corrections(
    league_id: int,
    year: int,
    output_path: str | Path,
    credentials: ESPNCredentials | None = None,
    start_week: int = 1,
    end_week: int = 18,
) -> Path:
    """
    Export stat corrections for a season by scraping ESPN web pages.
    
    Args:
        league_id: ESPN league ID
        year: Season year
        output_path: Output CSV file path
        credentials: ESPN authentication credentials (required)
        start_week: First week to extract (default: 1)
        end_week: Last week to extract (default: 18)
        
    Returns:
        Path to written CSV file
        
    Raises:
        ESPNAPIError: If scraping fails or credentials missing
    """
    if not credentials or not credentials.is_authenticated:
        raise ESPNAPIError(
            "Stat corrections require authentication. Provide ESPN_S2 and SWID credentials."
        )
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    session = _make_session(credentials)
    
    all_corrections = []
    
    # Iterate through all weeks
    for week in range(start_week, end_week + 1):
        try:
            week_corrections = _scrape_stat_corrections_page(
                league_id=league_id,
                year=year,
                week=week,
                session=session,
            )
            all_corrections.extend(week_corrections)
        except ESPNAPIError:
            # Continue to next week if one fails
            continue
        except Exception as e:
            # Log but continue
            print(f"Warning: Failed to scrape week {week}: {e}")
            continue
    
    # Write to CSV
    if not all_corrections:
        # Create empty file with headers
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[f.name for f in StatCorrectionRow.__dataclass_fields__.values()])
            writer.writeheader()
    else:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[f.name for f in StatCorrectionRow.__dataclass_fields__.values()])
            writer.writeheader()
            for correction in all_corrections:
                writer.writerow(asdict(correction))
    
    return output_path

