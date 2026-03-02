"""
Kyro — Emergency Synthetic Data Generator

Generates realistic synthetic emergency department cases
to augment real NHAMCS data.

Produces physiologically coherent patient records with
medically-grounded severity labels.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from app.ai.features import (
    CHRONIC_CONDITION_COLS,
    compute_engineered_features,
)
from app.core.logging import get_logger

logger = get_logger("ai.synthetic")


def generate_synthetic_emergency_data(
    n_samples: int = 3000,
    seed: int = 42,
    class_distribution: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Generate synthetic emergency department cases.

    Class distribution targets (default):
      Low    ~ 40%
      Medium ~ 30%
      High   ~ 20%
      Critical ~10%

    Returns
    -------
    pd.DataFrame with all RAW + ENGINEERED feature columns + severity.
    """
    if class_distribution is None:
        class_distribution = {0: 0.40, 1: 0.30, 2: 0.20, 3: 0.10}

    rng = np.random.RandomState(seed)

    # Allocate samples per class
    n_per_class = {
        cls: int(n_samples * pct) for cls, pct in class_distribution.items()
    }
    # Adjust rounding remainder
    remainder = n_samples - sum(n_per_class.values())
    n_per_class[0] += remainder

    frames = []
    for cls, count in n_per_class.items():
        df = _generate_class(cls, count, rng)
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)

    # Shuffle
    data = data.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Compute engineered features
    data = compute_engineered_features(data)

    logger.info(
        "Synthetic data generated: %d samples | Distribution: %s",
        len(data),
        data["severity"].value_counts().sort_index().to_dict(),
    )
    return data


def _generate_class(cls: int, n: int, rng: np.random.RandomState) -> pd.DataFrame:
    """Generate n samples for a specific severity class with realistic vitals."""

    if cls == 0:
        return _generate_low(n, rng)
    elif cls == 1:
        return _generate_medium(n, rng)
    elif cls == 2:
        return _generate_high(n, rng)
    else:
        return _generate_critical(n, rng)


def _base_demographics(n: int, rng: np.random.RandomState, age_range=(18, 90)) -> dict:
    """Generate common demographic fields."""
    return {
        "age": rng.randint(age_range[0], age_range[1] + 1, n),
        "gender": rng.randint(0, 2, n),  # 0=Female, 1=Male
    }


def _generate_chronic_conditions(n: int, rng: np.random.RandomState, prob: float = 0.1) -> dict:
    """Generate binary chronic condition flags."""
    return {col: rng.binomial(1, prob, n) for col in CHRONIC_CONDITION_COLS}


# ----------------------------------------------------------------
# Low severity (class 0) — stable vitals, no admission
# ----------------------------------------------------------------
def _generate_low(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    data = _base_demographics(n, rng, age_range=(18, 70))
    data.update({
        "temperature": rng.normal(98.2, 0.5, n).clip(97.0, 99.5),
        "heart_rate": rng.normal(75, 10, n).clip(55, 95),
        "respiratory_rate": rng.normal(16, 2, n).clip(12, 20),
        "systolic_bp": rng.normal(120, 10, n).clip(100, 140),
        "diastolic_bp": rng.normal(78, 8, n).clip(60, 90),
        "pain_scale": rng.choice(range(0, 5), n),
        "immediate_triage": np.zeros(n, dtype=int),
        "arrival_by_ems": rng.binomial(1, 0.05, n),
    })
    data.update(_generate_chronic_conditions(n, rng, prob=0.05))
    data["severity"] = 0
    return pd.DataFrame(data)


# ----------------------------------------------------------------
# Medium severity (class 1) — moderately abnormal
# ----------------------------------------------------------------
def _generate_medium(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    data = _base_demographics(n, rng, age_range=(25, 80))
    data.update({
        "temperature": rng.normal(99.5, 1.0, n).clip(98.0, 101.5),
        "heart_rate": rng.normal(95, 12, n).clip(70, 120),
        "respiratory_rate": rng.normal(20, 3, n).clip(14, 28),
        "systolic_bp": rng.normal(110, 15, n).clip(90, 145),
        "diastolic_bp": rng.normal(75, 10, n).clip(55, 95),
        "pain_scale": rng.choice(range(4, 8), n),
        "immediate_triage": np.zeros(n, dtype=int),
        "arrival_by_ems": rng.binomial(1, 0.2, n),
    })
    data.update(_generate_chronic_conditions(n, rng, prob=0.15))
    data["severity"] = 1
    return pd.DataFrame(data)


# ----------------------------------------------------------------
# High severity (class 2) — admitted, multiple comorbidities
# ----------------------------------------------------------------
def _generate_high(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    data = _base_demographics(n, rng, age_range=(40, 90))
    data.update({
        "temperature": rng.normal(100.5, 1.5, n).clip(98.0, 104.0),
        "heart_rate": rng.normal(115, 15, n).clip(85, 145),
        "respiratory_rate": rng.normal(24, 4, n).clip(16, 35),
        "systolic_bp": rng.normal(100, 18, n).clip(80, 170),
        "diastolic_bp": rng.normal(68, 12, n).clip(45, 100),
        "pain_scale": rng.choice(range(6, 10), n),
        "immediate_triage": rng.binomial(1, 0.15, n),
        "arrival_by_ems": rng.binomial(1, 0.5, n),
    })
    data.update(_generate_chronic_conditions(n, rng, prob=0.35))
    data["severity"] = 2
    return pd.DataFrame(data)


# ----------------------------------------------------------------
# Critical severity (class 3) — extreme vitals, immediate care
# ----------------------------------------------------------------
def _generate_critical(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    data = _base_demographics(n, rng, age_range=(30, 90))

    # Mix of shock (low BP + high HR) and severe presentations
    data.update({
        "temperature": rng.normal(102.0, 2.0, n).clip(95.0, 106.0),
        "heart_rate": rng.normal(140, 20, n).clip(100, 200),
        "respiratory_rate": rng.normal(30, 5, n).clip(20, 45),
        "systolic_bp": rng.normal(75, 12, n).clip(50, 100),
        "diastolic_bp": rng.normal(45, 10, n).clip(25, 65),
        "pain_scale": rng.choice(range(8, 11), n),
        "immediate_triage": rng.binomial(1, 0.85, n),
        "arrival_by_ems": rng.binomial(1, 0.8, n),
    })
    data.update(_generate_chronic_conditions(n, rng, prob=0.45))
    data["severity"] = 3
    return pd.DataFrame(data)
