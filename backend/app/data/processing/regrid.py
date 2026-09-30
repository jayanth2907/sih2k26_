"""
Spatial Standardization, Coordinate Transformation and Regridding Engine for PS26080.
Standardizes multi-source meteorological grids (0.1° IMERG, 0.25° ERA5/GFS, 12km NCUM) to canonical WGS84 coordinates.
"""

import math
from typing import Dict, List, Optional, Tuple


class SpatialStandardizer:
    """Standardizes spatial coordinates, computes geodetic distances, and regrids gridded matrices."""

    EARTH_RADIUS_KM = 6371.0088

    @staticmethod
    def normalize_longitude(lon: float) -> float:
        """Standardize longitude to [-180.0, 180.0] domain."""
        wrapped_lon = float(lon)
        while wrapped_lon > 180.0:
            wrapped_lon -= 360.0
        while wrapped_lon < -180.0:
            wrapped_lon += 360.0
        return round(wrapped_lon, 6)

    @staticmethod
    def normalize_coordinates(lat: float, lon: float) -> Tuple[float, float]:
        """
        Normalize latitude [-90.0, 90.0] and wrap longitude [-180.0, 180.0].
        """
        clamped_lat = max(-90.0, min(90.0, float(lat)))
        wrapped_lon = SpatialStandardizer.normalize_longitude(lon)
        return round(clamped_lat, 6), round(wrapped_lon, 6)

    @classmethod
    def haversine_distance_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Compute spherical great-circle distance between two geographic coordinates using the Haversine formula.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(cls.EARTH_RADIUS_KM * c, 3)

    @classmethod
    def haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Alias for haversine_distance_km."""
        return cls.haversine_distance_km(lat1, lon1, lat2, lon2)

    @classmethod
    def bearing_degrees(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Compute initial compass bearing from point 1 to point 2 (0° - 360°).
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_lambda = math.radians(lon2 - lon1)

        y = math.sin(delta_lambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
        bearing_rad = math.atan2(y, x)
        bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
        return round(bearing_deg, 2)

    @classmethod
    def calculate_initial_bearing(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Alias for bearing_degrees."""
        return cls.bearing_degrees(lat1, lon1, lat2, lon2)

    @staticmethod
    def bilinear_interpolation(
        target_lat: float,
        target_lon: float,
        grid_lats: List[float],
        grid_lons: List[float],
        grid_values: List[List[float]],
    ) -> float:
        """
        Perform 2D bilinear interpolation from a regular latitude-longitude grid to target coordinates.
        """
        if not grid_lats or not grid_lons or not grid_values:
            raise ValueError("Grid definitions and values must be non-empty")

        # Find bounding indices
        lat_idx = -1
        for i in range(len(grid_lats) - 1):
            if (grid_lats[i] <= target_lat <= grid_lats[i + 1]) or (grid_lats[i + 1] <= target_lat <= grid_lats[i]):
                lat_idx = i
                break

        lon_idx = -1
        for j in range(len(grid_lons) - 1):
            if (grid_lons[j] <= target_lon <= grid_lons[j + 1]) or (grid_lons[j + 1] <= target_lon <= grid_lons[j]):
                lon_idx = j
                break

        # Fallback to nearest neighbor if outside strict bounding box
        if lat_idx == -1 or lon_idx == -1:
            best_dist = float("inf")
            best_val = 0.0
            for i, g_lat in enumerate(grid_lats):
                for j, g_lon in enumerate(grid_lons):
                    d = (g_lat - target_lat) ** 2 + (g_lon - target_lon) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_val = grid_values[i][j]
            return round(best_val, 3)

        lat0, lat1 = grid_lats[lat_idx], grid_lats[lat_idx + 1]
        lon0, lon1 = grid_lons[lon_idx], grid_lons[lon_idx + 1]

        q11 = grid_values[lat_idx][lon_idx]
        q12 = grid_values[lat_idx][lon_idx + 1]
        q21 = grid_values[lat_idx + 1][lon_idx]
        q22 = grid_values[lat_idx + 1][lon_idx + 1]

        # Weights
        t_lat = (target_lat - lat0) / (lat1 - lat0) if lat1 != lat0 else 0.5
        t_lon = (target_lon - lon0) / (lon1 - lon0) if lon1 != lon0 else 0.5

        # Interpolate
        r1 = q11 * (1.0 - t_lon) + q12 * t_lon
        r2 = q21 * (1.0 - t_lon) + q22 * t_lon
        val = r1 * (1.0 - t_lat) + r2 * t_lat

        return round(float(val), 3)

    @classmethod
    def bilinear_interpolate(
        cls,
        grid_values: List[List[float]],
        grid_lats: List[float],
        grid_lons: List[float],
        target_lat: float,
        target_lon: float,
    ) -> float:
        """Flexible parameter order wrapper for bilinear_interpolation."""
        return cls.bilinear_interpolation(target_lat, target_lon, grid_lats, grid_lons, grid_values)


# Uniform alias
SpatialGridStandardizer = SpatialStandardizer
