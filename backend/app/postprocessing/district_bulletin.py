"""
Deterministic District Bulletin Generation Engine (Phase 14).
Synthesizes structured machine-generated meteorological bulletins without LLM hallucination.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.schemas.district_decision import (
    DistrictBulletin,
    DistrictForecastProduct,
)


class DistrictBulletinEngine:
    """
    Deterministic bulletin builder for administrative district rainfall outlooks.
    Generates structured plain-text bulletins conforming to Section 20 & 21 specifications.
    """

    @classmethod
    def generate_bulletin(
        cls,
        product: DistrictForecastProduct,
        forecast_period: str = "24-Hour Accumulation (08:30 IST to 08:30 IST)",
    ) -> DistrictBulletin:
        """Construct structured DistrictBulletin from a completed forecast product."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        stats = product.spatial_stats
        probs = product.probabilities
        unc = product.uncertainty
        drivers = product.atmospheric_drivers

        # Deterministic text formatting
        driver_bullets = "\n".join([f"    * {d}" for d in drivers.major_drivers]) or "    * Standard regional synoptic background"

        text_lines = [
            "================================================================================",
            "        DISTRICT METEOROLOGICAL & DECISION-SUPPORT OUTLOOK BULLETIN             ",
            "  Regime-Aware AI Post-Processing System (PS26080 — MoES / NCMRWF Research)    ",
            "================================================================================",
            f"DISTRICT:             {product.district_name.upper()} ({product.district_id})",
            f"STATE / UT:           {product.state_name}",
            f"FORECAST PERIOD:      {forecast_period}",
            f"VALID TIMESTAMP:      {product.forecast_valid_time}",
            f"BULLETIN GENERATED:   {now_utc}",
            "--------------------------------------------------------------------------------",
            "1. EXPECTED PRECIPITATION (SPATIAL DISTRIBUTION):",
            f"   - Area-Weighted Mean:         {stats.mean_24h_mm:.1f} mm/24h",
            f"   - Median Forecast (P50):      {stats.median_24h_mm:.1f} mm/24h",
            f"   - Lower Bound (P10):          {unc.p10_mm:.1f} mm/24h",
            f"   - Upper Bound (P90):          {unc.p90_mm:.1f} mm/24h",
            f"   - Peak Localized Maximum:     {stats.max_24h_mm:.1f} mm/24h",
            f"   - Minimum District Cell:      {stats.min_24h_mm:.1f} mm/24h",
            "",
            "2. CALIBRATED HEAVY RAINFALL PROBABILITIES:",
            f"   - P(Rainfall >= 64.5 mm):     {probs.heavy_probability * 100:.1f}%",
            f"   - P(Rainfall >= 115.6 mm):    {probs.very_heavy_probability * 100:.1f}%",
            f"   - P(Rainfall >= 204.5 mm):    {probs.extreme_probability * 100:.1f}%",
            "",
            "3. DISTRICT SPATIAL AREA EXPOSURE FRACTIONS:",
            f"   - Area >= 64.5 mm:            {stats.heavy_area_fraction * 100:.1f}% of district area",
            f"   - Area >= 115.6 mm:           {stats.very_heavy_area_fraction * 100:.1f}% of district area",
            f"   - Area >= 204.5 mm:           {stats.extreme_area_fraction * 100:.1f}% of district area",
            f"   - Valid Spatial Coverage:     {stats.valid_area_fraction * 100:.1f}% ({stats.intersected_cell_count} cells)",
            "",
            "4. SYNOPTIC REGIME & MESOSCALE DRIVERS:",
            f"   - Dominant Weather Regime:    {product.primary_regime.value} (Confidence: {product.regime_confidence * 100:.1f}%)",
            "   - Key Physical Drivers:",
            f"{driver_bullets}",
            "",
            "5. FORECAST UNCERTAINTY & ENSEMBLE SPREAD:",
            f"   - Spread Category:            {unc.uncertainty_category}",
            f"   - Inter-Quantile Width:       {unc.ensemble_spread_mm:.1f} mm (Agg: {unc.method})",
            "",
            "6. MODEL-DERIVED DECISION SUPPORT:",
            f"   - Decision Category:          {product.decision_category.value}",
            f"   - Decision Basis:             {product.decision_reason}",
            f"   - Evaluation Confidence:      {product.confidence * 100:.1f}%",
            "",
            "7. PROVENANCE & LINEAGE:",
            f"   - Meteorological Data:        {product.data_provenance}",
            f"   - Post-Processing Model:      {product.model_provenance}",
            f"   - Boundary Dataset:           {product.boundary_version} ({product.area_km2:.1f} km²)",
            f"   - Population Weighting:       {product.population_weighting_status}",
            "--------------------------------------------------------------------------------",
            "DISCLAIMER:",
            "  Prototype model-derived decision support for meteorological & disaster",
            "  management research. NOT an official IMD warning. Statutory forecasts",
            "  and warnings are issued solely by the India Meteorological Department (IMD).",
            "================================================================================",
        ]

        formatted_text = "\n".join(text_lines)

        return DistrictBulletin(
            district_id=product.district_id,
            district_name=product.district_name,
            state_name=product.state_name,
            forecast_period=forecast_period,
            generated_at=now_utc,
            rainfall_mean_mm=stats.mean_24h_mm,
            rainfall_p50_mm=stats.median_24h_mm,
            rainfall_p90_mm=unc.p90_mm,
            rainfall_max_mm=stats.max_24h_mm,
            heavy_probability_pct=round(probs.heavy_probability * 100, 1),
            very_heavy_probability_pct=round(probs.very_heavy_probability * 100, 1),
            extreme_probability_pct=round(probs.extreme_probability * 100, 1),
            heavy_area_fraction_pct=round(stats.heavy_area_fraction * 100, 1),
            very_heavy_area_fraction_pct=round(stats.very_heavy_area_fraction * 100, 1),
            extreme_area_fraction_pct=round(stats.extreme_area_fraction * 100, 1),
            dominant_regime=product.primary_regime.value,
            regime_confidence_pct=round(product.regime_confidence * 100, 1),
            major_drivers=drivers.major_drivers,
            uncertainty_level=unc.uncertainty_category,
            category=product.decision_category.value,
            decision_reason=product.decision_reason,
            data_provenance=product.data_provenance,
            boundary_version=product.boundary_version,
            model_version=product.model_provenance,
            decision_threshold_version="PS26080_PROTO_v14.0",
            formatted_bulletin_text=formatted_text,
            disclaimer="Prototype model-derived decision support. Not an official IMD warning.",
        )
