"""
Multi-Format District Product Export Engine (Phase 14).
Supports standardized exports to JSON, CSV, GeoJSON FeatureCollections,
and GeoPackage / SQLite table exports with full provenance and disclaimers.
"""

import csv
import io
import json
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional
from backend.app.data.sources.district_boundaries import DistrictBoundaryProvider
from backend.app.schemas.district_decision import DistrictForecastProduct


class DistrictExportEngine:
    """
    Serializes district forecast and decision-support intelligence products
    into standard geospatial and tabular formats.
    """

    @classmethod
    def export_to_json(cls, products: List[DistrictForecastProduct]) -> str:
        """Export products as formatted JSON string."""
        data = [p.model_dump() for p in products]
        return json.dumps(
            {
                "format": "PS26080_DISTRICT_DECISION_JSON",
                "version": "1.0",
                "count": len(products),
                "products": data,
            },
            indent=2,
            default=str,
        )

    @classmethod
    def export_to_csv(cls, products: List[DistrictForecastProduct]) -> str:
        """Export products as CSV string."""
        output = io.StringIO()
        fieldnames = [
            "district_id",
            "district_name",
            "state_id",
            "state_name",
            "lat",
            "lon",
            "area_km2",
            "aggregation_method",
            "raw_nwp_mean_mm",
            "mean_rainfall_mm",
            "median_p50_mm",
            "p90_rainfall_mm",
            "max_rainfall_mm",
            "heavy_probability",
            "very_heavy_probability",
            "extreme_probability",
            "heavy_area_fraction",
            "very_heavy_area_fraction",
            "extreme_area_fraction",
            "primary_regime",
            "regime_confidence",
            "decision_category",
            "decision_reason",
            "uncertainty_category",
            "ensemble_spread_mm",
            "population_weighting_status",
            "quality_status",
            "data_provenance",
            "model_provenance",
            "boundary_version",
            "forecast_valid_time",
            "is_official_imd_warning",
            "disclaimer",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for p in products:
            stats = p.spatial_stats
            probs = p.probabilities
            unc = p.uncertainty

            writer.writerow({
                "district_id": p.district_id,
                "district_name": p.district_name,
                "state_id": p.state_id,
                "state_name": p.state_name,
                "lat": p.lat,
                "lon": p.lon,
                "area_km2": p.area_km2,
                "aggregation_method": p.aggregation_method.value,
                "raw_nwp_mean_mm": p.raw_nwp_mean_mm,
                "mean_rainfall_mm": stats.mean_24h_mm,
                "median_p50_mm": stats.median_24h_mm,
                "p90_rainfall_mm": unc.p90_mm,
                "max_rainfall_mm": stats.max_24h_mm,
                "heavy_probability": probs.heavy_probability,
                "very_heavy_probability": probs.very_heavy_probability,
                "extreme_probability": probs.extreme_probability,
                "heavy_area_fraction": stats.heavy_area_fraction,
                "very_heavy_area_fraction": stats.very_heavy_area_fraction,
                "extreme_area_fraction": stats.extreme_area_fraction,
                "primary_regime": p.primary_regime.value,
                "regime_confidence": p.regime_confidence,
                "decision_category": p.decision_category.value,
                "decision_reason": p.decision_reason,
                "uncertainty_category": unc.uncertainty_category,
                "ensemble_spread_mm": unc.ensemble_spread_mm,
                "population_weighting_status": p.population_weighting_status,
                "quality_status": p.quality_status.value,
                "data_provenance": p.data_provenance,
                "model_provenance": p.model_provenance,
                "boundary_version": p.boundary_version,
                "forecast_valid_time": p.forecast_valid_time,
                "is_official_imd_warning": p.is_official_imd_warning,
                "disclaimer": p.disclaimer,
            })

        return output.getvalue()

    @classmethod
    def export_to_geojson(cls, products: List[DistrictForecastProduct]) -> Dict[str, Any]:
        """Export products as GeoJSON FeatureCollection with polygon boundaries."""
        features = []

        for p in products:
            boundary = DistrictBoundaryProvider.get_district_by_id(p.district_id)
            if boundary is None:
                continue

            stats = p.spatial_stats
            probs = p.probabilities
            unc = p.uncertainty

            properties = {
                "district_id": p.district_id,
                "district_name": p.district_name,
                "state_id": p.state_id,
                "state_name": p.state_name,
                "centroid_lat": p.lat,
                "centroid_lon": p.lon,
                "area_km2": p.area_km2,
                "raw_nwp_mean_mm": p.raw_nwp_mean_mm,
                "mean_rainfall_mm": stats.mean_24h_mm,
                "median_p50_mm": stats.median_24h_mm,
                "p90_rainfall_mm": unc.p90_mm,
                "max_rainfall_mm": stats.max_24h_mm,
                "heavy_probability": probs.heavy_probability,
                "very_heavy_probability": probs.very_heavy_probability,
                "extreme_probability": probs.extreme_probability,
                "heavy_area_fraction": stats.heavy_area_fraction,
                "very_heavy_area_fraction": stats.very_heavy_area_fraction,
                "extreme_area_fraction": stats.extreme_area_fraction,
                "primary_regime": p.primary_regime.value,
                "regime_confidence": p.regime_confidence,
                "decision_category": p.decision_category.value,
                "decision_reason": p.decision_reason,
                "uncertainty_category": unc.uncertainty_category,
                "population_weighting_status": p.population_weighting_status,
                "quality_status": p.quality_status.value,
                "data_provenance": p.data_provenance,
                "model_provenance": p.model_provenance,
                "boundary_version": p.boundary_version,
                "forecast_valid_time": p.forecast_valid_time,
                "is_official_imd_warning": p.is_official_imd_warning,
                "disclaimer": p.disclaimer,
            }

            feature = {
                "type": "Feature",
                "id": p.district_id,
                "geometry": {
                    "type": boundary.geometry.type,
                    "coordinates": boundary.geometry.coordinates,
                },
                "properties": properties,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "name": "PS26080_India_District_Forecasts",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
            "features": features,
        }

    @classmethod
    def export_to_sqlite_geopackage_buffer(cls, products: List[DistrictForecastProduct]) -> bytes:
        """Export products to SQLite-backed geospatial table buffer."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE district_forecasts (
                district_id TEXT PRIMARY KEY,
                district_name TEXT,
                state_name TEXT,
                mean_rainfall_mm REAL,
                median_p50_mm REAL,
                p90_rainfall_mm REAL,
                heavy_probability REAL,
                very_heavy_probability REAL,
                extreme_probability REAL,
                heavy_area_fraction REAL,
                decision_category TEXT,
                primary_regime TEXT,
                geojson_geometry TEXT,
                provenance TEXT
            )
        """)

        for p in products:
            boundary = DistrictBoundaryProvider.get_district_by_id(p.district_id)
            geom_json = json.dumps(boundary.geometry.coordinates) if boundary else "[]"
            cursor.execute("""
                INSERT INTO district_forecasts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.district_id,
                p.district_name,
                p.state_name,
                p.spatial_stats.mean_24h_mm,
                p.spatial_stats.median_24h_mm,
                p.uncertainty.p90_mm,
                p.probabilities.heavy_probability,
                p.probabilities.very_heavy_probability,
                p.probabilities.extreme_probability,
                p.spatial_stats.heavy_area_fraction,
                p.decision_category.value,
                p.primary_regime.value,
                geom_json,
                p.data_provenance,
            ))

        conn.commit()

        # Dump to bytes
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        dest = sqlite3.connect(temp_db.name)
        conn.backup(dest)
        dest.close()
        conn.close()

        with open(temp_db.name, "rb") as f:
            data = f.read()

        import os
        try:
            os.remove(temp_db.name)
        except Exception:
            pass

        return data
