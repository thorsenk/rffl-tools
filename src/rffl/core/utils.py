"""Utility functions for RFFL tools."""

import math
import os
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import yaml

from .constants import BENCH_SLOTS, FLEX_ELIGIBLE_POSITIONS, STARTER_SLOTS


def norm_slot(s: str | None, pos: str | None) -> str:
    """Normalize slot name from ESPN API."""
    s = (s or "").upper()
    p = (pos or "").upper()
    if s in ("RB/WR/TE", "FLEX"):
        return "FLEX"
    if s in ("DST", "D/ST", "DEFENSE"):
        return "D/ST"
    if s in ("BE", "BENCH"):
        return "Bench"
    if s in ("IR",):
        return "IR"
    if s in ("QB", "RB", "WR", "TE", "K"):
        return s
    if p in ("QB", "RB", "WR", "TE", "K"):
        return p
    if p in ("D/ST", "DST"):
        return "D/ST"
    return s or p or "Bench"


def is_starter(slot: str) -> bool:
    """Check if slot is a starter slot."""
    return slot in STARTER_SLOTS


def safe_float(x: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return default
        return float(x)
    except Exception:
        return default


def get_team_abbrev(team: Any) -> str:
    """Get team abbreviation from ESPN API Team object."""
    # Try different possible attribute names for team abbreviation
    for attr in ["abbrev", "team_abbrev", "abbreviation", "team_id", "name"]:
        if hasattr(team, attr):
            value: Any = getattr(team, attr)
            if value and isinstance(value, str):
                str_value: str = value
                return str_value
    return "Unknown"


def load_alias_index(mapping_path: str | Path) -> dict[str, list[dict]]:
    """Load team alias mapping index."""
    try:
        with open(mapping_path, encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
        aliases = y.get("aliases", []) if isinstance(y, dict) else []
        idx: dict[str, list[dict]] = {}
        for a in aliases:
            alias = a.get("alias")
            if not alias:
                continue
            idx.setdefault(alias, []).append(a)
        return idx
    except Exception:
        return {}


def resolve_canonical(abbrev: str, year: int | None, idx: dict[str, list[dict[str, Any]]]) -> str:
    """Resolve canonical team code from alias."""
    rules = idx.get(abbrev)
    if not rules:
        return abbrev
    if year is None:
        for r in rules:
            if not r.get("start_year") and not r.get("end_year"):
                canonical = r.get("canonical")
                return str(canonical) if canonical else abbrev
        canonical = rules[0].get("canonical")
        return str(canonical) if canonical else abbrev
    for r in rules:
        s = r.get("start_year")
        e = r.get("end_year")
        if (s is None or year >= int(s)) and (e is None or year <= int(e)):
            canonical = r.get("canonical")
            return str(canonical) if canonical else abbrev
    canonical = rules[0].get("canonical")
    return str(canonical) if canonical else abbrev


def load_canonical_meta(repo_root: Path | None = None) -> dict[tuple[int, str], dict]:
    """
    Load canonical team metadata keyed by (year, team_code).
    
    Uses RFFL_REG_TEAMS_001 (Python registry) as the Source of Truth.
    The repo_root parameter is kept for backward compatibility but is no longer used.
    """
    from .registry import REGISTRY
    
    meta: dict[tuple[int, str], dict] = {}
    for team in REGISTRY:
        meta[(team.season_year, team.team_code)] = {
            "team_full_name": team.team_full_name,
            "is_co_owned": "Yes" if team.is_co_owned else "No",
            "owner_code_1": team.owner_code_1,
            "owner_code_2": team.owner_code_2 or "",
        }
    return meta

