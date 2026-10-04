"""
Survey of India Administrative District Boundaries Provider for PS26080.
Provides district lookups, state mapping, and spatial centroid coordinates across India.
"""

from typing import Dict, List, Optional


class DistrictProvider:
    """Provides district boundary metadata for regional rainfall post-processing products."""

    DISTRICT_DIRECTORY: List[Dict[str, any]] = [
        {"district_id": "MH_MUMBAI_CITY", "district": "Mumbai City", "state": "Maharashtra", "lat": 18.9388, "lon": 72.8354, "coastal": True},
        {"district_id": "MH_MUMBAI_SUBURBAN", "district": "Mumbai Suburban", "state": "Maharashtra", "lat": 19.1136, "lon": 72.8697, "coastal": True},
        {"district_id": "MH_THANE", "district": "Thane", "state": "Maharashtra", "lat": 19.2183, "lon": 72.9781, "coastal": True},
        {"district_id": "MH_RAIGAD", "district": "Raigad", "state": "Maharashtra", "lat": 18.5158, "lon": 73.1822, "coastal": True},
        {"district_id": "MH_RATNAGIRI", "district": "Ratnagiri", "state": "Maharashtra", "lat": 16.9902, "lon": 73.3120, "coastal": True},
        {"district_id": "MH_SINDHUDURG", "district": "Sindhudurg", "state": "Maharashtra", "lat": 16.1264, "lon": 73.6976, "coastal": True},
        {"district_id": "MH_SATARA", "district": "Satara", "state": "Maharashtra", "lat": 17.6805, "lon": 73.9935, "coastal": False},
        {"district_id": "MH_PUNE", "district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "coastal": False},
        {"district_id": "MH_NAGPUR", "district": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "coastal": False},
        {"district_id": "ML_EAST_KHASI_HILLS", "district": "East Khasi Hills", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "coastal": False},
        {"district_id": "TN_CHENNAI", "district": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "coastal": True},
        {"district_id": "JK_SRINAGAR", "district": "Srinagar", "state": "Jammu and Kashmir", "lat": 34.0837, "lon": 74.7973, "coastal": False},
        {"district_id": "OD_PURI", "district": "Puri", "state": "Odisha", "lat": 19.8135, "lon": 85.8312, "coastal": True},
        {"district_id": "KL_ERNAKULAM", "district": "Ernakulam", "state": "Kerala", "lat": 9.9816, "lon": 76.2999, "coastal": True},
    ]

    # India National Bounding Box (WGS84 approx: Lat [6.0, 37.5], Lon [68.0, 98.0])
    INDIA_BOUNDS = {
        "min_lat": 6.0,
        "max_lat": 37.5,
        "min_lon": 68.0,
        "max_lon": 98.0,
    }

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
            "district_id": "CUSTOM_BASIN",
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

    @classmethod
    def get_district_by_id(cls, district_id: str) -> Optional[Dict[str, any]]:
        """Retrieve district metadata by stable district_id."""
        for d in cls.DISTRICT_DIRECTORY:
            if d.get("district_id") == district_id:
                return d
        return None

    @classmethod
    def validate_district_registry(cls) -> Dict[str, any]:
        """Validate all district records for uniqueness, coordinate bounds, and completeness."""
        ids = [d["district_id"] for d in cls.DISTRICT_DIRECTORY]
        names = [(d["district"], d["state"]) for d in cls.DISTRICT_DIRECTORY]
        unique_ids = set(ids)
        unique_names = set(names)

        is_unique_ids = len(ids) == len(unique_ids)
        is_unique_names = len(names) == len(unique_names)

        invalid_coords = []
        for d in cls.DISTRICT_DIRECTORY:
            lat = d["lat"]
            lon = d["lon"]
            if not (cls.INDIA_BOUNDS["min_lat"] <= lat <= cls.INDIA_BOUNDS["max_lat"] and
                    cls.INDIA_BOUNDS["min_lon"] <= lon <= cls.INDIA_BOUNDS["max_lon"]):
                invalid_coords.append(d["district_id"])

        return {
            "total_districts": len(cls.DISTRICT_DIRECTORY),
            "unique_ids": is_unique_ids,
            "unique_names_per_state": is_unique_names,
            "invalid_coordinate_count": len(invalid_coords),
            "invalid_district_ids": invalid_coords,
            "status": "VALID" if (is_unique_ids and is_unique_names and len(invalid_coords) == 0) else "INVALID",
        }


# Alias for backward compatibility & uniform naming
DistrictsSource = DistrictProvider

