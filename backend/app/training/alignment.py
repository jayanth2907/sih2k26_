"""
Spatial and Temporal Alignment Engine for PS26080.
Harmonizes multi-source grids, temporal forecast steps, and rainfall accumulations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


def convert_precip_units(value: float, from_unit: str = "kg m**-2") -> float:
    """
    Convert precipitation rate/accumulation to standard mm depth.
    """
    u = from_unit.strip().lower()
    if u in ("kg m**-2", "kg m^-2", "kg/m^2", "mm"):
        return round(float(value), 3)
    elif u in ("m", "meters"):
        return round(float(value) * 1000.0, 3)
    elif u in ("m s**-1", "m s^-1", "m/s"):
        return round(float(value) * 3600.0, 3)
    return round(float(value), 3)


def validate_accumulation_window(window_hours: int) -> bool:
    """
    Validate that accumulation window is standard (1, 3, 6, 12, 24, 48, 72 hours).
    """
    return window_hours in {1, 3, 6, 12, 24, 48, 72}


def accumulate_rainfall(
    hourly_series: List[float],
    window_hours: int = 24,
) -> float:
    """
    Compute sliding window rainfall accumulation in mm.
    """
    if not validate_accumulation_window(window_hours):
        raise ValueError(f"Unsupported accumulation window: {window_hours}h. Must be in [1, 3, 6, 12, 24, 48, 72].")
    
    if not hourly_series:
        return 0.0

    slice_series = hourly_series[:window_hours]
    total = sum(slice_series)
    return round(max(0.0, float(total)), 2)


class GridAlignmentMetadata:
    """Metadata tracking spatial interpolation / regridding."""
    def __init__(
        self,
        source_grid: str,
        target_grid: str = "EPSG:4326_0.25deg",
        regridding_method: str = "bilinear",
    ):
        self.source_grid = source_grid
        self.target_grid = target_grid
        self.regridding_method = regridding_method

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_grid": self.source_grid,
            "target_grid": self.target_grid,
            "regridding_method": self.regridding_method,
        }


class DataAlignmentEngine:
    """
    Aligns atmospheric reanalysis/forecast predictors with observational rainfall targets.
    """

    @staticmethod
    def verify_temporal_causality(
        init_time: str,
        valid_time: str,
        obs_time: str,
        lead_hours: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify:
        1. valid_time == init_time + lead_hours
        2. obs_time == valid_time
        3. No future observation used before forecast valid time
        """
        try:
            init_dt = datetime.fromisoformat(init_time.replace("Z", "+00:00"))
            valid_dt = datetime.fromisoformat(valid_time.replace("Z", "+00:00"))
            obs_dt = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
        except Exception as err:
            return False, f"Timestamp parsing failed: {err}"

        expected_valid = init_dt + timedelta(hours=lead_hours)
        if abs((valid_dt - expected_valid).total_seconds()) > 60:
            return False, f"Lead time mismatch: {init_time} + {lead_hours}h != {valid_time}"

        if abs((valid_dt - obs_dt).total_seconds()) > 3600: # allow 1h tolerance for daily 03Z vs 00Z cycles if documented
            return False, f"Observation timestamp ({obs_time}) does not match valid time ({valid_time})"

        return True, None

    @staticmethod
    def align_forecast_and_observation(
        forecast_record: Dict[str, Any],
        observation_record: Dict[str, Any],
        grid_alignment: Optional[GridAlignmentMetadata] = None,
    ) -> Dict[str, Any]:
        """
        Produce a unified aligned sample containing predictors, raw NWP, and ground-truth observation.
        """
        aligned = dict(forecast_record)
        obs_rain = observation_record.get("rainfall", observation_record.get("observed_rainfall", 0.0))
        aligned["observed_rainfall"] = round(float(obs_rain), 3)
        aligned["raw_nwp_rainfall"] = round(float(forecast_record.get("rainfall", 0.0)), 3)
        aligned["residual_target"] = round(aligned["observed_rainfall"] - aligned["raw_nwp_rainfall"], 3)

        if grid_alignment:
            aligned["grid_alignment"] = grid_alignment.to_dict()

        return aligned
