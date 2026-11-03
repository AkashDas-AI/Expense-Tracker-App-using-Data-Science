"""
Anomaly Detection Module

Author: Akash Das
Description: Statistical outlier detection baselines (IQR and Z-score) and unsupervised
             multivariate anomaly detection using Isolation Forest, with strict separation
             from ground-truth evaluation labels.
"""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

from expense_tracker.config.settings import RANDOM_SEED
from expense_tracker.features.feature_engineering import (
    engineer_features,
    extract_ground_truth_labels,
    get_model_feature_matrix,
)


def detect_outliers_statistical(
    df: pd.DataFrame,
    method: str = "iqr",
    threshold: float = 1.5,
    column: str = "amount",
    upper_only: bool = True,
) -> pd.Series:
    """Detect unusual transaction amounts using statistical baselines (Tukey's IQR or Z-score).

    Serves as an intuitive univariate benchmark against which multivariate ML models can be compared.

    Args:
        df: Input DataFrame containing numeric transaction column.
        method: Statistical method ('iqr' or 'zscore'). Defaults to 'iqr'.
        threshold: Scale multiplier (1.5 for standard IQR fence; 3.0 for standard Z-score).
        column: Column name to evaluate (defaults to 'amount').
        upper_only: If True, flags only upper-tail spikes (spending spikes). If False, flags both tails.

    Returns:
        pd.Series: Boolean Series where True indicates a statistical outlier.

    Raises:
        TypeError: If df is not a pandas DataFrame.
        ValueError: If method is unsupported or column not present in df.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty or column not in df.columns:
        return pd.Series(False, index=df.index, dtype=bool)

    method_clean = method.strip().lower()
    if method_clean not in ("iqr", "zscore"):
        raise ValueError(f"Unsupported outlier detection method '{method}'. Supported: 'iqr', 'zscore'.")

    series = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    if len(series) < 4 or series.nunique() <= 1:
        return pd.Series(False, index=df.index, dtype=bool)

    if method_clean == "iqr":
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + threshold * iqr
        lower_bound = q1 - threshold * iqr

        if upper_only:
            outlier_mask = series > upper_bound
        else:
            outlier_mask = (series > upper_bound) | (series < lower_bound)

    else:  # zscore
        mean = series.mean()
        std = series.std(ddof=1)
        if std == 0.0 or np.isnan(std):
            return pd.Series(False, index=df.index, dtype=bool)

        z = (series - mean) / std
        if upper_only:
            outlier_mask = z > threshold
        else:
            outlier_mask = z.abs() > threshold

    return outlier_mask.astype(bool)


def train_isolation_forest(
    matrix: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = RANDOM_SEED,
    n_estimators: int = 100,
    **kwargs: Any,
) -> IsolationForest:
    """Train an Isolation Forest model on an approved numeric feature matrix.

    Preprocessing:
    - Imputes missing values arising from early rolling lookback periods with 0.0
      (representing zero prior expenditure history).
    - Uses reproducible random_state to ensure deterministic tree partitioning.

    Args:
        matrix: Clean numeric modeling feature matrix (strictly devoid of identifiers or text).
        contamination: Expected proportion of outliers in the dataset (float in (0, 0.5]).
        random_state: Integer seed for reproducible random partitioning.
        n_estimators: Number of isolation trees in the ensemble.
        **kwargs: Additional keyword arguments passed to IsolationForest.

    Returns:
        Fitted IsolationForest instance.

    Raises:
        TypeError: If matrix is not a pandas DataFrame.
        ValueError: If matrix is empty or contamination is out of bounds.
    """
    if not isinstance(matrix, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(matrix).__name__}.")

    if matrix.empty:
        raise ValueError("Cannot train Isolation Forest on an empty feature matrix.")

    if not (0.0 < contamination <= 0.5):
        raise ValueError(f"Contamination parameter must be in (0, 0.5], got {contamination}.")

    # Deliberate imputation for initial lag/rolling warmup rows
    clean_matrix = matrix.fillna(0.0)

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=n_estimators,
        **kwargs,
    )
    model.fit(clean_matrix)
    return model


def detect_anomalies_isolation_forest(
    df: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = RANDOM_SEED,
    model: Optional[IsolationForest] = None,
) -> Tuple[pd.Series, pd.Series]:
    """Identify transaction anomalies using an Isolation Forest ensemble.

    Strict Leakage Prevention Protocol:
    1. Transforms transaction records via Phase 5 feature engineering pipeline.
    2. Extracts approved numeric modeling matrix via get_model_feature_matrix(),
       strictly stripping entity IDs, raw descriptions, text lengths, timestamps,
       and ground-truth evaluation markers.
    3. Retains original DataFrame indices to map predictions back to source records.

    Anomaly Scoring Semantics:
    - Anomaly Flags: True for detected anomalies, False for normal transactions.
    - Decision Scores: Lower / negative values represent higher anomaly severity
      (average path length through trees is shorter).

    Args:
        df: Raw or cleaned transaction DataFrame.
        contamination: Calibrated contamination rate parameter (e.g., 0.01 to 0.05).
        random_state: Reproducible random seed.
        model: Optional pre-fitted IsolationForest model. If None, fits a new instance.

    Returns:
        Tuple[pd.Series, pd.Series]: (is_anomaly_series, decision_score_series)
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        empty_flags = pd.Series(False, index=df.index, dtype=bool)
        empty_scores = pd.Series(0.0, index=df.index, dtype=float)
        return empty_flags, empty_scores

    # Feature Engineering & Strict Leakage Elimination
    enriched = engineer_features(df, include_categorical_encoding=True)
    matrix = get_model_feature_matrix(enriched, include_categorical_dummies=True, drop_na_rows=False)

    # Impute missing values arising from initial rolling window warmup with 0.0
    clean_matrix = matrix.fillna(0.0)

    if model is None:
        model = train_isolation_forest(
            clean_matrix,
            contamination=contamination,
            random_state=random_state,
        )

    # Predictions (-1 = anomaly, 1 = normal)
    raw_preds = model.predict(clean_matrix)
    is_anomaly = pd.Series(raw_preds == -1, index=df.index, dtype=bool)

    # Decision function (negative = anomalous, positive = inlier)
    scores = pd.Series(model.decision_function(clean_matrix), index=df.index, dtype=float)

    return is_anomaly, scores


def evaluate_anomaly_detection(
    y_true: Union[pd.Series, np.ndarray, list],
    y_pred: Union[pd.Series, np.ndarray, list],
) -> Dict[str, Any]:
    """Evaluate anomaly detector predictions against synthetic ground-truth test markers.

    Synthetic Benchmark Disclaimer:
    Evaluations reflect deliberately injected high-value shocks in synthetic transaction
    records. Performance on this benchmark demonstrates algorithm integration and feature
    discrimination, but does not establish real-world fraud or financial crime detection capability.

    Args:
        y_true: Ground truth binary labels (1 = unusual shock, 0 = normal transaction).
        y_pred: Model predictions (1 / True = anomaly, 0 / False = normal).

    Returns:
        Dict[str, Any]: Performance report containing precision, recall, f1_score,
                       confusion matrix counts, and analytical commentary.
    """
    true_arr = np.asarray(y_true, dtype=int)
    pred_arr = np.asarray(y_pred, dtype=int)

    if len(true_arr) == 0 or len(pred_arr) == 0:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
            "ground_truth_count": 0,
            "predicted_count": 0,
            "total_samples": 0,
        }

    p = float(precision_score(true_arr, pred_arr, zero_division=0))
    r = float(recall_score(true_arr, pred_arr, zero_division=0))
    f1 = float(f1_score(true_arr, pred_arr, zero_division=0))

    cm = confusion_matrix(true_arr, pred_arr, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    return {
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
        "ground_truth_count": int(true_arr.sum()),
        "predicted_count": int(pred_arr.sum()),
        "total_samples": int(len(true_arr)),
    }


def evaluate_anomaly_detection_out_of_sample(
    df: pd.DataFrame,
    test_size: Union[float, int] = 0.2,
    contamination: float = 0.02,
    random_state: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """Evaluate Isolation Forest anomaly detection in an inductive out-of-sample hold-out setup.

    Evaluation Methodology & Disclosures:
    - Chronologically partitions transaction records into training and test sets (default: 80/20).
    - Fits Isolation Forest strictly on the training feature matrix without access to test observations.
    - Evaluates predictions on the unseen test set against quarantined ground-truth labels.
    - Leakage Prevention: Evaluation markers ('[UNUSUAL]'), raw descriptions, transaction IDs,
      and text length proxies are strictly excluded from both training and test matrices.
    - Discloses sample distribution limitations: In highly imbalanced datasets (~0.24% anomalies),
      chronological test partitions may contain very few ground-truth anomalies (e.g. 1 out of 1,000).

    Args:
        df: Input DataFrame containing transaction records.
        test_size: Fraction or count for hold-out test set (defaults to 0.2).
        contamination: A priori contamination rate parameter.
        random_state: Integer seed for reproducible partitioning.

    Returns:
        Dict[str, Any]: Evaluation report on unseen test data.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty or len(df) < 10:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
            "ground_truth_count": 0,
            "predicted_count": 0,
            "total_samples": 0,
            "train_samples": 0,
            "test_samples": 0,
        }

    n = len(df)
    if isinstance(test_size, float) and 0.0 < test_size < 1.0:
        split_idx = int(n * (1.0 - test_size))
    elif isinstance(test_size, int) and 0 < test_size < n:
        split_idx = n - test_size
    else:
        split_idx = int(n * 0.8)

    split_idx = max(1, min(split_idx, n - 1))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    # Engineer features separately to prevent any cross-split leakage
    train_feat = engineer_features(train_df, include_categorical_encoding=True)
    train_mat = get_model_feature_matrix(train_feat, include_categorical_dummies=True, drop_na_rows=False).fillna(0.0)

    test_feat = engineer_features(test_df, include_categorical_encoding=True)
    test_mat = get_model_feature_matrix(test_feat, include_categorical_dummies=True, drop_na_rows=False).fillna(0.0)

    # Train model strictly on training observations
    model = train_isolation_forest(
        train_mat,
        contamination=contamination,
        random_state=random_state,
    )

    # Predict on unseen test observations
    test_preds = pd.Series(model.predict(test_mat) == -1, index=test_df.index, dtype=bool)
    y_test_true = extract_ground_truth_labels(test_df)

    eval_results = evaluate_anomaly_detection(y_test_true, test_preds)
    eval_results["train_samples"] = len(train_df)
    eval_results["test_samples"] = len(test_df)
    eval_results["train_ground_truth_count"] = int(extract_ground_truth_labels(train_df).sum())
    eval_results["test_ground_truth_count"] = int(y_test_true.sum())

    return eval_results


def get_anomaly_records(
    df: pd.DataFrame,
    is_anomaly: pd.Series,
    anomaly_scores: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Extract flagged anomalous transaction records with presentation sanitization.

    - Masks synthetic '[UNUSUAL]' markers in display descriptions.
    - Preserves transaction dates, amounts, categories, and payment instruments.
    - Sorts records by anomaly severity (lowest decision score first).

    Args:
        df: Original transaction DataFrame.
        is_anomaly: Boolean Series indicating flagged anomalies.
        anomaly_scores: Optional decision function scores (lower = more severe).

    Returns:
        pd.DataFrame containing flagged anomalous transaction records.
    """
    if df.empty or not is_anomaly.any():
        cols = ["transaction_id", "date", "type", "category", "amount", "payment_method", "description"]
        avail_cols = [c for c in cols if c in df.columns]
        empty_res = pd.DataFrame(columns=avail_cols)
        empty_res["anomaly_score"] = pd.Series(dtype=float)
        return empty_res

    flagged = df[is_anomaly].copy()

    if anomaly_scores is not None:
        flagged["anomaly_score"] = anomaly_scores.loc[flagged.index].round(4)
        flagged = flagged.sort_values(by="anomaly_score", ascending=True)
    else:
        flagged["anomaly_score"] = 0.0
        flagged = flagged.sort_values(by="amount", ascending=False)

    if "description" in flagged.columns:
        flagged["display_description"] = (
            flagged["description"].astype(str).str.replace(r"\[UNUSUAL\]\s*", "", regex=True).str.strip()
        )

    return flagged.reset_index(drop=True)
