"""
Synthetic Transaction Data Generator

Author: Akash Das
Description: Configurable, reproducible synthetic personal financial transaction generator
             tailored for personal finance tracking and analytical modeling in INR.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


# Allowed Enums & Categories
TRANSACTION_TYPES = ("Income", "Expense")

INCOME_CATEGORIES = (
    "Salary",
    "Freelance",
    "Business Income",
    "Investment Income",
    "Other Income",
)

EXPENSE_CATEGORIES = (
    "Rent",
    "Groceries",
    "Utilities",
    "Transport",
    "Healthcare",
    "Education",
    "Shopping",
    "Entertainment",
    "Dining",
    "Travel",
    "Subscriptions",
    "Other Expenses",
)

PAYMENT_METHODS = (
    "UPI",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Bank Transfer",
)

# Realistic Merchant / Description Templates
MERCHANT_POOLS: Dict[str, List[str]] = {
    # Income
    "Salary": ["Monthly Salary - Tech Solutions Corp", "Monthly Salary - Consulting Ltd"],
    "Freelance": [
        "Upwork Client Payment - UI Design",
        "Freelance Software Project Milestone",
        "Technical Writing Consultation",
        "Advisory Retainer Fee",
    ],
    "Business Income": [
        "E-commerce Store Revenue",
        "Consulting Services Invoice #412",
        "Digital Products Sales Payout",
    ],
    "Investment Income": [
        "Mutual Fund Dividend Payout",
        "Equity Shares Dividend Credit",
        "Fixed Deposit Quarterly Interest",
        "Treasury Bond Coupon Payment",
    ],
    "Other Income": [
        "Cashback & Rewards Redemption",
        "Tax Refund Credit",
        "Gift Credit from Family",
        "Reimbursement from Employer",
    ],
    # Expenses
    "Rent": ["Apartment Monthly Rent Transfer", "Society Maintenance & Rent Charges"],
    "Groceries": [
        "Blinkit Quick Grocery Delivery",
        "Zepto Daily Essentials",
        "BigBasket Weekly Grocery",
        "Local Kirana Supermarket",
        "Nature's Basket Organic Store",
        "Fresh Produce & Vegetable Market",
    ],
    "Utilities": [
        "Electricity Bill - State Power Board",
        "Piped Gas Monthly Bill",
        "Broadband High-Speed Internet",
        "Mobile Postpaid Recharge",
        "Water & Municipal Utilities",
    ],
    "Transport": [
        "Uber City Commute",
        "Ola Auto Ride",
        "Metro Card Smart Recharge",
        "HPCL Petrol & Fuel Station",
        "Indian Oil Fuel Refill",
        "Fastag Highway Toll Payment",
    ],
    "Healthcare": [
        "Apollo Pharmacy Medicines",
        "Dr. Diagnostic Blood Tests",
        "Dental Clinic Consultation",
        "Health & Wellness Checkup",
        "Optometrist & Eyewear",
    ],
    "Education": [
        "Coursera Specialization Subscription",
        "Udemy Data Science Masterclass",
        "Academic Textbooks & E-books",
        "Professional Certification Exam Fee",
    ],
    "Shopping": [
        "Amazon Online Retail Order",
        "Flipkart Electronics Purchase",
        "Myntra Fashion & Apparel",
        "Zara Clothing Store",
        "IKEA Home Decor & Furniture",
        "Uniqlo Casual Wear",
    ],
    "Entertainment": [
        "PVR Inox Movie Tickets",
        "BookMyShow Concert Passes",
        "Board Game Cafe & Arcade",
        "Weekend Theme Park Entry",
    ],
    "Dining": [
        "Swiggy Gourmet Dinner",
        "Zomato Quick Lunch",
        "Starbucks Coffee Outing",
        "Third Wave Coffee Roasters",
        "Haldiram's Family Dinner",
        "Mainland China Restaurant",
        "Local Street Food & Chaat",
    ],
    "Travel": [
        "MakeMyTrip Flight Booking",
        "IRCTC Train Ticket Reservation",
        "Airbnb Weekend Getaway Stay",
        "Taj Hotels Weekend Booking",
        "Uber Outstation Cab Fare",
    ],
    "Subscriptions": [
        "Netflix Premium Plan",
        "Spotify Family Music",
        "Amazon Prime Annual Membership",
        "YouTube Premium Family",
        "Apple iCloud 200GB Storage",
        "Gym & Fitness Club Membership",
    ],
    "Other Expenses": [
        "Courier & Postal Services",
        "Home Hardware & Tools",
        "Pet Care & Supplies",
        "Dry Cleaning & Laundry",
        "Charitable Donation",
    ],
}

# Deliberate Large Outlier Expenses (Synthetic Test Cases)
ANOMALY_TEMPLATES = [
    ("Healthcare", "Emergency Hospitalization & Surgery Deposit", 85000.0, 115000.0, "Credit Card"),
    ("Shopping", "Apple MacBook Pro M3 Laptop Purchase", 135000.0, 165000.0, "Credit Card"),
    ("Travel", "International Vacation Flight & Resort Booking", 95000.0, 140000.0, "Bank Transfer"),
    ("Shopping", "Designer Jewelry & Gold Coin Purchase", 80000.0, 120000.0, "Bank Transfer"),
    ("Other Expenses", "Emergency Home Renovation & Plumbing Overhaul", 65000.0, 90000.0, "Debit Card"),
]


def generate_synthetic_transactions(
    n_records: int = 5000,
    start_date: str = "2025-11-01",
    end_date: str = "2026-10-31",
    random_seed: int = 42,
    **kwargs: Any,
) -> pd.DataFrame:
    """Generate reproducible synthetic financial transactions covering a configured date range.

    Args:
        n_records: Total number of transactions to generate (must be >= 10).
        start_date: Start date string formatted as 'YYYY-MM-DD'.
        end_date: End date string formatted as 'YYYY-MM-DD'.
        random_seed: Random seed for reproducibility.
        **kwargs: Backward compatibility options ('num_records', 'random_state').

    Returns:
        DataFrame containing synthetic transaction records adhering to standard schema.

    Raises:
        ValueError: If parameters are invalid (e.g. n_records < 10, start_date > end_date).
    """
    # Backward-compatibility parameter handling
    if "num_records" in kwargs:
        n_records = kwargs["num_records"]
    if "random_state" in kwargs:
        random_seed = kwargs["random_state"]

    if n_records < 10:
        raise ValueError(f"n_records must be at least 10, got {n_records}.")

    try:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        dt_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Dates must be in 'YYYY-MM-DD' format: {e}")

    if dt_start > dt_end:
        raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date}).")

    rng = np.random.default_rng(random_seed)

    # Calculate month periods within range
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    total_days = len(date_range)
    if total_days < 1:
        raise ValueError("Date range must span at least 1 day.")

    monthly_periods = pd.period_range(start=start_date, end=end_date, freq="M")
    n_months = len(monthly_periods)

    records: List[Dict[str, Any]] = []

    # 1. Monthly Recurring Salary Income (1 per month)
    for m in monthly_periods:
        # Salary credited between 28th and 1st of month
        month_days = pd.date_range(start=m.start_time.date(), end=m.end_time.date(), freq="D")
        eligible_days = [d.date() for d in month_days if d.day in (1, 2, 28, 29, 30, 31)]
        salary_date = rng.choice(eligible_days) if eligible_days else m.start_time.date()
        salary_amount = float(round(rng.normal(loc=85000, scale=3500), 2))
        records.append({
            "date": salary_date.strftime("%Y-%m-%d"),
            "type": "Income",
            "category": "Salary",
            "amount": max(70000.0, salary_amount),
            "payment_method": "Bank Transfer",
            "description": rng.choice(MERCHANT_POOLS["Salary"]),
        })

    # 2. Monthly Recurring Rent Expense (1 per month)
    for m in monthly_periods:
        month_days = pd.date_range(start=m.start_time.date(), end=m.end_time.date(), freq="D")
        eligible_days = [d.date() for d in month_days if 1 <= d.day <= 5]
        rent_date = rng.choice(eligible_days) if eligible_days else m.start_time.date()
        rent_amount = float(round(rng.normal(loc=25000, scale=1000), 2))
        records.append({
            "date": rent_date.strftime("%Y-%m-%d"),
            "type": "Expense",
            "category": "Rent",
            "amount": max(22000.0, rent_amount),
            "payment_method": rng.choice(["Bank Transfer", "UPI"], p=[0.7, 0.3]),
            "description": rng.choice(MERCHANT_POOLS["Rent"]),
        })

    # 3. Monthly Recurring Subscriptions (2-3 per month)
    sub_descriptions = MERCHANT_POOLS["Subscriptions"]
    for m in monthly_periods:
        n_subs = rng.integers(2, 4)
        chosen_subs = rng.choice(sub_descriptions, size=n_subs, replace=False)
        for sub_name in chosen_subs:
            sub_date = (m.start_time + pd.Timedelta(days=int(rng.integers(1, 20)))).date()
            if "Netflix" in sub_name:
                cost = 649.0
            elif "Spotify" in sub_name:
                cost = 179.0
            elif "Prime" in sub_name:
                cost = 1499.0
            elif "YouTube" in sub_name:
                cost = 189.0
            elif "iCloud" in sub_name:
                cost = 219.0
            else:
                cost = float(round(rng.uniform(1500, 3000), 2))
            records.append({
                "date": sub_date.strftime("%Y-%m-%d"),
                "type": "Expense",
                "category": "Subscriptions",
                "amount": cost,
                "payment_method": rng.choice(["Credit Card", "UPI"], p=[0.75, 0.25]),
                "description": sub_name,
            })

    # 4. Deliberate Synthetic Anomaly Transactions (~0.25% of records, at least 3)
    n_anomalies = max(3, min(15, int(n_records * 0.0025)))
    anomaly_indices = rng.choice(len(date_range), size=n_anomalies, replace=False)
    for idx in anomaly_indices:
        template_idx = int(rng.integers(0, len(ANOMALY_TEMPLATES)))
        t_cat, t_desc, min_amt, max_amt, t_pay = ANOMALY_TEMPLATES[template_idx]
        anom_amt = float(round(rng.uniform(float(min_amt), float(max_amt)), 2))
        records.append({
            "date": date_range[idx].strftime("%Y-%m-%d"),
            "type": "Expense",
            "category": t_cat,
            "amount": anom_amt,
            "payment_method": t_pay,
            "description": f"[UNUSUAL] {t_desc}",
        })

    # 5. Remaining Variable Transactions to meet exact n_records
    fixed_count = len(records)
    if fixed_count > n_records:
        # If requested n_records is small, truncate to requested count
        records = records[:n_records]
    else:
        remaining_needed = n_records - fixed_count

        # Probability distribution across types for remaining transactions
        # ~6% supplementary income, ~94% variable daily expenses
        type_choices = rng.choice(["Income", "Expense"], size=remaining_needed, p=[0.06, 0.94])

        income_weights = [0.40, 0.25, 0.25, 0.10]
        supp_income_cats = ["Freelance", "Business Income", "Investment Income", "Other Income"]

        expense_weights = [
            0.30,  # Groceries
            0.10,  # Utilities
            0.20,  # Transport
            0.05,  # Healthcare
            0.04,  # Education
            0.10,  # Shopping
            0.06,  # Entertainment
            0.12,  # Dining
            0.02,  # Travel
            0.01,  # Other Expenses
        ]
        var_expense_cats = [
            "Groceries",
            "Utilities",
            "Transport",
            "Healthcare",
            "Education",
            "Shopping",
            "Entertainment",
            "Dining",
            "Travel",
            "Other Expenses",
        ]

        # Random dates drawn across date_range
        random_date_indices = rng.integers(0, total_days, size=remaining_needed)

        for i, txn_type in enumerate(type_choices):
            d_str = date_range[random_date_indices[i]].strftime("%Y-%m-%d")

            if txn_type == "Income":
                cat = rng.choice(supp_income_cats, p=income_weights)
                desc = rng.choice(MERCHANT_POOLS[cat])
                if cat == "Freelance":
                    amt = float(round(rng.uniform(12000, 45000), 2))
                    pay = rng.choice(["Bank Transfer", "UPI"], p=[0.7, 0.3])
                elif cat == "Business Income":
                    amt = float(round(rng.uniform(8000, 35000), 2))
                    pay = "Bank Transfer"
                elif cat == "Investment Income":
                    amt = float(round(rng.uniform(2500, 15000), 2))
                    pay = "Bank Transfer"
                else:
                    amt = float(round(rng.uniform(500, 5000), 2))
                    pay = rng.choice(["UPI", "Bank Transfer", "Cash"], p=[0.7, 0.2, 0.1])
            else:
                cat = rng.choice(var_expense_cats, p=expense_weights)
                desc = rng.choice(MERCHANT_POOLS[cat])
                if cat == "Groceries":
                    amt = float(round(rng.lognormal(mean=6.5, sigma=0.6), 2))  # ~₹300 - ₹3,500
                    pay = rng.choice(["UPI", "Credit Card", "Debit Card", "Cash"], p=[0.55, 0.25, 0.10, 0.10])
                elif cat == "Dining":
                    amt = float(round(rng.lognormal(mean=6.2, sigma=0.7), 2))  # ~₹200 - ₹2,200
                    pay = rng.choice(["UPI", "Credit Card", "Debit Card", "Cash"], p=[0.60, 0.30, 0.05, 0.05])
                elif cat == "Transport":
                    amt = float(round(rng.uniform(60, 1800), 2))
                    pay = rng.choice(["UPI", "Cash", "Credit Card"], p=[0.65, 0.20, 0.15])
                elif cat == "Utilities":
                    amt = float(round(rng.uniform(400, 4500), 2))
                    pay = rng.choice(["UPI", "Credit Card", "Bank Transfer"], p=[0.70, 0.20, 0.10])
                elif cat == "Shopping":
                    amt = float(round(rng.lognormal(mean=7.5, sigma=0.8), 2))  # ~₹800 - ₹8,000
                    pay = rng.choice(["Credit Card", "UPI", "Debit Card"], p=[0.50, 0.35, 0.15])
                elif cat == "Entertainment":
                    amt = float(round(rng.uniform(300, 3500), 2))
                    pay = rng.choice(["UPI", "Credit Card", "Debit Card"], p=[0.60, 0.30, 0.10])
                elif cat == "Healthcare":
                    amt = float(round(rng.uniform(250, 4500), 2))
                    pay = rng.choice(["Credit Card", "UPI", "Debit Card", "Cash"], p=[0.40, 0.35, 0.15, 0.10])
                elif cat == "Education":
                    amt = float(round(rng.uniform(800, 7500), 2))
                    pay = rng.choice(["Credit Card", "UPI", "Debit Card"], p=[0.50, 0.40, 0.10])
                elif cat == "Travel":
                    amt = float(round(rng.uniform(2500, 22000), 2))
                    pay = rng.choice(["Credit Card", "Bank Transfer", "UPI"], p=[0.60, 0.25, 0.15])
                else:
                    amt = float(round(rng.uniform(150, 2500), 2))
                    pay = rng.choice(["UPI", "Cash", "Debit Card"], p=[0.60, 0.30, 0.10])

            # Ensure valid bounds
            amt = max(10.0, float(round(amt, 2)))

            records.append({
                "date": d_str,
                "type": txn_type,
                "category": cat,
                "amount": amt,
                "payment_method": pay,
                "description": desc,
            })

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Sort chronologically
    df["sort_date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["sort_date"]).reset_index(drop=True)
    df = df.drop(columns=["sort_date"])

    # Generate sequential unique transaction IDs: TXN-00001, TXN-00002, ...
    df.insert(0, "transaction_id", [f"TXN-{i+1:05d}" for i in range(len(df))])

    # Reorder columns explicitly matching standard schema
    schema_cols = [
        "transaction_id",
        "date",
        "type",
        "category",
        "amount",
        "payment_method",
        "description",
    ]
    df = df[schema_cols]

    return df
