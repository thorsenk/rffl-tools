"""Transaction export logic."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import requests  # type: ignore[import-untyped]
from espn_api.football import League  # type: ignore[import-untyped]

from .api import ESPNCredentials
from .exceptions import ESPNAPIError


@dataclass
class TransactionRow:
    """Row data structure for transaction export."""

    season_year: int
    bid_amount: float | None
    date: str
    effective_date: str | None
    id: str
    is_pending: bool
    rating: int | None
    status: str
    type: str
    team_id: int | None
    team_code: str | None
    member_id: int | None
    player_id: int | None
    player_name: str | None
    to_team_id: int | None
    to_team_code: str | None
    from_team_id: int | None
    from_team_code: str | None


def export_transactions(
    league_id: int,
    year: int,
    output_path: str | Path,
    credentials: ESPNCredentials | None = None,
    public_only: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """
    Export transaction history using modern ESPN v3 API for 2018+ seasons.

    Args:
        league_id: ESPN league ID
        year: Season year
        output_path: Output CSV file path
        credentials: Optional ESPN authentication credentials
        public_only: If True, ignore credentials (public league mode)
        repo_root: Repository root path (for team mappings if needed)

    Returns:
        Path to written CSV file

    Raises:
        ESPNAPIError: If ESPN API calls fail
    """
    # Set up cookies for private leagues
    cookies = {}
    if not public_only and credentials and credentials.is_authenticated:
        if credentials.espn_s2:
            cookies["espn_s2"] = credentials.espn_s2
        if credentials.swid:
            cookies["SWID"] = credentials.swid

    # For 2018+ seasons, use espn_api library which handles transactions properly
    if year >= 2018:
        try:
            # Use espn_api library to get transactions
            if not public_only and credentials and credentials.is_authenticated:
                league = League(
                    league_id=league_id,
                    year=year,
                    espn_s2=credentials.espn_s2,
                    swid=credentials.swid,
                )
            else:
                league = League(league_id=league_id, year=year)
            
            # Get transactions from league object
            # The espn_api library stores transactions in league._espn_request_cache
            # or we can access them via league.recent_activity or league.transactions
            transactions = []
            
            # Try multiple ways to get transactions
            if hasattr(league, 'recent_activity'):
                try:
                    recent_activity = league.recent_activity
                    if isinstance(recent_activity, list):
                        transactions = recent_activity
                except:
                    pass
            
            # If still empty, try transactions attribute/method
            if not transactions and hasattr(league, 'transactions'):
                trans_attr = getattr(league, 'transactions')
                if callable(trans_attr):
                    try:
                        transactions = trans_attr()
                    except:
                        pass
                else:
                    transactions = trans_attr
            
            # If still empty, check internal cache
            if not transactions and hasattr(league, '_espn_request_cache'):
                cache = league._espn_request_cache
                if isinstance(cache, dict):
                    # Check for transaction-related keys in cache
                    for key in ['transactions', 'recentTransactions', 'activity', 'recentActivity']:
                        if key in cache:
                            val = cache[key]
                            if isinstance(val, list):
                                transactions = val
                                break
            
            # Convert espn_api transaction objects to dicts for processing
            transactions_list = []
            for txn in transactions:
                if hasattr(txn, '__dict__'):
                    # Convert transaction object to dict
                    txn_dict = {}
                    for attr in ['id', 'type', 'status', 'isPending', 'rating', 'bidAmount', 
                                'date', 'effectiveDate', 'teamId', 'memberId', 'items',
                                'proposingTeamId', 'acceptingTeamId', 'scoringPeriodId']:
                        if hasattr(txn, attr):
                            txn_dict[attr] = getattr(txn, attr)
                    transactions_list.append(txn_dict)
                elif isinstance(txn, dict):
                    transactions_list.append(txn)
                else:
                    # Try to convert to dict
                    transactions_list.append(txn)
            
            transactions = transactions_list
            
            # Get team data for mapping
            teams_data = []
            if hasattr(league, 'teams'):
                for team in league.teams:
                    team_dict = {}
                    if hasattr(team, 'team_id'):
                        team_dict['id'] = team.team_id
                    if hasattr(team, 'team_abbrev'):
                        team_dict['abbrev'] = team.team_abbrev
                    elif hasattr(team, 'team_name'):
                        # Try to extract abbrev from team name or use team_id
                        team_dict['abbrev'] = f"T{team.team_id}" if hasattr(team, 'team_id') else "UNK"
                    teams_data.append(team_dict)
            
            # If no teams found, try to get from league settings or status
            if not teams_data and hasattr(league, '_fetch_league'):
                # Try alternative method to get teams
                try:
                    league_data = league._fetch_league()
                    if 'teams' in league_data:
                        teams_data = league_data['teams']
                except:
                    pass
            
            # If no transactions found via espn_api, try direct API call per-week
            # Transactions are returned per scoring period, so we need to iterate through weeks
            if not transactions:
                base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
                all_transactions = []
                seen_transaction_ids = set()
                
                # Try to get final scoring period from league status
                final_scoring_period = 18  # Default to 18 weeks
                if hasattr(league, 'settings') and hasattr(league.settings, 'matchup_period_count'):
                    final_scoring_period = league.settings.matchup_period_count
                elif hasattr(league, '_fetch_league'):
                    try:
                        league_data = league._fetch_league()
                        if 'status' in league_data and 'finalScoringPeriod' in league_data['status']:
                            final_scoring_period = league_data['status']['finalScoringPeriod']
                    except:
                        pass
                
                # Iterate through all weeks to collect transactions
                for week in range(1, final_scoring_period + 1):
                    week_url = f"{base_url}/seasons/{year}/segments/0/leagues/{league_id}?scoringPeriodId={week}&view=mTransactions2&view=mTeam"
                    try:
                        week_response = requests.get(week_url, cookies=cookies, timeout=10)
                        if week_response.status_code == 200:
                            week_data = week_response.json()
                            # Extract transactions from this week
                            for key in ["transactions", "recentTransactions", "activity", "recentActivity"]:
                                if key in week_data and isinstance(week_data[key], list):
                                    for txn in week_data[key]:
                                        txn_id = txn.get("id") if isinstance(txn, dict) else getattr(txn, 'id', None)
                                        # Avoid duplicates
                                        if txn_id and txn_id not in seen_transaction_ids:
                                            seen_transaction_ids.add(txn_id)
                                            all_transactions.append(txn)
                                    break
                            # Get teams from first successful week response
                            if not teams_data and 'teams' in week_data:
                                teams_data = week_data['teams']
                    except Exception:
                        continue
                
                transactions = all_transactions
            
        except Exception as e:
            # If espn_api fails, try direct API call as fallback
            base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
            fallback_url = f"{base_url}/seasons/{year}/segments/0/leagues/{league_id}?view=mTransactions2&view=mTeam"
            try:
                fallback_response = requests.get(fallback_url, cookies=cookies, timeout=10)
                if fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    transactions = []
                    for key in ["transactions", "recentTransactions", "activity", "recentActivity"]:
                        if key in fallback_data and isinstance(fallback_data[key], list):
                            transactions = fallback_data[key]
                            break
                    teams_data = fallback_data.get("teams", [])
                else:
                    raise ESPNAPIError(f"Failed to fetch transactions using espn_api library: {e}") from e
            except requests.exceptions.RequestException as fallback_error:
                raise ESPNAPIError(f"Failed to fetch transactions using espn_api library and fallback API call: {e} | {fallback_error}") from e
    else:
        # For historical seasons (< 2018), use direct API calls
        base_url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
        url = f"{base_url}/leagueHistory/{league_id}?seasonId={year}&view=mTransactions"
        
        try:
            response = requests.get(url, cookies=cookies, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response structures
            if isinstance(data, list) and data:
                league_data = data[0]
            else:
                league_data = data
            
            # Extract transaction data - try multiple possible keys
            transactions = []
            possible_keys = ["transactions", "recentTransactions", "activity", "recentActivity"]
            
            for key in possible_keys:
                if key in league_data:
                    transactions = league_data[key]
                    break
            
            # Get team data for mapping
            teams_data = league_data.get("teams", [])
            
        except requests.exceptions.RequestException as e:
            raise ESPNAPIError(f"Failed to fetch transaction data from ESPN API: {e}") from e
        except (KeyError, IndexError, ValueError) as e:
            raise ESPNAPIError(f"Failed to parse ESPN API response: {e}") from e

    # Create team code mapping
    team_id_to_code = {}
    for team in teams_data:
        team_id = team.get("id")
        # Use existing team abbrev logic
        team_code = None
        if "abbrev" in team:
            team_code = team["abbrev"]
        elif "teamAbbrev" in team:
            team_code = team["teamAbbrev"]
        elif "location" in team and "nickname" in team:
            team_code = (
                f"{team['location'][:2].upper()}{team['nickname'][:2].upper()}"
            )
        else:
            team_code = f"T{team_id}"

        team_id_to_code[team_id] = team_code

    # Process transactions
    rows: list[TransactionRow] = []
    for txn in transactions:
        # Extract basic transaction info
        txn_id = str(txn.get("id", ""))
        txn_type = txn.get("type", "")
        txn_status = txn.get("status", "")
        is_pending = txn.get("isPending", False)
        rating = txn.get("rating")
        bid_amount = txn.get("bidAmount")

        # Handle timestamps
        date_epoch = txn.get("date", 0)
        date_str = ""
        if date_epoch:
            try:
                date_str = datetime.fromtimestamp(date_epoch / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, OSError, OverflowError):
                date_str = str(date_epoch)

        effective_date_epoch = txn.get("effectiveDate")
        effective_date_str = None
        if effective_date_epoch:
            try:
                effective_date_str = datetime.fromtimestamp(
                    effective_date_epoch / 1000
                ).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError, OverflowError):
                effective_date_str = str(effective_date_epoch)

        # Handle team and member info
        team_id = txn.get("teamId")
        team_code = team_id_to_code.get(team_id) if team_id else None
        member_id = txn.get("memberId")

        # Process transaction items (players involved)
        items = txn.get("items", []) if isinstance(txn, dict) else getattr(txn, "items", [])
        if not items:
            # Transaction with no items (rare but possible)
            rows.append(
                TransactionRow(
                    season_year=year,
                    bid_amount=bid_amount,
                    date=date_str,
                    effective_date=effective_date_str,
                    id=txn_id,
                    is_pending=is_pending,
                    rating=rating,
                    status=txn_status,
                    type=txn_type,
                    team_id=team_id,
                    team_code=team_code,
                    member_id=member_id,
                    player_id=None,
                    player_name=None,
                    to_team_id=None,
                    to_team_code=None,
                    from_team_id=None,
                    from_team_code=None,
                )
            )
        else:
            # Process each player/item in transaction
            for item in items:
                # Handle both dict and object items
                if isinstance(item, dict):
                    player_id = item.get("playerId")
                    player_name = item.get("playerName", "")
                    to_team_id = item.get("toTeamId")
                    from_team_id = item.get("fromTeamId")
                else:
                    # Handle object items (from espn_api library)
                    player_id = getattr(item, "playerId", None)
                    player_name = getattr(item, "playerName", "")
                    to_team_id = getattr(item, "toTeamId", None)
                    from_team_id = getattr(item, "fromTeamId", None)
                
                to_team_code = team_id_to_code.get(to_team_id) if to_team_id else None
                from_team_code = (
                    team_id_to_code.get(from_team_id) if from_team_id else None
                )

                rows.append(
                    TransactionRow(
                        season_year=year,
                        bid_amount=bid_amount,
                        date=date_str,
                        effective_date=effective_date_str,
                        id=txn_id,
                        is_pending=is_pending,
                        rating=rating,
                        status=txn_status,
                        type=txn_type,
                        team_id=team_id,
                        team_code=team_code,
                        member_id=member_id,
                        player_id=player_id,
                        player_name=player_name,
                        to_team_id=to_team_id,
                        to_team_code=to_team_code,
                        from_team_id=from_team_id,
                        from_team_code=from_team_code,
                    )
                )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "season_year",
                "bid_amount",
                "date",
                "effective_date",
                "id",
                "is_pending",
                "rating",
                "status",
                "type",
                "team_id",
                "team_code",
                "member_id",
                "player_id",
                "player_name",
                "to_team_id",
                "to_team_code",
                "from_team_id",
                "from_team_code",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    return out_path

