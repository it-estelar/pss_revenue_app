import streamlit as st

from core import (
    apply_app_styles,
    build_report_period,
    get_module_runner,
    render_sidebar_logo,
    render_sidebar_navigation,
    safe_unique_sorted,
    show_header,
    show_kpis,
)
from db_data_loader import load_db_data, test_db_connection
from load_service import (
    execute_uploaded_csv_load,
    fetch_load_history,
    preview_uploaded_csv,
)
from services.auth_service import (
    authenticate_user,
    create_app_user,
    get_app_users,
)

# -----------------------------------------------------------------------------
# App bootstrap
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Estelar Revenue Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_styles()

def apply_login_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background: #f4f6f9;
        }

        div[data-testid="stForm"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        div[data-testid="stForm"] > div {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        div[data-testid="stTextInput"] > label {
            font-weight: 600 !important;
            color: #17375e !important;
        }

        div[data-testid="stTextInput"] > div > div {
            border-radius: 10px !important;
            border: 1px solid #d4dbe5 !important;
            box-shadow: none !important;
        }

        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 10px !important;
            border: none !important;
            background: #17375e !important;
            color: white !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover {
            background: #20497f !important;
            border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Shared data access helpers
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_module_data(date_from=None, date_to=None):
    """
    Cached wrapper around the DB loader used by analytic modules.
    """
    return load_db_data(date_from=date_from, date_to=date_to)


def load_data_or_stop(date_from=None, date_to=None):
    """
    Load analytic data and stop Streamlit execution if the query fails
    or if the selected range returns no rows.
    """
    try:
        df, coupons_long, kpis, tax_columns, routes = load_module_data(
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as e:
        st.error(f"Error cargando datos desde la base: {e}")
        st.stop()

    if df.empty:
        st.warning("No hay datos para el rango seleccionado.")
        st.stop()

    return df, coupons_long, kpis, tax_columns, routes


def build_app_context() -> dict:
    """
    Shared dependency container passed into each module runner.
    """
    current_user = st.session_state.get("current_user")
    current_role = (current_user or {}).get("role", "user")

    return {
        "load_data_or_stop": load_data_or_stop,
        "show_kpis": show_kpis,
        "build_report_period": build_report_period,
        "safe_unique_sorted": safe_unique_sorted,
        "preview_fn": preview_uploaded_csv,
        "execute_fn": execute_uploaded_csv_load,
        "history_fn": fetch_load_history,
        "current_user": current_user,
        "current_role": current_role,
    }


def ensure_database_connection() -> None:
    """
    Validate DB connectivity before allowing module execution.
    """
    try:
        test_db_connection()
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        st.stop()


def run_selected_module() -> None:
    current_user = st.session_state.get("current_user")

    if not current_user:
        st.error("Sesión inválida. Debes iniciar sesión nuevamente.")
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.stop()

    current_role = (current_user.get("role") or "user").strip().lower()

    module_name = render_sidebar_navigation(current_role)
    runner = get_module_runner(module_name)

    if runner is None:
        st.warning("Módulo no reconocido.")
        st.stop()

    app_context = build_app_context()

    try:
        runner(app_context)
    except TypeError as e:
        st.error(f"Error de firma del módulo '{module_name}': {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error ejecutando el módulo '{module_name}': {e}")
        st.stop()


# -----------------------------------------------------------------------------
# Authentication helpers
# -----------------------------------------------------------------------------

def init_auth_state():
    """
    Initialize authentication state.

    The auth_bootstrap_version key forces a clean reset the first time
    this auth system is deployed, so old Streamlit session state from
    previous app versions does not bypass login.
    """
    AUTH_BOOTSTRAP_VERSION = 1

    if st.session_state.get("auth_bootstrap_version") != AUTH_BOOTSTRAP_VERSION:
        st.session_state.auth_bootstrap_version = AUTH_BOOTSTRAP_VERSION
        st.session_state.authenticated = False
        st.session_state.current_user = None

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "current_user" not in st.session_state:
        st.session_state.current_user = None

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()


def has_any_app_users() -> bool:
    try:
        df = get_app_users()
        return not df.empty
    except Exception as e:
        st.error(f"No se pudieron consultar los usuarios de acceso: {e}")
        st.stop()


def render_first_admin_setup():
    st.title("Configuración inicial")
    st.subheader("Crear el primer usuario administrador")

    with st.form("first_admin_setup_form"):
        username = st.text_input("Usuario administrador")
        full_name = st.text_input("Nombre completo")
        password = st.text_input("Contraseña", type="password")
        password_confirm = st.text_input("Confirmar contraseña", type="password")
        submitted = st.form_submit_button("Crear administrador")

    if submitted:
        username = (username or "").strip()
        full_name = (full_name or "").strip()

        if not username:
            st.error("El usuario es obligatorio.")
            return

        if not password:
            st.error("La contraseña es obligatoria.")
            return

        if password != password_confirm:
            st.error("Las contraseñas no coinciden.")
            return

        try:
            create_app_user(
                username=username,
                password=password,
                full_name=full_name,
                role="admin",
                is_active=True,
            )
            st.success("Administrador inicial creado. Inicia sesión.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo crear el administrador inicial: {e}")

def render_login():
    st.markdown("<br>", unsafe_allow_html=True)

    left, center, right = st.columns([1.2, 1, 1.2])

    with center:
        try:
            c1, c2, c3 = st.columns([1, 2, 1])

            with c2:
                st.image("logo_estelar_transparent.png", width=220)
        except Exception:
            pass

        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)

        if submitted:
            user = authenticate_user(username, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = user
                st.rerun()

            st.error("Usuario o contraseña inválidos.")

def render_authenticated_shell():
    current_user = st.session_state.get("current_user")

    if not current_user:
        st.session_state.authenticated = False
        st.rerun()

    show_header()
    render_sidebar_logo()

    display_name = current_user.get("full_name") or current_user.get("username") or "-"
    role = (current_user.get("role") or "user").strip().lower()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sesión")
    st.sidebar.write(f"**Usuario:** {display_name}")
    st.sidebar.write(f"**Rol:** {role}")

    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        logout()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="sidebar-section">Fuente de datos</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.success("Modo base de datos")

    ensure_database_connection()
    run_selected_module()

# -----------------------------------------------------------------------------
# Main app flow
# -----------------------------------------------------------------------------

init_auth_state()
ensure_database_connection()

if not has_any_app_users():
    render_first_admin_setup()
    st.stop()

if not st.session_state.authenticated:
    render_login()
    st.stop()

render_authenticated_shell()