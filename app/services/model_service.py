"""
Kyro — Model Lifecycle Service

Orchestrates AI model retraining:
  1. Process uploaded CSV training data
  2. Backup current model with version history
  3. Execute background training pipeline
  4. Hot-swap live inference engine
  5. Notify admins via WebSockets
"""

import os
import shutil
import threading
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.ai.train import train_model
from app.ai.inference import reload_model
from app.ai.features import RAW_FEATURES, compute_engineered_features, ALL_FEATURES
from app.core.config import settings
from app.core.logging import get_logger
from app.services.audit_service import log_event, AuditAction
from app.core.sockets import socketio

logger = get_logger("services.model")

HISTORY_DIR = Path("app/ai/history")
BACKUP_DIR = Path("app/ai/backups")
ARTIFACT_DIR = Path("app/ai/artifacts")

def retrain_from_csv(file_path: str, actor: str) -> str:
    """
    Staging point for model retraining.
    Validates data and kicks off a background training thread.
    Returns a tracking ID or raises an error.
    """
    # 1. Basic validation
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Invalid CSV file: {e}")

    # Check for required raw features + target
    required = RAW_FEATURES + ["severity"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

    # 2. Persist to history
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    history_path = HISTORY_DIR / f"dataset_{timestamp}.csv"
    df.to_csv(history_path, index=False)
    
    # 3. Start background training
    task_id = f"retrain_{timestamp}"
    thread = threading.Thread(
        target=_background_retrain_task,
        args=(df, actor, task_id)
    )
    thread.daemon = True
    thread.start()
    
    log_event(
        actor=actor,
        action=AuditAction.MODEL_RETRAIN_STARTED,
        resource="model",
        resource_id=task_id,
        metadata={"rows": len(df)}
    )
    
    return task_id

def _background_retrain_task(df: pd.DataFrame, actor: str, task_id: str):
    """Internal task runner for model training."""
    logger.info("Background retraining started [task=%s, actor=%s]", task_id, actor)
    socketio.emit("model:retrain_status", {"status": "processing", "taskId": task_id})
    
    try:
        # A. Pre-process / Feature Engineering
        # Users provide raw features, we need the full ALL_FEATURES for train_model
        df = compute_engineered_features(df)
        df = df[ALL_FEATURES + ["severity"]]
        
        # B. Backup Current Model
        model_path = Path(settings.ai.MODEL_PATH)
        if model_path.exists():
            backup_name = f"xgb_model_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy(model_path, BACKUP_DIR / backup_name)
            logger.info("Model backup created: %s", backup_name)

        # C. Run Training
        # This will save artifacts to settings.ai.MODEL_PATH (usually artifacts/xgb_severity_model.json)
        train_model(data=df)
        
        # D. Hot-Swap
        reload_model()
        logger.info("Model hot-swapped successfully")

        # E. Notify & Log
        socketio.emit("model:retrain_status", {
            "status": "success", 
            "taskId": task_id,
            "message": "AI model retrained and deployed."
        })
        
        log_event(
            actor=actor,
            action=AuditAction.MODEL_RETRAIN_SUCCESS,
            resource="model",
            resource_id=task_id,
            metadata={"backup": backup_name if model_path.exists() else None}
        )

    except Exception as e:
        logger.exception("Model retraining failed")
        socketio.emit("model:retrain_status", {
            "status": "error", 
            "taskId": task_id, 
            "message": str(e)
        })
        
        log_event(
            actor=actor,
            action=AuditAction.MODEL_RETRAIN_FAILED,
            resource="model",
            resource_id=task_id,
            metadata={"error": str(e)}
        )
