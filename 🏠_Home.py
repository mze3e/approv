import streamlit as st
from approv.Form import Form
import duckdb
import json
import yaml
from approv.Workflow import Workflow

with open('workflow.yaml', 'r') as f:
    workflow_config = yaml.safe_load(f.read())

with open('form.yaml', 'r') as f:
    form_config = yaml.safe_load(f.read())

#print(form_config)
st.selectbox("User", ["GENERAL_USER","PRESIDENT_USER"], key="user")

if 'form_data' not in st.session_state:
    with open('data.json', 'r') as f:
        st.session_state.form_data = dict(json.loads(f.read()))

if 'workflow' not in st.session_state:
    st.session_state.workflow = Workflow(st, workflow_config, form_config, st.session_state.form_data)

st.write(st.session_state.workflow.current_status)

if st.button("Start Workflow"):
    st.session_state.workflow.process_workflow(st.session_state.user, st.session_state.form_data)

if 'form_data' in st.session_state:
    #workflow.get_form(data=st.session_state.form_data, user=st.session_state.user, actions={'submit': {'title':"Submit"}})
    st.session_state.workflow.get_form(user_role=st.session_state.user)

    
# if 'form_data' in st.session_state:
#     if st.session_state.form_data not in ['start','stop']:
#         if st.button("Process"):
#             with st.spinner("Processing"):
#                 #st.write(workflow_config)
#                 form_data = workflow.form.get_form_data()
#                 st.write(workflow.current_status)
#                 try:
#                     updated_form_data = workflow.process_workflow(st.session_state.user, form_data)
#                 except Exception as e:
#                     st.error("Error occurred while processing")
#                     st.error(e)
#                 st.session_state.form_data = updated_form_data
#                 st.session_state.prev_form_data = st.session_state.form_data.copy()
#                 st.experimental_rerun()