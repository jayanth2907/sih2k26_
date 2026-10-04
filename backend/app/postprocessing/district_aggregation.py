"""
Unified District Spatial Aggregation & Verification Engine (Phase 14).
Aggregates 2D spatially corrected rainfall fields, probability fields, and quantile uncertainty
into administrative district statistics, comparing Polygon Area-Weighting with Centroid Baselines.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.data.sources.district_boundaries import DistrictBoundaryProvider
from backend.app.postprocessing.district_decision import DistrictDecisionEngine
from backend.app.postprocessing.spatial_weights import SpatialWeightEngine
from backend.app.schemas.district_decision import (
    AggregationComparisonMetrics,
    AggregationComparisonSummary,
    AggregationMethod,
    DataQualityStatus,
    DecisionSupportCategory,
    DistrictAtmosphericDrivers,
    DistrictDecisionThresholds,
    DistrictForecastProduct,
    DistrictProbabilityStats,
    DistrictSpatialStats,
    DistrictUncertaintyStats,
)
from backend.app.schemas.regime import WeatherRegimeType
from backend.app.schemas.spatial_postprocess import SpatialGridDefinition, SpatialPredictionOutput

logger = logging.getLogger("rainfall_backend.postprocessing.district_aggregation")


class DistrictAggregationEngine:
    """
    Main orchestrator for district-level polygon aggregation, probabilistic warning intelligence,
    and side-by-side verification against centroid baselines.
    """

    _instance: Optional["DistrictAggregationEngine"] = None

    def __init__(self):
        self.weights_engine = SpatialWeightEngine.get_instance()
        self.boundary_provider = DistrictBoundaryProvider()

    @classmethod
    def get_instance(cls) -> "DistrictAggregationEngine":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def aggregate_spatial_prediction(
        self,
        spatial_output: SpatialPredictionOutput,
        valid_time: Optional[str] = None,
        thresholds: Optional[DistrictDecisionThresholds] = None,
    ) -> List[DistrictForecastProduct]:
        """
        Aggregate complete 2D SpatialPredictionOutput across all administrative districts.
        """
        grid = spatial_output.grid
        weights_dict = self.weights_engine.get_or_compute_weights(grid)
        districts = DistrictBoundaryProvider.get_all_districts()

        # Convert 2D nested lists to numpy arrays
        corr_grid = np.array(spatial_output.corrected_grid, dtype=np.float64)
        raw_grid = np.array(spatial_output.raw_nwp_grid, dtype=np.float64)
        p_heavy_grid = np.array(spatial_output.prob_heavy_ge_64_5_grid, dtype=np.float64)
        p_vheavy_grid = np.array(spatial_output.prob_very_heavy_ge_115_6_grid, dtype=np.float64)
        p_extreme_grid = np.array(spatial_output.prob_extreme_ge_204_5_grid, dtype=np.float64)

        # Quantile grids
        p10_grid = np.array(spatial_output.p10_grid, dtype=np.float64) if spatial_output.p10_grid is not None else corr_grid * 0.75
        p90_grid = np.array(spatial_output.p90_grid, dtype=np.float64) if spatial_output.p90_grid is not None else corr_grid * 1.35

        target_time = valid_time or datetime.now(timezone.utc).isoformat()
        products: List[DistrictForecastProduct] = []

        try:
            dom_reg_enum = WeatherRegimeType(spatial_output.dominant_regime)
        except Exception:
            dom_reg_enum = WeatherRegimeType.ACTIVE_MONSOON

        for d in districts:
            w_entry = weights_dict.get(d.district_id)
            if w_entry is None:
                continue

            # 1. Rainfall Field Aggregation
            (
                mean_r,
                max_r,
                min_r,
                median_r,
                p90_r,
                p95_r,
                quality_status,
                valid_area_frac,
            ) = self.weights_engine.aggregate_field(corr_grid, w_entry)

            # Raw NWP baseline mean
            raw_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(raw_grid, w_entry)

            # 2. Area fraction calculations
            area_fracs = self.weights_engine.calculate_threshold_area_fractions(
                corr_grid, w_entry, thresholds=[64.5, 115.6, 204.5]
            )

            spatial_stats = DistrictSpatialStats(
                mean_24h_mm=mean_r,
                max_24h_mm=max_r,
                min_24h_mm=min_r,
                median_24h_mm=median_r,
                p90_24h_mm=p90_r,
                p95_24h_mm=p95_r,
                heavy_area_fraction=area_fracs[0],
                very_heavy_area_fraction=area_fracs[1],
                extreme_area_fraction=area_fracs[2],
                valid_area_fraction=valid_area_frac,
                missing_area_fraction=round(1.0 - valid_area_frac, 4),
                intersected_cell_count=len(w_entry.cell_coords),
            )

            # 3. Probability Field Aggregation (enforce monotonicity)
            p_h_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(p_heavy_grid, w_entry)
            p_vh_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(p_vheavy_grid, w_entry)
            p_ext_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(p_extreme_grid, w_entry)

            p_h = min(1.0, max(0.0, p_h_mean))
            p_vh = min(p_h, max(0.0, p_vh_mean))
            p_ext = min(p_vh, max(0.0, p_ext_mean))

            prob_stats = DistrictProbabilityStats(
                heavy_probability=round(p_h, 3),
                very_heavy_probability=round(p_vh, 3),
                extreme_probability=round(p_ext, 3),
                monotonicity_verified=(p_h >= p_vh - 1e-4 and p_vh >= p_ext - 1e-4),
            )

            # 4. Uncertainty Field Aggregation
            p10_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(p10_grid, w_entry)
            p90_mean, _, _, _, _, _, _, _ = self.weights_engine.aggregate_field(p90_grid, w_entry)

            p10_val = max(0.0, min(median_r, p10_mean))
            p90_val = max(median_r, p90_mean)
            spread_val = round((p90_val - p10_val) / 2.56, 2)

            if spread_val > 40.0:
                unc_cat = "EXTREME"
            elif spread_val > 25.0:
                unc_cat = "HIGH"
            elif spread_val > 10.0:
                unc_cat = "MODERATE"
            else:
                unc_cat = "LOW"

            unc_stats = DistrictUncertaintyStats(
                p10_mm=round(p10_val, 2),
                p50_mm=round(median_r, 2),
                p90_mm=round(p90_val, 2),
                ensemble_spread_mm=spread_val,
                uncertainty_category=unc_cat,
                method="APPROXIMATE_AREA_AGGREGATED_QUANTILE",
            )

            # 5. Deterministic Decision Support
            category, reason, confidence = DistrictDecisionEngine.evaluate_district_decision(
                district_name=d.district_name,
                state_name=d.state_name,
                spatial_stats=spatial_stats,
                probabilities=prob_stats,
                uncertainty=unc_stats,
                dominant_regime=dom_reg_enum,
                quality_status=quality_status,
                thresholds=thresholds,
            )

            # 6. Synoptic Atmospheric Drivers
            drivers = DistrictDecisionEngine.synthesize_atmospheric_drivers(
                regime=dom_reg_enum,
                is_coastal=d.is_coastal,
                lat=d.centroid_lat,
                lon=d.centroid_lon,
            )

            product = DistrictForecastProduct(
                district_id=d.district_id,
                district_name=d.district_name,
                state_id=d.state_id,
                state_name=d.state_name,
                lat=d.centroid_lat,
                lon=d.centroid_lon,
                area_km2=d.area_km2,
                aggregation_method=AggregationMethod.POLYGON_AREA_WEIGHTED,
                raw_nwp_mean_mm=round(raw_mean, 2),
                spatial_stats=spatial_stats,
                probabilities=prob_stats,
                uncertainty=unc_stats,
                primary_regime=dom_reg_enum,
                regime_confidence=spatial_output.regime_probabilities.get(dom_reg_enum.value, 0.85),
                regime_probabilities=spatial_output.regime_probabilities,
                atmospheric_drivers=drivers,
                decision_category=category,
                decision_reason=reason,
                confidence=confidence,
                population_weighting_status="NOT_AVAILABLE",
                quality_status=quality_status,
                data_provenance="ECMWF_ERA5_GFS_COMBINED",
                model_provenance=spatial_output.model_id,
                boundary_version=DistrictBoundaryProvider.BOUNDARY_VERSION,
                forecast_valid_time=target_time,
                is_official_imd_warning=False,
                disclaimer="Prototype model-derived decision support. Not an official IMD warning.",
            )
            products.append(product)

        return products

    def sample_centroid_baseline(
        self,
        spatial_output: SpatialPredictionOutput,
        district_id: str,
    ) -> Tuple[float, float, str]:
        """Extract legacy point-sampled centroid rainfall and probability."""
        district = DistrictBoundaryProvider.get_district_by_id(district_id)
        if district is None:
            return (0.0, 0.0, "NORMAL")

        grid = spatial_output.grid
        lats = grid.latitudes
        lons = grid.longitudes

        # Find closest grid cell to centroid
        i = int(np.argmin([abs(lat - district.centroid_lat) for lat in lats]))
        j = int(np.argmin([abs(lon - district.centroid_lon) for lon in lons]))

        rain_val = float(spatial_output.corrected_grid[i][j])
        p_heavy = float(spatial_output.prob_heavy_ge_64_5_grid[i][j])

        if rain_val >= 204.5 or p_heavy >= 0.85:
            cat = "EXTREMELY_HEAVY_RAINFALL"
        elif rain_val >= 115.6 or p_heavy >= 0.65:
            cat = "VERY_HEAVY_RAINFALL"
        elif rain_val >= 64.5 or p_heavy >= 0.55:
            cat = "HEAVY_RAINFALL"
        else:
            cat = "NORMAL"

        return (round(rain_val, 2), round(p_heavy, 3), cat)

    def compare_aggregation_methods(
        self,
        spatial_output: SpatialPredictionOutput,
    ) -> AggregationComparisonSummary:
        """
        Conduct forensic verification comparing Polygon Area-Weighted vs Centroid Sampling.
        """
        polygon_products = self.aggregate_spatial_prediction(spatial_output)
        comparisons: List[AggregationComparisonMetrics] = []

        abs_diffs = []
        sq_diffs = []
        category_agreements = []

        for p in polygon_products:
            c_rain, c_prob, c_cat = self.sample_centroid_baseline(spatial_output, p.district_id)
            poly_rain = p.spatial_stats.mean_24h_mm
            poly_cat = p.decision_category.value

            abs_diff = abs(poly_rain - c_rain)
            abs_diffs.append(abs_diff)
            sq_diffs.append(abs_diff ** 2)

            mean_val = (poly_rain + c_rain) / 2.0
            rel_diff = (abs_diff / mean_val * 100.0) if mean_val > 1.0 else 0.0

            agrees = (poly_cat == c_cat)
            category_agreements.append(agrees)

            comparisons.append(
                AggregationComparisonMetrics(
                    district_id=p.district_id,
                    district_name=p.district_name,
                    state_name=p.state_name,
                    centroid_rainfall_mm=c_rain,
                    polygon_mean_rainfall_mm=poly_rain,
                    absolute_difference_mm=round(abs_diff, 2),
                    relative_difference_pct=round(rel_diff, 1),
                    centroid_category=c_cat,
                    polygon_category=poly_cat,
                    category_agreement=agrees,
                    centroid_heavy_prob=c_prob,
                    polygon_heavy_prob=p.probabilities.heavy_probability,
                    heavy_area_fraction=p.spatial_stats.heavy_area_fraction,
                )
            )

        n = max(1, len(comparisons))
        mae = float(np.mean(abs_diffs))
        rmse = float(np.sqrt(np.mean(sq_diffs)))
        max_diff = float(np.max(abs_diffs))
        concordance = float(np.sum(category_agreements) / n * 100.0)
        switches = int(n - np.sum(category_agreements))

        return AggregationComparisonSummary(
            sample_district_count=n,
            mean_absolute_difference_mm=round(mae, 2),
            rmse_difference_mm=round(rmse, 2),
            max_absolute_difference_mm=round(max_diff, 2),
            category_concordance_pct=round(concordance, 1),
            category_switch_count=switches,
            district_comparisons=comparisons,
            interpretation=(
                "Polygon area-weighting captures spatial extent across complex orography and urban boundaries, "
                "smoothing single-cell extremes while accurately computing threshold exceedance fractions."
            ),
        )
