"""Shared constants for RFFL tools."""

STARTER_SLOTS = {"QB", "RB", "WR", "TE", "D/ST", "K", "FLEX", "RB/WR/TE"}
BENCH_SLOTS = {"Bench", "IR"}

# RFFL lineup requirements
RFFL_LINEUP_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 1,
    "D/ST": 1,
    "K": 1,
}

# Valid positions for FLEX slot
FLEX_ELIGIBLE_POSITIONS = {"RB", "WR", "TE"}

