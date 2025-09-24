"""
Main Shiny application for the BPMS (Business Process Management System)
Converted from Streamlit to Shiny Python
"""

from shiny import App, render, ui, reactive
import pandas as pd

# Import our configuration manager
from shiny_modules.config import config_manager, db_manager

# Initialize configurations
workflow_config = config_manager.get_workflow_config()
form_config = config_manager.get_form_config()
initial_form_data = config_manager.get_form_data()

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
            ui.br(),
            ui.div(id="dynamic_form_container")
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
    workflow_status_value = reactive.Value("Ready to start workflow")
    
    # Home page: Workflow status
    @output
    @render.text
    def workflow_status_display():
        return f"Current Status: {workflow_status_value()}"
    
    # Home page: Start workflow button
    @reactive.Effect
    @reactive.event(input.start_workflow)
    def handle_start_workflow():
        user_role = input.user_role()
        workflow_status_value.set(f"Workflow started for {user_role}")
        # TODO: Implement actual workflow processing
    
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