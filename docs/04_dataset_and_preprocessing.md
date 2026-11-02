# 04. Dataset & Preprocessing

## 1. Dataset Profile

*(To be filled with the chosen dataset specifications upon selection)*

| Property | Details |
| :--- | :--- |
| **Dataset Name** | *Pending Selection* |
| **Source / Origin** | *Kaggle / Custom / Synthetic / Financial Statement* |
| **Total Records** | *Pending* |
| **Number of Features** | *Pending* |
| **Target Variable** | Category / Spending Class |

---

## 2. Expected Schema & Attribute Dictionary

| Field Name | Data Type | Description | Constraints / Examples |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String / UUID | Unique transaction identifier | Non-null, Unique |
| `date` | Date / Timestamp | Date of transaction | ISO 8601 (`YYYY-MM-DD`) |
| `description` | String | Raw merchant or transaction description | Non-empty text |
| `amount` | Float | Transaction amount | Non-negative numeric |
| `transaction_type` | Categorical | Debit or Credit | `debit`, `credit` |
| `category` | Categorical | Target classification label | e.g., `Groceries`, `Utilities`, `Dining`, `Entertainment` |

---

## 3. Data Cleaning & Handling Strategy

1. **Missing Value Imputation**:
   - Categorical defaults for missing descriptions.
   - Exclusion of records missing vital attributes (`date`, `amount`).
2. **Text Normalization**:
   - Lowercasing, removal of punctuation, elimination of dynamic transaction IDs/store numbers (e.g., `WALMART #1042` -> `walmart`).
3. **Outlier Detection**:
   - Identification of abnormal transaction amounts using interquartile range (IQR) or z-score filtering.
4. **Train / Validation / Test Splitting**:
   - Temporal splitting (chronological split) to avoid lookahead bias, or stratified k-fold when training static text classifiers.

