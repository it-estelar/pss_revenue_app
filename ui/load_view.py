import streamlit as st

from .shared import metric_text_int, render_table


def render_data_load_module(preview_fn, execute_fn, history_fn):
    """
    Render the Data Load module.

    Expected callables
    ------------------
    preview_fn(uploaded_file) -> dict
        Validates and previews the selected CSV before load.

    execute_fn(uploaded_file, load_type) -> dict
        Executes the selected load mode and returns load statistics.

    history_fn() -> pd.DataFrame
        Returns recent load-log history from the database.
    """
    st.subheader("Data Load")

    tab1, tab2, tab3 = st.tabs(["Upload & Validate", "Run Load", "Load History"])

    # -------------------------------------------------------------------------
    # Tab 1: file preview and validation
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### Upload & Validate")

        preview_type = st.radio(
            "Tipo de carga para previsualización",
            ["incremental", "massive"],
            horizontal=True,
            key="preview_load_type",
        )

        uploaded_preview = st.file_uploader(
            "Sube un CSV para validar",
            type=["csv"],
            key="preview_csv_uploader",
        )

        if uploaded_preview is not None:
            try:
                preview = preview_fn(uploaded_preview)

                c1, c2, c3 = st.columns(3)
                c1.metric("Rows in file", metric_text_int(preview["total_rows"]))
                c2.metric("Unique tickets", metric_text_int(preview["unique_tickets_in_file"]))
                c3.metric("Duplicates in file", metric_text_int(preview["duplicate_tickets_in_file"]))

                c4, c5, c6 = st.columns(3)
                c4.metric("Would insert", metric_text_int(preview["would_insert"]))
                c5.metric("Would update", metric_text_int(preview["would_update"]))
                c6.metric("Would skip", metric_text_int(preview["would_skip"]))

                d1, d2 = st.columns(2)
                d1.write(f"**File:** {preview['file_name']}")
                d2.write(f"**Mode:** {preview_type}")

                if preview["date_min"] and preview["date_max"]:
                    st.write(f"**Date range in file:** {preview['date_min']} → {preview['date_max']}")

                if preview["missing_required"]:
                    st.error(f"Faltan columnas requeridas: {preview['missing_required']}")
                else:
                    st.success("Archivo válido para carga.")

            except Exception as e:
                st.error(f"Error validando archivo: {e}")

    # -------------------------------------------------------------------------
    # Tab 2: actual load execution
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### Run Load")

        run_type = st.radio(
            "Tipo de carga",
            ["incremental", "massive"],
            horizontal=True,
            key="run_load_type",
        )

        uploaded_run = st.file_uploader(
            "Sube un CSV para cargar",
            type=["csv"],
            key="run_csv_uploader",
        )

        if uploaded_run is not None:
            st.info(f"Archivo seleccionado: {uploaded_run.name}")

            if run_type == "massive":
                st.warning(
                    "La carga masiva es para históricos o reconstrucción. "
                    "Úsala solo cuando corresponda."
                )

            if st.button("Run Load", type="primary"):
                try:
                    result = execute_fn(uploaded_run, run_type)

                    st.success("Carga ejecutada correctamente.")

                    r1, r2, r3 = st.columns(3)
                    r1.metric("Rows", metric_text_int(result["total_rows"]))
                    r2.metric("Inserted", metric_text_int(result["inserted_rows"]))
                    r3.metric("Updated", metric_text_int(result["updated_rows"]))

                    r4, r5 = st.columns(2)
                    r4.metric("Skipped", metric_text_int(result["skipped_rows"]))
                    r5.metric("Errors", metric_text_int(result["error_rows"]))

                    st.write(f"**File:** {result['file_name']}")

                    # Clear Streamlit cached data so other modules see fresh DB data.
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"Error ejecutando la carga: {e}")

    # -------------------------------------------------------------------------
    # Tab 3: recent load-log history
    # -------------------------------------------------------------------------
    with tab3:
        st.markdown("### Load History")

        try:
            history_df = history_fn()

            if history_df.empty:
                st.info("No hay cargas registradas todavía.")
            else:
                render_table(history_df, "Soft Gray", "load_history")

        except Exception as e:
            st.error(f"Error cargando historial: {e}")