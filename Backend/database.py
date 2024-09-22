import sqlite3
from datetime import datetime

sqlite_connection = 0

def getGroup(id):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'select * from groups where id = {id};')
        record = cursor.fetchall()
        if (len(record) == 0):
            cursor.execute(f'insert into groups (id, lastReport, startReset) values ({id}, \'\', 0);')
            sqlite_connection.commit()
            cursor.execute(f'select * from groups where id = {id};')
            record = cursor.fetchall()
        record = record[0]
        result = { 'id': record[0], 'lastReport': record[1], 'startReset': record[2] }
        return result
    finally:
        cursor.close()

def getSpendings(groupId):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'select * from costs where groupId = {groupId};')
        records = cursor.fetchall()
        return list(map(lambda record: {
            'messageId': record[0],
            'groupId': record[1],
            'isCompleted': record[2],
            'telegramFromId': record[3],
            'costAmount': record[4],
            'debtors': record[5],
            'desc': record[6],
            'date': datetime.fromtimestamp(record[7])
            }, records))
    finally:
        cursor.close()

def insertCost(messageId, groupId, isCompleted, telegramFromId, costAmount, debtors, desc):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        now = int(datetime.now().timestamp())
        cursor.execute(f'insert into costs (messageId, groupId, isCompleted, telegramFromId, costAmount, debtors, desc, date) values ({messageId}, {groupId}, {isCompleted}, \'{telegramFromId}\', {costAmount}, \'{debtors}\', \'{desc}\', {now});')
        sqlite_connection.commit()
    finally:
        cursor.close()

def updateCost(groupId, messageId, isCompleted, debtors):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'update costs set isCompleted = {isCompleted}, debtors = \'{debtors}\' where groupId = {groupId} and messageId = {messageId};')
        sqlite_connection.commit()
    finally:
        cursor.close()

def getCost(groupId, messageId):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'select * from costs where groupId = {groupId} and messageId = {messageId};')
        record = cursor.fetchall()
        record = record[0]
        result = { 'messageId': record[0], 'groupId': record[1], 'isCompleted': record[2], 'telegramFromId': record[3], 'costAmount': record[4], 'debtors': record[5], 'desc': record[6], 'date': datetime.fromtimestamp(record[7]) }
        return result
    finally:
        cursor.close()

def removeCosts(groupId):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'delete from costs where groupId = {groupId};')
        sqlite_connection.commit()
        return True
    finally:
        cursor.close()

def removeCost(groupId, messageId):
    global sqlite_connection
    try:
        cursor = sqlite_connection.cursor()
        cursor.execute(f'delete from costs where groupId = {groupId} and messageId = {messageId};')
        sqlite_connection.commit()
        return True
    finally:
        cursor.close()

def initDatabase():
    global sqlite_connection
    sqlite_connection = sqlite3.connect('/var/lib/kefirchik/kefirchik.db')
    cursor = sqlite_connection.cursor()
    sqlite_select_query = "select sqlite_version();"
    cursor.execute(sqlite_select_query)
    record = cursor.fetchall()
    print("SQLite version - ", record)
    cursor.execute("CREATE TABLE IF NOT EXISTS groups (id NUMERIC (8) PRIMARY KEY NOT NULL UNIQUE, lastReport BLOB, startReset INTEGER);")
    cursor.execute("CREATE TABLE IF NOT EXISTS costs (messageId NUMERIC (8) PRIMARY KEY UNIQUE NOT NULL, groupId INTEGER REFERENCES groups (id) NOT NULL, isCompleted INTEGER (1) NOT NULL, telegramFromId TEXT NOT NULL, costAmount REAL (8) NOT NULL, Debtors TEXT NOT NULL, Desc TEXT NOT NULL);")
    cursor.close()
