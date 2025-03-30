import json

class Group:
    def __init__(self, obj: any):
        self.id = int(obj['id'])
        self.lastReport = obj['lastReport']
        self.startReset = obj['startReset']
