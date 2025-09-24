"""
Shiny Workflow module - converted from Streamlit Workflow.py
Manages workflow state and processing with reactive programming
"""

from shiny import reactive, render
import yaml
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
from .form import ShinyForm, ShinyFormRenderer

class ShinyWorkflow:
    """
    Shiny equivalent of the Streamlit Workflow class
    Handles workflow state management and processing with reactive state
    """
    
    def __init__(self, workflow_config: Dict[str, Any], form_config: Dict[str, Any], initial_form_data: Optional[Dict] = None):
        self.config = workflow_config
        self.form_config = form_config
        self.form_data = initial_form_data or {}
        
        # Initialize workflow state
        self.current_status = reactive.Value(
            'start' if not self.form_data.get('status') else self.form_data['status']
        )
        
        # Initialize audit trail
        self.audit_data = reactive.Value([])
        
        # Create form instance (without reactive audit data during init)
        self.form = ShinyForm(self.form_config, self.form_data, [])
        self.form_renderer = ShinyFormRenderer(self.form)
        
        # Reactive values for workflow processing
        self.processing = reactive.Value(False)
        self.error_message = reactive.Value("")
        self.submitted_action = reactive.Value("")
        
    def audit(self, action: str, user: str, description: str = ""):
        """Add an audit entry to the audit trail"""
        new_audit = {
            'status': self.current_status(),
            'action': action,
            'description': description,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'user': user
        }
        
        try:
            current_audit = self.audit_data()
            current_audit.append(new_audit)
            self.audit_data.set(current_audit)
            
            # Update form's audit data
            self.form.audit_data = current_audit
        except RuntimeError:
            # Handle case where we're not in reactive context
            if not hasattr(self, '_temp_audit'):
                self._temp_audit = []
            self._temp_audit.append(new_audit)
    
    def initiate(self):
        """Initiate the workflow"""
        self.current_status.set("start")
        self.audit("Workflow Initiated", 'system')
        return self.form_data
    
    def cancel(self):
        """Cancel the workflow"""
        self.current_status.set("stop")
        self.audit("Workflow canceled", 'system')
        return self.form_data
    
    @staticmethod
    def evaluate_condition(operator: str, attribute_value: Any, condition_value: Any) -> bool:
        """
        Evaluate a condition based on the given operator
        
        Args:
            operator: The condition operator
            attribute_value: The value from the form_data
            condition_value: The value specified in the condition
            
        Returns:
            Boolean indicating if the condition is met
        """
        if operator == "Equal":
            return attribute_value == condition_value
        elif operator == "GreaterThan":
            return attribute_value > condition_value
        elif operator == "LessThan":
            return attribute_value < condition_value
        elif operator == "GreaterThanOrEqual":
            return attribute_value >= condition_value
        elif operator == "LessThanOrEqual":
            return attribute_value <= condition_value
        elif operator == "Contains":
            return condition_value in attribute_value
        elif operator == "InList":
            return attribute_value in condition_value
        
        return False
    
    def check_user_permission(self, step_config: Dict[str, Any], user_role: str) -> bool:
        """Check if user has permission to execute a workflow step"""
        if 'role' in step_config and step_config['role']:
            return user_role in step_config['role']
        return True
    
    def process_workflow(self, user_role: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the workflow with the given form data
        
        Args:
            user_role: The role of the user executing the workflow
            form_data: The form data to process
            
        Returns:
            Updated form data
            
        Raises:
            PermissionError: If user doesn't have permission for the step
            Exception: If workflow processing fails
        """
        self.processing.set(True)
        self.error_message.set("")
        
        try:
            # Handle comments if present
            if form_data.get('comments'):
                self.audit("Commented", user_role, form_data['comments'])
                form_data['comments'] = ""
            
            # Process one workflow step (non-blocking approach)
            current_status = self.current_status()
            
            # Check if we have workflow configuration for current status
            if current_status not in self.config.get('workflow', {}):
                form_data['status'] = 'stop'
                self.current_status.set('stop')
                return form_data
            
            step_config = self.config['workflow'][current_status]
            
            # Check user permissions for this step
            if not self.check_user_permission(step_config, user_role) and step_config.get('require_user_action', False):
                raise PermissionError("User does not have permission to execute this step.")
            
            # Process the step (simplified - in real implementation you'd import and use WorkflowStep classes)
            step_class = step_config.get('class', 'Simple')
            decision = f"Processed step: {current_status}"
            
            # Determine next status based on step configuration
            next_status = self._determine_next_status(step_config, form_data)
            
            # Update status and audit
            self.current_status.set(next_status)
            self.audit(decision, user_role)
            form_data['status'] = next_status
            
            # If next step doesn't require user action, schedule continued processing
            if next_status != 'stop' and not step_config.get('require_user_action', True):
                # Use reactive.invalidate_later for non-blocking continuation
                # This would be implemented in the UI layer with reactive.Effect
                pass
                    
        except Exception as e:
            self.error_message.set(str(e))
            raise e
        finally:
            self.processing.set(False)
        
        return form_data
    
    def _determine_next_status(self, step_config: Dict[str, Any], form_data: Dict[str, Any]) -> str:
        """
        Determine the next workflow status based on step configuration and form data
        
        Args:
            step_config: Configuration for the current step
            form_data: Current form data
            
        Returns:
            Next workflow status
        """
        # Check if there are conditions to evaluate
        if 'conditions' in step_config:
            for condition_name, condition in step_config['conditions'].items():
                operator = condition.get('operator')
                attribute = condition.get('attribute')
                value = condition.get('value')
                next_status = condition.get('next_status')
                
                if operator and attribute and value is not None and next_status:
                    attribute_value = form_data.get(attribute)
                    if self.evaluate_condition(operator, attribute_value, value):
                        return next_status
        
        # Check for simple outputs configuration
        if 'outputs' in step_config and step_config['outputs']:
            return step_config['outputs'][0]  # Use first output as default
        
        # Default to stop if no next status determined
        return 'stop'
    
    def create_form_ui(self, user_role: str) -> List:
        """Create the form UI for the current workflow status"""
        current_status = self.current_status()
        
        # Update form data in the form instance
        self.form.form_data = self.form_data
        
        # Create form elements
        form_elements = self.form.create_form_ui([user_role])
        
        # Add action buttons if not in start/stop state
        if current_status not in ['start', 'stop']:
            action_buttons = self.form.create_action_buttons(current_status)
            form_elements.extend(action_buttons)
        
        return form_elements
    
    def handle_form_submission(self, input_values: Dict[str, Any], action: str, user_role: str) -> Dict[str, Any]:
        """
        Handle form submission and process workflow
        
        Args:
            input_values: Values from Shiny input widgets
            action: The action that was submitted
            user_role: The role of the user submitting
            
        Returns:
            Updated form data
        """
        # Extract form data
        form_data = self.form.get_form_data(input_values, action)
        
        if form_data:
            # Update internal form data
            self.form_data.update(form_data)
            
            # Process workflow
            try:
                updated_data = self.process_workflow(user_role, self.form_data)
                self.form_data = updated_data
                return updated_data
            except Exception as e:
                self.error_message.set(str(e))
                return self.form_data
        
        return self.form_data

class ShinyWorkflowRenderer:
    """
    Helper class to render Shiny workflow components in server functions
    """
    
    def __init__(self, workflow: ShinyWorkflow):
        self.workflow = workflow
    
    def setup_workflow_outputs(self, output, input, user_role_reactive: reactive.Value):
        """Setup reactive outputs for workflow display"""
        
        @output
        @render.text
        def workflow_status():
            status = self.workflow.current_status()
            processing = self.workflow.processing()
            if processing:
                return f"Status: {status} (Processing...)"
            return f"Status: {status}"
        
        @output
        @render.text
        def workflow_error():
            error = self.workflow.error_message()
            return error if error else ""
        
        @output
        @render.data_frame
        def audit_trail():
            audit_data = self.workflow.audit_data()
            if audit_data:
                return pd.DataFrame(audit_data)
            return pd.DataFrame(columns=['status', 'action', 'description', 'time', 'user'])
        
        # Setup form dataframe outputs
        self.workflow.form_renderer.setup_dataframe_outputs(output, input)
    
    def setup_workflow_handlers(self, input, user_role_reactive: reactive.Value):
        """Setup reactive handlers for workflow actions"""
        
        def handle_action(action: str):
            user_role = user_role_reactive()
            current_input = {}
            
            # Extract all input values
            for field_name in self.workflow.form.form_fields.keys():
                if hasattr(input, field_name):
                    current_input[field_name] = getattr(input, field_name)()
            
            # Process the workflow
            self.workflow.handle_form_submission(current_input, action, user_role)
        
        # Setup action button handlers
        self.workflow.form_renderer.setup_action_handlers(input, handle_action)
        
        return handle_action