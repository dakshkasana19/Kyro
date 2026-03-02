"""
Kyro — Model Training Pipeline (NHAMCS + Synthetic Hybrid)

Trains an XGBoost severity classifier and Logistic Regression baseline.

Data strategy:
  Layer 1: Real NHAMCS 2022 Emergency Department data (if available)
  Layer 2: Synthetic severe-case augmentation (~20-30% of dataset)

Usage (standalone):
    python -m app.ai.train
    python -m app.ai.train --synthetic-only     # Without NHAMCS data
    python -m app.ai.train --nhamcs data/nhamcs_ed_2022.csv
"""

from __future__ import annotations

import argparse
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.ai.features import ALL_FEATURES, get_feature_names
from app.ai.synthetic_generator import generate_synthetic_emergency_data
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.train")


def _load_nhamcs_if_available(nhamcs_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Attempt to load real NHAMCS data. Tries preprocessed first, then raw."""
    from app.ai.nhamcs_loader import load_preprocessed_dataset, load_nhamcs_raw

    # Strategy 1: Use already-preprocessed dataset.csv (fast path)
    try:
        df = load_preprocessed_dataset(nhamcs_path)
        logger.info("Pre-processed NHAMCS data loaded: %d rows", len(df))
        return df
    except FileNotFoundError:
        logger.info("Pre-processed dataset not found, trying raw NHAMCS...")

    # Strategy 2: Process from raw ed2022.csv
    try:
        df = load_nhamcs_raw(nhamcs_path)
        logger.info("Raw NHAMCS data loaded & processed: %d rows", len(df))
        return df
    except FileNotFoundError as e:
        logger.warning("NHAMCS data not available: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to load NHAMCS data: %s", e)
        return None


def prepare_hybrid_dataset(
    nhamcs_path: Optional[str] = None,
    synthetic_ratio: float = 0.25,
    synthetic_samples: int = 3000,
    synthetic_only: bool = False,
) -> pd.DataFrame:
    """
    Build the hybrid training dataset.

    Strategy:
      1. Load real NHAMCS data (if available)
      2. Generate synthetic emergency data
      3. Merge, shuffle, and return

    Parameters
    ----------
    nhamcs_path : str, optional
        Path to NHAMCS CSV. If None, uses default.
    synthetic_ratio : float
        Target proportion of synthetic data (0.2–0.3).
    synthetic_samples : int
        Number of synthetic samples to generate.
    synthetic_only : bool
        If True, skip NHAMCS loading entirely.

    Returns
    -------
    pd.DataFrame with ALL_FEATURES columns + 'severity'.
    """
    frames = []

    # Layer 1: Real NHAMCS data
    if not synthetic_only:
        nhamcs_df = _load_nhamcs_if_available(nhamcs_path)
        if nhamcs_df is not None:
            # Ensure columns align
            feature_cols = get_feature_names()
            available = [c for c in feature_cols if c in nhamcs_df.columns]
            missing = set(feature_cols) - set(available)
            for col in missing:
                nhamcs_df[col] = 0
            frames.append(nhamcs_df[feature_cols + ["severity"]])
            logger.info("NHAMCS contributes %d rows", len(nhamcs_df))

    # Layer 2: Synthetic augmentation
    if frames:
        # Calculate synthetic count to reach target ratio
        real_count = sum(len(f) for f in frames)
        synth_count = int(real_count * synthetic_ratio / (1 - synthetic_ratio))
        synth_count = max(synth_count, 500)  # minimum synthetic samples
    else:
        synth_count = synthetic_samples
        logger.info("No real data — using synthetic-only mode (%d samples)", synth_count)

    synthetic_df = generate_synthetic_emergency_data(n_samples=synth_count, seed=42)
    feature_cols = get_feature_names()
    frames.append(synthetic_df[feature_cols + ["severity"]])
    logger.info("Synthetic data contributes %d rows", len(synthetic_df))

    # Merge and shuffle
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    logger.info(
        "Hybrid dataset: %d total rows | Severity distribution: %s",
        len(combined),
        combined["severity"].value_counts().sort_index().to_dict(),
    )
    return combined


def _compute_class_weights(y: pd.Series) -> dict:
    """Compute sample weights to boost minority classes (especially Critical)."""
    class_counts = y.value_counts().to_dict()
    total = len(y)
    n_classes = len(class_counts)
    weights = {}
    for cls, count in class_counts.items():
        weights[cls] = total / (n_classes * count)
    # Extra boost for Critical class
    if 3 in weights:
        weights[3] *= 1.5
    logger.info("Class weights: %s", {k: round(v, 3) for k, v in weights.items()})
    return weights


def train_model(
    data: Optional[pd.DataFrame] = None,
    nhamcs_path: Optional[str] = None,
    synthetic_only: bool = False,
) -> Tuple[XGBClassifier, LogisticRegression]:
    """
    Train XGBoost (primary) and Logistic Regression (baseline).

    Pipeline:
      1. Load/merge hybrid data
      2. Stratified train/test split
      3. Cross-validation
      4. Train XGBoost with class weighting
      5. Train Logistic Regression baseline
      6. Save all artifacts

    Returns
    -------
    (xgb_model, lr_model)
    """
    # Step 1: Prepare data
    if data is None:
        data = prepare_hybrid_dataset(
            nhamcs_path=nhamcs_path,
            synthetic_only=synthetic_only,
        )

    feature_cols = get_feature_names()
    X = data[feature_cols].copy()
    y = data["severity"].copy()

    # Step 2: Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    # Compute sample weights for training
    class_weights = _compute_class_weights(y_train)
    sample_weights = y_train.map(class_weights).values

    # Step 3: Train XGBoost with optimized hyperparameters
    xgb_model = XGBClassifier(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        subsample=0.8,
        colsample_bytree=0.8,
        gamma=2,
        reg_lambda=2,
        reg_alpha=0.5,
        min_child_weight=3,
        random_state=42,
        n_jobs=-1,
    )

    xgb_model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    xgb_preds = xgb_model.predict(X_test)
    xgb_report = classification_report(y_test, xgb_preds, zero_division=0)
    logger.info("XGBoost classification report:\n%s", xgb_report)

    # Step 4: Cross-validation (5-fold)
    logger.info("Running 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        xgb_model, X, y, cv=cv, scoring="f1_macro", n_jobs=-1,
    )
    logger.info("CV Macro F1: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())

    # Step 5: Logistic Regression baseline
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr_model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)
    lr_report = classification_report(y_test, lr_preds, zero_division=0)
    logger.info("Logistic Regression classification report:\n%s", lr_report)

    # Step 6: Save artifacts
    _save_artifacts(
        xgb_model, lr_model, scaler,
        feature_cols, X_train, X_test, y_test,
        xgb_preds, cv_scores,
    )

    return xgb_model, lr_model


def _save_artifacts(
    xgb_model: XGBClassifier,
    lr_model: LogisticRegression,
    scaler: StandardScaler,
    feature_cols: list,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    xgb_preds: np.ndarray,
    cv_scores: np.ndarray,
) -> None:
    """Save model files and metadata to disk."""
    artifact_dir = Path(settings.ai.MODEL_PATH).parent
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # XGBoost model
    xgb_model.save_model(settings.ai.MODEL_PATH)
    logger.info("XGBoost model saved → %s", settings.ai.MODEL_PATH)

    # Logistic Regression + Scaler (pickle)
    lr_path = artifact_dir / "lr_baseline_model.pkl"
    with open(lr_path, "wb") as f:
        pickle.dump({"model": lr_model, "scaler": scaler}, f)
    logger.info("LR baseline saved → %s", lr_path)

    # SHAP-ready feature importance
    importance = dict(zip(feature_cols, xgb_model.feature_importances_))
    importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    # Metadata
    meta = {
        "model_version": settings.ai.MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features": feature_cols,
        "n_features": len(feature_cols),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "severity_classes": {str(k): v for k, v in settings.ai.SEVERITY_CLASSES.items()},
        "cv_macro_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_macro_f1_std": round(float(cv_scores.std()), 4),
        "xgb_params": xgb_model.get_params(),
        "feature_importance_top10": dict(list(importance_sorted.items())[:10]),
        "class_distribution_test": {
            str(k): int(v) for k, v in
            pd.Series(y_test).value_counts().sort_index().items()
        },
    }
    meta_path = artifact_dir / "model_meta.json"

    # Handle numpy types for JSON serialization
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    meta_path.write_text(json.dumps(meta, indent=2, cls=NumpyEncoder))
    logger.info("Model metadata saved → %s", meta_path)


# ----------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Kyro — Train severity model")
    parser.add_argument(
        "--nhamcs", type=str, default=None,
        help="Path to NHAMCS 2022 CSV file",
    )
    parser.add_argument(
        "--synthetic-only", action="store_true",
        help="Train on synthetic data only (no NHAMCS)",
    )
    args = parser.parse_args()

    from app.core.logging import setup_logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("KYRO MODEL TRAINING PIPELINE")
    logger.info("=" * 60)

    xgb_model, lr_model = train_model(
        nhamcs_path=args.nhamcs,
        synthetic_only=args.synthetic_only,
    )

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)


# Allow: python -m app.ai.train
if __name__ == "__main__":
    main()
