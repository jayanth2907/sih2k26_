"""
Temporal Alignment and Causality Verification Engine for PS26080.
Enforces strict chronological causality, lead-time offsets, and prevents observation data leakage into model inputs.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple


class TemporalAligner:
    """
    Handles timestamp parsing, lead-time validation, and strict causality verification.
    """

    @staticmethod
    def parse_iso_utc(ts_str: str) -> datetime:
        """Parse ISO 8601 timestamp string into timezone-aware UTC datetime."""
        if not ts_str:
            raise ValueError("Timestamp string cannot be empty")
        
        # Replace Z with +00:00 for standard fromisoformat parsing
        cleaned = ts_str.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            # Try YYYY-MM-DD format
            dt = datetime.strptime(cleaned, "%Y-%m-%d")
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    @classmethod
    def calculate_lead_time_hours(cls, init_time_iso: str, valid_time_iso: str) -> int:
        """
        Calculate forecast lead time in integer hours: (valid_time - init_time).
        Raises ValueError if valid_time precedes initialization.
        """
        t_init = cls.parse_iso_utc(init_time_iso)
        t_valid = cls.parse_iso_utc(valid_time_iso)

        diff_seconds = (t_valid - t_init).total_seconds()
        if diff_seconds < 0:
            raise ValueError(
                f"Invalid temporal alignment: valid_time ({valid_time_iso}) precedes init_time ({init_time_iso})"
            )

        lead_hours = int(round(diff_seconds / 3600.0))
        return lead_hours

    @classmethod
    def verify_no_data_leakage(cls, observation_time_iso: str, forecast_init_iso: str) -> bool:
        """
        Verify that an observation timestamp strictly precedes or equals the forecast initialization.
        Prevents lookahead bias / data leakage during feature generation and AI post-processing.
        """
        t_obs = cls.parse_iso_utc(observation_time_iso)
        t_init = cls.parse_iso_utc(forecast_init_iso)

        if t_obs > t_init:
            raise ValueError(
                f"Data Leakage Detected: Observation at {observation_time_iso} is from the future relative to forecast initialization {forecast_init_iso}"
            )
        return True
