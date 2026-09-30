"""
Survey of India Administrative District Boundaries Provider for PS26080.
Provides district lookups, state mapping, and spatial centroid coordinates across India.
"""

from typing import Dict, List, Optional


class DistrictProvider:
    """Provides district boundary metadata for regional rainfall post-processing products."""

    DISTRICT_DIRECTORY: List[Dict[str, any]] = [
        {"district": "Mumbai City", "state": "Maharashtra", "lat": 18.9388, "lon": 72.8354, "coastal": True},
        {"district": "Mumbai Suburban", "state": "Maharashtra", "lat": 19.1136, "lon": 72.8697, "coastal": True},
        {"district": "Thane", "state": "Maharashtra", "lat": 19.2183, "lon": 72.9781, "coastal": True},
        {"district": "Raigad", "state": "Maharashtra", "lat": 18.5158, "lon": 73.1822, "coastal": True},
        {"district": "Ratnagiri", "state": "Maharashtra", "lat": 16.9902, "lon": 73.3120, "coastal": True},
        {"district": "Sindhudurg", "state": "Maharashtra", "lat": 16.1264, "lon": 73.6976, "coastal": True},
        {"district": "Satara", "state": "Maharashtra", "lat": 17.6805, "lon": 73.9935, "coastal": False},
        {"district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "coastal": False},
        {"district": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "coastal": False},
        {"district": "East Khasi Hills", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "coastal": False},
        {"district": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "coastal": True},
        {"district": "Srinagar", "state": "Jammu and Kashmir", "lat": 34.0837, "lon": 74.7973, "coastal": False},
        {"district": "Puri", "state": "Odisha", "lat": 19.8135, "lon": 85.8312, "coastal": True},
        {"district": "Ernakulam", "state": "Kerala", "lat": 9.9816, "lon": 76.2999, "coastal": True},
    ]

    @classmethod
    def lookup_district(cls, lat: float, lon: float) -> Dict[str, any]:
        """Find the closest administrative district to the given coordinates."""
        closest = None
        min_dist_sq = float("inf")

        for d in cls.DISTRICT_DIRECTORY:
            dist_sq = (d["lat"] - lat) ** 2 + (d["lon"] - lon) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest = d

        return closest or {
            "district": "Custom Meteorological Basin",
            "state": "National Domain",
            "lat": lat,
            "lon": lon,
            "coastal": False,
        }

    @classmethod
    def get_all_districts(cls) -> List[Dict[str, any]]:
        """Return all supported district records."""
        return cls.DISTRICT_DIRECTORY

    @classmethod
    def find_district_by_coords(cls, lat: float, lon: float) -> Dict[str, any]:
        """Alias for lookup_district."""
        return cls.lookup_district(lat, lon)


# Alias for backward compatibility & uniform naming
DistrictsSource = DistrictProvider
