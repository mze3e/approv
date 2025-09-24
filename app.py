"""
Main Shiny application for the BPMS (Business Process Management System)
Converted from Streamlit to Shiny Python
"""

from shiny import App, render, ui, reactive
import pandas as pd
import copy

# Import our configuration manager and new modules
from shiny_modules.config import config_manager, db_manager
from shiny_modules.workflow import ShinyWorkflow

# Initialize configurations
workflow_config = config_manager.get_workflow_config()
form_config = config_manager.get_form_config()
initial_form_data = config_manager.get_form_data()

# Initialize workflow instance
workflow_instance = ShinyWorkflow(workflow_config, form_config, initial_form_data)
# Workflow renderer removed - using unified approach

# App UI
app_ui = ui.page_navbar(
    ui.nav_panel("Home", 
        ui.div(
            ui.h1("BPMS - Business Process Management System"),
            ui.br(),
            ui.input_selectize(
                "user_role", 
                "Select User Role:", 
                choices=["GENERAL_USER", "PRESIDENT_USER"],
                selected="GENERAL_USER"
            ),
            ui.br(),
            ui.input_action_button("start_workflow", "Start Workflow", class_="btn btn-primary"),
            ui.br(),
            ui.output_text("workflow_status_display"),
            ui.output_text("workflow_error_display"),
            ui.br(),
            ui.div(
                ui.h3("Dynamic Workflow Form"),
                ui.output_ui("dynamic_form_container"),
                ui.br(),
                ui.h4("Audit Trail"),
                ui.output_data_frame("audit_trail")
            )
        )
    ),
    ui.nav_panel("Workflow Admin",
        ui.div(
            ui.h1("Workflow Administration"),
            ui.br(),
            
            # Workflow Nodes Section
            ui.div(
                ui.h3("Workflow Nodes"),
                ui.output_data_frame("workflow_nodes_table"),
                ui.br(),
                
                # Node editing section
                ui.h4("Edit Workflow Node"),
                ui.output_ui("node_selector"),
                ui.output_ui("node_edit_form"),
                ui.br(),
                
                # Workflow visualization section
                ui.h4("Workflow Visualization"),
                ui.output_ui("workflow_graph_display"),
                ui.br(),
                
                # Node operations section
                ui.h4("Node Operations"),
                ui.div(
                    ui.input_action_button("add_new_node", "Add New Node", class_="btn btn-primary"),
                    ui.input_action_button("delete_selected_node", "Delete Selected Node", class_="btn btn-danger"),
                    ui.input_action_button("validate_workflow", "Validate Workflow", class_="btn btn-info"),
                    style="margin-bottom: 1rem;"
                ),
                
                # Save changes section
                ui.div(
                    ui.input_action_button("save_workflow_changes", "Save Changes", class_="btn btn-success"),
                    ui.input_action_button("reload_workflow_instance", "Reload Workflow Instance", class_="btn btn-warning"),
                    ui.output_text("save_status_display")
                )
            )
        )
    ),
    ui.nav_panel("User Admin",
        ui.div(
            ui.h1("User Administration"),
            # User Management Section
            ui.div(
                ui.h2("User Management"),
                ui.row(
                    ui.column(8,
                        ui.output_data_frame("users_table_display")
                    ),
                    ui.column(4,
                        ui.div(
                            ui.h4("User Details"),
                            ui.input_selectize("selected_user", "Select User:", choices={}, selected=None),
                            ui.input_text("user_username", "Username:", placeholder="Enter username"),
                            ui.input_text("user_email", "Email:", placeholder="Enter email address"),
                            ui.input_text("user_phone", "Phone:", placeholder="Enter phone number"),
                            ui.input_checkbox("user_is_active", "Active User", value=True),
                            ui.br(),
                            ui.input_action_button("add_new_user", "Add New User", class_="btn btn-success"),
                            ui.input_action_button("update_user", "Update User", class_="btn btn-primary"),
                            ui.input_action_button("delete_user", "Delete User", class_="btn btn-danger"),
                            ui.br(), ui.br(),
                            ui.h5("User Roles"),
                            ui.output_ui("user_roles_display"),
                            ui.input_selectize("assign_role_to_user", "Assign Role:", choices={}, selected=None),
                            ui.input_action_button("assign_role", "Assign Role", class_="btn btn-info"),
                            ui.input_action_button("remove_user_role", "Remove Role", class_="btn btn-warning")
                        )
                    )
                )
            ),
            ui.hr(),
            # Role Management Section  
            ui.div(
                ui.h2("Role Management"),
                ui.row(
                    ui.column(8,
                        ui.output_data_frame("roles_table_display")
                    ),
                    ui.column(4,
                        ui.div(
                            ui.h4("Role Details"),
                            ui.input_selectize("selected_role", "Select Role:", choices={}, selected=None),
                            ui.input_text("role_name", "Role Name:", placeholder="Enter role name"),
                            ui.input_text_area("role_description", "Description:", placeholder="Enter role description"),
                            ui.input_checkbox("role_is_active", "Active Role", value=True),
                            ui.br(),
                            ui.input_action_button("add_new_role", "Add New Role", class_="btn btn-success"),
                            ui.input_action_button("update_role", "Update Role", class_="btn btn-primary"),
                            ui.input_action_button("delete_role", "Delete Role", class_="btn btn-danger"),
                            ui.br(), ui.br(),
                            ui.h5("Role Permissions"),
                            ui.output_ui("role_permissions_display"),
                            ui.input_selectize("assign_permission_to_role", "Assign Permission:", choices={}, selected=None),
                            ui.input_action_button("assign_permission", "Assign Permission", class_="btn btn-info"),
                            ui.input_action_button("remove_role_permission", "Remove Permission", class_="btn btn-warning")
                        )
                    )
                )
            ),
            ui.hr(),
            # Permission Management Section
            ui.div(
                ui.h2("Permission Management"),
                ui.row(
                    ui.column(8,
                        ui.output_data_frame("permissions_table_display")
                    ),
                    ui.column(4,
                        ui.div(
                            ui.h4("Permission Details"),
                            ui.input_selectize("selected_permission", "Select Permission:", choices={}, selected=None),
                            ui.input_text("permission_name", "Permission Name:", placeholder="Enter permission name"),
                            ui.input_text_area("permission_description", "Description:", placeholder="Enter permission description"),
                            ui.input_checkbox("permission_is_active", "Active Permission", value=True),
                            ui.br(),
                            ui.input_action_button("add_new_permission", "Add New Permission", class_="btn btn-success"),
                            ui.input_action_button("update_permission", "Update Permission", class_="btn btn-primary"),
                            ui.input_action_button("delete_permission", "Delete Permission", class_="btn btn-danger")
                        )
                    )
                )
            ),
            ui.hr(),
            # System Status & SQL Console
            ui.div(
                ui.h3("System Administration"),
                ui.output_text("user_admin_status_display"),
                ui.br(),
                ui.h4("SQL Console (Read-Only)"),
                ui.input_text("sql_query", "SQL Query:", placeholder="Enter read-only SQL query (SELECT, SHOW, DESCRIBE, EXPLAIN)..."),
                ui.input_action_button("execute_query", "Execute", class_="btn btn-secondary"),
                ui.output_text("query_error_display"),
                ui.output_data_frame("query_results")
            )
        )
    ),
    title="BPMS - Shiny Version",
    id="page"
)

# Server logic
def server(input, output, session):
    # Reactive values for state management
    form_data = reactive.Value(initial_form_data)
    user_role_reactive = reactive.Value("GENERAL_USER")
    
    # Update user role when changed
    @reactive.Effect
    def update_user_role():
        user_role_reactive.set(input.user_role())
    
    # No longer using workflow renderer - using unified approach instead
    
    # Setup action handlers for form buttons
    def handle_form_action(action_name: str):
        """Handle form action button clicks"""
        user_role = input.user_role()
        
        # Collect current input values
        current_input = {}
        for field_name in workflow_instance.form.form_fields.keys():
            if hasattr(input, field_name):
                try:
                    current_input[field_name] = getattr(input, field_name)()
                except:
                    # Handle cases where input doesn't exist yet
                    current_input[field_name] = None
        
        # Process the workflow with the submitted action
        try:
            updated_data = workflow_instance.handle_form_submission(current_input, action_name, user_role)
            form_data.set(updated_data)
            workflow_instance.form_data = updated_data
        except Exception as e:
            workflow_instance.error_message.set(str(e))
    
    # Register action handlers
    workflow_instance.form_renderer.setup_action_handlers(input, handle_form_action)
    
    # Home page: Workflow status display
    @output
    @render.text
    def workflow_status_display():
        status = workflow_instance.current_status()
        processing = workflow_instance.processing()
        if processing:
            return f"Current Status: {status} (Processing...)"
        return f"Current Status: {status}"
    
    # Home page: Workflow error display
    @output
    @render.text
    def workflow_error_display():
        error = workflow_instance.error_message()
        return f"Error: {error}" if error else ""
    
    # Home page: Start workflow button
    @reactive.Effect
    @reactive.event(input.start_workflow)
    def handle_start_workflow():
        user_role = input.user_role()
        workflow_instance.initiate()
        # Process workflow to move beyond 'start' status
        try:
            updated_data = workflow_instance.process_workflow(user_role, form_data())
            form_data.set(updated_data)
            workflow_instance.form_data = updated_data
        except Exception as e:
            workflow_instance.error_message.set(str(e))
    
    # Workflow continuation effect for non-blocking processing
    @reactive.Effect
    def workflow_continuation():
        current_status = workflow_instance.current_status()
        user_role = input.user_role()
        
        # Auto-advance through non-user-action steps
        if current_status not in ['start', 'stop']:
            workflow_config = workflow_instance.config
            if current_status in workflow_config.get('workflow', {}):
                step_config = workflow_config['workflow'][current_status]
                
                # If this step doesn't require user action, auto-advance
                if not step_config.get('require_user_action', True):
                    # Schedule continuation with a slight delay
                    reactive.invalidate_later(0.5)
                    try:
                        current_data = form_data()
                        updated_data = workflow_instance.process_workflow(user_role, current_data)
                        form_data.set(updated_data)
                        workflow_instance.form_data = updated_data
                    except Exception as e:
                        workflow_instance.error_message.set(str(e))
    
    # Dynamic form rendering
    @output
    @render.ui
    def dynamic_form_container():
        current_status = workflow_instance.current_status()
        user_role = input.user_role()
        
        if current_status in ['start', 'stop']:
            if current_status == 'start':
                return ui.div(
                    ui.p("Click 'Start Workflow' to begin the process."),
                    class_="text-muted"
                )
            else:
                return ui.div(
                    ui.p("Workflow completed."),
                    class_="text-success"
                )
        
        # Create dynamic form for current workflow step
        try:
            form_elements = workflow_instance.create_form_ui(user_role)
            if form_elements:
                return ui.div(*form_elements)
            else:
                return ui.div(
                    ui.p("No form fields available for this step."),
                    class_="text-info"
                )
        except Exception as e:
            return ui.div(
                ui.p(f"Error rendering form: {str(e)}"),
                class_="text-danger"
            )
    
    # Audit trail data frame
    @output
    @render.data_frame
    def audit_trail():
        audit_data = workflow_instance.audit_data()
        if audit_data:
            return pd.DataFrame(audit_data)
        return pd.DataFrame(columns=['status', 'action', 'description', 'time', 'user'])
    
    # Reactive value to store query results
    query_result = reactive.Value(pd.DataFrame())
    query_error = reactive.Value("")
    
    # User Admin: Execute SQL query
    @reactive.Effect
    @reactive.event(input.execute_query)
    def handle_sql_query():
        query = input.sql_query().strip()
        if not query:
            return
            
        # Basic security: restrict to read-only operations for now
        query_upper = query.upper().strip()
        if not query_upper.startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            query_error.set("Error: Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed for security.")
            query_result.set(pd.DataFrame())
            return
            
        try:
            result = db_manager.execute_query(query)
            query_result.set(result)
            query_error.set("")
        except Exception as e:
            query_error.set(f"Database error: {str(e)}")
            query_result.set(pd.DataFrame())
    
    # User Admin: Query results
    @output
    @render.data_frame
    def query_results():
        result = query_result()
        if result.empty:
            return pd.DataFrame(columns=['No data'])
        return result
    
    # User Admin: Query error display
    @output
    @render.text
    def query_error_display():
        error = query_error()
        return error if error else ""
    
    # Database helper function
    def execute_db_query(query):
        """Execute database query and return DataFrame"""
        return db_manager.execute_query(query)
    
    # User Admin: Users table
    @output
    @render.data_frame
    def users_table():
        try:
            return db_manager.get_users()
        except Exception:
            return pd.DataFrame(columns=['username', 'email', 'phone'])
    
    # User Admin: Roles table
    @output
    @render.data_frame
    def roles_table():
        try:
            return db_manager.get_roles()
        except Exception:
            return pd.DataFrame(columns=['role_name', 'description'])
    
    # User Admin: Permissions table
    @output
    @render.data_frame
    def permissions_table():
        try:
            return db_manager.get_permissions()
        except Exception:
            return pd.DataFrame(columns=['permission_name', 'description'])
    
    # ==============================================================
    # USER ADMIN: ENTERPRISE-GRADE CRUD OPERATIONS & DATA MANAGEMENT
    # ==============================================================
    
    # Helper functions for User Admin database operations
    def execute_user_admin_query(query, params=None):
        """Execute user admin queries with proper error handling"""
        try:
            # SECURITY: For now using basic query execution
            # TODO: Implement parameterized queries to prevent SQL injection
            result = db_manager.execute_query(query)
            # Trigger UI refresh after any mutation
            if any(keyword in query.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                data_refresh_counter.set(data_refresh_counter() + 1)
            return result
        except Exception as e:
            user_admin_status.set(f"Database error: {str(e)}")
            return pd.DataFrame()
    
    def load_users_data():
        """Load comprehensive users data with role information"""
        query = """
        SELECT u.user_id, u.username, u.email, u.phone, u.is_active,
               STRING_AGG(r.role_name, ', ') as roles,
               u.created_at, u.updated_at
        FROM users u
        LEFT JOIN user_roles ur ON u.user_id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.role_id
        GROUP BY u.user_id, u.username, u.email, u.phone, u.is_active, u.created_at, u.updated_at
        ORDER BY u.username
        """
        return execute_user_admin_query(query)
    
    def load_roles_data():
        """Load comprehensive roles data with permission and user counts"""
        query = """
        SELECT r.role_id, r.role_name, r.description, r.is_active,
               COUNT(DISTINCT ur.user_id) as user_count,
               COUNT(DISTINCT rp.permission_id) as permission_count,
               r.created_at, r.updated_at
        FROM roles r
        LEFT JOIN user_roles ur ON r.role_id = ur.role_id
        LEFT JOIN role_permissions rp ON r.role_id = rp.role_id
        GROUP BY r.role_id, r.role_name, r.description, r.is_active, r.created_at, r.updated_at
        ORDER BY r.role_name
        """
        return execute_user_admin_query(query)
    
    def load_permissions_data():
        """Load comprehensive permissions data with usage information"""
        query = """
        SELECT p.permission_id, p.permission_name, p.description, p.is_active,
               COUNT(DISTINCT rp.role_id) as role_count,
               p.created_at
        FROM permissions p
        LEFT JOIN role_permissions rp ON p.permission_id = rp.permission_id
        GROUP BY p.permission_id, p.permission_name, p.description, p.is_active, p.created_at
        ORDER BY p.permission_name
        """
        return execute_user_admin_query(query)
    
    def get_available_roles():
        """Get all active roles for dropdown selection"""
        query = "SELECT role_id, role_name FROM roles WHERE is_active = TRUE ORDER BY role_name"
        df = execute_user_admin_query(query)
        if not df.empty:
            return {str(row['role_id']): row['role_name'] for _, row in df.iterrows()}
        return {}
    
    def get_available_permissions():
        """Get all active permissions for dropdown selection"""
        query = "SELECT permission_id, permission_name FROM permissions WHERE is_active = TRUE ORDER BY permission_name"
        df = execute_user_admin_query(query)
        if not df.empty:
            return {str(row['permission_id']): row['permission_name'] for _, row in df.iterrows()}
        return {}
    
    def get_user_roles(user_id):
        """Get roles assigned to a specific user"""
        query = f"""
        SELECT r.role_id, r.role_name, ur.assigned_at
        FROM roles r
        JOIN user_roles ur ON r.role_id = ur.role_id
        WHERE ur.user_id = {user_id}
        ORDER BY r.role_name
        """
        return execute_user_admin_query(query)
    
    def get_role_permissions(role_id):
        """Get permissions assigned to a specific role"""
        query = f"""
        SELECT p.permission_id, p.permission_name, rp.assigned_at
        FROM permissions p
        JOIN role_permissions rp ON p.permission_id = rp.permission_id
        WHERE rp.role_id = {role_id}
        ORDER BY p.permission_name
        """
        return execute_user_admin_query(query)
    
    # ==============================================================
    # USER ADMIN: TABLE DISPLAYS WITH ENHANCED DATA
    # ==============================================================
    
    @output
    @render.data_frame
    def users_table_display():
        """Enhanced users table with comprehensive information - reactive to changes"""
        # Force refresh when data changes
        data_refresh_counter()
        try:
            df = load_users_data()
            current_users_data.set(df)
            return df
        except Exception:
            return pd.DataFrame(columns=['username', 'email', 'phone', 'roles', 'is_active'])
    
    @output
    @render.data_frame
    def roles_table_display():
        """Enhanced roles table with user and permission counts - reactive to changes"""
        # Force refresh when data changes
        data_refresh_counter()
        try:
            df = load_roles_data()
            current_roles_data.set(df)
            return df
        except Exception:
            return pd.DataFrame(columns=['role_name', 'description', 'user_count', 'permission_count', 'is_active'])
    
    @output
    @render.data_frame
    def permissions_table_display():
        """Enhanced permissions table with usage information - reactive to changes"""
        # Force refresh when data changes
        data_refresh_counter()
        try:
            df = load_permissions_data()
            current_permissions_data.set(df)
            return df
        except Exception:
            return pd.DataFrame(columns=['permission_name', 'description', 'role_count', 'is_active'])
    
    # Dynamic dropdown population - reactive to data changes
    @reactive.Effect
    def update_user_admin_dropdowns():
        """Update dropdown choices based on current data - reactive to changes"""
        # React to data changes
        data_refresh_counter()
        
        # Update user choices
        users_df = current_users_data()
        if not users_df.empty:
            user_choices = {str(row['user_id']): f"{row['username']} ({row['email']})" 
                          for _, row in users_df.iterrows()}
            ui.update_selectize("selected_user", choices=user_choices)
        
        # Update role choices
        roles_df = current_roles_data()
        if not roles_df.empty:
            role_choices = {str(row['role_id']): row['role_name'] 
                          for _, row in roles_df.iterrows()}
            ui.update_selectize("selected_role", choices=role_choices)
            ui.update_selectize("assign_role_to_user", choices=role_choices)
        
        # Update permission choices
        permissions_df = current_permissions_data()
        if not permissions_df.empty:
            permission_choices = {str(row['permission_id']): row['permission_name'] 
                                for _, row in permissions_df.iterrows()}
            ui.update_selectize("selected_permission", choices=permission_choices)
            ui.update_selectize("assign_permission_to_role", choices=permission_choices)
    
    # User role assignments display
    @output
    @render.ui
    def user_roles_display():
        """Display roles assigned to selected user"""
        selected_user_id = input.selected_user()
        if not selected_user_id:
            return ui.p("Select a user to view their roles")
        
        try:
            roles_df = get_user_roles(int(selected_user_id))
            if roles_df.empty:
                return ui.p("No roles assigned")
            
            role_badges = [ui.span(role, class_="badge badge-primary me-1") 
                          for role in roles_df['role_name']]
            return ui.div(*role_badges)
        except Exception:
            return ui.p("Error loading user roles")
    
    # Role permission assignments display
    @output
    @render.ui
    def role_permissions_display():
        """Display permissions assigned to selected role"""
        selected_role_id = input.selected_role()
        if not selected_role_id:
            return ui.p("Select a role to view its permissions")
        
        try:
            permissions_df = get_role_permissions(int(selected_role_id))
            if permissions_df.empty:
                return ui.p("No permissions assigned")
            
            permission_badges = [ui.span(perm, class_="badge badge-info me-1") 
                               for perm in permissions_df['permission_name']]
            return ui.div(*permission_badges)
        except Exception:
            return ui.p("Error loading role permissions")
    
    # User Admin status display
    @output
    @render.text
    def user_admin_status_display():
        """Display User Admin operation status"""
        return user_admin_status()
    
    # ==============================================================
    # USER ADMIN: ENTERPRISE-GRADE CRUD OPERATIONS
    # ==============================================================
    
    # User CRUD Operations
    @reactive.Effect
    @reactive.event(input.add_new_user)
    def handle_add_new_user():
        """Add new user with validation"""
        username = input.user_username().strip()
        email = input.user_email().strip()
        phone = input.user_phone().strip()
        is_active = input.user_is_active()
        
        if not username or not email:
            user_admin_status.set("Error: Username and email are required")
            return
        
        try:
            # Check for existing username/email
            check_query = f"SELECT COUNT(*) as count FROM users WHERE username = '{username}' OR email = '{email}'"
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Username '{username}' or email '{email}' already exists")
                return
            
            # Insert new user
            insert_query = f"""
            INSERT INTO users (username, email, phone, is_active, updated_at) 
            VALUES ('{username}', '{email}', '{phone}', {is_active}, CURRENT_TIMESTAMP)
            """
            execute_user_admin_query(insert_query)
            user_admin_status.set(f"✓ User '{username}' created successfully")
            
            # Clear form
            ui.update_text("user_username", value="")
            ui.update_text("user_email", value="")
            ui.update_text("user_phone", value="")
            
        except Exception as e:
            user_admin_status.set(f"Error creating user: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.update_user)
    def handle_update_user():
        """Update selected user with validation"""
        selected_user_id = input.selected_user()
        if not selected_user_id:
            user_admin_status.set("Error: No user selected for update")
            return
        
        username = input.user_username().strip()
        email = input.user_email().strip()
        phone = input.user_phone().strip()
        is_active = input.user_is_active()
        
        if not username or not email:
            user_admin_status.set("Error: Username and email are required")
            return
        
        try:
            # Check for conflicts with other users
            check_query = f"""
            SELECT COUNT(*) as count FROM users 
            WHERE (username = '{username}' OR email = '{email}') 
            AND user_id != {selected_user_id}
            """
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Username '{username}' or email '{email}' already exists")
                return
            
            # Update user
            update_query = f"""
            UPDATE users 
            SET username = '{username}', email = '{email}', phone = '{phone}', 
                is_active = {is_active}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = {selected_user_id}
            """
            execute_user_admin_query(update_query)
            user_admin_status.set(f"✓ User updated successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error updating user: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.delete_user)
    def handle_delete_user():
        """Delete selected user with reference safety"""
        selected_user_id = input.selected_user()
        if not selected_user_id:
            user_admin_status.set("Error: No user selected for deletion")
            return
        
        try:
            # Check for role assignments
            check_query = f"SELECT COUNT(*) as count FROM user_roles WHERE user_id = {selected_user_id}"
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set("🚫 DELETION BLOCKED: User has assigned roles. Remove roles first.")
                return
            
            # Safe to delete user
            delete_query = f"DELETE FROM users WHERE user_id = {selected_user_id}"
            execute_user_admin_query(delete_query)
            user_admin_status.set("✓ User deleted successfully")
            
            # Clear selection
            ui.update_selectize("selected_user", selected=None)
            
        except Exception as e:
            user_admin_status.set(f"Error deleting user: {str(e)}")
    
    # User-Role Assignment Operations
    @reactive.Effect
    @reactive.event(input.assign_role)
    def handle_assign_role():
        """Assign role to selected user"""
        selected_user_id = input.selected_user()
        selected_role_id = input.assign_role_to_user()
        
        if not selected_user_id or not selected_role_id:
            user_admin_status.set("Error: Select both user and role")
            return
        
        try:
            # Check if already assigned
            check_query = f"""
            SELECT COUNT(*) as count FROM user_roles 
            WHERE user_id = {selected_user_id} AND role_id = {selected_role_id}
            """
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set("Error: Role already assigned to user")
                return
            
            # Assign role
            insert_query = f"""
            INSERT INTO user_roles (user_id, role_id, assigned_at) 
            VALUES ({selected_user_id}, {selected_role_id}, CURRENT_TIMESTAMP)
            """
            execute_user_admin_query(insert_query)
            user_admin_status.set("✓ Role assigned successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error assigning role: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.remove_user_role)
    def handle_remove_user_role():
        """Remove role from selected user"""
        selected_user_id = input.selected_user()
        selected_role_id = input.assign_role_to_user()
        
        if not selected_user_id or not selected_role_id:
            user_admin_status.set("Error: Select both user and role to remove")
            return
        
        try:
            # Remove role assignment
            delete_query = f"""
            DELETE FROM user_roles 
            WHERE user_id = {selected_user_id} AND role_id = {selected_role_id}
            """
            execute_user_admin_query(delete_query)
            user_admin_status.set("✓ Role removed successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error removing role: {str(e)}")
    
    # Role CRUD Operations
    @reactive.Effect
    @reactive.event(input.add_new_role)
    def handle_add_new_role():
        """Add new role with validation"""
        role_name = input.role_name().strip()
        description = input.role_description().strip()
        is_active = input.role_is_active()
        
        if not role_name:
            user_admin_status.set("Error: Role name is required")
            return
        
        try:
            # Check for existing role name
            check_query = f"SELECT COUNT(*) as count FROM roles WHERE role_name = '{role_name}'"
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Role '{role_name}' already exists")
                return
            
            # Insert new role
            insert_query = f"""
            INSERT INTO roles (role_name, description, is_active, updated_at) 
            VALUES ('{role_name}', '{description}', {is_active}, CURRENT_TIMESTAMP)
            """
            execute_user_admin_query(insert_query)
            user_admin_status.set(f"✓ Role '{role_name}' created successfully")
            
            # Clear form
            ui.update_text("role_name", value="")
            ui.update_text_area("role_description", value="")
            
        except Exception as e:
            user_admin_status.set(f"Error creating role: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.update_role)
    def handle_update_role():
        """Update selected role with validation"""
        selected_role_id = input.selected_role()
        if not selected_role_id:
            user_admin_status.set("Error: No role selected for update")
            return
        
        role_name = input.role_name().strip()
        description = input.role_description().strip()
        is_active = input.role_is_active()
        
        if not role_name:
            user_admin_status.set("Error: Role name is required")
            return
        
        try:
            # Check for conflicts with other roles
            check_query = f"""
            SELECT COUNT(*) as count FROM roles 
            WHERE role_name = '{role_name}' AND role_id != {selected_role_id}
            """
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Role name '{role_name}' already exists")
                return
            
            # Update role
            update_query = f"""
            UPDATE roles 
            SET role_name = '{role_name}', description = '{description}', 
                is_active = {is_active}, updated_at = CURRENT_TIMESTAMP
            WHERE role_id = {selected_role_id}
            """
            execute_user_admin_query(update_query)
            user_admin_status.set(f"✓ Role updated successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error updating role: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.delete_role)
    def handle_delete_role():
        """Delete selected role with reference safety"""
        selected_role_id = input.selected_role()
        if not selected_role_id:
            user_admin_status.set("Error: No role selected for deletion")
            return
        
        try:
            # Check for user assignments and permissions
            user_check_query = f"SELECT COUNT(*) as count FROM user_roles WHERE role_id = {selected_role_id}"
            perm_check_query = f"SELECT COUNT(*) as count FROM role_permissions WHERE role_id = {selected_role_id}"
            
            user_result = execute_user_admin_query(user_check_query)
            perm_result = execute_user_admin_query(perm_check_query)
            
            references = []
            if not user_result.empty and user_result.iloc[0]['count'] > 0:
                references.append("user assignments")
            if not perm_result.empty and perm_result.iloc[0]['count'] > 0:
                references.append("permission assignments")
            
            if references:
                user_admin_status.set(f"🚫 DELETION BLOCKED: Role has {', '.join(references)}. Remove assignments first.")
                return
            
            # Safe to delete role
            delete_query = f"DELETE FROM roles WHERE role_id = {selected_role_id}"
            execute_user_admin_query(delete_query)
            user_admin_status.set("✓ Role deleted successfully")
            
            # Clear selection
            ui.update_selectize("selected_role", selected=None)
            
        except Exception as e:
            user_admin_status.set(f"Error deleting role: {str(e)}")
    
    # Role-Permission Assignment Operations
    @reactive.Effect
    @reactive.event(input.assign_permission)
    def handle_assign_permission():
        """Assign permission to selected role"""
        selected_role_id = input.selected_role()
        selected_permission_id = input.assign_permission_to_role()
        
        if not selected_role_id or not selected_permission_id:
            user_admin_status.set("Error: Select both role and permission")
            return
        
        try:
            # Check if already assigned
            check_query = f"""
            SELECT COUNT(*) as count FROM role_permissions 
            WHERE role_id = {selected_role_id} AND permission_id = {selected_permission_id}
            """
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set("Error: Permission already assigned to role")
                return
            
            # Assign permission
            insert_query = f"""
            INSERT INTO role_permissions (role_id, permission_id, assigned_at) 
            VALUES ({selected_role_id}, {selected_permission_id}, CURRENT_TIMESTAMP)
            """
            execute_user_admin_query(insert_query)
            user_admin_status.set("✓ Permission assigned successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error assigning permission: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.remove_role_permission)
    def handle_remove_role_permission():
        """Remove permission from selected role"""
        selected_role_id = input.selected_role()
        selected_permission_id = input.assign_permission_to_role()
        
        if not selected_role_id or not selected_permission_id:
            user_admin_status.set("Error: Select both role and permission to remove")
            return
        
        try:
            # Remove permission assignment
            delete_query = f"""
            DELETE FROM role_permissions 
            WHERE role_id = {selected_role_id} AND permission_id = {selected_permission_id}
            """
            execute_user_admin_query(delete_query)
            user_admin_status.set("✓ Permission removed successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error removing permission: {str(e)}")
    
    # Permission CRUD Operations
    @reactive.Effect
    @reactive.event(input.add_new_permission)
    def handle_add_new_permission():
        """Add new permission with validation"""
        permission_name = input.permission_name().strip()
        description = input.permission_description().strip()
        is_active = input.permission_is_active()
        
        if not permission_name:
            user_admin_status.set("Error: Permission name is required")
            return
        
        try:
            # Check for existing permission name
            check_query = f"SELECT COUNT(*) as count FROM permissions WHERE permission_name = '{permission_name}'"
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Permission '{permission_name}' already exists")
                return
            
            # Insert new permission
            insert_query = f"""
            INSERT INTO permissions (permission_name, description, is_active) 
            VALUES ('{permission_name}', '{description}', {is_active})
            """
            execute_user_admin_query(insert_query)
            user_admin_status.set(f"✓ Permission '{permission_name}' created successfully")
            
            # Clear form
            ui.update_text("permission_name", value="")
            ui.update_text_area("permission_description", value="")
            
        except Exception as e:
            user_admin_status.set(f"Error creating permission: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.update_permission)
    def handle_update_permission():
        """Update selected permission with validation"""
        selected_permission_id = input.selected_permission()
        if not selected_permission_id:
            user_admin_status.set("Error: No permission selected for update")
            return
        
        permission_name = input.permission_name().strip()
        description = input.permission_description().strip()
        is_active = input.permission_is_active()
        
        if not permission_name:
            user_admin_status.set("Error: Permission name is required")
            return
        
        try:
            # Check for conflicts with other permissions
            check_query = f"""
            SELECT COUNT(*) as count FROM permissions 
            WHERE permission_name = '{permission_name}' AND permission_id != {selected_permission_id}
            """
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set(f"Error: Permission name '{permission_name}' already exists")
                return
            
            # Update permission
            update_query = f"""
            UPDATE permissions 
            SET permission_name = '{permission_name}', description = '{description}', is_active = {is_active}
            WHERE permission_id = {selected_permission_id}
            """
            execute_user_admin_query(update_query)
            user_admin_status.set(f"✓ Permission updated successfully")
            
        except Exception as e:
            user_admin_status.set(f"Error updating permission: {str(e)}")
    
    @reactive.Effect
    @reactive.event(input.delete_permission)
    def handle_delete_permission():
        """Delete selected permission with reference safety"""
        selected_permission_id = input.selected_permission()
        if not selected_permission_id:
            user_admin_status.set("Error: No permission selected for deletion")
            return
        
        try:
            # Check for role assignments
            check_query = f"SELECT COUNT(*) as count FROM role_permissions WHERE permission_id = {selected_permission_id}"
            check_result = execute_user_admin_query(check_query)
            
            if not check_result.empty and check_result.iloc[0]['count'] > 0:
                user_admin_status.set("🚫 DELETION BLOCKED: Permission has role assignments. Remove assignments first.")
                return
            
            # Safe to delete permission
            delete_query = f"DELETE FROM permissions WHERE permission_id = {selected_permission_id}"
            execute_user_admin_query(delete_query)
            user_admin_status.set("✓ Permission deleted successfully")
            
            # Clear selection
            ui.update_selectize("selected_permission", selected=None)
            
        except Exception as e:
            user_admin_status.set(f"Error deleting permission: {str(e)}")
    
    # Form population when items are selected
    @reactive.Effect
    @reactive.event(input.selected_user)
    def handle_user_selection():
        """Populate user form when user is selected"""
        selected_user_id = input.selected_user()
        if not selected_user_id:
            return
        
        try:
            users_df = current_users_data()
            if not users_df.empty:
                user_row = users_df[users_df['user_id'] == int(selected_user_id)]
                if not user_row.empty:
                    user = user_row.iloc[0]
                    ui.update_text("user_username", value=user['username'])
                    ui.update_text("user_email", value=user['email'])
                    ui.update_text("user_phone", value=user['phone'] if pd.notna(user['phone']) else "")
                    ui.update_checkbox("user_is_active", value=user['is_active'])
        except Exception:
            pass
    
    @reactive.Effect
    @reactive.event(input.selected_role)
    def handle_role_selection():
        """Populate role form when role is selected"""
        selected_role_id = input.selected_role()
        if not selected_role_id:
            return
        
        try:
            roles_df = current_roles_data()
            if not roles_df.empty:
                role_row = roles_df[roles_df['role_id'] == int(selected_role_id)]
                if not role_row.empty:
                    role = role_row.iloc[0]
                    ui.update_text("role_name", value=role['role_name'])
                    ui.update_text_area("role_description", value=role['description'] if pd.notna(role['description']) else "")
                    ui.update_checkbox("role_is_active", value=role['is_active'])
        except Exception:
            pass
    
    @reactive.Effect
    @reactive.event(input.selected_permission)
    def handle_permission_selection():
        """Populate permission form when permission is selected"""
        selected_permission_id = input.selected_permission()
        if not selected_permission_id:
            return
        
        try:
            permissions_df = current_permissions_data()
            if not permissions_df.empty:
                permission_row = permissions_df[permissions_df['permission_id'] == int(selected_permission_id)]
                if not permission_row.empty:
                    permission = permission_row.iloc[0]
                    ui.update_text("permission_name", value=permission['permission_name'])
                    ui.update_text_area("permission_description", value=permission['description'] if pd.notna(permission['description']) else "")
                    ui.update_checkbox("permission_is_active", value=permission['is_active'])
        except Exception:
            pass
    
    # Workflow Admin: Reactive values for node editing
    current_workflow_config = reactive.Value(config_manager.get_workflow_config())
    save_status = reactive.Value("")
    
    # User Admin: Reactive values for user/role/permission management  
    user_admin_status = reactive.Value("")
    current_users_data = reactive.Value(pd.DataFrame())
    current_roles_data = reactive.Value(pd.DataFrame()) 
    current_permissions_data = reactive.Value(pd.DataFrame())
    data_refresh_counter = reactive.Value(0)  # Forces UI refresh after CRUD operations
    
    # Node selector that updates dynamically
    @output
    @render.ui
    def node_selector():
        """Dynamic node selector that updates when config changes"""
        config = current_workflow_config()
        choices = []
        if config and 'workflow' in config:
            choices = list(config['workflow'].keys())
        
        return ui.input_selectize(
            "edit_node_name", 
            "Select Node to Edit:", 
            choices=choices, 
            selected=choices[0] if choices else None
        )
    
    # Workflow Admin: Workflow nodes table
    @output
    @render.data_frame
    def workflow_nodes_table():
        """Display workflow nodes from configuration"""
        config = current_workflow_config()
        
        if not config or 'workflow' not in config:
            return pd.DataFrame(columns=['Node Name', 'Class', 'ID', 'Require User Action', 'Inputs', 'Outputs'])
            
        workflow_nodes = []
        for node_name, node_details in config['workflow'].items():
            inputs = ', '.join(node_details.get('inputs', []))
            outputs = ', '.join(node_details.get('outputs', []))
            
            workflow_nodes.append({
                'Node Name': node_name,
                'Class': node_details.get('class', 'Unknown'),
                'ID': node_details.get('id', 'N/A'),
                'Require User Action': node_details.get('require_user_action', False),
                'Inputs': inputs,
                'Outputs': outputs
            })
        
        return pd.DataFrame(workflow_nodes)
    
    # Workflow Admin: Node edit form
    @output
    @render.ui
    def node_edit_form():
        """Render form to edit selected workflow node"""
        selected_node = input.edit_node_name()
        if not selected_node:
            return ui.div(
                ui.p("Select a node to edit its properties."),
                class_="text-muted"
            )
        
        config = current_workflow_config()
        if not config or 'workflow' not in config or selected_node not in config['workflow']:
            return ui.div(
                ui.p("Node not found in workflow configuration."),
                class_="text-danger"
            )
        
        node_details = config['workflow'][selected_node]
        
        # Node class options
        class_options = [
            "Start", "Simple", "ExclusiveChoice", "RESTCall", 
            "EmailNotify", "SMSNotify", "Cancel", "MultiChoice", 
            "MutexChoice", "Stop"
        ]
        
        return ui.div(
            ui.input_text("edit_node_name_field", "Node Name:", value=selected_node),
            ui.input_selectize(
                "edit_node_class", 
                "Node Class:", 
                choices=class_options,
                selected=node_details.get('class', 'Simple')
            ),
            ui.input_numeric("edit_node_id", "Node ID:", value=node_details.get('id', 1)),
            ui.input_checkbox(
                "edit_node_require_action", 
                "Require User Action", 
                value=node_details.get('require_user_action', False)
            ),
            ui.input_text_area(
                "edit_node_inputs", 
                "Inputs (comma-separated):", 
                value=', '.join(node_details.get('inputs', []))
            ),
            ui.input_text_area(
                "edit_node_outputs", 
                "Outputs (comma-separated):", 
                value=', '.join(node_details.get('outputs', []))
            ),
            ui.br(),
            ui.input_action_button("apply_node_changes", "Apply Changes", class_="btn btn-primary")
        )
    
    # Workflow Admin: Workflow graph visualization
    @output
    @render.ui
    def workflow_graph_display():
        """Display workflow as an interactive graph visualization"""
        config = current_workflow_config()
        
        if not config or 'workflow' not in config:
            return ui.div(
                ui.p("No workflow configuration available."),
                class_="text-muted"
            )
        
        # Generate interactive graph using Vis.js
        workflow = config['workflow']
        
        # Create nodes and edges for the graph
        nodes = []
        edges = []
        
        # Define node colors by class type
        node_colors = {
            'Start': '#28a745',      # Green
            'Stop': '#dc3545',       # Red  
            'ExclusiveChoice': '#ffc107',  # Yellow/Amber
            'Simple': '#007bff',     # Blue
            'RESTCall': '#6f42c1',   # Purple
            'EmailNotify': '#fd7e14', # Orange
            'SMSNotify': '#20c997',  # Teal
            'Cancel': '#6c757d',     # Gray
            'MultiChoice': '#e83e8c', # Pink
            'MutexChoice': '#17a2b8'  # Cyan
        }
        
        # Create nodes
        for node_name, node_details in workflow.items():
            node_class = node_details.get('class', 'Unknown')
            node_id = node_details.get('id', 0)
            require_action = node_details.get('require_user_action', False)
            
            color = node_colors.get(node_class, '#6c757d')
            
            # Create node with enhanced styling
            shape = 'diamond' if node_class == 'ExclusiveChoice' else 'box'
            if node_class == 'Start':
                shape = 'ellipse'
            elif node_class == 'Stop':
                shape = 'ellipse'
                
            border_width = 3 if require_action else 1
            
            nodes.append({
                'id': node_name,
                'label': f"{node_name}\\n({node_class})\\nID: {node_id}",
                'color': {
                    'background': color,
                    'border': '#2e3d49',
                    'highlight': {'background': color, 'border': '#2e3d49'}
                },
                'shape': shape,
                'borderWidth': border_width,
                'font': {'size': 12, 'color': 'white' if node_class in ['Start', 'Stop'] else 'black'}
            })
        
        # Create edges
        for node_name, node_details in workflow.items():
            outputs = node_details.get('outputs', [])
            conditions = node_details.get('conditions', {})
            
            for output in outputs:
                edge_label = "Default"
                edge_color = '#848484'
                
                # Check for conditional edges
                for condition_name, condition_details in conditions.items():
                    if condition_details.get('next_status') == output:
                        operator = condition_details.get('operator', '')
                        attribute = condition_details.get('attribute', '')
                        value = condition_details.get('value', '')
                        edge_label = f"{attribute} {operator} {value}"
                        edge_color = '#007bff'  # Blue for conditional edges
                        break
                
                edges.append({
                    'from': node_name,
                    'to': output,
                    'label': edge_label,
                    'color': {'color': edge_color},
                    'arrows': 'to',
                    'font': {'size': 10, 'align': 'middle'},
                    'smooth': {'type': 'continuous'}
                })
        
        # Convert to JSON for JavaScript
        import json
        nodes_json = json.dumps(nodes)
        edges_json = json.dumps(edges)
        
        # Create the interactive graph HTML
        graph_html = f"""
        <div id="workflow-graph" style="width: 100%; height: 600px; border: 1px solid #ccc; border-radius: 8px;"></div>
        
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <script>
            // Create nodes and edges
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});
            
            // Create a network
            var container = document.getElementById('workflow-graph');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            
            var options = {{
                nodes: {{
                    borderWidth: 2,
                    shadow: true,
                    font: {{
                        size: 12,
                        face: 'Tahoma'
                    }}
                }},
                edges: {{
                    width: 2,
                    shadow: true,
                    smooth: {{
                        type: 'continuous'
                    }}
                }},
                physics: {{
                    enabled: true,
                    stabilization: {{
                        enabled: true,
                        iterations: 100
                    }},
                    barnesHut: {{
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95,
                        springConstant: 0.04,
                        damping: 0.09,
                        avoidOverlap: 0.1
                    }}
                }},
                layout: {{
                    hierarchical: {{
                        enabled: true,
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 100,
                        nodeSpacing: 150
                    }}
                }},
                interaction: {{
                    zoomView: true,
                    dragView: true,
                    hover: true,
                    selectConnectedEdges: false
                }}
            }};
            
            var network = new vis.Network(container, data, options);
            
            // Add click event listener
            network.on("click", function (params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    alert('Clicked on node: ' + nodeId);
                }}
            }});
        </script>
        """
        
        return ui.div(
            ui.h5("Interactive Workflow Graph"),
            ui.HTML(graph_html),
            ui.br(),
            ui.div(
                ui.row(
                    ui.column(6,
                        ui.h6("Legend:"),
                        ui.div(
                            ui.span("●", style="color: #28a745; font-size: 16px;"), " Start Node", ui.br(),
                            ui.span("●", style="color: #dc3545; font-size: 16px;"), " Stop Node", ui.br(),
                            ui.span("◆", style="color: #ffc107; font-size: 16px;"), " Decision Node", ui.br(),
                            ui.span("■", style="color: #007bff; font-size: 16px;"), " Process Node", ui.br(),
                            ui.span("■", style="color: #6f42c1; font-size: 16px;"), " API Call", ui.br(),
                            ui.span("■", style="color: #fd7e14; font-size: 16px;"), " Email Notify", ui.br(),
                            ui.span("■", style="color: #20c997; font-size: 16px;"), " SMS Notify"
                        )
                    ),
                    ui.column(6,
                        ui.h6("Features:"),
                        ui.div(
                            "• Zoom and pan the graph", ui.br(),
                            "• Click nodes for details", ui.br(), 
                            "• Thick borders = User Action Required", ui.br(),
                            "• Blue edges = Conditional flows", ui.br(),
                            "• Gray edges = Default flows", ui.br(),
                            "• Hierarchical layout shows flow direction"
                        )
                    )
                ),
                class_="text-muted",
                style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.375rem; margin-top: 1rem;"
            )
        )
    
    # Helper function to validate workflow integrity
    def validate_workflow_integrity(config):
        """Validate workflow configuration for comprehensive integrity issues"""
        errors = []
        warnings = []
        
        if not config or 'workflow' not in config:
            errors.append("No workflow configuration found")
            return errors, warnings
        
        # Work on a copy to avoid mutating the original config
        workflow_copy = copy.deepcopy(config['workflow'])
        node_names = set(workflow_copy.keys())
        
        # Check for required Start and Stop nodes
        if 'start' not in node_names:
            errors.append("Missing required 'start' node")
        if 'stop' not in node_names:
            errors.append("Missing required 'stop' node")
        
        # Check Start/Stop name-class alignment
        if 'start' in workflow_copy:
            start_class = workflow_copy['start'].get('class')
            if start_class != 'Start':
                errors.append(f"Node 'start' should have class 'Start', but has '{start_class}'")
        
        if 'stop' in workflow_copy:
            stop_class = workflow_copy['stop'].get('class')
            if stop_class != 'Stop':
                errors.append(f"Node 'stop' should have class 'Stop', but has '{stop_class}'")
        
        # Check for multiple Start or Stop nodes
        start_nodes = [name for name, details in workflow_copy.items() if details.get('class') == 'Start']
        stop_nodes = [name for name, details in workflow_copy.items() if details.get('class') == 'Stop']
        
        if len(start_nodes) > 1:
            errors.append(f"Multiple Start nodes found: {start_nodes}")
        if len(stop_nodes) > 1:
            errors.append(f"Multiple Stop nodes found: {stop_nodes}")
        
        # Check for duplicate node IDs and type validation
        node_ids = []
        for name, details in workflow_copy.items():
            original_id = details.get('id')
            
            # Type validation for ID - work with local variable
            if not isinstance(original_id, int):
                try:
                    coerced_id = int(original_id)  # Coerce to int locally
                    warnings.append(f"Node '{name}' ID coerced to integer")
                    validated_id = coerced_id
                except (ValueError, TypeError):
                    errors.append(f"Node '{name}' has invalid ID type: {type(original_id)}")
                    continue
            else:
                validated_id = original_id
            
            if validated_id in node_ids:
                errors.append(f"Duplicate node ID {validated_id} found")
            node_ids.append(validated_id)
        
        # Validate node classes
        valid_classes = [
            "Start", "Simple", "ExclusiveChoice", "RESTCall", 
            "EmailNotify", "SMSNotify", "Cancel", "MultiChoice", 
            "MutexChoice", "Stop"
        ]
        
        for node_name, node_details in workflow_copy.items():
            node_class = node_details.get('class')
            if node_class not in valid_classes:
                errors.append(f"Node '{node_name}' has invalid class '{node_class}'")
        
        # Check Start node constraints
        if 'start' in workflow_copy:
            start_inputs = workflow_copy['start'].get('inputs', [])
            if start_inputs:
                errors.append("Start node should not have inputs")
        
        # Check Stop node constraints  
        if 'stop' in workflow_copy:
            stop_outputs = workflow_copy['stop'].get('outputs', [])
            if stop_outputs:
                errors.append("Stop node should not have outputs")
        
        # Check for broken references
        for node_name, node_details in workflow_copy.items():
            # Check inputs
            for input_node in node_details.get('inputs', []):
                if input_node not in node_names:
                    errors.append(f"Node '{node_name}' references unknown input '{input_node}'")
            
            # Check outputs
            for output_node in node_details.get('outputs', []):
                if output_node not in node_names:
                    errors.append(f"Node '{node_name}' references unknown output '{output_node}'")
            
            # Check conditions next_status
            conditions = node_details.get('conditions', {})
            for condition_name, condition_details in conditions.items():
                next_status = condition_details.get('next_status')
                if next_status and next_status not in node_names:
                    errors.append(f"Node '{node_name}' condition '{condition_name}' references unknown next_status '{next_status}'")
        
        # Check for consistency between outputs and conditions
        for node_name, node_details in workflow_copy.items():
            outputs = set(node_details.get('outputs', []))
            conditions = node_details.get('conditions', {})
            
            if conditions:
                condition_targets = set()
                for condition_details in conditions.values():
                    next_status = condition_details.get('next_status')
                    if next_status:
                        condition_targets.add(next_status)
                
                # For conditional nodes, make outputs vs condition targets mismatches errors (more strict)
                if outputs != condition_targets and outputs and condition_targets:
                    errors.append(f"Node '{node_name}' outputs {outputs} don't match condition targets {condition_targets}")
        
        # Check reachability from start to stop
        if 'start' in workflow_copy and 'stop' in workflow_copy:
            visited = set()
            def dfs_reachable(node):
                if node in visited or node not in workflow_copy:
                    return set()
                visited.add(node)
                reachable = {node}
                for output in workflow_copy[node].get('outputs', []):
                    reachable.update(dfs_reachable(output))
                return reachable
            
            reachable_from_start = dfs_reachable('start')
            if 'stop' not in reachable_from_start:
                errors.append("Stop node is not reachable from Start node")
            
            # Check for unreachable nodes
            unreachable_nodes = node_names - reachable_from_start
            if unreachable_nodes:
                warnings.append(f"Unreachable nodes found: {unreachable_nodes}")
        
        return errors, warnings
    
    # Helper function to update references when node is renamed
    def update_node_references(config, old_name, new_name):
        """Update all references to a node when it's renamed"""
        workflow = config['workflow']
        
        for node_name, node_details in workflow.items():
            # Update inputs
            if 'inputs' in node_details:
                node_details['inputs'] = [new_name if inp == old_name else inp for inp in node_details['inputs']]
            
            # Update outputs
            if 'outputs' in node_details:
                node_details['outputs'] = [new_name if out == old_name else out for out in node_details['outputs']]
            
            # Update conditions next_status
            if 'conditions' in node_details:
                for condition_name, condition_details in node_details['conditions'].items():
                    if condition_details.get('next_status') == old_name:
                        condition_details['next_status'] = new_name
        
        return config
    
    # Workflow Admin: Apply node changes (with integrity checks)
    @reactive.Effect
    @reactive.event(input.apply_node_changes)
    def handle_apply_node_changes():
        """Apply changes to selected workflow node with integrity checks"""
        selected_node = input.edit_node_name()
        if not selected_node:
            return
        
        config = current_workflow_config()
        if not config or 'workflow' not in config:
            return
        
        # Get updated values from form
        new_name = input.edit_node_name_field().strip()
        new_class = input.edit_node_class()
        new_id = int(input.edit_node_id())  # Ensure integer type
        new_require_action = input.edit_node_require_action()
        new_inputs = [inp.strip() for inp in input.edit_node_inputs().split(',') if inp.strip()]
        new_outputs = [out.strip() for out in input.edit_node_outputs().split(',') if out.strip()]
        
        # Validation checks
        if not new_name:
            save_status.set("Error: Node name cannot be empty")
            return
        
        # Check for duplicate names (excluding current node)
        if new_name != selected_node and new_name in config['workflow']:
            save_status.set(f"Error: Node name '{new_name}' already exists")
            return
        
        # Update the configuration (deep copy to prevent state bleed-through)
        updated_config = copy.deepcopy(config)
        
        # If name changed, rename the node and update all references
        if new_name != selected_node:
            # Update references first
            updated_config = update_node_references(updated_config, selected_node, new_name)
            # Then rename the node
            updated_config['workflow'][new_name] = updated_config['workflow'][selected_node]
            del updated_config['workflow'][selected_node]
            selected_node = new_name
        
        # Update node properties
        updated_config['workflow'][selected_node].update({
            'class': new_class,
            'id': new_id,
            'require_user_action': new_require_action,
            'inputs': new_inputs,
            'outputs': new_outputs
        })
        
        # Validate the updated configuration
        errors, warnings = validate_workflow_integrity(updated_config)
        if errors:
            save_status.set(f"Validation errors: {'; '.join(errors)}")
            return
        
        # Update reactive configuration
        current_workflow_config.set(updated_config)
        save_status.set("Changes applied and validated. Click 'Save Changes' to persist to file.")
    
    # Workflow Admin: Save changes to file (with validation gate and transactional write)
    @reactive.Effect
    @reactive.event(input.save_workflow_changes)
    def handle_save_workflow_changes():
        """Save workflow configuration to file with comprehensive validation gate and atomic write"""
        try:
            config = current_workflow_config()
            if not config:
                save_status.set("Error: No configuration to save.")
                return
            
            # Deep copy for validation safety
            config_to_validate = copy.deepcopy(config)
            
            # Strict validation gate before any persist operation
            errors, warnings = validate_workflow_integrity(config_to_validate)
            if errors:
                save_status.set(f"BLOCKED: Cannot save due to validation errors: {'; '.join(errors[:2])}")
                return
            
            # Atomic transactional write with rollback protection
            try:
                config_manager.save_workflow_config(config_to_validate)
                save_status.set("✓ Workflow saved successfully with atomic write!" + 
                              (f" Warnings: {'; '.join(warnings[:2])}" if warnings else ""))
            except Exception as write_error:
                save_status.set(f"WRITE FAILED: Configuration validation passed but file write failed: {str(write_error)}")
                return
            
        except Exception as e:
            save_status.set(f"SAVE ERROR: {str(e)}")
    
    # Workflow Admin: Add new node
    @reactive.Effect
    @reactive.event(input.add_new_node)
    def handle_add_new_node():
        """Add a new workflow node with default values"""
        config = current_workflow_config()
        if not config or 'workflow' not in config:
            return
        
        # Generate unique node name
        base_name = "new_node"
        counter = 1
        while f"{base_name}_{counter}" in config['workflow']:
            counter += 1
        
        new_node_name = f"{base_name}_{counter}"
        
        # Generate unique ID
        existing_ids = [details.get('id', 0) for details in config['workflow'].values()]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        # Create new node with default values
        new_node = {
            'class': 'Simple',
            'id': new_id,
            'require_user_action': True,
            'inputs': [],
            'outputs': []
        }
        
        # Update configuration (deep copy to prevent state bleed-through)
        updated_config = copy.deepcopy(config)
        updated_config['workflow'][new_node_name] = new_node
        
        current_workflow_config.set(updated_config)
        save_status.set(f"New node '{new_node_name}' added. Configure it and save changes.")
    
    # Workflow Admin: Delete selected node
    @reactive.Effect
    @reactive.event(input.delete_selected_node)
    def handle_delete_selected_node():
        """Delete the selected workflow node and clean up references"""
        selected_node = input.edit_node_name()
        if not selected_node:
            save_status.set("Error: No node selected for deletion")
            return
        
        config = current_workflow_config()
        if not config or 'workflow' not in config or selected_node not in config['workflow']:
            save_status.set("Error: Selected node not found")
            return
        
        # Prevent deletion of start and stop nodes (critical nodes)
        if selected_node in ['start', 'stop']:
            save_status.set("Error: Cannot delete start or stop nodes")
            return
        
        # Reference safety check - prevent deletion if node is referenced
        node_to_delete = selected_node
        references = []
        
        # Check all nodes for references to the node being deleted
        for name, details in config['workflow'].items():
            if name == node_to_delete:
                continue
                
            # Check inputs
            if node_to_delete in details.get('inputs', []):
                references.append(f"'{name}' inputs")
            
            # Check outputs  
            if node_to_delete in details.get('outputs', []):
                references.append(f"'{name}' outputs")
            
            # Check conditions next_status
            for condition_name, condition_details in details.get('conditions', {}).items():
                if condition_details.get('next_status') == node_to_delete:
                    references.append(f"'{name}' condition '{condition_name}'")
        
        # *** PRODUCTION-SAFE: Block deletion if ANY references exist ***
        if references:
            save_status.set(f"🚫 DELETION BLOCKED: Node '{node_to_delete}' is referenced by: {'; '.join(references)}. Remove references first or use 'Force Delete' if available.")
            return
        
        # Only proceed with deletion if NO references found
        # Update configuration (deep copy to prevent state bleed-through)
        updated_config = copy.deepcopy(config)
        
        # Safe to remove the node (no references exist)
        del updated_config['workflow'][selected_node]
        
        current_workflow_config.set(updated_config)
        save_status.set(f"✓ Node '{selected_node}' safely deleted (no references found). Save changes to persist.")
    
    # Workflow Admin: Validate workflow
    @reactive.Effect
    @reactive.event(input.validate_workflow)
    def handle_validate_workflow():
        """Validate the current workflow configuration"""
        config = current_workflow_config()
        errors, warnings = validate_workflow_integrity(config)
        
        if errors:
            save_status.set(f"Validation FAILED: {'; '.join(errors)}")
        elif warnings:
            save_status.set(f"Validation passed with warnings: {'; '.join(warnings)}")
        else:
            save_status.set("Validation passed: Workflow configuration is valid!")
    
    # Workflow Admin: Complete runtime workflow reconstruction 
    @reactive.Effect
    @reactive.event(input.reload_workflow_instance)
    def handle_reload_workflow_instance():
        """Complete runtime workflow reconstruction with new instance creation and handler rebinding"""
        try:
            # Get current working configuration
            config = current_workflow_config()
            if not config:
                save_status.set("ERROR: No configuration available for reload")
                return
            
            # Deep copy for validation safety
            candidate_config = copy.deepcopy(config)
            
            # Strict validation gate - abort on any errors
            errors, warnings = validate_workflow_integrity(candidate_config)
            if errors:
                save_status.set(f"BLOCKED: Cannot reload due to validation errors: {'; '.join(errors[:2])}")
                return
            
            # Store reference to old instance for rollback
            global workflow_instance, form_data
            old_instance = workflow_instance
            old_form_data = form_data.get()
            
            try:
                # *** COMPLETE WORKFLOW RECONSTRUCTION ***
                # 1. Create entirely new ShinyWorkflow instance
                new_workflow_instance = ShinyWorkflow(
                    candidate_config, 
                    form_config, 
                    copy.deepcopy(initial_form_data)
                )
                
                # 2. Atomic swap of global workflow instance
                workflow_instance = new_workflow_instance
                
                # 3. Reset reactive state to match new instance
                form_data.set(copy.deepcopy(initial_form_data))
                
                # 4. *** CRITICAL: Rebind all action handlers to new instance ***
                workflow_instance.form_renderer.setup_action_handlers(input, handle_form_action)
                
                # 5. Reset workflow state to start
                workflow_instance.current_status.set('start')
                workflow_instance.audit_data.set([])
                workflow_instance.error_message.set("")
                
                save_status.set("✓ COMPLETE RELOAD: New workflow instance created, handlers rebound, state reset!" + 
                              (f" Warnings: {'; '.join(warnings[:2])}" if warnings else ""))
                
            except Exception as reconstruction_error:
                # *** ROLLBACK ON FAILURE ***
                workflow_instance = old_instance
                form_data.set(old_form_data)
                save_status.set(f"ROLLBACK: Reconstruction failed, restored previous instance: {str(reconstruction_error)}")
                
        except Exception as e:
            save_status.set(f"RELOAD ERROR: {str(e)}")
    
    # Workflow Admin: Save status display
    @output
    @render.text
    def save_status_display():
        """Display save operation status"""
        return save_status()

# Create the app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)