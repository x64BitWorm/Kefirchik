class BotException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.text = args[0]
    
    def __str__(self):
        return self.text

class BotWrongInputException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
