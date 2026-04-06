import pandas as pd

from reports import build_revenue_by_currency_class


def get_currency_options(revenue_by_currency_class_df: pd.DataFrame, safe_unique_sorted):
    if revenue_by_currency_class_df is None or revenue_by_currency_class_df.empty:
        return []

    if "Moneda" not in revenue_by_currency_class_df.columns:
        return []

    currencies = revenue_by_currency_class_df.loc[
        revenue_by_currency_class_df["Moneda"].astype(str).str.upper() != "TOTAL",
        "Moneda",
    ]

    return safe_unique_sorted(currencies)


def prepare_tariff_style_outputs(df: pd.DataFrame, safe_unique_sorted):
    revenue_by_currency_class_df = build_revenue_by_currency_class(df)
    currency_options = get_currency_options(
        revenue_by_currency_class_df,
        safe_unique_sorted,
    )

    return {
        "revenue_by_currency_class_df": revenue_by_currency_class_df,
        "currency_options": currency_options,
    }