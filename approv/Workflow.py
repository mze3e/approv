import yaml
from approv.WorkflowStep import Start, Stop, Simple, RESTCall, ExclusiveChoice
import time
from datetime import datetime
from ast import literal_eval
from approv.Form import Form

class Workflow:
    def __init__(self, st, workflow_config, form_config, form_data=None):
        self.config = workflow_config
        try:
            self.current_status = 'start' if form_data['status'] == '' else form_data['status']
        except:
            self.current_status = 'start'

        self.form_data = form_data
        self.form_config = form_config
        self.st = st
        if 'audit' not in st.session_state:
            st.session_state['audit'] = []
            self.audit_data = st.session_state.audit
        else:
            self.audit_data = st.session_state.audit

        self.form = Form(self.st, self.form_config, self.audit_data)

    def audit(self, action, user, description=""):
        new_audit = {'status': self.current_status, 'action': action, 'description': description, 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'user': user}
        self.audit_data.append(new_audit)
        # self.form_data['audit'] = str(self.audit_data)
                
    def initiate(self):
        self.current_status = "start"
        self.audit("Workflow Initiated", 'system')
        return self.form_data

    def cancel(self):
        self.current_status = "stop"
        self.audit("Workflow canceled", 'system')
        return self.form_data
        
    def evaluate_condition(operator, attribute_value, condition_value):
        """
        Evaluates a condition based on the given operator.

        :param operator: The condition operator
        :param attribute_value: The value from the form_data
        :param condition_value: The value specified in the condition
        :return: Boolean indicating if the condition is met
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
            # Assuming both are lists or strings
            return condition_value in attribute_value
        elif operator == "InList":
            # Assuming attribute_value is a single item and condition_value is a list
            return attribute_value in condition_value

        return False

    def get_status(self):
        return self.current_status()

    def process_workflow(self, user_role, form_data):
        # New: Check if the user has permission to execute this step
        # try:
        #     self.audit_data = literal_eval(form_data['audit'])
        # except:
        #     pass
        
        try:
            if len(form_data['comments']) > 0:
                self.audit("Commented", user_role, form_data['comments'])
                form_data['comments'] = ""
        except:
            form_data['comments'] = ""

        while True:
            time.sleep(1)            
            step_config = self.config['workflow'][self.current_status]
            if not self.check_user_permission(step_config, user_role) and self.config['workflow'][self.current_status]['require_user_action']:
                raise PermissionError("User does not have permission to execute this step.")

            step_class = step_config['class']
            step = globals()[step_class](step_config)
            self.current_status, decision = step.process(form_data)
            self.audit(decision, user_role)
            self.form_data['status'] = self.current_status #post process status

            if self.current_status == 'stop':
                break
            try:
                if self.config['workflow'][self.current_status]['require_user_action'] == False:
                    continue
                else:
                    break
            except:
                break

        return self.form_data

    def check_user_permission(self, step_config, user_role):
        if 'role' in step_config and step_config['role'] and user_role not in step_config['role']:
            return False
        return True

    def get_form(self, user_role):
        self.form.get_form(data=self.form_data , user=user_role, actions=None)
        
        if 'submitted_by' in self.st.session_state:
            if self.st.session_state.submitted_by != "":
                self.st.session_state.form_data = self.form.get_form_data()
                self.st.write(self.st.session_state.form_data)
                self.st.session_state.submitted_by = ""
                with self.st.spinner("Processing"):
                    try:
                        updated_form_data = self.process_workflow(self.st.session_state.user, self.st.session_state.form_data)
                        self.st.session_state.form_data = updated_form_data
                        self.st.session_state.prev_form_data = self.st.session_state.form_data.copy()
                        self.st.session_state.submitted_by = ""
                        self.st.experimental_rerun()
                    except Exception as e:
                        self.st.error("Error occurred while processing")
                        self.st.error(e)
                   
"""
# Updated to use the evaluate_condition function for conditions
for condition_name, condition in self.config['conditions'].items():
    operator = condition['operator']
    attribute = condition['attribute']
    value = condition['value']

    if self.evaluate_condition(operator, form_data.get(attribute, None), value):
        self.current_status, decision = step.process(form_data)
        form_data['audit'].append(decision)
        return form_data

# If none of the conditions are met, return the default
self.current_status, decision = step.process(form_data)
form_data['audit'].append(decision)
"""