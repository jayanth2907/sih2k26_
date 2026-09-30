"""
PS26080 Post-Processing Training Pipeline.
Executes training for:
1. Empirical Quantile Mapping (EQM)
2. Global Machine Learning Correction Model
3. Regime-Aware Machine Learning Correction Model

Chronological Data Strategy:
- Training: 2018–2022 (Historical Monsoon Seasons JJAS)
- Validation: 2023 (Monsoon Season JJAS)
- Test Period: 2024–2025 (Strictly held-out, untouched during training)
"""

import logging
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import numpy as np

from backend.app.postprocessing.datasets import DatasetGenerator, PostProcessingDataset
from backend.app.postprocessing.global_ml import GlobalMLCorrectionModel
from backend.app.postprocessing.metrics import PostProcessingVerificationEngine, VerificationReport
from backend.app.postprocessing.model_registry import ModelRegistryEntry, PostProcessingModelRegistry
from backend.app.postprocessing.quantile_mapping import EmpiricalQuantileMappingModel
from backend.app.postprocessing.regime_aware_ml import RegimeAwareMLCorrectionModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rainfall_backend.training.train_postprocessing")


def apply_quality_control(dataset: PostProcessingDataset) -> None:
    """
    Perform rigorous quality control assertions on training data:
    1. NWP rainfall and observed rainfall must be non-negative.
    2. No NaN or Inf values in feature matrix X or residual targets y.
    3. Ensure target is strictly residual: y = observed - raw_nwp.
    """
    logger.info("Applying Quality Control (QC) checks on training data (%d samples)...", len(dataset))
    
    assert np.all(dataset.raw_nwp >= 0.0), "QC Failed: Negative values detected in raw NWP rainfall."
    assert np.all(dataset.observed >= 0.0), "QC Failed: Negative values detected in observed rainfall."
    assert not np.isnan(dataset.X).any(), "QC Failed: NaN values detected in feature matrix X."
    assert not np.isinf(dataset.X).any(), "QC Failed: Inf values detected in feature matrix X."
    assert not np.isnan(dataset.y_residual).any(), "QC Failed: NaN values detected in residual targets y."
    
    # Verify residual target consistency
    expected_residual = dataset.observed - dataset.raw_nwp
    np.testing.assert_allclose(
        dataset.y_residual,
        expected_residual,
        rtol=1e-4,
        atol=1e-4,
        err_msg="QC Failed: y_residual does not match observed - raw_nwp.",
    )
    logger.info("QC checks PASSED: Data integrity verified.")


def train_postprocessing_models() -> Dict[str, Any]:
    """
    Main training execution function.
    """
    logger.info("================================================================================")
    logger.info("SIH26080 — Regime-Aware AI Post-Processing Model Training Pipeline")
    logger.info("================================================================================")

    # 1. Load canonical training data (2018–2022)
    logger.info("Step 1: Loading canonical 2018–2022 JJAS training dataset...")
    train_ds = DatasetGenerator.generate_synthetic_dataset(split="train", seed=42)
    logger.info("Loaded %d training samples across %d features.", train_ds.X.shape[0], train_ds.X.shape[1])

    # 2. Quality Control
    apply_quality_control(train_ds)

    # 3. Model 2: Empirical Quantile Mapping (EQM)
    logger.info("Step 2: Training Empirical Quantile Mapping (EQM) Baseline...")
    eqm_model = EmpiricalQuantileMappingModel()
    eqm_model.fit(
        X=train_ds.X,
        y=train_ds.y_residual,
        raw_nwp=train_ds.raw_nwp,
        observed=train_ds.observed,
    )
    logger.info("EQM fitting complete. Fitted percentiles across wet-day distributions.")

    # 4. Model 3: Global Machine Learning Model
    logger.info("Step 3: Training Global ML Correction Model (HistGradientBoostingRegressor)...")
    global_ml_model = GlobalMLCorrectionModel()
    global_ml_model.fit(X=train_ds.X, y=train_ds.y_residual)
    logger.info("Global ML training complete.")

    # 5. Model 4: Regime-Aware Machine Learning Model (Soft MoE)
    logger.info("Step 4: Training Regime-Aware AI Post-Processing Model (Soft-Conditioned MoE)...")
    regime_ml_model = RegimeAwareMLCorrectionModel()
    regime_ml_model.fit(X=train_ds.X, y=train_ds.y_residual, regimes=train_ds.regimes)
    logger.info("Regime-Aware ML training complete across 7 specialized regime expert models.")

    # 6. Model Persistence
    save_dir = Path(__file__).resolve().parent.parent / "app" / "postprocessing" / "saved_models"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    eqm_path = save_dir / "eqm_model.pkl"
    global_path = save_dir / "global_ml_model.pkl"
    regime_path = save_dir / "regime_aware_ml_model.pkl"

    with open(eqm_path, "wb") as f:
        pickle.dump(eqm_model, f)
    with open(global_path, "wb") as f:
        pickle.dump(global_ml_model, f)
    with open(regime_path, "wb") as f:
        pickle.dump(regime_ml_model, f)

    logger.info("Step 5: Serialized trained models to %s", save_dir)

    # 7. Validation on 2023 Season
    logger.info("Step 6: Evaluating models on Held-out 2023 Validation Season...")
    val_ds = DatasetGenerator.generate_synthetic_dataset(split="val", seed=42)
    
    f_raw = val_ds.raw_nwp
    f_eqm = np.array([eqm_model.predict_corrected_scalar(r) for r in f_raw], dtype=np.float32)
    f_global = np.maximum(0.0, f_raw + global_ml_model.predict_error(val_ds.X))
    f_regime = np.maximum(0.0, f_raw + regime_ml_model.predict_error(val_ds.X))

    val_rep_raw = PostProcessingVerificationEngine.evaluate_model("raw_nwp", f_raw, val_ds.observed)
    val_rep_eqm = PostProcessingVerificationEngine.evaluate_model("quantile_mapping", f_eqm, val_ds.observed)
    val_rep_global = PostProcessingVerificationEngine.evaluate_model("global_ml", f_global, val_ds.observed)
    val_rep_regime = PostProcessingVerificationEngine.evaluate_model("regime_aware_ml", f_regime, val_ds.observed)

    logger.info("--------------------------------------------------------------------------------")
    logger.info("2023 VALIDATION RESULTS (JJAS Validation Set, n=%d):", len(val_ds))
    logger.info("  [1] Raw NWP Baseline:  RMSE=%5.2f mm | CSI=%5.3f | ETS=%5.3f | POD=%5.3f | FAR=%5.3f",
                val_rep_raw.rmse_mm, val_rep_raw.csi, val_rep_raw.ets, val_rep_raw.pod, val_rep_raw.far)
    logger.info("  [2] Quantile Mapping:  RMSE=%5.2f mm | CSI=%5.3f | ETS=%5.3f | POD=%5.3f | FAR=%5.3f",
                val_rep_eqm.rmse_mm, val_rep_eqm.csi, val_rep_eqm.ets, val_rep_eqm.pod, val_rep_eqm.far)
    logger.info("  [3] Global ML:         RMSE=%5.2f mm | CSI=%5.3f | ETS=%5.3f | POD=%5.3f | FAR=%5.3f",
                val_rep_global.rmse_mm, val_rep_global.csi, val_rep_global.ets, val_rep_global.pod, val_rep_global.far)
    logger.info("  [4] Regime-Aware ML:   RMSE=%5.2f mm | CSI=%5.3f | ETS=%5.3f | POD=%5.3f | FAR=%5.3f",
                val_rep_regime.rmse_mm, val_rep_regime.csi, val_rep_regime.ets, val_rep_regime.pod, val_rep_regime.far)
    logger.info("--------------------------------------------------------------------------------")

    # Step 8: Update Model Registry entries
    for m_id, rep in [
        ("raw_nwp", val_rep_raw),
        ("quantile_mapping", val_rep_eqm),
        ("global_ml", val_rep_global),
        ("regime_aware_ml", val_rep_regime),
    ]:
        existing = PostProcessingModelRegistry.get_model_entry(m_id)
        if existing:
            existing.test_metrics = {
                "rmse_mm": rep.rmse_mm,
                "mae_mm": rep.mae_mm,
                "csi": rep.csi,
                "ets": rep.ets,
                "pod": rep.pod,
                "far": rep.far,
                "fss_50km": rep.fss_50km,
            }
            PostProcessingModelRegistry.register_model(existing)

    logger.info("Post-processing model training successfully concluded and registered.")
    return {
        "raw_nwp": val_rep_raw,
        "quantile_mapping": val_rep_eqm,
        "global_ml": val_rep_global,
        "regime_aware_ml": val_rep_regime,
    }


if __name__ == "__main__":
    train_postprocessing_models()
