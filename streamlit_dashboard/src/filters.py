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


def apply_filters(
    df: pd.DataFrame,
    *,
    year: int | None = None,
    state: str | None = None,
    ntee_sector: str | None = None,
    size_bucket: str | None = None,
    resilience_tier: str | None = None,
) -> pd.DataFrame:
    """
    Return a filtered subset of the enriched DataFrame.

    Parameters
    ----------
    df              : Output of feature_engineering.engineer_features()
    year            : TaxYear to keep (None = all years)
    state           : 2-letter state code (None = all states)
    ntee_sector     : Single NTEE major-sector letter (None = all sectors)
    size_bucket     : "Small" | "Mid" | "Large" (None = all sizes)
    resilience_tier : "Stable" | "Watch" | "At Risk" (None = all tiers)
    """
    mask = pd.Series(True, index=df.index)

    if year is not None:
        mask &= pd.to_numeric(df["TaxYear"], errors="coerce") == year

    if state is not None:
        mask &= df["State"].astype(str).str.upper() == state.upper()

    if ntee_sector is not None:
        mask &= df["NTEEMajorSector"].astype(str).str.upper() == ntee_sector.upper()

    if size_bucket is not None:
        mask &= df["SizeBucket"].astype(str) == size_bucket

    if resilience_tier is not None:
        mask &= df["ResilienceTier"] == resilience_tier

    return df[mask].reset_index(drop=True)


def available_years(df: pd.DataFrame) -> list[int]:
    return sorted(pd.to_numeric(df["TaxYear"], errors="coerce").dropna().unique().astype(int).tolist())


def available_states(df: pd.DataFrame) -> list[str]:
    return sorted(df["State"].dropna().astype(str).str.upper().unique().tolist())


def available_ntee_sectors(df: pd.DataFrame) -> list[str]:
    """Returns sorted list of NTEE letters present in the data."""
    return sorted(df["NTEEMajorSector"].dropna().astype(str).unique().tolist())


def ntee_sector_display_options(df: pd.DataFrame) -> dict[str, str]:
    """Returns {display label: letter} for all NTEE sectors present in the data."""
    letters = available_ntee_sectors(df)
    return {
        f"{letter} — {NTEE_SECTOR_LABELS.get(letter, 'Unknown')}": letter
        for letter in letters
    }


def available_size_buckets(df: pd.DataFrame) -> list[str]:
    order = ["Small", "Mid", "Large"]
    present = set(df["SizeBucket"].dropna().astype(str).unique())
    return [b for b in order if b in present]


def available_resilience_tiers(df: pd.DataFrame) -> list[str]:
    order = ["Stable", "Watch", "At Risk"]
    present = set(df["ResilienceTier"].dropna().astype(str).unique())
    return [t for t in order if t in present]
