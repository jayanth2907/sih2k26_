"""
Spatial and Temporal Normalization Layer for PS26080 (MoES / NCMRWF).
Enforces uniform coordinate conventions and ISO-8601 UTC temporal standards.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


class SpatialTemporalNormalizer:
    """
    Standardizes spatial coordinates and forecast time steps across NWP systems.
    South Asia Domain Envelope: Lat [6.0°N, 38.0°N], Lon [66.0°E, 100.0°E].
    """

    LAT_MIN = 6.0
    LAT_MAX = 38.0
    LON_MIN = 66.0
    LON_MAX = 100.0

    @staticmethod
    def normalize_longitude(lon: float) -> float:
        """
        Normalize longitude from [0, 360] to [-180, 180] standard domain.
        Example: 287.5° -> -72.5°, 77.2° -> 77.2°.
        """
        norm = (lon + 180.0) % 360.0 - 180.0
        return round(norm, 6)

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """
        Validate latitude in [-90, 90] and normalized longitude in [-180, 180].
        """
        if not (-90.0 <= lat <= 90.0):
            return False, f"Latitude {lat} out of physical bounds [-90, 90]"
        norm_lon = SpatialTemporalNormalizer.normalize_longitude(lon)
        if not (-180.0 <= norm_lon <= 180.0):
            return False, f"Longitude {lon} out of physical bounds [-180, 180]"
        return True, None

    @staticmethod
    def is_in_south_asia_domain(lat: float, lon: float) -> bool:
        """Check if coordinates fall within the South Asian monsoon domain."""
        norm_lon = SpatialTemporalNormalizer.normalize_longitude(lon)
        return (
            SpatialTemporalNormalizer.LAT_MIN <= lat <= SpatialTemporalNormalizer.LAT_MAX
            and SpatialTemporalNormalizer.LON_MIN <= norm_lon <= SpatialTemporalNormalizer.LON_MAX
        )

    @classmethod
    def is_in_india_domain(cls, lat: float, lon: float) -> bool:
        """Alias for is_in_south_asia_domain."""
        return cls.is_in_south_asia_domain(lat, lon)

    @staticmethod
    def format_utc_to_ist(dt: datetime) -> str:
        """Convert UTC datetime to Indian Standard Time (+05:30) string."""
        ist_offset = timedelta(hours=5, minutes=30)
        ist_dt = dt + ist_offset
        return ist_dt.strftime("%Y-%m-%d %H:%M IST (+05:30)")


    @staticmethod
    def parse_iso_utc(ts_str: str) -> datetime:
        """Parse ISO-8601 timestamp and normalize to UTC timezone."""
        cleaned = ts_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except Exception:
            # Fallback for date-only format YYYY-MM-DD
            dt = datetime.strptime(ts_str[:10], "%Y-%m-%d")
            dt = dt.replace(tzinfo=timezone.utc)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    @staticmethod
    def format_iso_utc(dt: datetime) -> str:
        """Format datetime object into standardized ISO 8601 UTC string with Z suffix."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def verify_lead_time(
        cls,
        init_time_str: str,
        valid_time_str: str,
        lead_hours: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforce physical temporal invariant: valid_time == init_time + lead_time_hours.
        """
        try:
            init_dt = cls.parse_iso_utc(init_time_str)
            valid_dt = cls.parse_iso_utc(valid_time_str)
        except Exception as err:
            return False, f"Timestamp parsing failed: {err}"

        expected_valid_dt = init_dt + timedelta(hours=lead_hours)
        if abs((valid_dt - expected_valid_dt).total_seconds()) > 60:
            return False, (
                f"Temporal mismatch: init ({init_time_str}) + {lead_hours}h lead "
                f"yields {cls.format_iso_utc(expected_valid_dt)}, but got valid_time={valid_time_str}"
            )
        return True, None

    @classmethod
    def deduplicate_and_sort_steps(
        cls,
        records: List[Dict[str, Any]],
        time_key: str = "valid_time",
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate forecast valid times and sort chronologically.
        """
        seen = set()
        unique_records = []
        for r in records:
            key = r.get(time_key)
            if key and key not in seen:
                seen.add(key)
                unique_records.append(r)

        unique_records.sort(key=lambda x: cls.parse_iso_utc(x.get(time_key, "1970-01-01T00:00:00Z")))
        return unique_records
