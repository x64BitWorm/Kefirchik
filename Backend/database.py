import sqlite3

sqlite_connection = 0



def initDatabase():
    global sqlite_connection
    sqlite_connection = sqlite3.connect('..\\Database\\kefirchik.db')
    cursor = sqlite_connection.cursor()
    sqlite_select_query = "select sqlite_version();"
    cursor.execute(sqlite_select_query)
    record = cursor.fetchall()
    print("SQLite version - ", record)
    cursor.execute("CREATE TABLE IF NOT EXISTS groups (id NUMERIC (8) PRIMARY KEY NOT NULL UNIQUE, lastReport BLOB, startReset INTEGER);")
    cursor.execute("CREATE TABLE IF NOT EXISTS costs (messageId NUMERIC (8) PRIMARY KEY UNIQUE NOT NULL, groupId INTEGER REFERENCES groups (id) NOT NULL, isCompleted INTEGER (1) NOT NULL, telegramFromId NUMERIC (8) NOT NULL, costAmount REAL (8) NOT NULL, Debtors TEXT NOT NULL);")
    cursor.close()
