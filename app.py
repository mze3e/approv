"""
Main Shiny application for the BPMS (Business Process Management System)
Converted from Streamlit to Shiny Python
"""

from shiny import App, render, ui, reactive
import pandas as pd

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
            ui.p("Workflow management interface will be implemented here."),
            ui.output_data_frame("workflow_nodes_table")
        )
    ),
    ui.nav_panel("User Admin",
        ui.div(
            ui.h1("User Administration"),
            ui.input_text("sql_query", "SQL Query:", placeholder="Enter read-only SQL query (SELECT, SHOW, DESCRIBE, EXPLAIN)..."),
            ui.input_action_button("execute_query", "Execute", class_="btn btn-secondary"),
            ui.br(),
            ui.output_text("query_error_display"),
            ui.output_data_frame("query_results"),
            ui.br(),
            ui.h3("Users"),
            ui.output_data_frame("users_table"),
            ui.br(),
            ui.h3("Roles"),
            ui.output_data_frame("roles_table"),
            ui.br(),
            ui.h3("Permissions"),
            ui.output_data_frame("permissions_table")
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
        return query_result()
    
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
        return db_manager.get_users()
    
    # User Admin: Roles table
    @output
    @render.data_frame
    def roles_table():
        return db_manager.get_roles()
    
    # User Admin: Permissions table
    @output
    @render.data_frame
    def permissions_table():
        return db_manager.get_permissions()
    
    # Workflow Admin: Workflow nodes table
    @output
    @render.data_frame
    def workflow_nodes_table():
        """Display workflow nodes from configuration"""
        current_workflow_config = config_manager.get_workflow_config()
        
        if not current_workflow_config or 'workflow' not in current_workflow_config:
            return pd.DataFrame()
            
        workflow_nodes = []
        for node_name, node_details in current_workflow_config['workflow'].items():
            workflow_nodes.append({
                'Node Name': node_name,
                'Class': node_details.get('class', 'Unknown'),
                'ID': node_details.get('id', 'N/A'),
                'Require User Action': node_details.get('require_user_action', False)
            })
        
        return pd.DataFrame(workflow_nodes)

# Create the app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)