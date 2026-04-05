"""ApproV - Home page: Login + Workflow interaction."""

import streamlit as st
import sys
import os

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.api_client import ApprovClient, ValidationError
from client.form_renderer import render_form, render_audit_trail

st.set_page_config(page_title="ApproV", page_icon="🏠", layout="wide")

API_URL = os.environ.get("APPROV_API_URL", "http://localhost:8000")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = ApprovClient(API_URL)

client: ApprovClient = st.session_state.api_client


def show_login():
    """Render login form."""
    st.title("ApproV")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            try:
                data = client.login(username, password)
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")


def show_sidebar():
    """Show user info and logout in sidebar."""
    user = st.session_state.user
    with st.sidebar:
        st.write(f"**{user['username']}**")
        st.caption(f"Roles: {', '.join(user.get('roles', []))}")
        if st.button("Logout"):
            for key in ["token", "user", "active_instance_id"]:
                st.session_state.pop(key, None)
            client.token = None
            st.rerun()


def show_home():
    """Main workflow interaction page."""
    show_sidebar()
    st.title("ApproV")

    # Start new workflow section
    st.subheader("Start New Workflow")
    try:
        definitions = client.get_workflow_definitions()
    except Exception:
        definitions = []

    if definitions:
        options = {d["name"]: d["wf_def_id"] for d in definitions}
        selected = st.selectbox("Workflow", list(options.keys()))

        if st.button("Start Workflow"):
            try:
                result = client.start_workflow(options[selected])
                st.session_state.active_instance_id = result["instance_id"]
                st.success(f"Workflow started (Instance #{result['instance_id']})")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start workflow: {e}")
    else:
        st.info("No workflow definitions available.")

    st.divider()

    # Active workflow section
    instance_id = st.session_state.get("active_instance_id")
    if instance_id:
        st.subheader(f"Workflow Instance #{instance_id}")

        try:
            form_spec = client.get_form_spec(instance_id)
        except Exception as e:
            st.error(f"Failed to load form: {e}")
            return

        st.caption(f"Status: **{form_spec['status']}**")

        if form_spec["status"] == "stop":
            st.success("Workflow completed.")
            # Show audit trail
            try:
                wf = client.get_workflow(instance_id)
                render_audit_trail(wf.get("audit_trail", []))
            except Exception:
                pass
            if st.button("Clear"):
                del st.session_state.active_instance_id
                st.rerun()
            return

        # Render dynamic form
        field_values, action_key = render_form(form_spec)

        if action_key and field_values is not None:
            try:
                result = client.submit_action(instance_id, action_key, field_values)
                st.session_state.active_instance_id = result["instance_id"]
                st.rerun()
            except ValidationError as e:
                st.session_state.validation_errors = e.errors
                st.rerun()
            except Exception as e:
                st.error(f"Action failed: {e}")

        # Show audit trail below form
        st.divider()
        st.subheader("Audit Trail")
        try:
            wf = client.get_workflow(instance_id)
            render_audit_trail(wf.get("audit_trail", []))
        except Exception:
            pass


# Main flow
if "token" not in st.session_state or not st.session_state.token:
    show_login()
else:
    client.token = st.session_state.token
    show_home()
