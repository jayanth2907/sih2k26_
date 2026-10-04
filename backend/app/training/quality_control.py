"""
Quality Control and Dataset Validation Engine for PS26080 Real-Data Training.
Audits NaN fractions, physical bounds, coordinate validity, and generates deterministic QC summaries.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.data.processing.quality_control import MeteorologicalQualityControl


class DatasetQCReport(BaseModel):
    """Forensic summary of quality control audit on training dataset."""
    records_total: int = Field(..., description="Total input records processed")
    records_valid: int = Field(..., description="Records passing all strict QC rules")
    records_rejected: int = Field(..., description="Records rejected due to physical or coordinate violations")
    missing_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of missing predictor fields")
    duplicate_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of duplicate timestamps/coordinates")
    out_of_range_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of values clamped or rejected")
    coverage_start: str = Field(..., description="Earliest valid timestamp (ISO UTC)")
    coverage_end: str = Field(..., description="Latest valid timestamp (ISO UTC)")
    spatial_coverage_cells: int = Field(..., description="Count of unique spatial grid points")
    qc_passed: bool = Field(..., description="Whether dataset is approved for model training")
    rejection_reasons: Dict[str, int] = Field(default_factory=dict, description="Breakdown of rejection causes")


class TrainingQualityController:
    """
    Validates meteorological training samples against physical bounds and data integrity standards.
    """

    def __init__(self, max_allowed_missing_pct: float = 0.05):
        self.max_allowed_missing_pct = max_allowed_missing_pct
        self.base_qc = MeteorologicalQualityControl()

    def audit_and_clean_records(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], DatasetQCReport]:
        """
        Audit a collection of raw training records, sanitize fields, and generate DatasetQCReport.
        """
        total = len(records)
        if total == 0:
            now_iso = datetime.now(timezone.utc).isoformat()
            empty_report = DatasetQCReport(
                records_total=0,
                records_valid=0,
                records_rejected=0,
                missing_fraction=0.0,
                duplicate_fraction=0.0,
                out_of_range_fraction=0.0,
                coverage_start=now_iso,
                coverage_end=now_iso,
                spatial_coverage_cells=0,
                qc_passed=False,
                rejection_reasons={"EMPTY_DATASET": 1},
            )
            return [], empty_report

        valid_records: List[Dict[str, Any]] = []
        seen_keys = set()
        duplicate_count = 0
        rejected_count = 0
        out_of_range_count = 0
        missing_values_count = 0
        total_fields_checked = 0
        rejection_reasons: Dict[str, int] = {}
        unique_cells = set()

        timestamps = []

        for r in records:
            t = r.get("timestamp") or r.get("valid_time")
            lat = r.get("latitude")
            lon = r.get("longitude")

            if not t or lat is None or lon is None:
                rejected_count += 1
                rejection_reasons["MISSING_COORDINATES"] = rejection_reasons.get("MISSING_COORDINATES", 0) + 1
                continue

            # Check duplicate
            key = (t, round(float(lat), 3), round(float(lon), 3))
            if key in seen_keys:
                duplicate_count += 1
                rejection_reasons["DUPLICATE_SAMPLE"] = rejection_reasons.get("DUPLICATE_SAMPLE", 0) + 1
                continue
            seen_keys.add(key)
            unique_cells.add((round(float(lat), 3), round(float(lon), 3)))
            timestamps.append(t)

            # Validate rainfall
            rain = r.get("rainfall") or r.get("observed_rainfall") or r.get("target_rainfall") or 0.0
            if rain < 0.0 or rain > 1500.0:
                out_of_range_count += 1
                rejection_reasons["RAINFALL_OUT_OF_BOUNDS"] = rejection_reasons.get("RAINFALL_OUT_OF_BOUNDS", 0) + 1
                continue

            # Check key predictors
            clean_rec = dict(r)
            clean_rec["rainfall"] = round(float(rain), 3)

            # Check for NaN or None in essential features
            essential_fields = ["u850", "v850", "temperature_850", "relative_humidity_850"]
            has_nan = False
            for f in essential_fields:
                total_fields_checked += 1
                val = r.get(f)
                if val is None:
                    missing_values_count += 1
                elif isinstance(val, (int, float)) and (val < -200.0 or val > 50000.0):
                    out_of_range_count += 1
                    has_nan = True

            if has_nan:
                rejected_count += 1
                rejection_reasons["UNREALISTIC_ATMOSPHERIC_VALUE"] = rejection_reasons.get("UNREALISTIC_ATMOSPHERIC_VALUE", 0) + 1
                continue

            valid_records.append(clean_rec)

        # Compute summary statistics
        valid_count = len(valid_records)
        missing_frac = (missing_values_count / max(1, total_fields_checked))
        dup_frac = duplicate_count / total
        oor_frac = out_of_range_count / total

        coverage_start = min(timestamps) if timestamps else datetime.now(timezone.utc).isoformat()
        coverage_end = max(timestamps) if timestamps else datetime.now(timezone.utc).isoformat()

        qc_passed = (valid_count > 0) and (missing_frac <= self.max_allowed_missing_pct)

        report = DatasetQCReport(
            records_total=total,
            records_valid=valid_count,
            records_rejected=rejected_count + duplicate_count,
            missing_fraction=round(missing_frac, 4),
            duplicate_fraction=round(dup_frac, 4),
            out_of_range_fraction=round(oor_frac, 4),
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            spatial_coverage_cells=len(unique_cells),
            qc_passed=qc_passed,
            rejection_reasons=rejection_reasons,
        )

        return valid_records, report
