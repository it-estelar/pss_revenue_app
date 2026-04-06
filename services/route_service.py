import re

import pandas as pd

from reports import build_route_class_report, build_route_emisor_report


def build_route_label(selected_routes):
    if not selected_routes:
        return "Todas las rutas"

    if len(selected_routes) == 1:
        return selected_routes[0]

    if len(selected_routes) <= 4:
        return " + ".join(selected_routes)

    return f"{len(selected_routes)} rutas seleccionadas"


def safe_filename_part(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text).strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "routes"


def get_emisor_options(coupons_long: pd.DataFrame):
    if coupons_long is None or coupons_long.empty or "Emisor" not in coupons_long.columns:
        return []

    values = (
        coupons_long["Emisor"]
        .fillna("")
        .astype(str)
        .map(str.strip)
    )

    values = values[values != ""]
    values = values.drop_duplicates()

    return sorted(values.tolist(), key=lambda x: x.upper())


def filter_route_coupons(coupons_long: pd.DataFrame, selected_routes, selected_emisores):
    if coupons_long is None or coupons_long.empty:
        return pd.DataFrame()

    filtered = coupons_long.copy()

    if selected_routes:
        filtered = filtered[
            filtered["Ruta"].astype(str).isin(selected_routes)
        ].copy()

    if selected_emisores:
        filtered = filtered[
            filtered["Emisor"].astype(str).isin(selected_emisores)
        ].copy()

    return filtered


def prepare_route_analysis_outputs(coupons_long: pd.DataFrame, selected_routes, selected_emisores):
    filtered_coupons = filter_route_coupons(coupons_long, selected_routes, selected_emisores)

    if filtered_coupons.empty:
        route_label = build_route_label(selected_routes)
        return {
            "filtered_coupons": filtered_coupons,
            "route_label": route_label,
            "route_emisor_df": pd.DataFrame(),
            "route_class_df": pd.DataFrame(),
            "filename_stub": safe_filename_part(route_label),
        }

    route_label = build_route_label(selected_routes)

    route_emisor_df = build_route_emisor_report(filtered_coupons, selected_routes)
    route_class_df = build_route_class_report(filtered_coupons, selected_routes)

    return {
        "filtered_coupons": filtered_coupons,
        "route_label": route_label,
        "route_emisor_df": route_emisor_df,
        "route_class_df": route_class_df,
        "filename_stub": safe_filename_part(route_label),
    }