import streamlit as st


MODULES_BY_ROLE = {
    "admin": [
        "Dashboard",
        "Revenue by Emisor",
        "Tariff Style",
        "Yield by Route",
        "Volado",
        "Programmed Revenue by Flight",
        "Route Analysis",
        "Purchase vs Programmed Heatmap",
        "Sales",
        "Sales by User",
        "Admin Panel",
        "Data Load",
    ],
    "user": [
        "Dashboard",
        "Revenue by Emisor",
        "Tariff Style",
        "Yield by Route",
        "Volado",
        "Programmed Revenue by Flight",
        "Route Analysis",
        "Purchase vs Programmed Heatmap",
        "Sales",
        "Sales by User",
    ],
}


def get_module_labels_for_role(role: str | None) -> list[str]:
    normalized_role = (role or "user").strip().lower()
    return MODULES_BY_ROLE.get(normalized_role, MODULES_BY_ROLE["user"])


def render_sidebar_navigation(role: str | None = "user") -> str:
    """
    Render the sidebar module selector and return the selected module label.
    The visible module list depends on the authenticated user role.
    """
    module_labels = get_module_labels_for_role(role)

    st.sidebar.markdown(
        '<div class="sidebar-section">Navegación</div>',
        unsafe_allow_html=True,
    )

    return st.sidebar.radio(
        "Ir a módulo",
        module_labels,
        label_visibility="visible",
    )