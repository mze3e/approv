class Stop:
    def __init__(self, config):
        self.config = config

    def process(self, form_data):
        return None, "Workflow stopped"
