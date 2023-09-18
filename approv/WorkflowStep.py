class RESTCall:
    def __init__(self, config):
        self.config = config

    def process(self, form_data):
        # Here, we're simulating a REST call.
        # You'd replace this with an actual HTTP request in a real-world application.
        response = True  # simulated success response
        if response:
            return self.config['outputs'][0], "RESTCall executed successfully"
        else:
            return "error", "RESTCall failed"

class Stop:
    def __init__(self, config):
        self.config = config

    def process(self, form_data):
        return None, "Workflow stopped"

class Simple:
    def __init__(self, config):
        self.config = config
        
    def process(self, form_data):
        return self.config['outputs'][0], "Simple step executed"

class Start:
    def __init__(self, config):
        self.config = config
        
    def process(self, form_data):
        return self.config['outputs'][0], "Started"
    
class Stop:
    def __init__(self, config):
        self.config = config

    def process(self, form_data):
        return None, "Workflow stopped"

class ExclusiveChoice:
    def __init__(self, config):
        self.config = config
        
    def process(self, form_data):
        #print("ExclusiveChoice Config: ", self.config)
        #print("FormData: ", form_data)
        for condition_name, condition in self.config['conditions'].items():
            if condition_name != "default":
                #print("\n\n\ncondition_name: ", condition_name)
                #print("condition: ", condition)
                operator = condition['operator']
                attribute = condition['attribute']
                value = condition['value']

                # Here we check the condition based on the operator.
                # We only handle the Equal operator for simplicity.
                if operator == "Equal" and form_data[attribute] == value:
                    return condition['next_status'], f"Decision made: {condition_name}"

        # If none of the conditions are met, return the default
        return self.config['conditions']['default'], "Decision made: default"