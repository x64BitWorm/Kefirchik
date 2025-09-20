import sqlite3
from datetime import datetime
import json

from models.db.group import Group
from models.db.spending import Spending

class IDatabase:
    def getGroup(self, id) -> Group:
        """TODO"""
        pass
    def getSpendings(self, groupId) -> list[Spending]:
        pass
    def insertCost(self, messageId, groupId, isCompleted, telegramFromId, costAmount, debtors, desc):
        pass
    def updateCost(self, groupId, messageId, isCompleted, debtors, desc):
        pass
    def getCost(self, groupId, messageId) -> Spending:
        pass
    def removeCosts(self, groupId):
        pass
    def removeCost(self, groupId, messageId):
        pass

class Database(IDatabase):
    def __init__(self, path: str = None):
        self.sqlite_connection = sqlite3.connect(':memory:' if path == None else path)
        cursor = self.sqlite_connection.cursor()
        sqlite_select_query = "select sqlite_version();"
        cursor.execute(sqlite_select_query)
        record = cursor.fetchall()
        # record - SQLite version
        cursor.execute("CREATE TABLE IF NOT EXISTS groups (id NUMERIC (8) PRIMARY KEY NOT NULL UNIQUE, lastReport BLOB, startReset INTEGER);")
        cursor.execute("CREATE TABLE IF NOT EXISTS costs (messageId NUMERIC (8) PRIMARY KEY UNIQUE NOT NULL, groupId INTEGER REFERENCES groups (id) NOT NULL, isCompleted INTEGER (1) NOT NULL, telegramFromId TEXT NOT NULL, costAmount REAL (8) NOT NULL, Debtors TEXT NOT NULL, Desc TEXT NOT NULL, date INTEGER(4) NOT NULL);")
        cursor.close()
    
    def getGroup(self, id) -> Group:
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'select * from groups where id = {id};')
            record = cursor.fetchall()
            if (len(record) == 0):
                cursor.execute(f'insert into groups (id, lastReport, startReset) values ({id}, \'\', 0);')
                self.sqlite_connection.commit()
                cursor.execute(f'select * from groups where id = {id};')
                record = cursor.fetchall()
            record = record[0]
            result = { 'id': record[0], 'lastReport': record[1], 'startReset': record[2] }
            return Group(result)
        finally:
            cursor.close()

    def getSpendings(self, groupId) -> list[Spending]:
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'select * from costs where groupId = {groupId};')
            records = cursor.fetchall()
            return list(map(lambda record: Spending({
                'messageId': record[0],
                'groupId': record[1],
                'isCompleted': record[2],
                'telegramFromId': record[3],
                'costAmount': record[4],
                'debtors': record[5],
                'desc': record[6],
                'date': datetime.fromtimestamp(record[7])
                }), records))
        finally:
            cursor.close()

    def insertCost(self, messageId, groupId, isCompleted, telegramFromId, costAmount, debtors, desc):
        try:
            cursor = self.sqlite_connection.cursor()
            now = int(datetime.now().timestamp())
            cursor.execute(f'insert into costs (messageId, groupId, isCompleted, telegramFromId, costAmount, debtors, desc, date) values ({messageId}, {groupId}, {isCompleted}, \'{telegramFromId}\', {costAmount}, \'{json.dumps(debtors)}\', \'{desc}\', {now});')
            self.sqlite_connection.commit()
        finally:
            cursor.close()

    def updateCost(self, groupId, messageId, isCompleted, debtors, desc):
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'update costs set isCompleted = {isCompleted}, debtors = \'{json.dumps(debtors)}\', desc = \'{desc}\' where groupId = {groupId} and messageId = {messageId};')
            self.sqlite_connection.commit()
        finally:
            cursor.close()

    def getCost(self, groupId, messageId) -> Spending:
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'select * from costs where groupId = {groupId} and messageId = {messageId};')
            record = cursor.fetchall()
            record = record[0]
            result = { 'messageId': record[0], 'groupId': record[1], 'isCompleted': record[2], 'telegramFromId': record[3], 'costAmount': record[4], 'debtors': record[5], 'desc': record[6], 'date': datetime.fromtimestamp(record[7]) }
            return Spending(result)
        except:
            return None
        finally:
            cursor.close()

    def removeCosts(self, groupId):
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'delete from costs where groupId = {groupId};')
            self.sqlite_connection.commit()
            return True
        finally:
            cursor.close()

    def removeCost(self, groupId, messageId):
        try:
            cursor = self.sqlite_connection.cursor()
            cursor.execute(f'delete from costs where groupId = {groupId} and messageId = {messageId};')
            self.sqlite_connection.commit()
            return True
        finally:
            cursor.close()
