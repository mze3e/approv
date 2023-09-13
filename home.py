import streamlit as st
from form import Form
import duckdb
import json

form = Form(st, 'form.yaml')

with open('data.json', 'r') as f:
    form_data = dict(json.loads(f.read()))


form.get_form(form_data)
st.header("Form Data")
st.write(form.get_form_data())
