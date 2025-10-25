CREATE TABLE IF NOT EXISTS groups (
    id NUMERIC (8) PRIMARY KEY NOT NULL UNIQUE,
    lastReport BLOB,
    startReset INTEGER
);

CREATE TABLE IF NOT EXISTS costs (
    messageId NUMERIC (8) PRIMARY KEY UNIQUE NOT NULL,
    groupId INTEGER REFERENCES groups (id) NOT NULL,
    isCompleted INTEGER (1) NOT NULL,
    telegramFromId TEXT NOT NULL,
    costAmount REAL (8) NOT NULL,
    Debtors TEXT NOT NULL,
    Desc TEXT NOT NULL,
    date INTEGER(4) NOT NULL
);
