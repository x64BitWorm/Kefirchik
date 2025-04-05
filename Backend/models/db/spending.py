import json

class Spending:
    def __init__(self, obj: any):
        self.messageId = int(obj['messageId'])
        self.groupId = int(obj['groupId'])
        self.isCompleted = bool(obj['isCompleted'])
        self.telegramFromId = str(obj['telegramFromId'])
        self.costAmount = float(obj['costAmount'])
        self.debtors = dict(json.loads(obj['debtors']))
        self.desc = str(obj['desc'])
        self.date = obj['date']
