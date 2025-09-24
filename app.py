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
    
    # Workflow Admin: Reactive values for node editing
    current_workflow_config = reactive.Value(config_manager.get_workflow_config())
    save_status = reactive.Value("")
    
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
        """Display workflow as a visual graph"""
        config = current_workflow_config()
        
        if not config or 'workflow' not in config:
            return ui.div(
                ui.p("No workflow configuration available."),
                class_="text-muted"
            )
        
        # Create a simple textual representation of the workflow graph
        # In a production app, you'd want to use a proper graph visualization library
        graph_description = []
        workflow = config['workflow']
        
        for node_name, node_details in workflow.items():
            inputs = node_details.get('inputs', [])
            outputs = node_details.get('outputs', [])
            node_class = node_details.get('class', 'Unknown')
            
            if inputs:
                input_str = ' ← '.join(inputs)
                graph_description.append(f"{input_str} → [{node_name}] ({node_class})")
            else:
                graph_description.append(f"[{node_name}] ({node_class})")
            
            if outputs:
                for output in outputs:
                    graph_description.append(f"  └─→ {output}")
        
        return ui.div(
            ui.h5("Workflow Flow Diagram"),
            ui.div(
                *[ui.p(desc, style="font-family: monospace; margin: 0.2em 0;") for desc in graph_description],
                style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.375rem; border: 1px solid #dee2e6;"
            ),
            ui.br(),
            ui.div(
                ui.strong("Legend: "),
                ui.span("[Node Name] (Class Type) ← Input → Output", style="font-family: monospace;"),
                class_="text-muted"
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