"""Centralized ESPN API client with authentication and error handling."""

from dataclasses import dataclass
from typing import Any

from espn_api.football import League  # type: ignore[import-untyped]

from .exceptions import ESPNAPIError, AuthenticationError


@dataclass
class ESPNCredentials:
    """ESPN authentication credentials."""

    espn_s2: str | None = None
    swid: str | None = None

    @property
    def is_authenticated(self) -> bool:
        """Check if credentials are provided."""
        return bool(self.espn_s2 and self.swid)


class ESPNClient:
    """Centralized ESPN Fantasy Football API client."""

    def __init__(
        self,
        league_id: int,
        year: int,
        credentials: ESPNCredentials | None = None,
        public_only: bool = True,
    ):
        """
        Initialize ESPN client.

        Args:
            league_id: ESPN league ID
            year: Season year
            credentials: Optional authentication credentials
            public_only: If True, ignore credentials even if provided
        """
        self.league_id = league_id
        self.year = year
        self.credentials = credentials or ESPNCredentials()
        self.public_only = public_only
        self._league: League | None = None

    def get_league(self) -> League:
        """Get League instance with proper authentication."""
        if self._league is None:
            try:
                if self.public_only or not self.credentials.is_authenticated:
                    self._league = League(
                        league_id=self.league_id,
                        year=self.year,
                    )
                else:
                    self._league = League(
                        league_id=self.league_id,
                        year=self.year,
                        espn_s2=self.credentials.espn_s2,
                        swid=self.credentials.swid,
                    )
            except Exception as e:
                raise ESPNAPIError(f"Failed to connect to ESPN: {e}") from e
        return self._league

    def get_boxscores(self, week: int) -> list[Any]:
        """Fetch boxscores for a specific week."""
        league = self.get_league()
        try:
            result: list[Any] = league.box_scores(week)
            return result
        except Exception as e:
            raise ESPNAPIError(f"Failed to fetch boxscores for week {week}: {e}") from e

    def get_draft(self) -> list[Any]:
        """Fetch draft picks."""
        league = self.get_league()
        try:
            result: list[Any] = league.draft
            return result
        except Exception as e:
            raise ESPNAPIError(f"Failed to fetch draft: {e}") from e

