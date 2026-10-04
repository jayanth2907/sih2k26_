"""
Physical Regime Transition Explainer for PS26080 (MoES / NCMRWF).
Translates quantified atmospheric feature shifts into transparent synoptic transition narratives.
"""

from typing import Any, Dict, List, Optional
from backend.app.schemas.regime import WeatherRegimeType
from backend.app.schemas.regime_temporal import RegimeFeatureSnapshot, RegimeTransitionExplanation


class RegimeTransitionExplainer:
    """
    Generates physically grounded transition explanations comparing state at time t vs t+1.
    """

    @staticmethod
    def explain_transition(
        from_regime: WeatherRegimeType,
        to_regime: WeatherRegimeType,
        transition_prob: float,
        initial_features: Optional[Dict[str, float]] = None,
        target_features: Optional[Dict[str, float]] = None,
    ) -> RegimeTransitionExplanation:
        """
        Synthesize meteorological narrative and identify dominant physical drivers from feature deltas.
        """
        init_f = initial_features or {}
        target_f = target_features or {}

        feature_deltas: Dict[str, float] = {}
        primary_drivers: List[str] = []

        # Quantify feature deltas if provided
        for k in ["llj_speed_kts", "ivt_kg_m_s", "vorticity_850", "rh850", "orographic_lift_index", "mslp_hpa"]:
            if k in init_f and k in target_f:
                delta = round(target_f[k] - init_f[k], 2)
                feature_deltas[k] = delta

        # Diagnose physical mechanisms
        if from_regime == to_regime:
            primary_drivers.append(f"Persistence of {from_regime.value} synoptic boundary forcings")
            narrative = f"The atmospheric flow pattern remains anchored in {from_regime.value} with strong physical persistence."
        elif from_regime == WeatherRegimeType.ACTIVE_MONSOON and to_regime == WeatherRegimeType.BREAK_MONSOON:
            primary_drivers.extend(["Monsoon trough northward migration to foothills", "Weakening Arabian Sea Low-Level Jet", "Positive MSLP departure over central India"])
            narrative = (
                "Transition from Active to Break Monsoon driven by northward shift of the monsoon trough axis "
                "towards the Himalayan foothills and a marked reduction in cross-equatorial low-level moisture transport."
            )
        elif from_regime == WeatherRegimeType.BREAK_MONSOON and to_regime == WeatherRegimeType.ACTIVE_MONSOON:
            primary_drivers.extend(["Southward trough axis revival", "Strengthening 850 hPa Somali Jet", "Enhanced moisture convergence"])
            narrative = (
                "Monsoon revival characterized by the re-establishment of the monsoon trough south of normal "
                "and an acceleration of the 850 hPa Low-Level Jet exceeding 25 knots."
            )
        elif from_regime == WeatherRegimeType.ACTIVE_MONSOON and to_regime == WeatherRegimeType.OROGRAPHIC_RAINFALL:
            primary_drivers.extend(["Enhanced orthogonal wind component against Western Ghats", "Deep atmospheric moisture saturation", "Strong orographic lift index"])
            narrative = (
                "Intense zonal westerlies impinging directly on the Western Ghats orography amplify convective precipitation "
                "via strong forced orographic ascent."
            )
        elif to_regime == WeatherRegimeType.MONSOON_LOW_LPS:
            primary_drivers.extend(["Mid-tropospheric cyclonic vorticity surge", "Central pressure deepening", "Bay of Bengal convective vortex genesis"])
            narrative = (
                "Cyclonic spin-up in the lower-to-middle troposphere accompanied by localized barometric pressure depression "
                "organizes active monsoon flow into a structured Low-Pressure System (LPS)."
            )
        elif to_regime == WeatherRegimeType.COASTAL_CONVERGENCE:
            primary_drivers.extend(["Offshore trough pressure gradient intensification", "Onshore moisture flux convergence", "Shallow coastal shear line"])
            narrative = (
                "Active offshore trough along the West Coast creates a localized coastal convergence zone "
                "trapping moisture and generating heavy coastal precipitation bands."
            )
        else:
            primary_drivers.append(f"Synoptic evolution from {from_regime.value} to {to_regime.value}")
            narrative = (
                f"Atmospheric thermodynamic and dynamic fields evolve from {from_regime.value} "
                f"into {to_regime.value} governed by regional monsoon circulation shifts."
            )

        return RegimeTransitionExplanation(
            current_regime=from_regime,
            next_regime=to_regime,
            transition_probability=round(float(transition_prob), 4),
            primary_drivers=primary_drivers,
            feature_deltas=feature_deltas,
            meteorological_narrative=narrative,
        )
