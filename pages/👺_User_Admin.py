import streamlit as st
import pandas as pd
import yaml


# with open('users_and_roles.yaml', 'r') as f:
#     data = yaml.safe_load(f.read())

import duckdb
# create a connection to a file called 'file.db'

import duckdb
# create a connection to a file called 'file.db'

def ddql(sql):
    con = duckdb.connect('bpms.db')
    try:
        return con.sql(sql).df().copy()
    except Exception as e:
        return con.sql(sql)
    finally:
        con.close()

query = st.text_input("Query")
if st.button("Execute"):
    st.dataframe(ddql(query))

# Display Users Table
st.subheader("Users")
#users_df = pd.DataFrame(data["User"])
users_df = ddql("select * from users")
st.table(users_df)

# Display Roles Table
st.subheader("Roles")
# roles_df = pd.DataFrame({
#     'Role': list(data["Role"].keys()),
#     'Users': [', '.join(role_data["Users"]) for role_data in data["Role"].values()],
#     'Permissions': [', '.join(role_data.get("Permissions", [])) for role_data in data["Role"].values()]
# })
roles_df = ddql("select * from roles")
st.table(roles_df)

# Parsing Permissions, Roles, and Users
permissions_mapping = {}
# for role, role_data in data["Role"].items():
#     for permission in role_data.get("Permissions", []):
#         if permission not in permissions_mapping:
#             permissions_mapping[permission] = {'roles': [], 'users': []}
#         permissions_mapping[permission]['roles'].append(role)
#         for user in role_data["Users"]:
#             if user not in permissions_mapping[permission]['users']:
#                 permissions_mapping[permission]['users'].append(user)

# Construct DataFrame for Permissions Display
# permissions_df = pd.DataFrame({
#     'Permission': list(permissions_mapping.keys()),
#     'Roles': [', '.join(info['roles']) for info in permissions_mapping.values()],
#     'Users': [', '.join(info['users']) for info in permissions_mapping.values()]
# })

permissions_df = ddql("select * from permissions")

# Display Permissions Table
st.subheader("Permissions")
st.table(permissions_df)


# Form to Add User
with st.form("user_form"):
    st.subheader("Add User")
    user_name = st.text_input("Username")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    submit_user = st.form_submit_button("Add User")
    
    if submit_user:
        if user_name not in data["User"]:
            data["User"][user_name] = {
                "email": email,
                "phone": phone
            }
            st.success(f"Added {user_name}")
        else:
            st.warning(f"{user_name} already exists!")

# Form to Add Role
with st.form("role_form"):
    st.subheader("Add Role")
    role_name = st.text_input("Role Name")
    users = st.text_area("Users (comma separated)").split(',')
    permissions = st.text_area("Permissions (comma separated)").split(',')
    submit_role = st.form_submit_button("Add Role")
    
    if submit_role:
        if role_name not in data["Role"]:
            data["Role"][role_name] = {
                "Users": users,
                "Permissions": permissions
            }
            st.success(f"Added role {role_name}")
        else:
            st.warning(f"{role_name} already exists!")

# Form to Add User to Role
with st.form("user_role_form"):
    st.subheader("Add User to Role")
    user_name = st.selectbox("Select User", list(data["User"].keys()))
    role_name = st.selectbox("Select Role", list(data["Role"].keys()))
    submit_user_role = st.form_submit_button("Add User to Role")

    if submit_user_role:
        if user_name not in data["Role"][role_name]["Users"]:
            data["Role"][role_name]["Users"].append(user_name)
            st.success(f"Added {user_name} to {role_name}")
        else:
            st.warning(f"{user_name} already in {role_name}")

# Note: In a real-world application, you'd want to save the updated data back to the YAML file or database.


# Form to Add Permission
with st.form("permission_form"):
    st.subheader("Add Permission")
    permission_name = st.text_input("Permission Name")
    submit_permission = st.form_submit_button("Add Permission")

    if submit_permission:
        if permission_name not in all_permissions:
            all_permissions.add(permission_name)
            st.success(f"Added permission {permission_name}")
        else:
            st.warning(f"{permission_name} already exists!")

con.close()