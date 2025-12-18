"""Tests for ESPN API client."""

import pytest
from unittest.mock import MagicMock, patch

from rffl.core.api import ESPNClient, ESPNCredentials
from rffl.core.exceptions import ESPNAPIError


def test_credentials_is_authenticated():
    """Test credentials authentication check."""
    creds = ESPNCredentials()
    assert not creds.is_authenticated

    creds = ESPNCredentials(espn_s2="test", swid="test")
    assert creds.is_authenticated

    creds = ESPNCredentials(espn_s2="test", swid=None)
    assert not creds.is_authenticated


def test_espn_client_initialization():
    """Test ESPN client initialization."""
    client = ESPNClient(league_id=323196, year=2024, public_only=True)
    assert client.league_id == 323196
    assert client.year == 2024
    assert client.public_only is True


@patch("rffl.core.api.League")
def test_espn_client_get_league_public(mock_league):
    """Test getting league instance in public mode."""
    mock_league_instance = MagicMock()
    mock_league.return_value = mock_league_instance

    client = ESPNClient(league_id=323196, year=2024, public_only=True)
    league = client.get_league()

    assert league == mock_league_instance
    mock_league.assert_called_once_with(league_id=323196, year=2024)


@patch("rffl.core.api.League")
def test_espn_client_get_league_with_credentials(mock_league):
    """Test getting league instance with credentials."""
    mock_league_instance = MagicMock()
    mock_league.return_value = mock_league_instance

    credentials = ESPNCredentials(espn_s2="test_s2", swid="test_swid")
    client = ESPNClient(
        league_id=323196, year=2024, credentials=credentials, public_only=False
    )
    league = client.get_league()

    assert league == mock_league_instance
    mock_league.assert_called_once_with(
        league_id=323196, year=2024, espn_s2="test_s2", swid="test_swid"
    )


@patch("rffl.core.api.League")
def test_espn_client_get_league_error(mock_league):
    """Test error handling when getting league fails."""
    mock_league.side_effect = Exception("Connection failed")

    client = ESPNClient(league_id=323196, year=2024)
    with pytest.raises(ESPNAPIError) as exc_info:
        client.get_league()

    assert "Failed to connect to ESPN" in str(exc_info.value)

