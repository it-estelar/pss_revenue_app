import pandas as pd
from sqlalchemy import text

from db_data_loader import _get_engine
from services.auth_service import (
    create_app_user,
    get_app_users,
    reset_app_user_password,
    update_app_user,
)


# -----------------------------------------------------------------------------
# Existing operational user catalog
# -----------------------------------------------------------------------------

def get_all_users():
    engine = _get_engine()

    query = """
        SELECT id, usuario, agente, estacion, activo
        FROM estelar_gds.admin_usuarios_emisores
        ORDER BY usuario
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df


def insert_user(usuario, agente, estacion):
    engine = _get_engine()

    query = """
        INSERT INTO estelar_gds.admin_usuarios_emisores (usuario, agente, estacion)
        VALUES (:usuario, :agente, :estacion)
    """

    with engine.begin() as conn:
        conn.execute(
            text(query),
            {
                "usuario": usuario,
                "agente": agente,
                "estacion": estacion,
            },
        )


def update_user(user_id, usuario, agente, estacion, activo):
    engine = _get_engine()

    query = """
        UPDATE estelar_gds.admin_usuarios_emisores
        SET usuario = :usuario,
            agente = :agente,
            estacion = :estacion,
            activo = :activo,
            updated_at = NOW()
        WHERE id = :id
    """

    with engine.begin() as conn:
        conn.execute(
            text(query),
            {
                "id": user_id,
                "usuario": usuario,
                "agente": agente,
                "estacion": estacion,
                "activo": activo,
            },
        )


def delete_user(user_id):
    engine = _get_engine()

    query = """
        DELETE FROM estelar_gds.admin_usuarios_emisores
        WHERE id = :id
    """

    with engine.begin() as conn:
        conn.execute(text(query), {"id": user_id})


# -----------------------------------------------------------------------------
# App access management
# -----------------------------------------------------------------------------

def get_all_app_users():
    return get_app_users()


def insert_app_user(username, password, full_name="", role="user", is_active=True):
    username = (username or "").strip()
    full_name = (full_name or "").strip()
    role = (role or "user").strip().lower()

    if not username:
        raise ValueError("El username es obligatorio.")

    if not password:
        raise ValueError("La contraseña es obligatoria.")

    if role not in {"admin", "user"}:
        raise ValueError("Rol inválido.")

    create_app_user(
        username=username,
        password=password,
        full_name=full_name,
        role=role,
        is_active=is_active,
    )


def save_app_user(user_id, username, full_name="", role="user", is_active=True):
    username = (username or "").strip()
    full_name = (full_name or "").strip()
    role = (role or "user").strip().lower()

    if not username:
        raise ValueError("El username es obligatorio.")

    if role not in {"admin", "user"}:
        raise ValueError("Rol inválido.")

    update_app_user(
        user_id=user_id,
        username=username,
        full_name=full_name,
        role=role,
        is_active=is_active,
    )


def change_app_user_password(user_id, new_password):
    if not new_password:
        raise ValueError("La nueva contraseña es obligatoria.")

    reset_app_user_password(
        user_id=user_id,
        new_password=new_password,
    )