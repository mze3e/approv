import streamlit as st
from form import Form
import duckdb
import json
import yaml

form = Form(st, 'form.yaml')
st.selectbox("User", ["GENERAL_USER","PRESIDENT_USER"], key="user")

if 'form_data' not in st.session_state:
    with open('data.json', 'r') as f:
        form_data = dict(json.loads(f.read()))
        st.session_state.form_data = form_data

form.get_form(data=st.session_state.form_data, user=st.session_state.user, actions={'submit': {'title':"Submit"}})
st.session_state.form_data = form.get_form_data()

st.write(st.session_state.form_data)

from approv.Workflow import Workflow

with open('workflow.yaml', 'r') as f:
    workflow_config = yaml.safe_load(f.read())

if st.button("Process"):
    #st.write(workflow_config)
    form_data = form.get_form_data()
    workflow = Workflow(workflow_config, form_data)
    st.write(workflow.current_status)
    updated_form_data = workflow.process_workflow("GENERAL_USER", form_data)
    st.session_state.form_data = updated_form_data
    st.write(st.session_state.form_data)
    st.experimental_rerun()