import io

import pandas as pd


def df_to_excel_bytes(sheets):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, index=False, sheet_name=str(sheet_name)[:31])
    output.seek(0)
    return output.getvalue()


def single_df_to_excel_bytes(df, sheet_name="report"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=str(sheet_name)[:31])
    output.seek(0)
    return output.getvalue()