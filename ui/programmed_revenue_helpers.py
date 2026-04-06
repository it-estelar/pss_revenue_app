from __future__ import annotations

import pandas as pd

from services.programmed_revenue_common import MESES, fmt_flight


def fmt_money(value) -> str:
    try:
        x = float(value)
    except Exception:
        x = 0.0
    s = f"{x:,.2f}"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(value) -> str:
    try:
        x = int(value)
    except Exception:
        x = 0
    return f"{x:,}".replace(",", ".")


def build_passenger_list(sub: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    passenger_cols = ["ticket", "pax", "cod_reserva", "foid"]

    pax_df = sub[passenger_cols].copy()
    pax_df["ticket"] = pax_df["ticket"].astype(str).str.strip()
    pax_df["pax"] = pax_df["pax"].astype(str).str.strip()
    pax_df["cod_reserva"] = pax_df["cod_reserva"].astype(str).str.strip()
    pax_df["foid"] = pax_df["foid"].astype(str).str.strip()

    duplicates_count = int(pax_df.duplicated(subset=["ticket"]).sum())

    pax_df = pax_df.drop_duplicates(subset=["ticket"], keep="first").reset_index(drop=True)

    pax_df = pax_df.rename(
        columns={
            "ticket": "Ticket Number",
            "pax": "Pax",
            "cod_reserva": "Cod Reserva",
            "foid": "FOID",
        }
    )

    return pax_df, duplicates_count