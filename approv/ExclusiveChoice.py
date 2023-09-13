class ExclusiveChoice:
    def __init__(self, config):
        self.config = config
        
    def process(self, form_data):
        for condition_name, condition in self.config['conditions'].items():
            operator = condition['operator']
            attribute = condition['attribute']
            value = condition['value']

            # Here we check the condition based on the operator.
            # We only handle the Equal operator for simplicity.
            if operator == "Equal" and form_data[attribute] == value:
                return condition_name, f"Decision made: {condition_name}"

        # If none of the conditions are met, return the default
        return self.config['conditions']['default'], "Decision made: default"