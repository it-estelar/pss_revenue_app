from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def get_database_url() -> str:
    # 🔥 FORZAR ruta absoluta del proyecto
    base_dir = Path(__file__).resolve().parent
    env_path = base_dir / ".env"

    # cargar SIEMPRE desde ruta absoluta
    load_dotenv(env_path)

    db_url = os.getenv("DATABASE_URL", "").strip()

    if not db_url:
        raise RuntimeError(
            "DATABASE_URL no está configurado. "
            "Verifica que el archivo .env exista y tenga la variable."
        )

    return db_url