"""Application configuration via environment variables."""
from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings:
    APP_NAME: str = "PulseML"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/pulseml.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # Drift thresholds
    KS_DRIFT_THRESHOLD: float = float(os.getenv("KS_DRIFT_THRESHOLD", "0.1"))
    PSI_DRIFT_THRESHOLD: float = float(os.getenv("PSI_DRIFT_THRESHOLD", "0.2"))
    CHISQ_PVALUE_THRESHOLD: float = float(os.getenv("CHISQ_PVALUE_THRESHOLD", "0.05"))
    PERFORMANCE_DROP_THRESHOLD: float = float(os.getenv("PERFORMANCE_DROP_THRESHOLD", "0.05"))

    # Minimum samples for drift analysis
    MIN_SAMPLES: int = int(os.getenv("MIN_SAMPLES", "50"))

settings = Settings()
