"""
Meteorological Quality Control (QC) and Validation Engine for PS26080.
Enforces physical plausibility bounds, detects sensor artifacts, and logs all automated corrections.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord, QualityControlLog

logger = logging.getLogger("rainfall_backend.qc")


class MeteorologicalQualityControl:
    """
    Physical quality control processor checking atmospheric fields against
    standard WMO / IMD operational bounds.
    """

    # Physical Bounds Reference
    MAX_VALID_RAINFALL_HOURLY_MM = 300.0 # Maximum convective burst (Cherrapunji cloudburst envelope)
    MAX_VALID_RAINFALL_DAILY_MM = 1500.0 # World record daily envelope
    MIN_VALID_HUMIDITY = 0.0
    MAX_VALID_HUMIDITY = 100.0
    MAX_VALID_WIND_SPEED_MS = 125.0 # Category 5 cyclone envelope
    MIN_VALID_MSLP_HPA = 870.0 # Deepest tropical cyclone central pressure
    MAX_VALID_MSLP_HPA = 1085.0 # Highest Siberian high pressure
    MIN_VALID_TEMP_K = 180.0 # ~ -93 deg C (mesopause / stratosphere)
    MAX_VALID_TEMP_K = 340.0 # ~ +67 deg C (extreme surface heat)

    def __init__(self):
        self.qc_logs: List[QualityControlLog] = []

    def log_action(self, field_name: str, original: any, corrected: any, rule: str, action: str) -> QualityControlLog:
        """Create and store an audit log entry for any QC modification."""
        entry = QualityControlLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            field_name=field_name,
            original_value=original,
            corrected_value=corrected,
            rule_applied=rule,
            action_taken=action,
        )
        self.qc_logs.append(entry)
        logger.info(
            "QC [%s] Field '%s': original=%s -> corrected=%s (Rule: %s)",
            action,
            field_name,
            original,
            corrected,
            rule,
        )
        return entry

    def sanitize_rainfall(self, value: Optional[float], is_daily: bool = False) -> Tuple[float, Optional[QualityControlLog]]:
        """Validate and clamp rainfall to non-negative physical bounds."""
        if value is None:
            log = self.log_action("rainfall", None, 0.0, "MISSING_RAINFALL_DEFAULT_ZERO", "CORRECTED")
            return 0.0, log

        if value < 0.0:
            log = self.log_action("rainfall", value, 0.0, "NEGATIVE_RAINFALL_CLAMP_ZERO", "CORRECTED")
            return 0.0, log

        max_limit = self.MAX_VALID_RAINFALL_DAILY_MM if is_daily else self.MAX_VALID_RAINFALL_HOURLY_MM
        if value > max_limit:
            log = self.log_action("rainfall", value, max_limit, f"EXCEEDED_PHYSICAL_LIMIT_{max_limit}MM", "CAPPED")
            return max_limit, log

        return round(float(value), 3), None

    def sanitize_relative_humidity(self, value: Optional[float], field_name: str = "relative_humidity") -> Tuple[Optional[float], Optional[QualityControlLog]]:
        """Clamp relative humidity strictly within [0.0%, 100.0%]."""
        if value is None:
            return None, None

        if value < self.MIN_VALID_HUMIDITY:
            log = self.log_action(field_name, value, 0.0, "NEGATIVE_HUMIDITY_CLAMP_ZERO", "CORRECTED")
            return 0.0, log

        if value > self.MAX_VALID_HUMIDITY:
            log = self.log_action(field_name, value, 100.0, "SUPERSATURATION_CLAMP_100PCT", "CAPPED")
            return 100.0, log

        return round(float(value), 2), None

    def sanitize_wind_components(self, u: Optional[float], v: Optional[float], level_hpa: int = 850) -> Tuple[Optional[float], Optional[float], List[QualityControlLog]]:
        """Validate horizontal wind components and ensure vector speed is realistic."""
        logs = []
        if u is None or v is None:
            return u, v, logs

        speed = (u**2 + v**2) ** 0.5
        if speed > self.MAX_VALID_WIND_SPEED_MS:
            # Scale down proportionally to max allowable physical envelope
            scale = self.MAX_VALID_WIND_SPEED_MS / speed
            u_corr = round(u * scale, 3)
            v_corr = round(v * scale, 3)
            log = self.log_action(
                f"wind_{level_hpa}",
                {"u": u, "v": v, "speed": speed},
                {"u": u_corr, "v": v_corr, "speed": self.MAX_VALID_WIND_SPEED_MS},
                "WIND_SPEED_EXCEEDED_MAX_ENVELOPE",
                "CAPPED",
            )
            logs.append(log)
            return u_corr, v_corr, logs

        return round(u, 3), round(v, 3), logs

    def sanitize_mslp(self, mslp: Optional[float]) -> Tuple[Optional[float], Optional[QualityControlLog]]:
        """Check Mean Sea Level Pressure against barometric extremes."""
        if mslp is None:
            return None, None

        # Unit mismatch detection: if in Pa (e.g. 101325), convert to hPa
        if mslp > 50000.0:
            converted = round(mslp / 100.0, 2)
            log = self.log_action("mslp", mslp, converted, "UNIT_CONVERT_PA_TO_HPA", "CORRECTED")
            return converted, log

        if mslp < self.MIN_VALID_MSLP_HPA or mslp > self.MAX_VALID_MSLP_HPA:
            clamped = max(self.MIN_VALID_MSLP_HPA, min(self.MAX_VALID_MSLP_HPA, mslp))
            log = self.log_action("mslp", mslp, clamped, "MSLP_OUT_OF_BOUNDS_CLAMPED", "CAPPED")
            return clamped, log

        return round(mslp, 2), None

    def process_record(self, record: CanonicalMeteorologicalRecord) -> Tuple[CanonicalMeteorologicalRecord, List[QualityControlLog]]:
        """
        Execute full quality control pipeline on a canonical record.
        Returns a clean validated record with QC log trail.
        """
        record_logs: List[QualityControlLog] = []

        # 1. Rainfall validation
        clean_rain, r_log = self.sanitize_rainfall(record.rainfall)
        if r_log:
            record_logs.append(r_log)
        record.rainfall = clean_rain

        if record.observed_rainfall is not None:
            clean_obs, obs_log = self.sanitize_rainfall(record.observed_rainfall, is_daily=True)
            if obs_log:
                record_logs.append(obs_log)
            record.observed_rainfall = clean_obs

        # 2. Relative Humidity at levels
        for level, field in [(850, "relative_humidity_850"), (700, "relative_humidity_700"), (500, "relative_humidity_500")]:
            val = getattr(record, field)
            clean_rh, rh_log = self.sanitize_relative_humidity(val, field)
            if rh_log:
                record_logs.append(rh_log)
            setattr(record, field, clean_rh)

        # 3. Wind components
        clean_u850, clean_v850, w_logs = self.sanitize_wind_components(record.u850, record.v850, 850)
        record_logs.extend(w_logs)
        record.u850, record.v850 = clean_u850, clean_v850

        # 4. MSLP validation
        clean_mslp, m_log = self.sanitize_mslp(record.mslp)
        if m_log:
            record_logs.append(m_log)
        record.mslp = clean_mslp

        # 5. Set final quality flag
        if record_logs:
            record.data_quality = "QC_CORRECTED"
        else:
            record.data_quality = "QC_PASSED"

        return record, record_logs
