import streamlit as st
import yaml
import xml.etree.ElementTree as ET
from streamlit_agraph import agraph, Node, Edge, Config


st.title("Admin Page for Workflow Management")


with open('workflow.yaml', 'r') as f:
    data = yaml.safe_load(f.read())

workflow = data['workflow']

# Display workflow nodes in a table
st.subheader("Workflow Nodes")
workflow_nodes = []
for key, value in workflow.items():
    workflow_nodes.append({
        'Node Name': key,
        'Class': value['class'],
        'ID': value['id'],
        'Require User Action': value['require_user_action']
    })
st.table(workflow_nodes)

# Create nodes and edges
nodes = []
edges = []

for node, details in workflow.items():
    nodes.append(Node(id=node, label=node, size=25, shape="box"))

for node, details in workflow.items():
    edge_label="Default"
    if 'outputs' in details:
        for output in details['outputs']:
            try:
                if 'conditions' in details:
                    for condition in details['conditions']:
                        if details['conditions'][condition]['next_status'] == output:
                            edge_label=f"{details['conditions'][condition]['attribute']} {details['conditions'][condition]['operator']} {details['conditions'][condition]['value']}"
            except:
                print("Error!")
                print(output)
                print(details['conditions'][condition])
                print(details['conditions'])
                
            edges.append(Edge(source=node, target=output, label=edge_label))

config = Config(width=1200, height=950, directed=True, physics=True, hierarchical=False)

agraph(nodes=nodes, edges=edges, config=config)

# Form to Edit Node
st.subheader("Edit Workflow Node")
edit_node_name = st.selectbox("Select Node to Edit", list(workflow.keys()))
selected_node = workflow[edit_node_name]
with st.form('edit_node_form'):
    node_name = st.text_input("Node Name", value=edit_node_name)
    node_class = st.selectbox("Node Class", ["Start", "Simple", "ExclusiveChoice", "RESTCall", "EmailNotify", "SMSNotify", "Cancel", "MultiChoice", "MutexChoice"], index=["Start", "Simple", "ExclusiveChoice", "RESTCall", "EmailNotify", "SMSNotify", "Cancel", "MultiChoice", "MutexChoice"].index(selected_node['class']))
    node_id = st.number_input("Node ID", value=selected_node['id'], format='%d')
    node_require_user_action = st.checkbox("Require User Action?", value=selected_node['require_user_action'])
    edit_node = st.form_submit_button("Edit Node")
    if edit_node:
        workflow[edit_node_name] = {
            'class': node_class,
            'id': node_id,
            'require_user_action': node_require_user_action
        }

# # Save changes (this can be expanded to save back to file, database, etc.)
# if st.button('Save Changes'):
#     with open('workflow.yaml', 'w') as f:
#         yaml.dump({'workflow': workflow}, f)

