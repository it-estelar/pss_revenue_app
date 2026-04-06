from __future__ import annotations

import pandas as pd
import streamlit as st

from exporters import single_df_to_excel_bytes

from .programmed_revenue_charts import render_flight_detail_charts
from .programmed_revenue_helpers import (
    build_passenger_list,
    fmt_flight,
    fmt_int,
    fmt_money,
)


def inject_exec_table_css():
    st.markdown(
        """
        <style>
        .exec-table-wrap {
            margin-top: 0.35rem;
            margin-bottom: 1rem;
            border: 1px solid #d7dee8;
            border-radius: 16px;
            overflow-x: auto;
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        }

        .exec-table-title {
            background: linear-gradient(90deg, #233b63 0%, #2e4f82 100%);
            color: white;
            font-weight: 700;
            font-size: 1.02rem;
            padding: 0.8rem 1rem;
            border-bottom: 1px solid #d7dee8;
        }

        table.exec-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
            min-width: 980px;
        }

        table.exec-table thead th {
            background: #30455f;
            color: #ffffff;
            text-align: center;
            padding: 0.75rem 0.7rem;
            border: 1px solid #d7dee8;
            font-weight: 700;
        }

        table.exec-table tbody td {
            background: #f8fafc;
            color: #1f2937;
            padding: 0.72rem 0.7rem;
            border: 1px solid #d7dee8;
            text-align: center;
        }

        table.exec-table tbody tr:nth-child(even) td {
            background: #eef3f9;
        }

        .exec-small-note {
            color: #667085;
            font-size: 0.87rem;
            margin-top: -0.3rem;
            margin-bottom: 0.7rem;
        }

        .flight-box {
            border: 1px solid #d7dee8;
            border-radius: 14px;
            background: #ffffff;
            padding: 0.65rem 0.85rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        }

        .flight-label {
            font-weight: 700;
            color: #233b63;
            font-size: 0.98rem;
        }

        .flight-sub {
            color: #475467;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_exec_table(df: pd.DataFrame, title: str, money_cols=None, int_cols=None):
    if df is None or df.empty:
        st.warning("No hay datos para mostrar.")
        return

    money_cols = money_cols or []
    int_cols = int_cols or []

    show_df = df.copy()

    for col in money_cols:
        if col in show_df.columns:
            show_df[col] = show_df[col].map(fmt_money)

    for col in int_cols:
        if col in show_df.columns:
            show_df[col] = show_df[col].map(fmt_int)

    html_table = show_df.to_html(index=False, classes="exec-table", border=0, escape=False)

    st.markdown(
        f"""
        <div class="exec-table-wrap">
            <div class="exec-table-title">{title}</div>
            {html_table}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flight_ticket_checkboxes(detail: pd.DataFrame):
    st.markdown("### Tickets por vuelo")
    st.markdown(
        '<div class="exec-small-note">Marca el checkbox del vuelo que quieras abrir para ver el detalle de tickets, clases, emisores y descargar la lista de pasajeros.</div>',
        unsafe_allow_html=True,
    )

    if detail is None or detail.empty:
        st.info("No hay detalle por documento para mostrar.")
        return

    work = detail.copy()
    work["vuelo"] = work["vuelo"].map(fmt_flight)

    flight_rows = (
        work.groupby(["fecha_prog", "origen", "destino", "vuelo"], dropna=False)
        .agg(
            Tickets=("ticket", pd.Series.nunique),
            Cupones=("ticket", "count"),
            Ingreso=("assigned_revenue", "sum"),
        )
        .reset_index()
        .sort_values(["fecha_prog", "origen", "destino", "vuelo"])
        .reset_index(drop=True)
    )

    for idx, row in flight_rows.iterrows():
        fecha = row["fecha_prog"]
        origen = row["origen"]
        destino = row["destino"]
        vuelo = row["vuelo"]

        box_key = f"show_flight_tickets_{fecha}_{origen}_{destino}_{vuelo}_{idx}"

        c1, c2 = st.columns([6, 1])

        with c1:
            st.markdown(
                f"""
                <div class="flight-box">
                    <div class="flight-label">{fecha} | {origen}-{destino} | Vuelo {vuelo}</div>
                    <div class="flight-sub">
                        Tickets: {fmt_int(row["Tickets"])} &nbsp;&nbsp;|&nbsp;&nbsp;
                        Cupones: {fmt_int(row["Cupones"])} &nbsp;&nbsp;|&nbsp;&nbsp;
                        Ingreso: {fmt_money(row["Ingreso"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            show_detail = st.checkbox("Ver", key=box_key)

        if show_detail:
            sub = work[
                (work["fecha_prog"] == fecha)
                & (work["origen"] == origen)
                & (work["destino"] == destino)
                & (work["vuelo"] == vuelo)
            ].copy()

            sub = sub.sort_values(["ticket", "transac", "coupon_number"]).reset_index(drop=True)

            rename_map = {
                "fecha_prog": "Fecha",
                "origen": "Origen",
                "destino": "Destino",
                "vuelo": "Vuelo",
                "ticket": "Ticket",
                "transac": "Transac",
                "source_doc": "Doc Fuente",
                "clase": "Clase",
                "emisor": "Emisor",
                "coupon_number": "Cupón",
                "coupon_count": "Cant. Cupones",
                "assigned_revenue": "Ingreso Asignado",
            }

            visible_cols = [
                "fecha_prog",
                "origen",
                "destino",
                "vuelo",
                "ticket",
                "transac",
                "source_doc",
                "clase",
                "emisor",
                "coupon_number",
                "coupon_count",
                "assigned_revenue",
            ]

            sub_show = sub[visible_cols].rename(columns=rename_map).copy()

            label = f"{fecha} | {origen}-{destino} | Vuelo {vuelo}"

            render_exec_table(
                sub_show,
                title=f"Detalle de tickets — {label}",
                money_cols=["Ingreso Asignado"],
                int_cols=["Cupón", "Cant. Cupones"],
            )

            render_flight_detail_charts(sub, label)

            passenger_list_df, duplicated_tickets = build_passenger_list(sub)

            cmsg, cbtn = st.columns([3, 2])

            with cmsg:
                if duplicated_tickets > 0:
                    st.warning(
                        f"Se detectaron {duplicated_tickets} registros duplicados por ticket en este vuelo. "
                        f"La lista de pasajeros se descargará deduplicada por número de ticket."
                    )
                else:
                    st.success("No se detectaron tickets duplicados en la lista de pasajeros de este vuelo.")

            with cbtn:
                pax_excel = single_df_to_excel_bytes(
                    passenger_list_df,
                    sheet_name="passenger_list",
                )
                st.download_button(
                    "Descargar lista de pasajeros",
                    data=pax_excel,
                    file_name=f"pax_list_{fecha}_{origen}_{destino}_{vuelo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_pax_{fecha}_{origen}_{destino}_{vuelo}_{idx}",
                )




                