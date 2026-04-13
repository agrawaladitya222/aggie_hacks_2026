"""Tests for data pipeline and peers."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import (
    add_targets,
    clean_base,
    dedupe_ein_tax_year,
    engineer_features,
)
from src.peers import add_peer_benchmarks


def _minimal_df():
    return pd.DataFrame(
        {
            "EIN": ["1", "1", "2"],
            "OrgName": ["A", "A", "B"],
            "State": ["CA", "CA", "NY"],
            "City": ["x", "x", "y"],
            "ZIP": ["1", "1", "2"],
            "TaxYear": [2018, 2018, 2019],
            "TaxPeriodEnd": ["2019-06-30", "2019-05-30", "2020-06-30"],
            "FormType": ["990", "990", "990"],
            "FormationYr": [2000, 2000, 1990],
            "Mission": ["education for youth", "education for youth", "food bank hunger"],
            "Employees": [10.0, 10.0, 5.0],
            "Volunteers": [1.0, 1.0, 0.0],
            "GrossReceipts": [2e6, 2e6, 1e6],
            "TotalRevenueCY": [1e6, 1e6, 500_000],
            "TotalRevenuePY": [900_000, 900_000, 400_000],
            "ContributionsGrantsCY": [500_000, 500_000, 200_000],
            "ContributionsGrantsPY": [400_000, 400_000, 150_000],
            "ProgramServiceRevCY": [400_000, 400_000, 250_000],
            "ProgramServiceRevPY": [400_000, 400_000, 200_000],
            "InvestmentIncomeCY": [100_000, 100_000, 50_000],
            "OtherRevenueCY": [0, 0, 0],
            "GovernmentGrantsAmt": [0, 0, 0],
            "TotalExpensesCY": [900_000, 900_000, 480_000],
            "TotalExpensesPY": [850_000, 850_000, 450_000],
            "SalariesCY": [400_000, 400_000, 200_000],
            "FundraisingExpCY": [50_000, 50_000, 20_000],
            "ProgramSvcExpenses": [400_000, 400_000, 220_000],
            "NetRevenueCY": [100_000, 100_000, 20_000],
            "NetRevenuePY": [50_000, 50_000, -10_000],
            "TotalAssetsEOY": [2e6, 2e6, 1e6],
            "TotalAssetsBOY": [1.9e6, 1.9e6, 0.9e6],
            "TotalLiabilitiesEOY": [200_000, 200_000, 100_000],
            "TotalLiabilitiesBOY": [200_000, 200_000, 100_000],
            "NetAssetsEOY": [1.8e6, 1.8e6, 900_000],
            "NetAssetsBOY": [1.7e6, 1.7e6, 800_000],
            "SourceFile": ["a", "b", "c"],
        }
    )


def test_dedupe_keeps_latest_period():
    raw = _minimal_df()
    d = dedupe_ein_tax_year(raw)
    assert len(d) == 2
    assert d[d["EIN"] == "1"]["TaxPeriodEnd"].iloc[0] == pd.Timestamp("2019-06-30")


def test_engineer_and_targets():
    raw = dedupe_ein_tax_year(_minimal_df())
    raw = clean_base(raw)
    e = engineer_features(raw)
    t = add_targets(e)
    assert "GrantDependencyPct" in t.columns
    assert "AtRisk" in t.columns
    assert "ResilienceScore" in t.columns
    assert t["AtRisk"].isin([0, 1]).all()


def test_peer_benchmarks():
    raw = dedupe_ein_tax_year(_minimal_df())
    raw = clean_base(raw)
    t = add_targets(engineer_features(raw))
    out = add_peer_benchmarks(t)
    assert any(c.endswith("_ZScore") for c in out.columns)
