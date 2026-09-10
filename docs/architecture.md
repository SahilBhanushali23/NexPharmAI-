# NexPharmAI System Architecture

## Overview
NexPharmAI is an AI-powered pharmaceutical smart manufacturing platform designed for high-regulatory pharmaceutical production plants. It combines IoT machine telemetry, predictive failure modeling, anomaly detection, material-gated production scheduling, and automated rescheduling.

## High-Level Architecture
1. **Frontend**: Next.js 14+ (App Router), React, TypeScript, Pure CSS (No Tailwind).
2. **Backend**: FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0, Alembic.
3. **Database**: PostgreSQL 16 relational database with relational constraints and audit logs.
4. **Machine Learning Engines**:
   - Machine Failure Classification: XGBoost, Random Forest, LightGBM, CatBoost (Trained on AI4I 2020 + SMOTE).
   - Anomaly Detection: Isolation Forest for unsupervised process drift and outlier scoring.
   - Batch Quality Prediction: Process parameter modeling.
   - Demand Forecasting: Time-series projection models.
5. **Optimization Engine**:
   - Google OR-Tools Constraint Programming (CP-SAT) for multi-machine, multi-order production scheduling with maintenance windows and inventory constraints.
   - Dynamic rescheduling engine that reruns optimization upon critical machine health degradation or failure alerts.
