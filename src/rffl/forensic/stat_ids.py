"""
ESPN Fantasy Football Stat IDs
Discovered via RFFL-INQ-2025-001 investigation

This module contains stat ID constants for identifying scoring events
in ESPN Fantasy Football API responses.

Stat IDs are used in player.stats[].appliedStats dictionaries where
the key is the stat ID (as string or int) and the value is the stat count/points.
"""


class PlayerStatID:
    """Individual player stat IDs."""

    # Offensive stats (common, for reference)
    PASSING_TD: int = 4
    RUSHING_TD: int = 25
    RECEIVING_TD: int = 43

    # Return stats (DISCOVERED via RFFL-INQ-2025-001)
    KICK_RETURN_TD: int = 102  # Discovered: Week 16, 2025 - Rashid Shaheed kick return TD
    PUNT_RETURN_TD: int | None = None  # TODO: Discover from punt return TD event

    # Return yards (for reference, not used in RFFL scoring)
    KICK_RETURN_YARDS: int | None = None  # TODO: Discover if needed
    PUNT_RETURN_YARDS: int | None = None  # TODO: Discover if needed


class DSTStatID:
    """D/ST unit stat IDs."""

    # Defensive stats (common, for reference - TO BE DISCOVERED)
    SACKS: int | None = None  # TODO: Discover
    INTERCEPTIONS: int | None = None  # TODO: Discover
    FUMBLE_RECOVERIES: int | None = None  # TODO: Discover
    SAFETIES: int | None = None  # TODO: Discover
    BLOCKED_KICKS: int | None = None  # TODO: Discover

    # TD stats (Phase 1 Priority - DISCOVERED)
    KICK_RETURN_TD: int = 102  # Discovered: Same stat ID as player (Week 16, 2025 - Seattle D/ST)
    PUNT_RETURN_TD: int | None = None  # TODO: Discover from punt return TD event

    # TD stats (Phase 2 - TO BE DISCOVERED)
    PICK_SIX: int | None = None  # TODO: INT returned for TD
    FUMBLE_RETURN_TD: int | None = None  # TODO: Fumble recovered and returned for TD
    BLOCKED_KICK_TD: int | None = None  # TODO: Blocked punt/FG returned for TD

    # Points allowed tiers (for reference - TO BE DISCOVERED)
    POINTS_ALLOWED_0: int | None = None  # TODO: Discover
    POINTS_ALLOWED_1_6: int | None = None  # TODO: Discover
    # ... etc


def get_player_return_td_stat_ids() -> dict[str, int | None]:
    """Get player return TD stat IDs."""
    return {
        "kick": PlayerStatID.KICK_RETURN_TD,
        "punt": PlayerStatID.PUNT_RETURN_TD,
    }


def get_dst_return_td_stat_ids() -> dict[str, int | None]:
    """Get D/ST return TD stat IDs."""
    return {
        "kick": DSTStatID.KICK_RETURN_TD,
        "punt": DSTStatID.PUNT_RETURN_TD,
    }


def validate_stat_ids() -> dict[str, bool]:
    """
    Validate that all required stat IDs have been discovered.
    
    Returns dict with validation status for each stat ID category.
    """
    return {
        "player_kick_return_td": PlayerStatID.KICK_RETURN_TD is not None,
        "player_punt_return_td": PlayerStatID.PUNT_RETURN_TD is not None,
        "dst_kick_return_td": DSTStatID.KICK_RETURN_TD is not None,
        "dst_punt_return_td": DSTStatID.PUNT_RETURN_TD is not None,
    }


