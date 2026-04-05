"""Pending workflow items for the logged-in user."""

import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.api_client import ApprovClient

st.set_page_config(page_title="Pending Items", page_icon="📋", layout="wide")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please login first.")
    st.stop()

client: ApprovClient = st.session_state.api_client
client.token = st.session_state.token

st.title("📋 Pending Items")
st.caption("Workflow items requiring your action")

try:
    tasks = client.get_pending_tasks()
except Exception as e:
    st.error(f"Failed to load pending tasks: {e}")
    st.stop()

if not tasks:
    st.info("No pending items for your role.")
else:
    for task in tasks:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{task['wf_def_name']}**")
            col2.write(f"Status: `{task['current_status']}`")
            col3.write(f"Role: `{task.get('assigned_role', 'N/A')}`")
            if col4.button("Open", key=f"open_{task['instance_id']}"):
                st.session_state.active_instance_id = task["instance_id"]
                st.switch_page("🏠_Home.py")

    st.divider()
    st.subheader("Summary")
    df = pd.DataFrame(tasks)
    display_cols = [c for c in ["instance_id", "wf_def_name", "current_status", "assigned_role", "updated_at"] if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)
