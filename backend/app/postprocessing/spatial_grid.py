"""
Canonical Spatial Grid Engine & Geodetic Coordinate Systems (Phase 13).
Manages 0.25° × 0.25° WGS84 target grids, geodesic physical cell metrics,
and multi-scale physical neighborhood mappings.
"""

import math
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.app.schemas.spatial_postprocess import SpatialGridDefinition


class SpatialGridManager:
    """
    Manages canonical 0.25° WGS84 spatial grids and geodetic coordinate transformations.
    """

    EARTH_RADIUS_KM = 6371.0088
    DEG_TO_KM_LAT = (2.0 * math.pi * EARTH_RADIUS_KM) / 360.0  # ~111.195 km per degree

    @classmethod
    def create_canonical_grid(
        cls,
        min_lat: float = 6.0,
        max_lat: float = 38.0,
        min_lon: float = 68.0,
        max_lon: float = 98.0,
        resolution_deg: float = 0.25,
        grid_name: str = "South_Asian_Monsoon_0.25deg",
    ) -> SpatialGridDefinition:
        """
        Generate a canonical regular latitude-longitude grid.
        Default domain covers South Asian Monsoon domain (6°N–38°N, 68°E–98°E).
        """
        # North-to-south ordering for standard tensor representation [lat, lon]
        num_lats = int(round((max_lat - min_lat) / resolution_deg)) + 1
        num_lons = int(round((max_lon - min_lon) / resolution_deg)) + 1

        lats = [round(max_lat - i * resolution_deg, 4) for i in range(num_lats)]
        lons = [round(min_lon + j * resolution_deg, 4) for j in range(num_lons)]

        mean_lat = (min_lat + max_lat) / 2.0
        dx_km = cls.calculate_dx_km(mean_lat, resolution_deg)
        dy_km = cls.calculate_dy_km(resolution_deg)

        return SpatialGridDefinition(
            grid_name=grid_name,
            resolution_deg=resolution_deg,
            crs="EPSG:4326",
            latitudes=lats,
            longitudes=lons,
            grid_shape=(num_lats, num_lons),
            extent_bbox=(min_lat, max_lat, min_lon, max_lon),
            dx_km_mean=round(dx_km, 2),
            dy_km=round(dy_km, 2),
            orientation="NORTH_TO_SOUTH",
        )

    @classmethod
    def create_regional_patch_grid(
        cls,
        center_lat: float = 18.5,
        center_lon: float = 73.5,
        size_cells: int = 32,
        resolution_deg: float = 0.25,
        grid_name: str = "Regional_Patch_32x32",
    ) -> SpatialGridDefinition:
        """
        Generate a localized square patch (e.g. 32x32 cells ~ 8°x8° ~ 888x888 km) centered on a key region.
        """
        span = (size_cells - 1) * resolution_deg
        half_span = span / 2.0
        min_lat = round(center_lat - half_span, 4)
        max_lat = round(center_lat + half_span, 4)
        min_lon = round(center_lon - half_span, 4)
        max_lon = round(center_lon + half_span, 4)

        return cls.create_canonical_grid(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            resolution_deg=resolution_deg,
            grid_name=grid_name,
        )

    @classmethod
    def calculate_dy_km(cls, resolution_deg: float = 0.25) -> float:
        """Calculate meridional distance per grid cell (constant across Earth)."""
        return resolution_deg * cls.DEG_TO_KM_LAT

    @classmethod
    def calculate_dx_km(cls, latitude_deg: float, resolution_deg: float = 0.25) -> float:
        """Calculate zonal distance per grid cell at a specific latitude."""
        lat_rad = math.radians(latitude_deg)
        return resolution_deg * cls.DEG_TO_KM_LAT * math.cos(lat_rad)

    @classmethod
    def map_physical_radius_to_window_size(
        cls,
        radius_km: float,
        latitude_deg: float = 20.0,
        resolution_deg: float = 0.25,
    ) -> int:
        """
        Map a requested physical distance scale (e.g. 25km, 50km, 100km) to an odd-sized kernel window (1, 3, 5, 7, 9).
        Ensures strict physical scale calibration rather than assuming 5x5 is exactly 50km without geodetic verification.
        """
        cell_size_km = (cls.calculate_dy_km(resolution_deg) + cls.calculate_dx_km(latitude_deg, resolution_deg)) / 2.0
        
        # Diameter in cells
        diameter_cells = (2.0 * radius_km) / cell_size_km
        
        # Round to nearest odd integer >= 1
        w = int(round(diameter_cells))
        if w % 2 == 0:
            w += 1
        return max(1, w)

    @classmethod
    def validate_grid_array(
        cls,
        array: np.ndarray,
        grid_def: SpatialGridDefinition,
    ) -> bool:
        """
        Validate that a 2D numpy array matches the grid definition dimensions.
        """
        if array.ndim != 2:
            return False
        return array.shape == grid_def.grid_shape
