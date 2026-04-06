import streamlit as st
from services.admin_service import (
    change_app_user_password,
    delete_user,
    get_all_app_users,
    get_all_users,
    insert_app_user,
    insert_user,
    save_app_user,
    update_user,
)


def render_admin_panel():
    st.title("⚙️ Admin Panel")

    tab1, tab2 = st.tabs(
        [
            "Usuarios operativos",
            "Accesos a la app",
        ]
    )

    # -------------------------------------------------------------------------
    # Tab 1: Existing operational catalog
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("## Crear nuevo usuario operativo")

        col1, col2, col3 = st.columns(3)

        with col1:
            usuario = st.text_input("Usuario", key="oper_user_usuario")

        with col2:
            agente = st.text_input("Agente", key="oper_user_agente")

        with col3:
            estacion = st.text_input("Estación", key="oper_user_estacion")

        if st.button("Agregar usuario operativo", key="btn_add_oper_user"):
            if usuario:
                try:
                    insert_user(usuario, agente, estacion)
                    st.success("Usuario operativo agregado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo agregar el usuario operativo: {e}")
            else:
                st.warning("Usuario es obligatorio.")

        st.markdown("---")
        st.markdown("## Lista de usuarios operativos")

        df = get_all_users()

        if df.empty:
            st.info("No hay usuarios operativos cargados.")
        else:
            for _, row in df.iterrows():
                with st.expander(f"{row['usuario']}"):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        new_usuario = st.text_input(
                            "Usuario",
                            value=row["usuario"],
                            key=f"user_{row['id']}",
                        )

                    with col2:
                        new_agente = st.text_input(
                            "Agente",
                            value=row["agente"],
                            key=f"agent_{row['id']}",
                        )

                    with col3:
                        new_estacion = st.text_input(
                            "Estación",
                            value=row["estacion"],
                            key=f"station_{row['id']}",
                        )

                    with col4:
                        activo = st.checkbox(
                            "Activo",
                            value=bool(row["activo"]),
                            key=f"active_{row['id']}",
                        )

                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("Guardar", key=f"save_{row['id']}"):
                            try:
                                update_user(
                                    row["id"],
                                    new_usuario,
                                    new_agente,
                                    new_estacion,
                                    activo,
                                )
                                st.success("Usuario operativo actualizado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"No se pudo actualizar: {e}")

                    with col_b:
                        if st.button("Eliminar", key=f"delete_{row['id']}"):
                            try:
                                delete_user(row["id"])
                                st.warning("Usuario operativo eliminado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"No se pudo eliminar: {e}")

    # -------------------------------------------------------------------------
    # Tab 2: App login users
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("## Crear acceso a la app")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            username = st.text_input("Login", key="app_login_username")

        with c2:
            full_name = st.text_input("Nombre completo", key="app_login_full_name")

        with c3:
            role = st.selectbox(
                "Rol",
                ["user", "admin"],
                index=0,
                key="app_login_role",
            )

        with c4:
            password = st.text_input(
                "Contraseña temporal",
                type="password",
                key="app_login_password",
            )

        active = st.checkbox(
            "Activo",
            value=True,
            key="app_login_active",
        )

        if st.button("Crear acceso", key="btn_create_app_access"):
            try:
                insert_app_user(
                    username=username,
                    password=password,
                    full_name=full_name,
                    role=role,
                    is_active=active,
                )
                st.success("Acceso creado.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo crear el acceso: {e}")

        st.markdown("---")
        st.markdown("## Accesos existentes")

        app_users_df = get_all_app_users()

        if app_users_df.empty:
            st.info("No hay accesos creados.")
            return

        for _, row in app_users_df.iterrows():
            label_name = row["full_name"] if row["full_name"] else row["username"]
            label_role = row["role"]
            status = "Activo" if bool(row["is_active"]) else "Inactivo"

            with st.expander(f"{label_name}  |  {row['username']}  |  {label_role}  |  {status}"):
                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    edit_username = st.text_input(
                        "Login",
                        value=row["username"],
                        key=f"app_username_{row['id']}",
                    )

                with c2:
                    edit_full_name = st.text_input(
                        "Nombre completo",
                        value=row["full_name"] or "",
                        key=f"app_full_name_{row['id']}",
                    )

                with c3:
                    current_role_index = 0 if row["role"] == "user" else 1
                    edit_role = st.selectbox(
                        "Rol",
                        ["user", "admin"],
                        index=current_role_index,
                        key=f"app_role_{row['id']}",
                    )

                with c4:
                    edit_is_active = st.checkbox(
                        "Activo",
                        value=bool(row["is_active"]),
                        key=f"app_active_{row['id']}",
                    )

                col_save, col_pwd = st.columns(2)

                with col_save:
                    if st.button("Guardar acceso", key=f"save_app_user_{row['id']}"):
                        try:
                            save_app_user(
                                user_id=int(row["id"]),
                                username=edit_username,
                                full_name=edit_full_name,
                                role=edit_role,
                                is_active=edit_is_active,
                            )
                            st.success("Acceso actualizado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo actualizar el acceso: {e}")

                with col_pwd:
                    new_password = st.text_input(
                        "Nueva contraseña",
                        type="password",
                        key=f"app_new_password_{row['id']}",
                    )

                    if st.button("Resetear contraseña", key=f"reset_pwd_{row['id']}"):
                        try:
                            change_app_user_password(
                                user_id=int(row["id"]),
                                new_password=new_password,
                            )
                            st.success("Contraseña actualizada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo cambiar la contraseña: {e}")