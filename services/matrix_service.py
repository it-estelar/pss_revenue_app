import pandas as pd

MONTH_NAMES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def _month_year_label(period_value) -> str:
    if pd.isna(period_value):
        return ""
    return f"{MONTH_NAMES_ES[int(period_value.month)]} {int(period_value.year)}"


def _prepare_coupon_frame(coupons_long: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "Ruta",
        "Date",
        "Fecha Programada de vuelo",
        "Nro Cupon",
    ]

    if coupons_long is None or coupons_long.empty:
        return pd.DataFrame(columns=base_cols)

    frame = coupons_long.copy()

    for col in base_cols:
        if col not in frame.columns:
            frame[col] = pd.NA

    frame["Ruta"] = frame["Ruta"].fillna("").astype(str).str.strip().str.upper()
    frame["Nro Cupon"] = frame["Nro Cupon"].fillna("").astype(str).str.strip()

    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame["Fecha Programada de vuelo"] = pd.to_datetime(
        frame["Fecha Programada de vuelo"],
        errors="coerce",
    )

    frame = frame[
        (frame["Ruta"] != "")
        & frame["Date"].notna()
        & frame["Fecha Programada de vuelo"].notna()
    ].copy()

    return frame


def get_available_reference_years(coupons_long: pd.DataFrame) -> list[int]:
    frame = _prepare_coupon_frame(coupons_long)
    if frame.empty:
        return []

    years = (
        frame["Fecha Programada de vuelo"]
        .dt.year
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    return sorted(years)


def prepare_route_matrix_outputs(
    coupons_long: pd.DataFrame,
    selected_route: str,
    reference_year: int,
):
    empty_export = pd.DataFrame(columns=["Mes/Año Programado"])
    empty_chart = pd.DataFrame(columns=["Mes/Año Programado"])

    frame = _prepare_coupon_frame(coupons_long)
    if frame.empty:
        return {
            "filtered_coupons": frame,
            "heatmap_df": empty_chart,
            "export_df": empty_export,
            "kpis": {
                "total_coupons": 0,
                "purchase_months": 0,
                "programmed_months": 0,
            },
            "title": "Heatmap Compra vs Programación",
            "subtitle": "",
        }

    route_value = str(selected_route).strip().upper()
    if route_value:
        frame = frame[frame["Ruta"] == route_value].copy()

    frame = frame[
        frame["Fecha Programada de vuelo"].dt.year == int(reference_year)
    ].copy()

    if frame.empty:
        return {
            "filtered_coupons": frame,
            "heatmap_df": empty_chart,
            "export_df": empty_export,
            "kpis": {
                "total_coupons": 0,
                "purchase_months": 0,
                "programmed_months": 0,
            },
            "title": f"Heatmap Compra vs Programación - {route_value}",
            "subtitle": f"Ruta: {route_value} | Año programado: {reference_year}",
        }

    frame["PurchasePeriod"] = frame["Date"].dt.to_period("M")
    frame["FlightPeriod"] = frame["Fecha Programada de vuelo"].dt.to_period("M")

    grouped = (
        frame.groupby(["FlightPeriod", "PurchasePeriod"], as_index=False)
        .agg(Cupones=("Nro Cupon", "count"))
    )

    flight_periods = pd.period_range(
        start=f"{int(reference_year)}-01",
        end=f"{int(reference_year)}-12",
        freq="M",
    )

    purchase_min = grouped["PurchasePeriod"].min()
    purchase_max = grouped["PurchasePeriod"].max()
    purchase_periods = pd.period_range(
        start=purchase_min,
        end=purchase_max,
        freq="M",
    )

    pivot = grouped.pivot_table(
        index="FlightPeriod",
        columns="PurchasePeriod",
        values="Cupones",
        aggfunc="sum",
        fill_value=0,
    )

    pivot = pivot.reindex(index=flight_periods, columns=purchase_periods, fill_value=0)

    display = pivot.copy()
    display.index = [_month_year_label(p) for p in display.index]
    display.columns = [_month_year_label(p) for p in display.columns]

    export_df = display.reset_index().rename(
        columns={"index": "Mes/Año Programado"}
    )

    purchase_months = int((pivot.sum(axis=0) > 0).sum())
    programmed_months = int((pivot.sum(axis=1) > 0).sum())
    total_coupons = int(pivot.to_numpy().sum())

    return {
        "filtered_coupons": frame,
        "heatmap_df": display,
        "export_df": export_df,
        "kpis": {
            "total_coupons": total_coupons,
            "purchase_months": purchase_months,
            "programmed_months": programmed_months,
        },
        "title": f"Heatmap Compra vs Programación - {route_value}",
        "subtitle": f"Ruta: {route_value} | Año programado: {reference_year}",
    }