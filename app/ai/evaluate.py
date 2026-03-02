"""
Kyro — Model Evaluation Module

Comprehensive evaluation suite for the severity prediction model:
  • Accuracy, Macro F1, Weighted F1
  • Per-class recall (critical focus)
  • Confusion matrix
  • ROC curves per class
  • SHAP feature importance summary

Usage:
    python -m app.ai.evaluate
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from xgboost import XGBClassifier

from app.ai.features import get_feature_names
from app.ai.train import prepare_hybrid_dataset
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.evaluate")

SEVERITY_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
OUTPUT_DIR = Path("app/ai/artifacts/eval_reports")


def evaluate_model(
    data: Optional[pd.DataFrame] = None,
    model_path: Optional[str] = None,
    save_plots: bool = True,
) -> Dict[str, Any]:
    """
    Run full evaluation on the trained XGBoost model.

    Parameters
    ----------
    data : DataFrame, optional
        If None, uses the hybrid dataset (test split).
    model_path : str, optional
        Path to saved model. Uses config default if None.
    save_plots : bool
        Whether to save confusion matrix and ROC plots.

    Returns
    -------
    dict with all evaluation metrics.
    """
    # Load model
    model_file = model_path or settings.ai.MODEL_PATH
    model = XGBClassifier()
    model.load_model(model_file)
    logger.info("Model loaded from %s", model_file)

    # Load data
    if data is None:
        data = prepare_hybrid_dataset()

    feature_cols = get_feature_names()
    X = data[feature_cols]
    y = data["severity"]

    # Use 20% holdout (same split as training)
    from sklearn.model_selection import train_test_split
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # ---- Metrics ----
    results: Dict[str, Any] = {}

    results["accuracy"] = round(accuracy_score(y_test, y_pred), 4)
    results["macro_f1"] = round(f1_score(y_test, y_pred, average="macro", zero_division=0), 4)
    results["weighted_f1"] = round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4)

    # Per-class recall
    per_class_recall = recall_score(y_test, y_pred, average=None, zero_division=0)
    results["recall_per_class"] = {
        SEVERITY_LABELS.get(i, str(i)): round(float(r), 4)
        for i, r in enumerate(per_class_recall)
    }
    results["recall_critical"] = results["recall_per_class"].get("Critical", 0.0)

    # Classification report
    report = classification_report(
        y_test, y_pred,
        target_names=list(SEVERITY_LABELS.values()),
        zero_division=0,
        output_dict=True,
    )
    results["classification_report"] = report

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    results["confusion_matrix"] = cm.tolist()

    # ROC AUC (one-vs-rest)
    try:
        roc_auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
        results["roc_auc_macro"] = round(float(roc_auc), 4)
    except Exception as e:
        logger.warning("ROC AUC calculation failed: %s", e)
        results["roc_auc_macro"] = None

    # Log critical metrics
    logger.info("=" * 50)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 50)
    logger.info("Accuracy:         %.4f", results["accuracy"])
    logger.info("Macro F1:         %.4f", results["macro_f1"])
    logger.info("Weighted F1:      %.4f", results["weighted_f1"])
    logger.info("Critical Recall:  %.4f", results["recall_critical"])
    if results["roc_auc_macro"]:
        logger.info("ROC AUC (macro):  %.4f", results["roc_auc_macro"])
    logger.info("Recall per class: %s", results["recall_per_class"])
    logger.info(
        "Classification report:\n%s",
        classification_report(
            y_test, y_pred,
            target_names=list(SEVERITY_LABELS.values()),
            zero_division=0,
        ),
    )

    # Check critical recall target
    if results["recall_critical"] >= 0.85:
        logger.info("✓ Critical recall target MET (>=0.85)")
    else:
        logger.warning("✗ Critical recall BELOW target: %.4f < 0.85", results["recall_critical"])

    # Save plots
    if save_plots:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        _plot_confusion_matrix(cm, y_test, y_pred)
        _plot_roc_curves(y_test, y_proba)
        _plot_shap_importance(model, X_test)

    # Save JSON report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "evaluation_report.json"
    report_path.write_text(json.dumps(results, indent=2))
    logger.info("Evaluation report saved → %s", report_path)

    return results


def _plot_confusion_matrix(cm: np.ndarray, y_test, y_pred) -> None:
    """Save confusion matrix heatmap."""
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        labels = list(SEVERITY_LABELS.values())
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)
        ax.set(
            xticks=np.arange(len(labels)),
            yticks=np.arange(len(labels)),
            xticklabels=labels,
            yticklabels=labels,
            ylabel="True",
            xlabel="Predicted",
            title="Severity Prediction — Confusion Matrix",
        )
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        # Add text annotations
        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], "d"),
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black")

        fig.tight_layout()
        path = OUTPUT_DIR / "confusion_matrix.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        logger.info("Confusion matrix plot saved → %s", path)
    except Exception as e:
        logger.warning("Failed to plot confusion matrix: %s", e)


def _plot_roc_curves(y_test, y_proba: np.ndarray) -> None:
    """Save per-class ROC curves."""
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["green", "orange", "red", "darkred"]

        for i, (label, color) in enumerate(zip(SEVERITY_LABELS.values(), colors)):
            y_binary = (np.array(y_test) == i).astype(int)
            if y_binary.sum() == 0:
                continue
            fpr, tpr, _ = roc_curve(y_binary, y_proba[:, i])
            auc = roc_auc_score(y_binary, y_proba[:, i])
            ax.plot(fpr, tpr, color=color, label=f"{label} (AUC={auc:.3f})")

        ax.plot([0, 1], [0, 1], "k--", alpha=0.3)
        ax.set(
            xlabel="False Positive Rate",
            ylabel="True Positive Rate",
            title="ROC Curves — Per Severity Class",
        )
        ax.legend(loc="lower right")
        fig.tight_layout()
        path = OUTPUT_DIR / "roc_curves.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        logger.info("ROC curves saved → %s", path)
    except Exception as e:
        logger.warning("Failed to plot ROC curves: %s", e)


def _plot_shap_importance(model: XGBClassifier, X_test: pd.DataFrame) -> None:
    """Save SHAP feature importance summary plot."""
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test.iloc[:200])  # Limit for performance

        fig, ax = plt.subplots(figsize=(10, 8))
        # For multi-class, pick class 3 (Critical) for SHAP bar plot
        if isinstance(shap_values, list) and len(shap_values) > 3:
            shap.summary_plot(
                shap_values[3], X_test.iloc[:200],
                feature_names=get_feature_names(),
                show=False, plot_type="bar",
            )
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # shap >= 0.45: shape (n_samples, n_features, n_classes)
            shap.summary_plot(
                shap_values[:, :, 3], X_test.iloc[:200],
                feature_names=get_feature_names(),
                show=False, plot_type="bar",
            )
        else:
            shap.summary_plot(
                shap_values, X_test.iloc[:200],
                feature_names=get_feature_names(),
                show=False, plot_type="bar",
            )

        path = OUTPUT_DIR / "shap_importance.png"
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close("all")
        logger.info("SHAP importance plot saved → %s", path)
    except Exception as e:
        logger.warning("Failed to plot SHAP importance: %s", e)


# CLI entry point
if __name__ == "__main__":
    from app.core.logging import setup_logging
    setup_logging()
    evaluate_model()
