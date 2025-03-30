import json
import random

class BotException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.text = args[0]
    
    def __str__(self):
        return self.text

class BotWrongInputException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

def getUncompletedSpending(spendings):
    unCompleted = []
    for item in spendings:
        if item['isCompleted'] == 0:
            unCompleted.append(item)
    if len(unCompleted) == 0:
        return None
    return random.choice(unCompleted)

def convertSpendingsToReportDto(spendings):
    return list(map(lambda record: {
        'amount': record['costAmount'],
        'creditor': record['telegramFromId'],
        'isCompleted': record['isCompleted'],
        'debtors': json.loads(record['debtors']),
        'comment': record['desc'],
        'date': record['date']
    }, spendings))