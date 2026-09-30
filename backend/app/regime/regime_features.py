"""
Synoptic Feature Extraction and Formatting for Weather Regime Classification.
Extracts synoptic indicators (Low-Level Jet, Monsoon Trough Position, OLR, Vorticity)
from canonical records and NWP forecasts.
"""

from typing import Dict, Optional
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord, MeteorologicalFeatureSet
from backend.app.schemas.regime import SynopticFeatures


class RegimeFeatureExtractor:
    """Extracts standardized synoptic feature structures for regime detectors."""

    @staticmethod
    def extract_synoptic_features(
        record: CanonicalMeteorologicalRecord,
        derived_features: MeteorologicalFeatureSet,
    ) -> SynopticFeatures:
        """Construct validated SynopticFeatures model from meteorological record."""
        # Low-Level Jet speed in knots (1 m/s = 1.94384 kts)
        llj_speed_kts = round(derived_features.wind_speed_850 * 1.94384, 1)

        # Monsoon Trough Position Diagnosis
        lat = record.latitude
        mslp = record.mslp or 1008.0

        if lat < 22.0:
            trough_pos = "active_south"
            trough_lat = 21.5
        elif lat > 26.5:
            trough_pos = "break_foothills"
            trough_lat = 27.5
        else:
            trough_pos = "normal"
            trough_lat = 24.5

        # OLR Convection Proxy (derived from vertical velocity and cloud cover / cape)
        # Deep convection: omega < 0, cape > 1500 -> OLR ~ 180-200 W/m^2
        omega = record.vertical_velocity or -0.3
        cape = record.cape_j_kg or 1200.0
        olr = max(160.0, min(280.0, 240.0 + (omega * 50.0) - (cape / 100.0)))

        # Mid-Tropospheric Relative Vorticity proxy (10^-5 s^-1)
        # Cyclonic vorticity enhanced near monsoon trough and LPS
        vorticity = max(-2.0, min(12.0, (1013.25 - mslp) * 0.8 + (derived_features.wind_speed_850 * 0.2)))

        # Surface Pressure Anomaly relative to standard 1013.25 hPa
        p_anomaly = round(mslp - 1013.25, 2)

        return SynopticFeatures(
            low_level_jet_speed_kts=llj_speed_kts,
            low_level_jet_direction_deg=derived_features.wind_direction_850,
            monsoon_trough_lat=trough_lat,
            trough_position=trough_pos,
            olr_w_m2=round(olr, 1),
            mid_tropospheric_vorticity_1e5_s=round(vorticity, 2),
            surface_pressure_anomaly_hpa=p_anomaly,
            cape_j_kg=round(cape, 1),
            integrated_vapor_transport_kg_m_s=round(derived_features.moisture_transport_proxy, 1),
            orographic_lift_index=round(derived_features.orographic_lift_index, 3),
            coastal_convergence_index=round(derived_features.coastal_moisture_indicator, 3),
        )
