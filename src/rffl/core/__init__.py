"""Core RFFL data processing modules."""

from .registry import (
    REGISTRY,
    TeamSeason,
    get_team,
    get_teams_by_season,
    get_owner_history,
    get_team_history,
    get_co_owned_teams,
    get_ironmen,
    get_unique_owners,
    get_unique_team_codes,
    validate_registry,
)

__all__ = [
    "REGISTRY",
    "TeamSeason",
    "get_team",
    "get_teams_by_season",
    "get_owner_history",
    "get_team_history",
    "get_co_owned_teams",
    "get_ironmen",
    "get_unique_owners",
    "get_unique_team_codes",
    "validate_registry",
]

