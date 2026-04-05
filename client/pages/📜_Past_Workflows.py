"""Historical workflows the user participated in or started."""

import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.api_client import ApprovClient
from client.form_renderer import render_form, render_audit_trail

st.set_page_config(page_title="Past Workflows", page_icon="📜", layout="wide")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please login first.")
    st.stop()

client: ApprovClient = st.session_state.api_client
client.token = st.session_state.token

st.title("📜 Past Workflows")

# Pagination
col1, col2 = st.columns(2)
page = col1.number_input("Page", min_value=1, value=1, step=1)
page_size = col2.selectbox("Per page", [10, 25, 50], index=1)
offset = (page - 1) * page_size

try:
    workflows = client.get_past_workflows(limit=page_size, offset=offset)
except Exception as e:
    st.error(f"Failed to load workflows: {e}")
    st.stop()

if not workflows:
    st.info("No past workflows found.")
else:
    df = pd.DataFrame(workflows)
    display_cols = [c for c in ["instance_id", "wf_def_name", "current_status", "started_by", "created_at", "completed_at"] if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)

    # View details
    st.subheader("View Details")
    instance_ids = [w["instance_id"] for w in workflows]
    selected_id = st.selectbox("Select workflow instance", instance_ids)

    if selected_id and st.button("View"):
        try:
            wf = client.get_workflow(selected_id)
            st.write(f"**Status:** `{wf['current_status']}`")
            st.write(f"**Started by:** {wf.get('started_by', 'N/A')}")

            # Show form in read-only mode
            form_spec = client.get_form_spec(selected_id)
            # Override all fields to disabled for read-only view
            for field in form_spec.get("fields", []):
                field["disabled"] = True
            form_spec["actions"] = []  # No actions for read-only
            render_form(form_spec)

            st.divider()
            st.subheader("Audit Trail")
            render_audit_trail(wf.get("audit_trail", []))
        except Exception as e:
            st.error(f"Failed to load workflow details: {e}")
