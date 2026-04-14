"""Apply user sidebar selections to the enriched DataFrame."""

from __future__ import annotations

import pandas as pd

NTEE_SECTOR_LABELS: dict[str, str] = {
    "A": "Arts, Culture & Humanities",
    "B": "Education",
    "C": "Environment",
    "D": "Animal-Related",
    "E": "Health Care",
    "F": "Mental Health & Crisis Intervention",
    "G": "Diseases, Disorders & Medical Disciplines",
    "H": "Medical Research",
    "I": "Crime & Legal-Related",
    "J": "Employment",
    "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter",
    "M": "Public Safety & Disaster Relief",
    "N": "Recreation & Sports",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International & Foreign Affairs",
    "R": "Civil Rights & Advocacy",
    "S": "Community Improvement & Capacity Building",
    "T": "Philanthropy & Grantmaking",
    "U": "Science & Technology",
    "V": "Social Science",
    "W": "Public & Societal Benefit",
    "X": "Religion-Related",
    "Y": "Mutual & Membership Benefit",
    "Z": "Unknown",
}

# Mission-based sector labels (from data_pipeline.classify_sector)
MISSION_SECTOR_ORDER = [
    "Education",
    "Healthcare",
    "Housing & Shelter",
    "Food & Nutrition",
    "Arts & Culture",
    "Environment",
    "Youth Services",
    "Religious",
    "Community Development",
    "Research & Science",
    "Other/General",
]

SIZE_CATEGORY_ORDER = ["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"]


def apply_filters(
    df: pd.DataFrame,
    *,
    year: int | None = None,
    state: str | None = None,
    sector: str | None = None,
    size_category: str | None = None,
    resilience_tier: str | None = None,
    at_risk_predicted: int | None = None,
) -> pd.DataFrame:
    """
    Return a filtered subset of the enriched DataFrame.

    Parameters
    ----------
    df                : Output of feature_engineering.engineer_features()
    year              : TaxYear to keep (None = all years)
    state             : 2-letter state code (None = all states)
    sector            : Mission-based sector string (None = all sectors)
    size_category     : One of SIZE_CATEGORY_ORDER values (None = all sizes)
    resilience_tier   : "Stable" | "Watch" | "At Risk" (None = all tiers)
    at_risk_predicted : 1 or 0 to filter by model prediction (None = all)
    """
    mask = pd.Series(True, index=df.index)

    if year is not None:
        mask &= pd.to_numeric(df["TaxYear"], errors="coerce") == year

    if state is not None:
        mask &= df["State"].astype(str).str.upper() == state.upper()

    if sector is not None:
        mask &= df["Sector"].astype(str) == sector

    if size_category is not None:
        mask &= df["SizeCategory"].astype(str) == size_category

    if resilience_tier is not None:
        mask &= df["ResilienceTier"] == resilience_tier

    if at_risk_predicted is not None:
        mask &= pd.to_numeric(df["AtRiskPredicted"], errors="coerce") == at_risk_predicted

    return df[mask].reset_index(drop=True)


def available_years(df: pd.DataFrame) -> list[int]:
    return sorted(pd.to_numeric(df["TaxYear"], errors="coerce").dropna().unique().astype(int).tolist())


def available_states(df: pd.DataFrame) -> list[str]:
    return sorted(df["State"].dropna().astype(str).str.upper().unique().tolist())


def available_sectors(df: pd.DataFrame) -> list[str]:
    present = set(df["Sector"].dropna().astype(str).unique())
    ordered = [s for s in MISSION_SECTOR_ORDER if s in present]
    extra = sorted(present - set(MISSION_SECTOR_ORDER))
    return ordered + extra


def available_size_categories(df: pd.DataFrame) -> list[str]:
    present = set(df["SizeCategory"].dropna().astype(str).unique())
    return [s for s in SIZE_CATEGORY_ORDER if s in present]


def available_resilience_tiers(df: pd.DataFrame) -> list[str]:
    order = ["Stable", "Watch", "At Risk"]
    present = set(df["ResilienceTier"].dropna().astype(str).unique())
    return [t for t in order if t in present]


# Legacy helpers kept for brand_map compatibility
def available_size_buckets(df: pd.DataFrame) -> list[str]:
    return available_size_categories(df)


def ntee_sector_display_options(df: pd.DataFrame) -> dict[str, str]:
    """Returns {display label: letter} for NTEE sectors — kept for compatibility."""
    if "NTEEMajorSector" not in df.columns:
        return {}
    letters = sorted(df["NTEEMajorSector"].dropna().astype(str).unique().tolist())
    return {
        f"{letter} — {NTEE_SECTOR_LABELS.get(letter, 'Unknown')}": letter
        for letter in letters
    }
