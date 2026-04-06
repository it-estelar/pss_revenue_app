from __future__ import annotations

import pandas as pd
import bcrypt
from sqlalchemy import text

from db_data_loader import _get_engine


def hash_password(password: str) -> str:
    if password is None:
        raise ValueError("La contraseña no puede ser nula.")

    password = str(password).strip()

    if not password:
        raise ValueError("La contraseña no puede estar vacía.")

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password is None or password_hash is None:
            return False

        return bcrypt.checkpw(
            str(password).encode("utf-8"),
            str(password_hash).encode("utf-8"),
        )
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> dict | None:
    username = (username or "").strip()

    if not username or not password:
        return None

    engine = _get_engine()

    sql = text("""
        SELECT
            id,
            username,
            password_hash,
            full_name,
            role,
            is_active
        FROM estelar_gds.app_users
        WHERE lower(username) = lower(:username)
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(sql, {"username": username}).mappings().first()

    if not row:
        return None

    if not bool(row["is_active"]):
        return None

    if not verify_password(password, row["password_hash"]):
        return None

    return {
        "id": int(row["id"]),
        "username": row["username"],
        "full_name": row["full_name"] or row["username"],
        "role": (row["role"] or "user").strip().lower(),
    }


def create_app_user(
    username: str,
    password: str,
    full_name: str = "",
    role: str = "user",
    is_active: bool = True,
):
    username = (username or "").strip()
    full_name = (full_name or "").strip()
    role = (role or "user").strip().lower()

    if not username:
        raise ValueError("El username es obligatorio.")

    if role not in {"admin", "user"}:
        raise ValueError("Rol inválido.")

    password_hash = hash_password(password)
    engine = _get_engine()

    sql = text("""
        INSERT INTO estelar_gds.app_users (
            username,
            password_hash,
            full_name,
            role,
            is_active,
            created_at,
            updated_at
        )
        VALUES (
            :username,
            :password_hash,
            :full_name,
            :role,
            :is_active,
            NOW(),
            NOW()
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": role,
                "is_active": bool(is_active),
            },
        )


def update_app_user(
    user_id: int,
    username: str,
    full_name: str = "",
    role: str = "user",
    is_active: bool = True,
):
    username = (username or "").strip()
    full_name = (full_name or "").strip()
    role = (role or "user").strip().lower()

    if not username:
        raise ValueError("El username es obligatorio.")

    if role not in {"admin", "user"}:
        raise ValueError("Rol inválido.")

    engine = _get_engine()

    sql = text("""
        UPDATE estelar_gds.app_users
        SET
            username = :username,
            full_name = :full_name,
            role = :role,
            is_active = :is_active,
            updated_at = NOW()
        WHERE id = :user_id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "user_id": int(user_id),
                "username": username,
                "full_name": full_name,
                "role": role,
                "is_active": bool(is_active),
            },
        )


def reset_app_user_password(user_id: int, new_password: str):
    password_hash = hash_password(new_password)
    engine = _get_engine()

    sql = text("""
        UPDATE estelar_gds.app_users
        SET
            password_hash = :password_hash,
            updated_at = NOW()
        WHERE id = :user_id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "user_id": int(user_id),
                "password_hash": password_hash,
            },
        )


def get_app_users() -> pd.DataFrame:
    engine = _get_engine()

    sql = text("""
        SELECT
            id,
            username,
            full_name,
            role,
            is_active,
            created_at,
            updated_at
        FROM estelar_gds.app_users
        ORDER BY username
    """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn)