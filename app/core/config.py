"""
Kyro — Core Application Configuration

Loads environment variables and provides typed config objects.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class FlaskConfig:
    """Flask server configuration."""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))


@dataclass(frozen=True)
class SupabaseConfig:
    """Supabase connection configuration."""
    URL: str = os.getenv("SUPABASE_URL", "")
    KEY: str = os.getenv("SUPABASE_KEY", "")
    JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    def validate(self) -> None:
        if not self.URL or not self.KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment. "
                "Copy .env.example to .env and fill in your Supabase credentials."
            )


@dataclass(frozen=True)
class AIConfig:
    """AI model configuration."""
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/ai/artifacts/xgb_severity_model.json")
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "1.0.0")
    SEVERITY_CLASSES: dict = field(default_factory=lambda: {
        0: "Low",
        1: "Medium",
        2: "High",
        3: "Critical",
    })
    # Feature configuration (NHAMCS-aligned)
    NUMERICAL_FEATURES: list = field(default_factory=lambda: [
        "age", "gender",
        "temperature", "heart_rate", "respiratory_rate",
        "systolic_bp", "diastolic_bp", "pain_scale",
        "immediate_triage", "arrival_by_ems",
    ])
    CHRONIC_CONDITION_FEATURES: list = field(default_factory=lambda: [
        "asthma", "cancer", "ckd", "copd", "chf", "cad",
        "diabetes_type1", "diabetes_type2", "esrd", "htn", "obesity", "osa",
    ])
    ENGINEERED_FEATURES: list = field(default_factory=lambda: [
        "shock_index", "mean_arterial_pressure",
        "tachycardia_flag", "hypotension_flag",
        "fever_flag", "high_pain_flag",
        "chronic_burden_score",
    ])
    # Data paths
    NHAMCS_DATA_PATH: str = os.getenv("NHAMCS_DATA_PATH", "app/ai/dataset.csv")
    NHAMCS_RAW_PATH: str = os.getenv("NHAMCS_RAW_PATH", "app/ai/ed2022.csv")


@dataclass(frozen=True)
class LogConfig:
    """Logging configuration."""
    LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    FILE: str = os.getenv("LOG_FILE", "logs/kyro.log")


class Settings:
    """Aggregated application settings — single source of truth."""

    def __init__(self) -> None:
        self.flask = FlaskConfig()
        self.supabase = SupabaseConfig()
        self.ai = AIConfig()
        self.log = LogConfig()

    def validate(self) -> None:
        """Run all configuration validations."""
        self.supabase.validate()


# Singleton
settings = Settings()
