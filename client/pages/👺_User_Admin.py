"""User and role administration."""

import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.api_client import ApprovClient

st.set_page_config(page_title="User Admin", page_icon="👺", layout="wide")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please login first.")
    st.stop()

client: ApprovClient = st.session_state.api_client
client.token = st.session_state.token

st.title("👺 User & Role Administration")

tab_users, tab_roles, tab_db = st.tabs(["Users", "Roles", "Database"])

# --- Users Tab ---
with tab_users:
    try:
        users = client.get_users()
        roles = client.get_roles()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        users, roles = [], []

    if users:
        st.subheader("Users")
        user_data = []
        for u in users:
            user_data.append({
                "ID": u["user_id"],
                "Username": u["username"],
                "Email": u.get("email", ""),
                "Roles": ", ".join(u.get("roles", [])),
            })
        st.dataframe(pd.DataFrame(user_data), use_container_width=True)

    # Add user form
    st.subheader("Add User")
    with st.form("add_user"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        password = st.text_input("Password", type="password")
        role_options = {r["role_name"]: r["role_id"] for r in roles}
        selected_roles = st.multiselect("Roles", list(role_options.keys()))

        if st.form_submit_button("Create User", use_container_width=True):
            if not username or not password:
                st.error("Username and password are required.")
            else:
                try:
                    role_ids = [role_options[r] for r in selected_roles]
                    client.create_user({
                        "username": username,
                        "email": email,
                        "phone": phone,
                        "password": password,
                        "role_ids": role_ids,
                    })
                    st.success(f"User '{username}' created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    # Edit user
    if users:
        st.subheader("Edit User")
        user_options = {u["username"]: u["user_id"] for u in users}
        selected_user = st.selectbox("Select User", list(user_options.keys()))
        user_id = user_options[selected_user]
        current = next(u for u in users if u["user_id"] == user_id)

        with st.form("edit_user"):
            new_email = st.text_input("Email", value=current.get("email", ""))
            new_phone = st.text_input("Phone")
            new_password = st.text_input("New Password (leave blank to keep)", type="password")
            new_roles = st.multiselect(
                "Roles",
                list(role_options.keys()),
                default=current.get("roles", []),
            )

            if st.form_submit_button("Update User", use_container_width=True):
                try:
                    update_data = {
                        "email": new_email,
                        "role_ids": [role_options[r] for r in new_roles],
                    }
                    if new_phone:
                        update_data["phone"] = new_phone
                    if new_password:
                        update_data["password"] = new_password
                    client.update_user(user_id, update_data)
                    st.success("User updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

# --- Roles Tab ---
with tab_roles:
    try:
        roles = client.get_roles()
    except Exception as e:
        st.error(f"Failed to load roles: {e}")
        roles = []

    if roles:
        st.subheader("Roles")
        role_data = []
        for r in roles:
            role_data.append({
                "ID": r["role_id"],
                "Name": r["role_name"],
                "Description": r.get("description", ""),
                "Permissions": ", ".join(r.get("permissions", [])),
            })
        st.dataframe(pd.DataFrame(role_data), use_container_width=True)

    st.subheader("Add Role")
    with st.form("add_role"):
        role_name = st.text_input("Role Name")
        role_desc = st.text_input("Description")

        if st.form_submit_button("Create Role", use_container_width=True):
            if not role_name:
                st.error("Role name is required.")
            else:
                try:
                    client.create_role({"role_name": role_name, "description": role_desc})
                    st.success(f"Role '{role_name}' created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

# --- Database Tab ---
with tab_db:
    st.subheader("Database Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Export Database**")
        if st.button("Download DB", use_container_width=True):
            try:
                db_bytes = client.export_db()
                st.download_button(
                    "Save File",
                    data=db_bytes,
                    file_name="approv_export.db",
                    mime="application/octet-stream",
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col2:
        st.write("**Import Database**")
        uploaded = st.file_uploader("Upload .db file", type=["db"])
        if uploaded and st.button("Import", use_container_width=True):
            try:
                client.import_db(uploaded.read())
                st.success("Database imported.")
            except Exception as e:
                st.error(f"Import failed: {e}")

    with col3:
        st.write("**S3 Backup**")
        if st.button("Backup Now", use_container_width=True):
            try:
                result = client.backup_db()
                st.success(f"Backup complete: {result.get('key', '')}")
            except Exception as e:
                st.error(f"Backup failed: {e}")
