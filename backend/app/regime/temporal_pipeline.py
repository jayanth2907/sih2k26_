"""
Unified Temporal Regime Pipeline Coordinator for PS26080.
Orchestrates snapshot classification, sequence extraction, Markov transitions,
persistence profiling, and Day 1–10 probability forecasting.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from backend.app.regime.regime_classifier import WeatherRegimeClassifier
from backend.app.regime.transition_engine import MarkovRegimeTransitionModel
from backend.app.regime.transition_explainer import RegimeTransitionExplainer
from backend.app.schemas.common import Coordinates
from backend.app.schemas.regime import WeatherRegimeType
from backend.app.schemas.regime_temporal import (
    Day10RegimeForecastResponse,
    RegimeFeatureSnapshot,
    RegimeForecastMode,
    RegimePersistenceReport,
    RegimeSequence,
    RegimeSequenceStep,
    RegimeState,
    RegimeTransitionExplanation,
    RegimeTransitionMatrix,
)


class TemporalRegimePipeline:
    """
    Coordinates temporal weather regime intelligence across classification,
    Markov transition propagation, and explainable feature deltas.
    """

    def __init__(self, transition_model: Optional[MarkovRegimeTransitionModel] = None):
        self.transition_model = transition_model or MarkovRegimeTransitionModel()
        self.explainer = RegimeTransitionExplainer()

    def get_regime_sequence(
        self,
        start_date: str,
        end_date: str,
        coordinates: Optional[Coordinates] = None,
    ) -> RegimeSequence:
        """
        Generate a multi-day temporal sequence of regime states.
        """
        start_dt = datetime.strptime(start_date[:10], "%Y-%m-%d")
        end_dt = datetime.strptime(end_date[:10], "%Y-%m-%d")
        days = max(1, min(30, (end_dt - start_dt).days + 1))

        # Sample plausible synoptic evolution: Active -> Active+Orographic -> Orographic -> Coastal
        trajectory_patterns = [
            WeatherRegimeType.ACTIVE_MONSOON,
            WeatherRegimeType.ACTIVE_MONSOON,
            WeatherRegimeType.OROGRAPHIC_RAINFALL,
            WeatherRegimeType.OROGRAPHIC_RAINFALL,
            WeatherRegimeType.COASTAL_CONVERGENCE,
            WeatherRegimeType.MONSOON_LOW_LPS,
            WeatherRegimeType.ACTIVE_MONSOON,
        ]

        steps: List[RegimeSequenceStep] = []
        for i in range(days):
            cur_dt = start_dt + timedelta(days=i)
            prim_regime = trajectory_patterns[i % len(trajectory_patterns)]
            
            # Formulate probabilities
            probs = {r.value: 0.05 for r in MarkovRegimeTransitionModel.REGIMES}
            probs[prim_regime.value] = 0.70
            # Normalize
            total_p = sum(probs.values())
            probs = {k: round(v / total_p, 3) for k, v in probs.items()}

            secondary = [WeatherRegimeType.OROGRAPHIC_RAINFALL] if prim_regime == WeatherRegimeType.ACTIVE_MONSOON else []

            steps.append(
                RegimeSequenceStep(
                    step_index=i,
                    timestamp=f"{cur_dt.strftime('%Y-%m-%d')}T00:00:00Z",
                    primary_regime=prim_regime,
                    secondary_regimes=secondary,
                    probabilities=probs,
                    confidence=0.88,
                )
            )

        summary = f"Temporal trajectory spanning {days} days showing active monsoon pulse transitioning through orographic enhancement."

        return RegimeSequence(
            sequence_id=f"SEQ_{start_date[:10]}_{end_date[:10]}",
            start_time=f"{start_date[:10]}T00:00:00Z",
            end_time=f"{end_date[:10]}T00:00:00Z",
            total_steps=len(steps),
            steps=steps,
            dominant_trajectory_summary=summary,
        )

    def get_transition_matrix(self) -> RegimeTransitionMatrix:
        """Retrieve the empirical 7x7 Markov transition matrix."""
        return self.transition_model.get_transition_matrix_schema()

    def get_persistence_report(self) -> RegimePersistenceReport:
        """Retrieve empirical persistence probabilities and median durations."""
        return self.transition_model.get_persistence_report()

    def forecast_day_1_10(
        self,
        current_regime: WeatherRegimeType,
        current_probabilities: Optional[Dict[str, float]] = None,
        init_time_iso: Optional[str] = None,
        mode: RegimeForecastMode = RegimeForecastMode.TRANSITION_BASED_PROJECTION,
    ) -> Day10RegimeForecastResponse:
        """Generate Day 1–10 temporal regime projections."""
        return self.transition_model.generate_day_1_10_projection(
            current_regime=current_regime,
            current_probabilities=current_probabilities,
            init_time_iso=init_time_iso,
            mode=mode,
        )

    def explain_transition(
        self,
        from_regime: WeatherRegimeType,
        to_regime: WeatherRegimeType,
        initial_features: Optional[Dict[str, float]] = None,
        target_features: Optional[Dict[str, float]] = None,
    ) -> RegimeTransitionExplanation:
        """Generate physically grounded transition explanation."""
        # Lookup transition probability from matrix
        mat_schema = self.transition_model.get_transition_matrix_schema()
        prob = mat_schema.transition_probabilities.get(from_regime.value, {}).get(to_regime.value, 0.15)

        return self.explainer.explain_transition(
            from_regime=from_regime,
            to_regime=to_regime,
            transition_prob=prob,
            initial_features=initial_features,
            target_features=target_features,
        )
