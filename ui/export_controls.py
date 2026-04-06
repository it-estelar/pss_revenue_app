import streamlit as st


def build_pdf_subtitle(base_text: str | None, report_period: str | None) -> str | None:
    pieces = []
    if report_period:
        pieces.append(report_period)
    if base_text:
        pieces.append(base_text)
    if not pieces:
        return None
    return " | ".join(pieces)


def render_export_buttons(excel_bytes, excel_name, pdf_bytes, pdf_name, excel_key, pdf_key):
    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "Exportar Excel",
            data=excel_bytes,
            file_name=excel_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=excel_key,
        )

    with c2:
        st.download_button(
            "Exportar PDF",
            data=pdf_bytes,
            file_name=pdf_name,
            mime="application/pdf",
            use_container_width=True,
            key=pdf_key,
        )