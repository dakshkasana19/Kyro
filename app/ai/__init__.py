"""
AI Severity Prediction Engine.

Modules:
  features            — NHAMCS-aligned feature engineering
  nhamcs_loader       — Real NHAMCS 2022 data ingestion
  synthetic_generator — Emergency synthetic data generation
  train               — Hybrid training pipeline (XGBoost + LR)
  evaluate            — Full evaluation suite (metrics, plots, SHAP)
  inference           — Production inference + SHAP explanations
"""
