import plotly.express as px

from .common import base_layout


def _normalize_currency_selection(selected_currency):
    if selected_currency is None:
        return []

    if isinstance(selected_currency, (list, tuple, set)):
        return [str(x).strip() for x in selected_currency if str(x).strip()]

    value = str(selected_currency).strip()
    return [value] if value else []


def chart_currency_class_mix(currency_class_df, selected_currency=None):
    if currency_class_df.empty:
        return base_layout(px.bar(title="Revenue por Clase"))

    df = currency_class_df.copy()
    df["Moneda"] = df["Moneda"].astype(str).str.strip()
    df["Clase"] = df["Clase"].fillna("").astype(str).str.strip()

    df = df[df["Moneda"].str.upper() != "TOTAL"].copy()
    df = df[~df["Clase"].str.upper().isin(["NONE", "NAN", "NULL", ""])].copy()

    selected_currencies = _normalize_currency_selection(selected_currency)
    if selected_currencies:
        df = df[df["Moneda"].isin(selected_currencies)].copy()

    if df.empty:
        return base_layout(px.bar(title="Revenue por Clase"))

    if len(selected_currencies) == 1:
        chart_title = f"Revenue por Clase Tarifaria - {selected_currencies[0]}"
    elif len(selected_currencies) > 1:
        chart_title = "Revenue por Clase Tarifaria - Monedas Seleccionadas"
    else:
        chart_title = "Revenue por Clase Tarifaria - Todas las Monedas"

    fig = px.bar(
        df,
        x="Clase",
        y="Monto_USD",
        color="Moneda",
        text="Monto_USD",
        title=chart_title,
    )
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Monto USD")
    return base_layout(fig)