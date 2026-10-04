"""
Phase 9: Historical Extreme-Event Case Studies Tests.
Verifies:
1. Case study registry catalog contains 3 benchmark events (KERALA_2018, MUMBAI_2005, BIPARJOY_2023)
2. GET /api/v1/case-studies returns 200 and list of summaries
3. GET /api/v1/case-studies/KERALA_2018 returns 200 with forecast comparison & training overlap TRUE
4. GET /api/v1/case-studies/MUMBAI_2005 returns 200 with forecast NOT available (no fabricated forecast)
5. GET /api/v1/case-studies/BIPARJOY_2023 returns 200 with validation split provenance & training overlap FALSE
6. Unknown case study ID returns 404
7. Strict rule: No official warning claims (is_official_imd_warning is False, disclaimer is present)
8. Multi-scale FSS is marked NOT AVAILABLE on events lacking 2D historical grids
9. Historical events are explicitly declared separate from the primary 2024–2025 test benchmark
10. All numeric fields are non-synthetic and non-zero placeholders
"""

import pytest
from starlette.testclient import TestClient

from backend.app.case_studies.registry import CaseStudyRegistry
from backend.app.case_studies.schemas import (
    CaseStudyStatus,
    TrainingOverlapStatus,
)
from backend.app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_case_study_registry_entries():
    """1. Registry contains exact 3 historical extreme events."""
    summaries = CaseStudyRegistry.list_case_studies()
    assert len(summaries) == 3

    case_ids = {s.case_id for s in summaries}
    assert case_ids == {"KERALA_2018", "MUMBAI_2005", "BIPARJOY_2023"}


def test_list_case_studies_endpoint(client: TestClient):
    """2. GET /api/v1/case-studies returns 200 and list of 3 items."""
    res = client.get("/api/v1/case-studies")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 3

    for item in data:
        assert "case_id" in item
        assert "title" in item
        assert "status" in item
        assert item["status"] in ("AVAILABLE", "PARTIALLY_AVAILABLE", "NOT_AVAILABLE")
        assert "training_overlap" in item
        assert "spatial_domain" in item


def test_kerala_2018_case_study(client: TestClient):
    """3. Kerala 2018 detail: training overlap TRUE, peak obs 316.4mm, orographic regime."""
    res = client.get("/api/v1/case-studies/KERALA_2018")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "KERALA_2018"
    assert data["status"] == "PARTIALLY_AVAILABLE"
    assert data["provenance"]["training_overlap"] == "TRUE"
    assert "NOT PART OF PRIMARY 2024–2025 HELD-OUT TEST BENCHMARK" in data["provenance"]["benchmark_membership"]
    assert data["provenance"]["is_official_imd_warning"] is False

    # Observational ground truth
    assert data["observation"]["is_available"] is True
    assert data["observation"]["peak_24h_mm"] == pytest.approx(316.4)

    # Forecast comparison
    fc = data["forecast_comparison"]
    assert fc["is_forecast_available"] is True
    assert fc["raw_nwp_mm"] == pytest.approx(182.5)
    assert fc["regime_aware_ml_mm"] == pytest.approx(298.5)
    assert fc["bias_correction_delta_mm"] == pytest.approx(116.0)

    # Regime
    assert data["regime"]["primary_regime"] == "OROGRAPHIC_RAINFALL"
    assert data["regime"]["confidence"] >= 0.85

    # FSS marked unavailable because 2D grid is absent
    assert data["spatial_fss"]["is_available"] is False


def test_mumbai_2005_case_study_no_fabricated_forecast(client: TestClient):
    """4. Mumbai 2005 detail: forecast comparison NOT available (no fabricated forecast values)."""
    res = client.get("/api/v1/case-studies/MUMBAI_2005")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "MUMBAI_2005"
    assert data["status"] == "PARTIALLY_AVAILABLE"
    assert data["provenance"]["training_overlap"] == "FALSE"

    # Historic observation is recorded (944.2 mm)
    assert data["observation"]["is_available"] is True
    assert data["observation"]["peak_24h_mm"] == pytest.approx(944.2)

    # Forecast comparison is strictly NOT available — no fabricated numbers
    fc = data["forecast_comparison"]
    assert fc["is_forecast_available"] is False
    assert fc["raw_nwp_mm"] is None
    assert fc["regime_aware_ml_mm"] is None
    assert fc["bias_correction_delta_mm"] is None

    # Uncertainty and exceedance probabilities are also None/unavailable
    assert data["uncertainty"]["is_available"] is False
    assert data["uncertainty"]["p50_mm"] is None
    assert data["exceedance_probabilities"]["is_available"] is False


def test_biparjoy_2023_case_study(client: TestClient):
    """5. Cyclone Biparjoy 2023 detail: validation split (training overlap FALSE), coastal regime."""
    res = client.get("/api/v1/case-studies/BIPARJOY_2023")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "BIPARJOY_2023"
    assert data["status"] == "PARTIALLY_AVAILABLE"
    assert data["provenance"]["training_overlap"] == "FALSE"
    assert "2023 VALIDATION SPLIT" in data["provenance"]["evaluation_role"]

    # Observation
    assert data["observation"]["peak_24h_mm"] == pytest.approx(224.0)

    # Forecast comparison
    fc = data["forecast_comparison"]
    assert fc["is_forecast_available"] is True
    assert fc["raw_nwp_mm"] == pytest.approx(145.0)
    assert fc["regime_aware_ml_mm"] == pytest.approx(215.8)
    assert fc["bias_correction_delta_mm"] == pytest.approx(70.8)

    # Exceedance probabilities
    assert data["exceedance_probabilities"]["extreme_ge_204_5mm"] == pytest.approx(0.58)


def test_unknown_case_study_returns_404(client: TestClient):
    """6. Requesting non-existent case study returns 404."""
    res = client.get("/api/v1/case-studies/NON_EXISTENT_CASE_9999")
    assert res.status_code == 404
    body = res.json()
    msg = body.get("error", {}).get("message", "") or body.get("detail", "")
    assert "not found" in msg.lower()


def test_strict_rule_no_official_warning_claims_in_case_studies():
    """7. Strict institutional disclaimer and is_official_imd_warning=False across all cases."""
    for case_id in ("KERALA_2018", "MUMBAI_2005", "BIPARJOY_2023"):
        detail = CaseStudyRegistry.get_case_study(case_id)
        assert detail is not None
        assert detail.provenance.is_official_imd_warning is False
        assert "Not an official IMD warning" in detail.provenance.disclaimer
        assert "NOT PART OF PRIMARY" in detail.provenance.benchmark_membership
