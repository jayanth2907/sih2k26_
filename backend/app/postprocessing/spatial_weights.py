"""
Precomputed Spatial Weights & Grid-Cell Intersection Cache Engine (Phase 14).
Determines fractional area intersections between meteorological 2D rainfall grid cells
and administrative district polygons, with checksum invalidation and fast vectorized caching.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from shapely.geometry import Polygon, box

from backend.app.data.sources.district_boundaries import DistrictBoundaryProvider
from backend.app.schemas.district_decision import DataQualityStatus
from backend.app.schemas.spatial_postprocess import SpatialGridDefinition

logger = logging.getLogger("rainfall_backend.postprocessing.spatial_weights")


class DistrictWeightEntry:
    """Precomputed weights for a single district polygon."""

    def __init__(
        self,
        district_id: str,
        cell_coords: List[Tuple[int, int]],  # (row_i, col_j) in grid
        cell_weights: List[float],           # Normalized weights summing to 1.0
        cell_intersection_areas_km2: List[float],
        district_area_km2: float,
        valid_area_fraction: float,
    ):
        self.district_id = district_id
        self.cell_coords = cell_coords
        self.cell_weights = np.array(cell_weights, dtype=np.float64)
        self.cell_intersection_areas_km2 = np.array(cell_intersection_areas_km2, dtype=np.float64)
        self.district_area_km2 = district_area_km2
        self.valid_area_fraction = valid_area_fraction


class SpatialWeightEngine:
    """
    Computes, caches, and applies fractional polygon-grid cell spatial weights.
    Guarantees O(K * N_cells) fast vectorized aggregation without repeated GIS clipping.
    """

    MIN_VALID_AREA_FRACTION = 0.60

    _instance: Optional["SpatialWeightEngine"] = None

    def __init__(self):
        self._cache: Dict[str, Dict[str, DistrictWeightEntry]] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> "SpatialWeightEngine":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def compute_grid_hash(grid: SpatialGridDefinition) -> str:
        """Create deterministic checksum for a grid definition."""
        grid_key = f"{grid.grid_name}_{grid.grid_shape}_{grid.resolution_deg}_{grid.extent_bbox}_{grid.orientation}"
        return hashlib.sha256(grid_key.encode("utf-8")).hexdigest()[:16]

    def get_or_compute_weights(
        self,
        grid: SpatialGridDefinition,
        boundary_version: str = DistrictBoundaryProvider.BOUNDARY_VERSION,
    ) -> Dict[str, DistrictWeightEntry]:
        """
        Retrieve precomputed weights from cache or compute them once.
        Invalidates cache if grid definition or boundary version changes.
        """
        grid_hash = self.compute_grid_hash(grid)
        cache_key = f"{boundary_version}_{grid_hash}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        logger.info(
            "Computing spatial intersection weights for Grid '%s' (%dx%d) and Boundary '%s'...",
            grid.grid_name,
            grid.grid_shape[0],
            grid.grid_shape[1],
            boundary_version,
        )

        entries = self._precompute_weights(grid)
        self._cache[cache_key] = entries
        self._cache_metadata[cache_key] = {
            "grid_name": grid.grid_name,
            "grid_shape": list(grid.grid_shape),
            "resolution_deg": grid.resolution_deg,
            "boundary_version": boundary_version,
            "grid_hash": grid_hash,
            "total_districts": len(entries),
            "total_intersected_pairs": sum(len(e.cell_coords) for e in entries.values()),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return entries

    def _precompute_weights(self, grid: SpatialGridDefinition) -> Dict[str, DistrictWeightEntry]:
        """Compute intersection weights for all registered districts."""
        districts = DistrictBoundaryProvider.get_all_districts()
        lats = grid.latitudes
        lons = grid.longitudes
        res = grid.resolution_deg
        half_res = res / 2.0

        num_lats = len(lats)
        num_lons = len(lons)

        entries: Dict[str, DistrictWeightEntry] = {}

        for d in districts:
            s_poly = DistrictBoundaryProvider.get_shapely_polygon(d.district_id)
            if s_poly is None or not s_poly.is_valid:
                continue

            d_bbox = d.bounding_box  # (min_lat, max_lat, min_lon, max_lon)

            cell_coords: List[Tuple[int, int]] = []
            raw_areas: List[float] = []

            # Fast bounding box screening
            for i, lat_c in enumerate(lats):
                cell_min_lat = lat_c - half_res
                cell_max_lat = lat_c + half_res

                # Check lat overlap
                if cell_max_lat < d_bbox[0] or cell_min_lat > d_bbox[1]:
                    continue

                for j, lon_c in enumerate(lons):
                    cell_min_lon = lon_c - half_res
                    cell_max_lon = lon_c + half_res

                    # Check lon overlap
                    if cell_max_lon < d_bbox[2] or cell_min_lon > d_bbox[3]:
                        continue

                    # Exact Shapely box intersection
                    cell_geom = box(cell_min_lon, cell_min_lat, cell_max_lon, cell_max_lat)
                    if s_poly.intersects(cell_geom):
                        try:
                            intersection = s_poly.intersection(cell_geom)
                            if not intersection.is_empty and intersection.area > 0:
                                # Convert degree-area to approx km2 via cosine of latitude
                                mean_lat = lat_c
                                lat_rad = math.radians(mean_lat)
                                dx_km = 111.195 * math.cos(lat_rad) * res
                                dy_km = 111.195 * res
                                cell_total_km2 = dx_km * dy_km
                                cell_deg_area = res * res
                                frac = min(1.0, intersection.area / cell_deg_area)
                                area_km2 = frac * cell_total_km2

                                cell_coords.append((i, j))
                                raw_areas.append(area_km2)
                        except Exception as exc:
                            logger.debug("Geometry intersection error: %s", exc)

            # If district falls outside grid entirely or has tiny intersection
            if len(cell_coords) == 0:
                # Fallback: assign to closest single cell in grid
                closest_i = min(range(num_lats), key=lambda idx: abs(lats[idx] - d.centroid_lat))
                closest_j = min(range(num_lons), key=lambda jdx: abs(lons[jdx] - d.centroid_lon))
                cell_coords = [(closest_i, closest_j)]
                raw_areas = [d.area_km2]
                valid_area_frac = 1.0
            else:
                total_intersected_area = sum(raw_areas)
                valid_area_frac = min(1.0, total_intersected_area / max(1e-3, d.area_km2))

            # Normalize weights
            sum_raw = sum(raw_areas)
            if sum_raw > 0:
                norm_weights = [a / sum_raw for a in raw_areas]
            else:
                norm_weights = [1.0 / len(raw_areas)] * len(raw_areas)

            entries[d.district_id] = DistrictWeightEntry(
                district_id=d.district_id,
                cell_coords=cell_coords,
                cell_weights=norm_weights,
                cell_intersection_areas_km2=raw_areas,
                district_area_km2=d.area_km2,
                valid_area_fraction=round(valid_area_frac, 4),
            )

        return entries

    def aggregate_field(
        self,
        grid_data: np.ndarray,
        weights: DistrictWeightEntry,
        missing_mask: Optional[np.ndarray] = None,
    ) -> Tuple[float, float, float, float, float, float, DataQualityStatus, float]:
        """
        Vectorized application of weights to a 2D scalar field (e.g. rainfall, probability).
        Returns: (mean, max, min, median, p90, p95, quality_status, valid_area_fraction)
        """
        coords = weights.cell_coords
        w = weights.cell_weights

        # Extract values at cell coords
        vals = np.array([grid_data[i, j] for (i, j) in coords], dtype=np.float64)

        if missing_mask is not None:
            mask_vals = np.array([missing_mask[i, j] for (i, j) in coords], dtype=bool)
            valid_indices = ~mask_vals
            if not np.any(valid_indices):
                return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, DataQualityStatus.INSUFFICIENT_SPATIAL_COVERAGE, 0.0)

            vals = vals[valid_indices]
            w = w[valid_indices]
            sum_w = np.sum(w)
            if sum_w > 0:
                w = w / sum_w
            actual_valid_frac = weights.valid_area_fraction * (np.sum(valid_indices) / len(coords))
        else:
            actual_valid_frac = weights.valid_area_fraction

        # Quality check against minimum coverage
        if actual_valid_frac < self.MIN_VALID_AREA_FRACTION:
            status = DataQualityStatus.INSUFFICIENT_SPATIAL_COVERAGE
        elif actual_valid_frac < 0.95:
            status = DataQualityStatus.PARTIAL
        else:
            status = DataQualityStatus.VALID

        # Area-weighted Mean
        weighted_mean = float(np.sum(vals * w))
        max_val = float(np.max(vals))
        min_val = float(np.min(vals))

        # Sort values and weights for weighted quantiles
        sorter = np.argsort(vals)
        sorted_vals = vals[sorter]
        sorted_w = w[sorter]
        cum_w = np.cumsum(sorted_w)

        # Weighted Median (P50)
        p50_idx = np.searchsorted(cum_w, 0.50)
        median_val = float(sorted_vals[min(p50_idx, len(sorted_vals) - 1)])

        # Weighted P90 and P95
        p90_idx = np.searchsorted(cum_w, 0.90)
        p90_val = float(sorted_vals[min(p90_idx, len(sorted_vals) - 1)])

        p95_idx = np.searchsorted(cum_w, 0.95)
        p95_val = float(sorted_vals[min(p95_idx, len(sorted_vals) - 1)])

        return (
            round(weighted_mean, 2),
            round(max_val, 2),
            round(min_val, 2),
            round(median_val, 2),
            round(p90_val, 2),
            round(p95_val, 2),
            status,
            round(actual_valid_frac, 4),
        )

    def calculate_threshold_area_fractions(
        self,
        grid_data: np.ndarray,
        weights: DistrictWeightEntry,
        thresholds: List[float] = [64.5, 115.6, 204.5],
    ) -> List[float]:
        """Calculate the fraction of district polygon area exceeding given rainfall thresholds."""
        coords = weights.cell_coords
        w = weights.cell_weights
        vals = np.array([grid_data[i, j] for (i, j) in coords], dtype=np.float64)

        fractions = []
        for t in thresholds:
            exceeds = (vals >= t).astype(np.float64)
            area_frac = float(np.sum(exceeds * w))
            fractions.append(round(min(1.0, max(0.0, area_frac)), 4))

        return fractions

    def get_cache_status(self) -> Dict[str, Any]:
        """Retrieve cache diagnostics."""
        return {
            "cached_grid_definitions": len(self._cache),
            "cached_keys": list(self._cache.keys()),
            "metadata": list(self._cache_metadata.values()),
            "total_pairs": sum(
                sum(len(e.cell_coords) for e in d_dict.values())
                for d_dict in self._cache.values()
            ),
        }
