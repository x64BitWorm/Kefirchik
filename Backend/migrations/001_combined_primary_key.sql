PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM costs;

DROP TABLE costs;

CREATE TABLE costs (
    messageId      NUMERIC (8) NOT NULL,
    groupId        INTEGER     REFERENCES groups (id) 
                               NOT NULL,
    isCompleted    INTEGER (1) NOT NULL,
    telegramFromId TEXT        NOT NULL,
    costAmount     REAL (8)    NOT NULL,
    Debtors        TEXT        NOT NULL,
    Desc           TEXT        NOT NULL,
    date           INTEGER (8),
    PRIMARY KEY (
        messageId,
        groupId
    ),
    UNIQUE (
        messageId,
        groupId
    )
);

INSERT INTO costs (
                      messageId,
                      groupId,
                      isCompleted,
                      telegramFromId,
                      costAmount,
                      Debtors,
                      Desc,
                      date
                  )
                  SELECT messageId,
                         groupId,
                         isCompleted,
                         telegramFromId,
                         costAmount,
                         Debtors,
                         Desc,
                         date
                    FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
