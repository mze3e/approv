"""Workflow definition administration."""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.api_client import ApprovClient

st.set_page_config(page_title="Workflow Admin", page_icon="⚙️", layout="wide")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please login first.")
    st.stop()

client: ApprovClient = st.session_state.api_client
client.token = st.session_state.token

st.title("⚙️ Workflow Administration")

# List definitions
try:
    definitions = client.get_workflow_definitions()
except Exception as e:
    st.error(f"Failed to load definitions: {e}")
    definitions = []

tab_edit, tab_create = st.tabs(["Edit Existing", "Create New"])

with tab_edit:
    if not definitions:
        st.info("No workflow definitions found.")
    else:
        options = {d["name"]: d["wf_def_id"] for d in definitions}
        selected_name = st.selectbox("Select Workflow Definition", list(options.keys()))
        wf_def_id = options[selected_name]

        try:
            detail = client.get_workflow_definition(wf_def_id)
        except Exception as e:
            st.error(f"Failed to load definition: {e}")
            st.stop()

        st.subheader("Workflow YAML")
        workflow_yaml = st.text_area(
            "workflow.yaml",
            value=detail.get("workflow_yaml", ""),
            height=400,
            key="edit_workflow_yaml",
        )

        st.subheader("Form YAML")
        form_yaml = st.text_area(
            "form.yaml",
            value=detail.get("form_yaml", ""),
            height=300,
            key="edit_form_yaml",
        )

        st.subheader("Seed Data JSON")
        seed_data = st.text_area(
            "data.json",
            value=detail.get("seed_data_json", "") or "",
            height=200,
            key="edit_seed_data",
        )

        col1, col2 = st.columns(2)
        if col1.button("Save Changes", use_container_width=True):
            try:
                client.update_workflow_definition(wf_def_id, {
                    "workflow_yaml": workflow_yaml,
                    "form_yaml": form_yaml,
                    "seed_data_json": seed_data if seed_data.strip() else None,
                })
                st.success("Workflow definition updated.")
            except Exception as e:
                st.error(f"Save failed: {e}")

        is_active = detail.get("is_active", True)
        if col2.button("Deactivate" if is_active else "Activate", use_container_width=True):
            try:
                client.update_workflow_definition(wf_def_id, {"is_active": not is_active})
                st.success("Status updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

with tab_create:
    st.subheader("Create New Workflow Definition")

    with st.form("create_wf_def"):
        name = st.text_input("Name")
        description = st.text_area("Description", height=80)
        wf_yaml = st.text_area("Workflow YAML", height=300)
        f_yaml = st.text_area("Form YAML", height=200)
        s_data = st.text_area("Seed Data JSON (optional)", height=100)

        if st.form_submit_button("Create", use_container_width=True):
            if not name or not wf_yaml or not f_yaml:
                st.error("Name, Workflow YAML, and Form YAML are required.")
            else:
                try:
                    client.create_workflow_definition({
                        "name": name,
                        "description": description,
                        "workflow_yaml": wf_yaml,
                        "form_yaml": f_yaml,
                        "seed_data_json": s_data if s_data.strip() else None,
                    })
                    st.success(f"Workflow '{name}' created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Creation failed: {e}")
