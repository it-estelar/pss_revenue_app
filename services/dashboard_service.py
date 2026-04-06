import pandas as pd

from reports import (
    build_revenue_by_currency_class,
    build_revenue_by_emisor,
    build_yield_by_route,
)


def prepare_dashboard_outputs(df: pd.DataFrame, coupons_long: pd.DataFrame):
    revenue_by_emisor_df = build_revenue_by_emisor(df)

    # IMPORTANT:
    # Tariff-style class mix was rebuilt to work from raw tickets (df),
    # not from coupon-level rows (coupons_long).
    revenue_by_currency_class_df = build_revenue_by_currency_class(df)

    yield_by_route_df = build_yield_by_route(coupons_long)

    routes_for_chart = yield_by_route_df.copy()
    if not routes_for_chart.empty and "Ruta" in routes_for_chart.columns:
        routes_for_chart = routes_for_chart[
            routes_for_chart["Ruta"].astype(str).str.upper() != "TOTAL"
        ].copy()

        if "Revenue" in routes_for_chart.columns:
            routes_for_chart = routes_for_chart.sort_values(
                "Revenue",
                ascending=False,
            ).reset_index(drop=True)

    return {
        "revenue_by_emisor_df": revenue_by_emisor_df,
        "revenue_by_currency_class_df": revenue_by_currency_class_df,
        "yield_by_route_df": yield_by_route_df,
        "routes_for_chart": routes_for_chart,
    }