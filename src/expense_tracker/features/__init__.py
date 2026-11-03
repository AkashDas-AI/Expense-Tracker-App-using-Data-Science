"""Feature engineering and transformation module.

Author: Akash Das
Description: Feature engineering pipelines, temporal features, amount transformations,
             lag metrics, rolling statistics, categorical encoding, and leakage prevention.
"""

from expense_tracker.features.feature_engineering import (
    CANONICAL_CATEGORIES,
    CANONICAL_PAYMENT_METHODS,
    encode_categorical_features,
    engineer_features,
    extract_amount_features,
    extract_calendar_features,
    extract_flow_indicators,
    extract_ground_truth_labels,
    extract_temporal_features,
    extract_temporal_sequence_features,
    extract_text_features,
    get_model_feature_matrix,
)

__all__ = [
    "CANONICAL_CATEGORIES",
    "CANONICAL_PAYMENT_METHODS",
    "encode_categorical_features",
    "engineer_features",
    "extract_amount_features",
    "extract_calendar_features",
    "extract_flow_indicators",
    "extract_ground_truth_labels",
    "extract_temporal_features",
    "extract_temporal_sequence_features",
    "extract_text_features",
    "get_model_feature_matrix",
]
