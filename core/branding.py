from pathlib import Path
import base64

import streamlit as st


def get_logo_path():
    candidates = [
        Path(__file__).resolve().parent.parent / "logo_estelar_transparent.png",
        Path(__file__).resolve().parent.parent / "logo_estelar.png",
        Path.cwd() / "logo_estelar_transparent.png",
        Path.cwd() / "logo_estelar.png",
        Path("/mnt/data/logo_estelar_transparent.png"),
        Path("/mnt/data/logo_estelar.png"),
    ]

    for path in candidates:
        if path.exists() and path.is_file():
            return path

    return None


def render_sidebar_logo():
    logo_path = get_logo_path()
    if not logo_path:
        return

    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        mime = "image/png" if logo_path.suffix.lower() == ".png" else "image/jpeg"

        st.sidebar.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                <img src="data:{mime};base64,{encoded}" alt="Estelar logo" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.sidebar.warning("No se pudo cargar el logo.")