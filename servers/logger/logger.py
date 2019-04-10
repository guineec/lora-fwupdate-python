class Logger:
    def __init__(self, server_instance):
        self.instance = server_instance
        self.json_dict = {}

    def __create_dict(self):

