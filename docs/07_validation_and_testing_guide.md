# 07. Validation & Testing Guide

## 1. Validation Philosophy
Every module, pipeline stage, and model implementation must have clear, reproducible verification criteria to validate correctness prior to progression.

---

## 2. Validation Checklist by Module

### 2.1. Ingestion & Preprocessing
- [ ] Schema validation rejects missing required columns (`amount`, `date`, `description`).
- [ ] Text cleaning correctly strips special characters and standardizes case.
- [ ] Datetime parsing reliably handles multiple date formats without crashing.

### 2.2. Feature Engineering & Pipelines
- [ ] No data leakage across train and test partitions.
- [ ] Vectorizer handles unseen vocabulary gracefully during inference.
- [ ] Feature transformations output consistent dimensions matching model expectations.

### 2.3. Model Training & Inference
- [ ] Model converges with loss consistently decreasing during training.
- [ ] Accuracy and Macro F1 score exceed predetermined baseline thresholds.
- [ ] Single-sample inference latency is within acceptable limits (<50ms).
- [ ] Predictions return valid category labels and normalized confidence scores.

### 2.4. Data Persistence & Analytics
- [ ] Database transactions are atomic; rolled back on failure.
- [ ] Monthly aggregation sums strictly match the sum of constituent transactions.

---

## 3. How to Run Validation Tests
*(Test commands will be updated as the test suite is configured)*

```bash
# Run full unit and integration test suite
pytest tests/ -v

# Run data validation checks
pytest tests/test_data_pipeline.py -v

# Run model inference tests
pytest tests/test_model_inference.py -v
```

