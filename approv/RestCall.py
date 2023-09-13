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
