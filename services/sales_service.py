import pandas as pd

from reports import (
    build_sales_monthly_report,
    build_sales_route_month_report,
    build_sales_weekly_report,
    get_sales_available_months,
    get_sales_available_years,
)


def get_sales_year_options(df):
    return get_sales_available_years(df)


def get_sales_month_options(df, selected_year: int):
    return get_sales_available_months(df, selected_year)


def build_sales_period_label(selected_year: int, selected_month_label: str) -> str:
    return f"Período: {selected_month_label} {selected_year}"


def compute_sales_kpis(monthly_df: pd.DataFrame, weekly_df: pd.DataFrame):
    monthly_no_total = monthly_df[
        monthly_df["Mes"].astype(str).str.upper() != "TOTAL AÑO"
    ].copy() if not monthly_df.empty else pd.DataFrame()

    weekly_no_total = weekly_df[
        weekly_df["Semana"].astype(str).str.upper() != "TOTAL MES"
    ].copy() if not weekly_df.empty else pd.DataFrame()

    total_year_revenue = (
        float(monthly_no_total["Revenue USD"].sum())
        if not monthly_no_total.empty and "Revenue USD" in monthly_no_total.columns
        else 0
    )
    total_year_coupons = (
        float(monthly_no_total["Cupones"].sum())
        if not monthly_no_total.empty and "Cupones" in monthly_no_total.columns
        else 0
    )
    total_month_revenue = (
        float(weekly_no_total["Ingreso USD"].sum())
        if not weekly_no_total.empty and "Ingreso USD" in weekly_no_total.columns
        else 0
    )
    total_month_coupons = (
        float(weekly_no_total["Cupones"].sum())
        if not weekly_no_total.empty and "Cupones" in weekly_no_total.columns
        else 0
    )

    return {
        "total_year_revenue": total_year_revenue,
        "total_year_coupons": total_year_coupons,
        "total_month_revenue": total_month_revenue,
        "total_month_coupons": total_month_coupons,
    }


def prepare_sales_outputs(df, coupons_long, selected_year: int, selected_month_value: int):
    monthly_df = build_sales_monthly_report(df, selected_year)
    weekly_df = build_sales_weekly_report(df, selected_year, selected_month_value)
    route_month_df = build_sales_route_month_report(coupons_long, selected_year)
    kpis = compute_sales_kpis(monthly_df, weekly_df)

    return {
        "monthly_df": monthly_df,
        "weekly_df": weekly_df,
        "route_month_df": route_month_df,
        "kpis": kpis,
    }