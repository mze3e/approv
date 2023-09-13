class Simple:
    def __init__(self, config):
        self.config = config
        
    def process(self, form_data):
        return self.config['outputs'][0], "Simple step executed"