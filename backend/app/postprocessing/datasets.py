"""
Dataset Loaders, Feature Matrix Construction, and Chronological Split Generators for PS26080.
Strictly separates:
- Training: 2018–2022 (JJAS)
- Validation: 2023 (JJAS)
- Test: 2024–2025 (JJAS)
"""

import math
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel

from backend.app.postprocessing.base import PostProcessingInput
from backend.app.schemas.regime import WeatherRegimeType


FEATURE_NAMES = [
    # 1. NWP Precipitation & Ensemble (0..6)
    "raw_nwp_rainfall",
    "lead_time_hours",
    "ensemble_mean",
    "ensemble_std",
    "ensemble_p10",
    "ensemble_p90",
    "ensemble_spread",

    # 2. Multi-Level Atmospheric Dynamics (7..17)
    "wind_speed_850",
    "wind_direction_850_sin",
    "wind_direction_850_cos",
    "wind_speed_700",
    "relative_humidity_850",
    "relative_humidity_700",
    "specific_humidity_850",
    "cape_j_kg",
    "moisture_transport_proxy",
    "vertical_wind_shear",
    "geopotential_500",
    "vertical_velocity",
    "mslp",

    # 3. Static Geographic & Orographic (18..24)
    "elevation",
    "slope",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness",
    "distance_to_coast",
    "orographic_lift_index",
    "coastal_moisture_indicator",

    # 4. Temporal Cyclical Encoding (25..28)
    "month_sin",
    "month_cos",
    "day_of_year_sin",
    "day_of_year_cos",

    # 5. Continuous Regime Probabilities (29..35)
    "prob_active_monsoon",
    "prob_break_monsoon",
    "prob_monsoon_low_lps",
    "prob_coastal_convergence",
    "prob_orographic_rainfall",
    "prob_western_disturbance",
    "prob_neutral",

    # 6. Physical Regime Interaction Features (36..40)
    "interact_rain_active",
    "interact_rain_orographic",
    "interact_rain_coastal",
    "interact_rain_lps",
    "interact_rain_break",
]


class PostProcessingDataset:
    """Standardized dataset container for tabular training and evaluation."""

    def __init__(
        self,
        X: np.ndarray,
        y_residual: np.ndarray,
        raw_nwp: np.ndarray,
        observed: np.ndarray,
        regimes: List[str],
        timestamps: List[str],
        metadata: List[Dict[str, any]],
    ):
        self.X = X
        self.y_residual = y_residual  # observed - raw_nwp
        self.raw_nwp = raw_nwp
        self.observed = observed
        self.regimes = regimes
        self.timestamps = timestamps
        self.metadata = metadata
        self.feature_names = list(FEATURE_NAMES)

    def __len__(self) -> int:
        return len(self.X)


def extract_feature_vector(sample: PostProcessingInput) -> np.ndarray:
    """Extract standard numeric feature vector from a PostProcessingInput instance."""
    # Cyclical trigonometric encodings
    wind_rad_850 = math.radians(sample.wind_direction_850)
    aspect_rad = math.radians(sample.aspect)
    month_rad = 2.0 * math.pi * (sample.month - 1) / 12.0
    doy_rad = 2.0 * math.pi * (sample.day_of_year - 1) / 365.25

    ens_mean = sample.ensemble_mean if sample.ensemble_mean is not None else sample.raw_nwp_rainfall
    ens_std = sample.ensemble_std if sample.ensemble_std is not None else sample.raw_nwp_rainfall * 0.15
    ens_p10 = sample.ensemble_p10 if sample.ensemble_p10 is not None else sample.raw_nwp_rainfall * 0.8
    ens_p90 = sample.ensemble_p90 if sample.ensemble_p90 is not None else sample.raw_nwp_rainfall * 1.25
    ens_spread = max(0.0, ens_p90 - ens_p10)

    # Regime probabilities
    probs = sample.regime_probabilities
    p_act = probs.get("ACTIVE_MONSOON", 0.0)
    p_brk = probs.get("BREAK_MONSOON", 0.0)
    p_lps = probs.get("MONSOON_LOW_LPS", 0.0)
    p_cst = probs.get("COASTAL_CONVERGENCE", 0.0)
    p_oro = probs.get("OROGRAPHIC_RAINFALL", 0.0)
    p_wd = probs.get("WESTERN_DISTURBANCE", 0.0)
    p_neu = probs.get("NEUTRAL", 0.0)

    rain = sample.raw_nwp_rainfall

    features = [
        # 1. NWP & Ensemble
        rain,
        float(sample.lead_time_hours),
        ens_mean,
        ens_std,
        ens_p10,
        ens_p90,
        ens_spread,

        # 2. Multi-level Atmospheric
        sample.wind_speed_850,
        math.sin(wind_rad_850),
        math.cos(wind_rad_850),
        sample.wind_speed_700,
        sample.relative_humidity_850,
        sample.relative_humidity_700,
        sample.specific_humidity_850,
        sample.cape_j_kg,
        sample.moisture_transport_proxy,
        sample.vertical_wind_shear,
        sample.geopotential_500,
        sample.vertical_velocity,
        sample.mslp,

        # 3. Geographic
        sample.elevation,
        sample.slope,
        math.sin(aspect_rad),
        math.cos(aspect_rad),
        sample.terrain_roughness,
        sample.distance_to_coast,
        sample.orographic_lift_index,
        sample.coastal_moisture_indicator,

        # 4. Temporal Cyclical
        math.sin(month_rad),
        math.cos(month_rad),
        math.sin(doy_rad),
        math.cos(doy_rad),

        # 5. Continuous Regime Probabilities
        p_act,
        p_brk,
        p_lps,
        p_cst,
        p_oro,
        p_wd,
        p_neu,

        # 6. Regime Interactions
        rain * p_act,
        rain * p_oro,
        rain * p_cst,
        rain * p_lps,
        rain * p_brk,
    ]

    return np.array(features, dtype=np.float32)


class DatasetGenerator:
    """
    Generates deterministic, scientifically realistic calibration & evaluation datasets
    matching South Asian Summer Monsoon error structures.
    """

    @staticmethod
    def generate_synthetic_dataset(
        split: str = "train",
        seed: int = 42,
    ) -> PostProcessingDataset:
        """
        Generate chronological dataset (Train: 2018-2022, Val: 2023, Test: 2024-2025).
        """
        rng = np.random.default_rng(seed + (0 if split == "train" else 100 if split == "val" else 200))

        if split == "train":
            n_samples = 2500
            years = [2018, 2019, 2020, 2021, 2022]
        elif split == "val":
            n_samples = 600
            years = [2023]
        else:  # test
            n_samples = 800
            years = [2024, 2025]

        # Key geographic anchors across India
        locations = [
            {"name": "Mumbai", "lat": 18.93, "lon": 72.83, "elev": 14.0, "slope": 1.2, "d_coast": 2.5, "regime_bias": "coastal"},
            {"name": "Mahabaleshwar", "lat": 17.92, "lon": 73.65, "elev": 1353.0, "slope": 8.4, "d_coast": 55.0, "regime_bias": "orographic"},
            {"name": "Cherrapunji", "lat": 25.27, "lon": 91.73, "elev": 1430.0, "slope": 12.5, "d_coast": 260.0, "regime_bias": "orographic"},
            {"name": "Puri", "lat": 19.81, "lon": 85.83, "elev": 10.0, "slope": 0.5, "d_coast": 1.5, "regime_bias": "lps"},
            {"name": "Nagpur", "lat": 21.14, "lon": 79.08, "elev": 310.0, "slope": 0.8, "d_coast": 580.0, "regime_bias": "active_break"},
            {"name": "Shimla", "lat": 31.10, "lon": 77.17, "elev": 2200.0, "slope": 14.0, "d_coast": 1150.0, "regime_bias": "western_disturbance"},
            {"name": "Bhopal", "lat": 23.25, "lon": 77.41, "elev": 520.0, "slope": 1.1, "d_coast": 620.0, "regime_bias": "active_break"},
            {"name": "Kochi", "lat": 9.98, "lon": 76.29, "elev": 5.0, "slope": 0.4, "d_coast": 1.2, "regime_bias": "coastal"},
        ]

        X_list: List[np.ndarray] = []
        y_res_list: List[float] = []
        raw_nwp_list: List[float] = []
        obs_list: List[float] = []
        regimes_list: List[str] = []
        ts_list: List[str] = []
        meta_list: List[Dict[str, any]] = []

        for i in range(n_samples):
            loc = locations[i % len(locations)]
            year = years[i % len(years)]
            month = rng.choice([6, 7, 8, 9])  # JJAS
            day = int(rng.integers(1, 29))
            doy = (month - 1) * 30 + day
            ts = f"{year}-{month:02d}-{day:02d}T00:00:00Z"

            # Base raw NWP forecast
            raw_rain = float(rng.exponential(scale=28.0 if loc["regime_bias"] in ["orographic", "coastal"] else 18.0))
            raw_rain = round(max(0.0, min(250.0, raw_rain)), 2)

            # Regime probability profile synthesis
            bias_type = loc["regime_bias"]
            if bias_type == "orographic":
                primary = WeatherRegimeType.OROGRAPHIC_RAINFALL.value
                p_oro = float(rng.uniform(0.60, 0.90))
                p_act = float(rng.uniform(0.30, 0.60))
                p_cst = float(rng.uniform(0.10, 0.35))
                p_brk = float(rng.uniform(0.01, 0.05))
                p_lps = float(rng.uniform(0.05, 0.20))
                p_wd = float(rng.uniform(0.01, 0.05))
                # Systematic NWP orographic underprediction error: +18 to +55 mm
                err = raw_rain * float(rng.uniform(0.55, 1.10)) + float(rng.normal(12.0, 4.0))
            elif bias_type == "coastal":
                primary = WeatherRegimeType.COASTAL_CONVERGENCE.value
                p_oro = float(rng.uniform(0.15, 0.40))
                p_act = float(rng.uniform(0.35, 0.65))
                p_cst = float(rng.uniform(0.60, 0.88))
                p_brk = float(rng.uniform(0.01, 0.05))
                p_lps = float(rng.uniform(0.10, 0.30))
                p_wd = float(rng.uniform(0.01, 0.04))
                # Coastal convergence underprediction: +10 to +30 mm
                err = raw_rain * float(rng.uniform(0.30, 0.65)) + float(rng.normal(6.0, 2.5))
            elif bias_type == "lps":
                primary = WeatherRegimeType.MONSOON_LOW_LPS.value
                p_oro = float(rng.uniform(0.05, 0.15))
                p_act = float(rng.uniform(0.50, 0.80))
                p_cst = float(rng.uniform(0.30, 0.50))
                p_brk = float(rng.uniform(0.01, 0.05))
                p_lps = float(rng.uniform(0.65, 0.92))
                p_wd = float(rng.uniform(0.01, 0.03))
                # LPS vortex placement / intensity error: +15 to +40 mm
                err = raw_rain * float(rng.uniform(0.40, 0.85)) + float(rng.normal(8.0, 3.0))
            elif bias_type == "western_disturbance":
                primary = WeatherRegimeType.WESTERN_DISTURBANCE.value
                p_oro = float(rng.uniform(0.30, 0.55))
                p_act = float(rng.uniform(0.10, 0.30))
                p_cst = float(rng.uniform(0.01, 0.05))
                p_brk = float(rng.uniform(0.05, 0.15))
                p_lps = float(rng.uniform(0.02, 0.08))
                p_wd = float(rng.uniform(0.65, 0.90))
                # Western Disturbance advection error
                err = raw_rain * float(rng.uniform(0.25, 0.60)) + float(rng.normal(5.0, 2.0))
            else:  # active_break
                if raw_rain > 20.0:
                    primary = WeatherRegimeType.ACTIVE_MONSOON.value
                    p_act = float(rng.uniform(0.65, 0.90))
                    p_brk = float(rng.uniform(0.02, 0.08))
                    p_oro = float(rng.uniform(0.10, 0.25))
                    p_cst = float(rng.uniform(0.10, 0.25))
                    p_lps = float(rng.uniform(0.15, 0.35))
                    p_wd = float(rng.uniform(0.01, 0.05))
                    # Active monsoon underprediction: +8 to +25 mm
                    err = raw_rain * float(rng.uniform(0.20, 0.50)) + float(rng.normal(4.0, 2.0))
                else:
                    primary = WeatherRegimeType.BREAK_MONSOON.value
                    p_act = float(rng.uniform(0.05, 0.15))
                    p_brk = float(rng.uniform(0.65, 0.92))
                    p_oro = float(rng.uniform(0.02, 0.08))
                    p_cst = float(rng.uniform(0.02, 0.08))
                    p_lps = float(rng.uniform(0.01, 0.05))
                    p_wd = float(rng.uniform(0.02, 0.08))
                    # Break monsoon: NWP overpredicts central India rainfall (negative residual error)
                    err = -float(rng.uniform(0.30, 0.85)) * raw_rain - float(rng.normal(2.0, 1.0))

            p_neu = max(0.02, 1.0 - max(p_act, p_brk, p_oro, p_cst, p_lps, p_wd))

            # Observed rainfall = raw_rain + err, clamped >= 0
            observed = max(0.0, raw_rain + err)
            y_residual = observed - raw_rain  # Exact definition

            # Synthesize input object
            sample_input = PostProcessingInput(
                raw_nwp_rainfall=raw_rain,
                lead_time_hours=24,
                latitude=loc["lat"],
                longitude=loc["lon"],
                month=month,
                day_of_year=doy,
                ensemble_mean=raw_rain * float(rng.uniform(0.95, 1.05)),
                ensemble_std=raw_rain * float(rng.uniform(0.10, 0.22)),
                ensemble_p10=raw_rain * 0.78,
                ensemble_p90=raw_rain * 1.28,
                wind_speed_850=float(rng.uniform(8.0, 22.0)),
                wind_direction_850=float(rng.uniform(230.0, 275.0)),
                wind_speed_700=float(rng.uniform(6.0, 16.0)),
                wind_direction_700=float(rng.uniform(240.0, 280.0)),
                relative_humidity_850=float(rng.uniform(65.0, 95.0)),
                relative_humidity_700=float(rng.uniform(55.0, 85.0)),
                specific_humidity_850=float(rng.uniform(11.0, 17.5)),
                cape_j_kg=float(rng.uniform(800.0, 2800.0)),
                moisture_transport_proxy=float(rng.uniform(120.0, 320.0)),
                vertical_wind_shear=float(rng.uniform(4.0, 16.0)),
                geopotential_500=5850.0 + float(rng.normal(0, 30)),
                vertical_velocity=-0.35 + float(rng.normal(0, 0.15)),
                mslp=1008.0 + float(rng.normal(0, 4.0)),
                elevation=loc["elev"],
                slope=loc["slope"],
                aspect=270.0,
                terrain_roughness=loc["slope"] * 4.5,
                distance_to_coast=loc["d_coast"],
                orographic_lift_index=round(loc["slope"] * (loc["elev"] / 1000.0) * 0.12, 3),
                coastal_moisture_indicator=round(math.exp(-loc["d_coast"] / 75.0) * 0.8, 3),
                regime_probabilities={
                    "ACTIVE_MONSOON": round(p_act, 3),
                    "BREAK_MONSOON": round(p_brk, 3),
                    "MONSOON_LOW_LPS": round(p_lps, 3),
                    "COASTAL_CONVERGENCE": round(p_cst, 3),
                    "OROGRAPHIC_RAINFALL": round(p_oro, 3),
                    "WESTERN_DISTURBANCE": round(p_wd, 3),
                    "NEUTRAL": round(p_neu, 3),
                },
                primary_regime=primary,
                regime_confidence=round(float(rng.uniform(0.72, 0.95)), 2),
                data_source="NCMRWF_NCUM_CALIBRATION_TRAIN" if split == "train" else "NCMRWF_NCUM_EVALUATION",
                is_demo=True,
                timestamp=ts,
            )

            vec = extract_feature_vector(sample_input)
            X_list.append(vec)
            y_res_list.append(y_residual)
            raw_nwp_list.append(raw_rain)
            obs_list.append(observed)
            regimes_list.append(primary)
            ts_list.append(ts)
            meta_list.append({"location": loc["name"], "year": year, "month": month, "day": day})

        return PostProcessingDataset(
            X=np.array(X_list, dtype=np.float32),
            y_residual=np.array(y_res_list, dtype=np.float32),
            raw_nwp=np.array(raw_nwp_list, dtype=np.float32),
            observed=np.array(obs_list, dtype=np.float32),
            regimes=regimes_list,
            timestamps=ts_list,
            metadata=meta_list,
        )
