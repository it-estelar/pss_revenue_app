import pandas as pd

from reports import (
    build_revenue_by_emisor,
    get_emisor_filter_options,
)


def prepare_revenue_by_emisor_outputs(df: pd.DataFrame, coupons_long: pd.DataFrame):
    revenue_by_emisor_df = build_revenue_by_emisor(df)
    emisor_filter_options = get_emisor_filter_options(coupons_long)

    return {
        "revenue_by_emisor_df": revenue_by_emisor_df,
        "emisor_filter_options": emisor_filter_options,
    }