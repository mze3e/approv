import yaml

class Workflow:
    def __init__(self, config):
        self.config = config
        self.current_status = "start"
        self.form_data = {"audit": []}
        
    def process_workflow(self, form_data):
        step_config = self.config['workflow'][self.current_status]
        step_class = step_config['class']
        
        step = globals()[step_class](step_config)
        
        self.current_status, decision = step.process(form_data)
        form_data['audit'].append(decision)
        
        return form_data

    def initiate(self):
        self.current_status = "start"
        self.form_data['audit'].append("Workflow initiated")
        return self.form_data

    def cancel(self):
        self.current_status = "stop"
        self.form_data['audit'].append("Workflow canceled")
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


    def process_workflow(self, user_role, form_data):
        # New: Check if the user has permission to execute this step
        step_config = self.config['workflow'][self.current_status]
        if not self.check_user_permission(step_config, user_role):
            raise PermissionError("User does not have permission to execute this step.")

        step_class = step_config['class']
        step = globals()[step_class](step_config)
        
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
        return form_data