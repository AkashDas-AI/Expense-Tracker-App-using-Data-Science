# Data Dictionary & Schema Specification

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  

---

## 1. Transaction Entity Specification

The primary entity of the application is the financial **Transaction**.

| Field Name | Type | Format / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | UUID4 or Auto-increment Int | Unique identifier for each transaction |
| `date` | Date | ISO 8601 (`YYYY-MM-DD`) | Date on which the transaction occurred |
| `description` | String | Cleaned UTF-8 string | Merchant name or description of purchase |
| `amount` | Float | Positive real number (`> 0.0`) | Financial value of the transaction |
| `category` | String | Standard Category Enum | Spending category label |
| `transaction_type` | String | `debit` \| `credit` | Direction of funds (expense or income) |
| `payment_method` | String | Enum (`Cash`, `Credit Card`, `Debit Card`, `UPI`, `Bank Transfer`) | Mechanism used to complete transaction |
| `is_anomaly` | Boolean | `True` \| `False` | Flag indicating whether transaction is an outlier |

---

## 2. Standard Category Taxonomy

- **Groceries & Essentials**: Supermarkets, household essentials, personal care.
- **Dining & Takeout**: Restaurants, cafes, food delivery services.
- **Utilities & Bills**: Electricity, water, internet, mobile recharge.
- **Housing & Rent**: Rent, mortgage, property taxes.
- **Transportation**: Fuel, public transit, rideshare services, vehicle maintenance.
- **Entertainment & Leisure**: Streaming services, movies, events, hobbies.
- **Healthcare & Medical**: Doctor visits, pharmacies, insurance.
- **Shopping & Electronics**: Apparel, gadgets, discretionary shopping.
- **Investments & Savings**: Mutual funds, stocks, fixed deposits.
- **Income & Salary**: Paychecks, dividends, freelance revenue.

