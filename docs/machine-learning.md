# NexPharmAI Machine Learning Architecture

## Predictive Maintenance Pipeline
- **Dataset**: AI4I 2020 Predictive Maintenance Dataset (UCI Machine Learning Repository).
- **Features**:
  - `Type`: Machine quality variant (L/M/H), categorical one-hot encoded.
  - `Air temperature [K]`: Ambient thermal sensor.
  - `Process temperature [K]`: Working fluid/chamber sensor.
  - `Rotational speed [rpm]`: Spindle velocity.
  - `Torque [Nm]`: Mechanical torque load.
  - `Tool wear [min]`: Cumulative tool usage duration.
- **Target**: `Machine failure` (0 = Normal, 1 = Failure).
- **Data Preprocessing**:
  - Dropped identification and leak columns: `UDI`, `Product ID`, `TWF`, `HDF`, `PWF`, `OSF`, `RNF`.
  - 80/20 Stratified train/test split (`random_state=42`).
  - Class balancing using SMOTE (Synthetic Minority Over-sampling Technique) applied strictly to training folds.
- **Model Benchmark**:
  - XGBoost Classifier
  - Random Forest Classifier
  - LightGBM Classifier
  - CatBoost Classifier
  - Logistic Regression
- **Evaluation Criteria**:
  - Balanced Accuracy, Precision, Recall, F1, ROC-AUC, with primary emphasis on Failure Recall and Failure F1 to prevent undetected failures.

## Anomaly Detection Pipeline
- **Algorithm**: Isolation Forest (`scikit-learn`).
- **Objective**: Detect operational drift and abnormal multivariate patterns without requiring historical failure labels.
- **Output**: Normalized anomaly score (0.0 - 1.0) and severity classification:
  - `NORMAL`: Expected operational envelope.
  - `LOW`: Slight variance from baseline.
  - `MEDIUM`: Noticeable behavioral shift.
  - `HIGH`: High probability of anomalous behavior.
  - `CRITICAL`: Extreme outlier requiring immediate technical assessment.

## Batch Quality & Forecasting Pipelines
- Architecture created; training triggered when process quality and demand data streams are connected.
