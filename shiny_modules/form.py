"""
Shiny Form module - converted from Streamlit Form.py
Provides dynamic form rendering based on YAML configuration with reactive state management
"""

from shiny import ui, reactive, render
import pandas as pd
import yaml
from datetime import datetime, date, time
from typing import Dict, Any, List, Optional, Union
import uuid

class ShinyForm:
    """
    Shiny equivalent of the Streamlit Form class
    Handles dynamic form rendering based on configuration with reactive state
    """
    
    def __init__(self, form_config: Dict[str, Any], form_data: Optional[Dict] = None, audit_data: Optional[List] = None):
        self.form_config = form_config
        self.form_data = form_data or {}
        self.audit_data = audit_data or []
        
        # Parse configuration
        self.form_fields, self.actions, self.permissions = self._get_config()
        
        # Create reactive values for form state
        self.field_values = {}
        self.submitted_action = reactive.Value("")
        
    def _get_config(self):
        """Parse form configuration from YAML or dict"""
        if isinstance(self.form_config, str):
            with open(self.form_config, 'r') as file:
                config = yaml.safe_load(file)
        elif isinstance(self.form_config, dict):
            config = self.form_config
        else:
            raise ValueError("form_config must be a dict or YAML file path")
        
        try:
            form_fields = config['form']['fields']
            actions = config['form']['actions']
            permissions = config['form']['permissions']
        except KeyError as e:
            raise KeyError(f"Missing required form configuration section: {e}")
        
        return form_fields, actions, permissions
    
    def _is_disabled(self, field_name: str, user_roles: List[str]) -> bool:
        """Check if field should be disabled based on editability and permissions"""
        # Flatten user_roles in case of nested lists (defensive guard)
        if user_roles and len(user_roles) > 0 and isinstance(user_roles[0], list):
            user_roles = [role for sublist in user_roles for role in sublist]
        
        # Check if field is marked as non-editable
        disabled_field = not self.form_fields[field_name].get('editable', True)
        
        # Check permission-based disabling
        disabled_perm = False
        try:
            field_permissions = self.permissions.get(field_name, [])
            if field_permissions:
                disabled_perm = not any(role in user_roles for role in field_permissions)
        except:
            disabled_perm = False
        
        return disabled_field or disabled_perm
    
    def _get_default_value(self, field_name: str) -> Any:
        """Get default value for a form field"""
        field_config = self.form_fields[field_name]
        field_type = field_config['type']
        
        # Check if explicit default is provided
        if 'default' in field_config:
            return field_config['default']
        
        # Type-specific defaults
        if field_type in ['checkbox', 'toggle']:
            return False
        elif field_type in ['radio', 'selectbox']:
            return 0  # index
        elif field_type == 'slider':
            return field_config.get('min_value', 0)
        elif field_type == 'multiselect':
            return []
        elif field_type == 'number_input':
            return 0.0
        elif field_type == 'date_input':
            return date.today()
        elif field_type == 'time_input':
            return datetime.now().time()
        elif field_type == 'color_picker':
            return '#ffffff'
        elif field_type == 'dataframe' and field_name == 'audit':
            return pd.DataFrame(self.audit_data)
        else:
            return ""
    
    def _create_input_widget(self, field_name: str, user_roles: List[str]) -> ui.Tag:
        """Create a Shiny input widget based on field configuration"""
        field_config = self.form_fields[field_name]
        field_type = field_config['type']
        title = field_config.get('title', field_name)
        
        # Get current value from form_data or use default
        try:
            current_value = self.form_data.get(field_name, self._get_default_value(field_name))
        except:
            current_value = self._get_default_value(field_name)
        
        # Check if field is disabled
        disabled = self._is_disabled(field_name, user_roles)
        
        # Create appropriate Shiny input widget with disabled state
        if field_type == 'checkbox':
            widget = ui.input_checkbox(field_name, title, value=current_value)
        
        elif field_type == 'toggle':
            # Shiny doesn't have toggle, use checkbox
            widget = ui.input_checkbox(field_name, title, value=current_value)
        
        elif field_type == 'radio':
            options = field_config['options']
            selected = options[current_value] if isinstance(current_value, int) else current_value
            widget = ui.input_radio_buttons(field_name, title, choices=options, selected=selected)
        
        elif field_type == 'selectbox':
            options = field_config['options']
            selected = options[current_value] if isinstance(current_value, int) else current_value
            widget = ui.input_selectize(field_name, title, choices=options, selected=selected)
        
        elif field_type == 'multiselect':
            options = field_config['options']
            widget = ui.input_checkbox_group(field_name, title, choices=options, selected=current_value or [])
        
        elif field_type == 'slider':
            min_val = field_config.get('min_value', 0)
            max_val = field_config.get('max_value', 100)
            step = field_config.get('step', 1)
            widget = ui.input_slider(field_name, title, min=min_val, max=max_val, value=current_value, step=step)
        
        elif field_type == 'select_slider':
            # Use selectize for select_slider equivalent
            options = field_config.get('options', ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet'])
            widget = ui.input_selectize(field_name, title, choices=options, selected=current_value)
        
        elif field_type == 'text_input':
            widget = ui.input_text(field_name, title, value=str(current_value))
        
        elif field_type == 'number_input':
            widget = ui.input_numeric(field_name, title, value=float(current_value))
        
        elif field_type == 'text_area':
            widget = ui.input_text_area(field_name, title, value=str(current_value))
        
        elif field_type == 'date_input':
            if isinstance(current_value, str):
                current_value = datetime.strptime(current_value, "%Y-%m-%d").date()
            widget = ui.input_date(field_name, title, value=current_value)
        
        elif field_type == 'time_input':
            # Shiny doesn't have time input, use text input with time format
            if isinstance(current_value, time):
                time_str = current_value.strftime("%H:%M:%S")
            else:
                time_str = str(current_value)
            widget = ui.input_text(field_name, f"{title} (HH:MM:SS)", value=time_str, placeholder="14:30:00")
        
        elif field_type == 'file_uploader':
            widget = ui.input_file(field_name, title)
        
        elif field_type == 'camera_input':
            # Shiny doesn't have camera input, use file input as fallback
            widget = ui.input_file(field_name, f"{title} (Camera)", accept="image/*")
        
        elif field_type == 'color_picker':
            # Shiny doesn't have color picker, use text input with color format
            widget = ui.input_text(field_name, f"{title} (Color)", value=str(current_value), placeholder="#ffffff")
        
        elif field_type == 'dataframe':
            # Return a placeholder div for dataframe display (will be handled separately)
            return ui.div(
                ui.h5(title),
                ui.output_data_frame(f"{field_name}_display")
            )
        
        else:
            # Fallback to text input
            widget = ui.input_text(field_name, title, value=str(current_value))
        
        # Apply disabled state by wrapping in a div with appropriate styling
        if disabled:
            return ui.div(
                widget,
                style="opacity: 0.6; pointer-events: none; user-select: none;",
                title="This field is disabled for your role"
            )
        else:
            return widget
    
    def create_form_ui(self, user_roles: List[str] = None) -> List[ui.Tag]:
        """Create the complete form UI with all fields and actions"""
        if user_roles is None:
            user_roles = []
        
        form_elements = []
        
        # Create input widgets for each field
        for field_name in self.form_fields.keys():
            widget = self._create_input_widget(field_name, user_roles)
            form_elements.append(widget)
            form_elements.append(ui.br())
        
        return form_elements
    
    def create_action_buttons(self, current_status: str = None) -> List[ui.Tag]:
        """Create action buttons based on workflow status"""
        if not self.actions or current_status in ['start', 'stop']:
            return []
        
        button_elements = []
        action_items = list(self.actions.items())
        
        # Create buttons in a grid layout (5 columns like Streamlit)
        num_cols = min(5, len(action_items))
        if num_cols > 0:
            col_width = 12 // num_cols
            
            button_rows = []
            for i, (action_key, action_config) in enumerate(action_items):
                if i % 5 == 0:  # Start new row every 5 buttons
                    button_rows.append([])
                
                button = ui.input_action_button(
                    action_key,
                    action_config.get('title', action_key),
                    class_="btn btn-primary"
                )
                button_rows[-1].append(button)
            
            # Create UI rows with columns
            for row in button_rows:
                if row:
                    cols = [ui.column(col_width, btn) for btn in row]
                    button_elements.append(ui.row(*cols))
        
        return button_elements
    
    def get_form_data(self, input_values: Dict[str, Any], submitted_action: str = None) -> Optional[Dict[str, Any]]:
        """Extract form data from Shiny input values"""
        if not submitted_action:
            return None
        
        values = {}
        
        # Extract field values
        for field_name in self.form_fields.keys():
            if field_name in input_values:
                values[field_name] = input_values[field_name]
        
        # Add action information
        values['actions'] = {}
        for action_name in self.actions.keys():
            if action_name in input_values:
                values['actions'][action_name] = input_values[action_name]
        
        values['action'] = submitted_action
        
        return values

class ShinyFormRenderer:
    """
    Helper class to render Shiny forms in server functions
    """
    
    def __init__(self, form: ShinyForm):
        self.form = form
    
    def setup_dataframe_outputs(self, output, input):
        """Setup reactive outputs for dataframe fields"""
        for field_name, field_config in self.form.form_fields.items():
            if field_config['type'] == 'dataframe':
                output_name = f"{field_name}_display"
                
                @output
                @render.data_frame
                def _dataframe_output():
                    if field_name == 'audit':
                        return pd.DataFrame(self.form.audit_data)
                    else:
                        # Get dataframe from form data
                        df_data = self.form.form_data.get(field_name)
                        if isinstance(df_data, pd.DataFrame):
                            return df_data
                        elif df_data:
                            try:
                                return pd.DataFrame(df_data)
                            except:
                                return pd.DataFrame()
                        return pd.DataFrame()
                
                # Register the output with a unique name
                setattr(output, output_name, _dataframe_output)
    
    def setup_action_handlers(self, input, on_action_callback):
        """Setup reactive handlers for action buttons"""
        for action_name in self.form.actions.keys():
            
            @reactive.Effect
            @reactive.event(getattr(input, action_name))
            def _action_handler(action=action_name):
                if on_action_callback:
                    on_action_callback(action)