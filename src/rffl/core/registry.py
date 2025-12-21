"""RFFL Team Owner Registry
========================
Doc ID: RFFL-REG-TEAMS-001
Version: 1.0.0
Status: Canonical
Authority: Commissioner (PCX)
Last Validated: 2025-12-19

Canonical registry of all RFFL teams and owners across 24 seasons (2002-2025).

Usage:
    from rffl.core.registry import (
        get_team,
        get_teams_by_season,
        get_owner_history,
        get_ironmen,
        REGISTRY
    )
    
    # Get all teams in 2011
    teams_2011 = get_teams_by_season(2011)
    
    # Get PCX ownership history
    pcx_history = get_owner_history("THORSEN_KYLE")
    
    # Find a specific team-season
    team = get_team("GFM", 2025)
"""

from dataclasses import dataclass
from typing import Any, Optional


# =============================================================================
# METADATA
# =============================================================================

DOC_ID = "RFFL-REG-TEAMS-001"
VERSION = "1.0.0"
STATUS = "canonical"
AUTHORITY = "Commissioner (PCX)"
LAST_VALIDATED = "2025-12-19"

STATISTICS = {
    "total_records": 278,
    "seasons_covered": 24,
    "date_range": (2002, 2025),
    "unique_team_codes": 31,
    "unique_owners": 29,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class TeamSeason:
    """A team's record for a single season."""
    season_year: int
    team_code: str
    team_full_name: str
    is_co_owned: bool
    owner_code_1: str
    owner_code_2: Optional[str] = None


@dataclass(frozen=True)
class Ironman:
    """Owner with unbroken consecutive seasons."""
    owner_code: str
    team_code: str
    seasons: int


@dataclass(frozen=True)
class Sabbatical:
    """Documented owner absence."""
    owner: str
    team: Optional[str]
    year_out: int
    year_returned: int
    notes: str


# =============================================================================
# IRONMEN (24 Consecutive Seasons)
# =============================================================================

IRONMEN = (
    Ironman("FEHLHABER_STEVE", "CHLK", 24),
    Ironman("GOWERY_GRANT", "JAGB", 24),
    Ironman("THORSEN_KYLE", "PCX", 24),
)


# =============================================================================
# SABBATICALS
# =============================================================================

SABBATICALS = (
    Sabbatical("TETZLAFF_LANCE", "SEX", 2007, 2008, "SEX team dormant; returned via PCX co-ownership"),
    Sabbatical("CLARK_JOSH", "BOON", 2004, 2005, "Final season 2005"),
    Sabbatical("MACK_DUSTIN", "MACK", 2003, 2004, "Final season 2007"),
)


# =============================================================================
# KNOWN ISSUES
# =============================================================================

KNOWN_ISSUES = {
    "DATA-001": {
        "status": "NEEDS_VERIFICATION",
        "description": (
            "VKGS and BANG team presence in 2005-2006 requires verification. "
            "Search results indicate 2002-2010 active range, but reconstruction shows gaps."
        ),
    },
}


# =============================================================================
# REGISTRY DATA
# =============================================================================

REGISTRY: tuple[TeamSeason, ...] = (
    # =========================================================================
    # FOUNDING ERA (2002-2006) — 10 Teams per Season
    # =========================================================================
    
    # --- 2002 ---
    TeamSeason(2002, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2002, "CUM", "De-Flowerers", False, "KNABE_MARK"),
    TeamSeason(2002, "MACK", "D-Macks", False, "MACK_DUSTIN"),
    TeamSeason(2002, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2002, "BANG", "Brandy Bangers", False, "VOSS_BRADY"),
    TeamSeason(2002, "TRSN", "Trouser Snakes", False, "CLEMENTS_CURT"),
    TeamSeason(2002, "SEX", "Sexual Predators", False, "TETZLAFF_LANCE"),
    TeamSeason(2002, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2002, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2002, "VKGS", "Stout Vikings", False, "MCLAUGHLIN_PAT"),
    
    # --- 2003 ---
    TeamSeason(2003, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2003, "CUM", "De-Flowerers", False, "KNABE_MARK"),
    TeamSeason(2003, "TRSN", "Trouser Snakes", False, "CLEMENTS_CURT"),
    TeamSeason(2003, "BANG", "Brandy Bangers", False, "VOSS_BRADY"),
    TeamSeason(2003, "SEX", "Sexual Predators", False, "TETZLAFF_LANCE"),
    TeamSeason(2003, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2003, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2003, "VKGS", "Stout Vikings", False, "MCLAUGHLIN_PAT"),
    TeamSeason(2003, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2003, "BOON", "Boone Docks", False, "CLARK_JOSH"),
    
    # --- 2004 ---
    TeamSeason(2004, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2004, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2004, "SEX", "Sexual Predators", False, "TETZLAFF_LANCE"),
    TeamSeason(2004, "TRSN", "Trouser Snakes", False, "CLEMENTS_CURT"),
    TeamSeason(2004, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2004, "BANG", "Brandy Bangers", False, "VOSS_BRADY"),
    TeamSeason(2004, "CUM", "De-Flowerers", False, "KNABE_MARK"),
    TeamSeason(2004, "VKGS", "Stout Vikings", False, "MCLAUGHLIN_PAT"),
    TeamSeason(2004, "MACK", "D-Macks", False, "MACK_DUSTIN"),
    TeamSeason(2004, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    
    # --- 2005 ---
    TeamSeason(2005, "SEX", "Sexual Predators", False, "TETZLAFF_LANCE"),
    TeamSeason(2005, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2005, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2005, "VKGS", "Stout Vikings", False, "MCLAUGHLIN_PAT"),
    TeamSeason(2005, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2005, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2005, "TRSN", "Trouser Snakes", False, "CLEMENTS_CURT"),
    TeamSeason(2005, "BOON", "Boone Docks", False, "CLARK_JOSH"),
    TeamSeason(2005, "MACK", "D-Macks", False, "MACK_DUSTIN"),
    TeamSeason(2005, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    
    # --- 2006 ---
    TeamSeason(2006, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2006, "SEX", "Sexual Predators", False, "TETZLAFF_LANCE"),
    TeamSeason(2006, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2006, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2006, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2006, "TGFY", "Too Good For You", False, "OLSON_WES"),
    TeamSeason(2006, "RSTY", "Rusty Trombones", False, "ROBINSON_RUSTY"),
    TeamSeason(2006, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2006, "MACK", "D-Macks", False, "MACK_DUSTIN"),
    TeamSeason(2006, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    
    # =========================================================================
    # MODERN ERA (2007-2025) — 12 Teams per Season
    # =========================================================================
    
    # --- 2007 ---
    TeamSeason(2007, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2007, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2007, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2007, "MACK", "D-Macks", False, "MACK_DUSTIN"),
    TeamSeason(2007, "DINO", "Dino Ciccarellis", False, "TVEDTEN_OLE"),
    TeamSeason(2007, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2007, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2007, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2007, "TGFY", "Too Good For You", False, "JOHANSEN_TYLER"),
    TeamSeason(2007, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2007, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    TeamSeason(2007, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    
    # --- 2008 ---
    TeamSeason(2008, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2008, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    TeamSeason(2008, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2008, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2008, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2008, "TGFY", "Too Good For You", False, "JOHANSEN_TYLER"),
    TeamSeason(2008, "PCX", "Gypsy Peacocks", True, "THORSEN_KYLE", "TETZLAFF_LANCE"),
    TeamSeason(2008, "DINO", "Dino Ciccarellis", False, "TVEDTEN_OLE"),
    TeamSeason(2008, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2008, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2008, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    TeamSeason(2008, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    
    # --- 2009 ---
    TeamSeason(2009, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2009, "TGFY", "Too Good For You", False, "JOHANSEN_TYLER"),
    TeamSeason(2009, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2009, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2009, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2009, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2009, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2009, "TRIG", "Trig Enterprises", True, "TETZLAFF_LANCE", "KNABE_JUSTIN"),
    TeamSeason(2009, "DINO", "Dino Ciccarellis", False, "TVEDTEN_OLE"),
    TeamSeason(2009, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2009, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    TeamSeason(2009, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    
    # --- 2010 ---
    TeamSeason(2010, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    TeamSeason(2010, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2010, "TRIG", "Trig Enterprises", True, "TETZLAFF_LANCE", "JOHANSEN_TYLER"),
    TeamSeason(2010, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2010, "DINO", "Dino Ciccarellis", False, "TVEDTEN_OLE"),
    TeamSeason(2010, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2010, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    TeamSeason(2010, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2010, "BBWZ", "Brimball Wizards", True, "FEATHERS_JASON", "OLSON_WES"),
    TeamSeason(2010, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2010, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2010, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    
    # --- 2011 ---
    TeamSeason(2011, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    TeamSeason(2011, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2011, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2011, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2011, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    TeamSeason(2011, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2011, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2011, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2011, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2011, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2011, "BBWZ", "Brimball Wizards", True, "FEATHERS_JASON", "OLSON_WES"),
    TeamSeason(2011, "2SCM", "2-Step Church Mice", True, "JOHANSEN_TYLER", "HAHN_CHRIS"),
    
    # --- 2012 ---
    TeamSeason(2012, "BALL", "Blue Ballers", False, "GEISLER_TIM"),
    TeamSeason(2012, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2012, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2012, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2012, "JACK", "Jackson Pines", True, "KNABE_JUSTIN", "HANSON_MARC"),
    TeamSeason(2012, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2012, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2012, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2012, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2012, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2012, "BBWZ", "Brimball Wizards", True, "FEATHERS_JASON", "OLSON_WES"),
    TeamSeason(2012, "2SCM", "2-Step Church Mice", True, "JOHANSEN_TYLER", "HAHN_CHRIS"),
    
    # --- 2013 ---
    TeamSeason(2013, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2013, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2013, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2013, "JACK", "Jackson Pines", False, "KNABE_JUSTIN"),
    TeamSeason(2013, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2013, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2013, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2013, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2013, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2013, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2013, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2013, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2014 ---
    TeamSeason(2014, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2014, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2014, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2014, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2014, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2014, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2014, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2014, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2014, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2014, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2014, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2014, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2015 ---
    TeamSeason(2015, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2015, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2015, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2015, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2015, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2015, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2015, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2015, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2015, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2015, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2015, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2015, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2016 ---
    TeamSeason(2016, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2016, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2016, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2016, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2016, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2016, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2016, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2016, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2016, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2016, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2016, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2016, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2017 ---
    TeamSeason(2017, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2017, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2017, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2017, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2017, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2017, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2017, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2017, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2017, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2017, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2017, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2017, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2018 ---
    TeamSeason(2018, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2018, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2018, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2018, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2018, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2018, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2018, "SSS", "Sweets Special Sauce", False, "SWEET_DERRICK"),
    TeamSeason(2018, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2018, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2018, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2018, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2018, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2019 ---
    TeamSeason(2019, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2019, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2019, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2019, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2019, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2019, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2019, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2019, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2019, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2019, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2019, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2019, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2020 ---
    TeamSeason(2020, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2020, "DKEG", "Da Keggers", False, "PARSONS_TORY"),
    TeamSeason(2020, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2020, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2020, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2020, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2020, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2020, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2020, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2020, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2020, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2020, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2021 ---
    TeamSeason(2021, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2021, "TACT", "Tactical Tacticians", True, "CUPERY_NICK", "SOVIAK_PAT"),
    TeamSeason(2021, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2021, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2021, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2021, "PITB", "Raging Pitbulls", False, "KRUEGER_DUSTIN"),
    TeamSeason(2021, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2021, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2021, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2021, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2021, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2021, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2022 ---
    TeamSeason(2022, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2022, "TACT", "Tactical Tacticians", True, "CUPERY_NICK", "SOVIAK_PAT"),
    TeamSeason(2022, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2022, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2022, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2022, "PKMC", "PKMC Unhinged", True, "KASPER_PAT", "CONLON_MIKE"),
    TeamSeason(2022, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2022, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2022, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2022, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2022, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2022, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    
    # --- 2023 ---
    TeamSeason(2023, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2023, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    TeamSeason(2023, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2023, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2023, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2023, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2023, "TACT", "Tactical Tacticians", True, "CUPERY_NICK", "SOVIAK_PAT"),
    TeamSeason(2023, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2023, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2023, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2023, "PKMC", "PKMC Unhinged", True, "KASPER_PAT", "CONLON_MIKE"),
    TeamSeason(2023, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    
    # --- 2024 ---
    TeamSeason(2024, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2024, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2024, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2024, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2024, "PKMC", "PKMC Unhinged", True, "KASPER_PAT", "CONLON_MIKE"),
    TeamSeason(2024, "TACT", "Tactical Tacticians", True, "CUPERY_NICK", "SOVIAK_PAT"),
    TeamSeason(2024, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2024, "SSBB", "SS Bobber Bandits", True, "SWEET_DERRICK", "DARNAUER_LUKE"),
    TeamSeason(2024, "WZRD", "White Wizards", False, "OLSON_WES"),
    TeamSeason(2024, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2024, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    TeamSeason(2024, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    
    # --- 2025 ---
    TeamSeason(2025, "JAGB", "Jag Bombers", False, "GOWERY_GRANT"),
    TeamSeason(2025, "MRYJ", "Mary Jane", False, "ALDEN-ANDERSON_ANDY"),
    TeamSeason(2025, "LNO", "Least Needlish Ones", True, "KNABE_JUSTIN", "HAHN_CHRIS"),
    TeamSeason(2025, "MXLB", "Mex-Banese", True, "JOHANSEN_TYLER", "ABREGO_JASON"),
    TeamSeason(2025, "TACT", "Tactical Tacticians", True, "CUPERY_NICK", "SOVIAK_PAT"),
    TeamSeason(2025, "TNT", "Tennessee Typicals", False, "SWEET_DERRICK"),
    TeamSeason(2025, "GFM", "Great Fantasy Minds", True, "TETZLAFF_LANCE", "TVEDTEN_OLE"),
    TeamSeason(2025, "PCX", "Gypsy Peacocks", False, "THORSEN_KYLE"),
    TeamSeason(2025, "CHLK", "Alpha Chalkers", False, "FEHLHABER_STEVE"),
    TeamSeason(2025, "BRIM", "Brimstone Bohemians", False, "FEATHERS_JASON"),
    TeamSeason(2025, "PKMC", "PKMC Unhinged", True, "KASPER_PAT", "CONLON_MIKE"),
    TeamSeason(2025, "WZRD", "White Wizards", False, "OLSON_WES"),
)


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_team(team_code: str, season: int) -> Optional[TeamSeason]:
    """
    Get a specific team's record for a given season.
    
    Args:
        team_code: The team identifier (e.g., "PCX", "GFM")
        season: The season year (e.g., 2025)
    
    Returns:
        TeamSeason if found, None otherwise
    
    Example:
        >>> get_team("GFM", 2025)
        TeamSeason(season_year=2025, team_code='GFM', team_full_name='Great Fantasy Minds', 
                   is_co_owned=True, owner_code_1='TETZLAFF_LANCE', owner_code_2='TVEDTEN_OLE')
    """
    for team in REGISTRY:
        if team.team_code == team_code and team.season_year == season:
            return team
    return None


def get_teams_by_season(season: int) -> list[TeamSeason]:
    """
    Get all teams for a given season.
    
    Args:
        season: The season year (e.g., 2011)
    
    Returns:
        List of TeamSeason records for that year
    
    Example:
        >>> len(get_teams_by_season(2011))
        12
    """
    return [team for team in REGISTRY if team.season_year == season]


def get_owner_history(owner_code: str) -> list[TeamSeason]:
    """
    Get all seasons where an owner participated (as owner_1 or owner_2).
    
    Args:
        owner_code: Owner identifier (e.g., "THORSEN_KYLE")
    
    Returns:
        List of TeamSeason records, sorted by season
    
    Example:
        >>> history = get_owner_history("THORSEN_KYLE")
        >>> len(history)
        24
    """
    results = [
        team for team in REGISTRY 
        if team.owner_code_1 == owner_code or team.owner_code_2 == owner_code
    ]
    return sorted(results, key=lambda t: t.season_year)


def get_team_history(team_code: str) -> list[TeamSeason]:
    """
    Get all seasons for a specific team code.
    
    Args:
        team_code: Team identifier (e.g., "PCX")
    
    Returns:
        List of TeamSeason records, sorted by season
    
    Example:
        >>> history = get_team_history("GFM")
        >>> history[0].season_year
        2011
    """
    results = [team for team in REGISTRY if team.team_code == team_code]
    return sorted(results, key=lambda t: t.season_year)


def get_co_owned_teams(season: Optional[int] = None) -> list[TeamSeason]:
    """
    Get all co-owned teams, optionally filtered by season.
    
    Args:
        season: Optional season year filter
    
    Returns:
        List of co-owned TeamSeason records
    """
    results = [team for team in REGISTRY if team.is_co_owned]
    if season:
        results = [team for team in results if team.season_year == season]
    return results


def get_ironmen() -> tuple[Ironman, ...]:
    """Return owners with 24 consecutive seasons."""
    return IRONMEN


def get_unique_owners() -> set[str]:
    """Get all unique owner codes across all seasons."""
    owners = set()
    for team in REGISTRY:
        owners.add(team.owner_code_1)
        if team.owner_code_2:
            owners.add(team.owner_code_2)
    return owners


def get_unique_team_codes() -> set[str]:
    """Get all unique team codes across all seasons."""
    return {team.team_code for team in REGISTRY}


def validate_registry() -> dict[str, Any]:
    """
    Run validation checks on the registry.

    Returns:
        Dict with validation results
    """
    # Check team counts per season
    team_counts_by_season: dict[int, dict[str, Any]] = {}
    for year in range(2002, 2026):
        count = len(get_teams_by_season(year))
        expected = 10 if year <= 2006 else 12
        team_counts_by_season[year] = {
            "actual": count,
            "expected": expected,
            "valid": count == expected
        }

    results: dict[str, Any] = {
        "total_records": len(REGISTRY),
        "expected_records": 278,
        "founding_era_count": len([t for t in REGISTRY if t.season_year <= 2006]),
        "modern_era_count": len([t for t in REGISTRY if t.season_year >= 2007]),
        "unique_owners": len(get_unique_owners()),
        "unique_team_codes": len(get_unique_team_codes()),
        "seasons": sorted(set(t.season_year for t in REGISTRY)),
        "team_counts_by_season": team_counts_by_season,
        "all_valid": all(v["valid"] for v in team_counts_by_season.values()),
    }

    return results


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print(f"RFFL Team Owner Registry")
    print(f"Doc ID: {DOC_ID}")
    print(f"Version: {VERSION}")
    print(f"Status: {STATUS}")
    print(f"")
    print(f"Total Records: {len(REGISTRY)}")
    print(f"Unique Owners: {len(get_unique_owners())}")
    print(f"Unique Team Codes: {len(get_unique_team_codes())}")
    print(f"")
    print(f"Ironmen (24 consecutive seasons):")
    for ironman in IRONMEN:
        print(f"  - {ironman.owner_code} ({ironman.team_code})")
    print(f"")
    print(f"2025 Teams:")
    for team in get_teams_by_season(2025):
        co = f" + {team.owner_code_2}" if team.owner_code_2 else ""
        print(f"  - {team.team_code}: {team.team_full_name} ({team.owner_code_1}{co})")

