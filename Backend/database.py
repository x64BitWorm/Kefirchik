import json
import os
from datetime import datetime
from typing import Any
import sqlalchemy as sa
from sqlalchemy import func, text
from sqlalchemy.orm import sessionmaker, Session

import utils
from models.db.migration import Migration
from models.db.base import Base
from models.db.group import Group
from models.db.spending import Spending

class IDbSession:
    def __init__(self, session: Session):
        self.u = session
    def close(self):
        """Close session after all operations"""
        pass
    def commit(self):
        """Apply all changes as transaction"""
        pass
    def rollback(self):
        """Cancel transaction"""
        pass
    def getGroup(self, id: int) -> Group:
        """Find group by id"""
        pass
    def getSpendings(self, groupId: int) -> list[Spending]:
        """Find all spendings related to group"""
        pass
    def insertSpending(self, messageId: int, groupId: int, isCompleted: bool, telegramFromId: str, costAmount: float, debtors, desc: str):
        """Attach new spending to group"""
        pass
    def updateSpending(self, groupId: int, messageId: int, isCompleted: bool, debtors: Any, desc: str):
        """Update spending data"""
        pass
    def getSpending(self, groupId: int, messageId: int) -> Spending:
        """Find spending by composite key"""
        pass
    def removeSpendings(self, groupId: int):
        """Delete all group spendings"""
        pass
    def removeSpending(self, groupId: int, messageId: int):
        """Delete specific spending"""
        pass

class DbSession(IDbSession):
    def __init__(self, session: Session):
        super().__init__(session)
    
    def close(self):
        self.u.close()
    
    def commit(self):
        self.u.commit()
    
    def rollback(self):
        self.u.rollback()
    
    def getGroup(self, id: int) -> Group:
        group = self.u.query(Group).filter(
            Group.id == id,
        ).first()
        if group == None:
            group = Group(id=id, lastReport='', startReset=0)
            self.u.add(group)
            self.u.commit()
        return group

    def getSpendings(self, groupId: int) -> list[Spending]:
        return self.u.query(Spending).filter(
            Spending.groupId == groupId
        ).all()

    def insertSpending(self, messageId: int, groupId: int, isCompleted: bool, telegramFromId: str, costAmount: float, debtors, desc: str):
        now = int(datetime.now().timestamp())
        self.u.add(Spending(
            messageId = messageId,
            groupId = groupId,
            isCompleted = isCompleted,
            telegramFromId = telegramFromId,
            costAmount = costAmount,
            debtors = debtors,
            desc = desc,
            date = now
        ))

    def updateSpending(self, groupId: int, messageId: int, isCompleted: bool, debtors: Any, desc: str):
        self.u.query(Spending).filter(
            (Spending.groupId == groupId) & (Spending.messageId == messageId)
            ).update({
                'isCompleted': isCompleted,
                'debtors': json.dumps(debtors),
                'desc': desc
            })

    def getSpending(self, groupId: int, messageId: int) -> Spending:
        return self.u.query(Spending).filter(
            (Spending.groupId == groupId) & (Spending.messageId == messageId),
        ).first()

    def removeSpendings(self, groupId: int):
        self.u.query(Spending).filter(Spending.groupId == groupId).delete()

    def removeSpending(self, groupId: int, messageId: int):
        self.u.query(Spending).filter((Spending.groupId == groupId) & (Spending.messageId == messageId)).delete()

class DbManager:
    def __init__(self, path: str = None):
        dbpath = 'sqlite:///:memory:'
        if path != None:
            dbpath = f'sqlite:///{os.path.abspath(path)}'
        self.main_engine = sa.create_engine(
            dbpath,
            echo=False,
        )
    
    def applyMigrations(self):
        """Applies all pending migrations to current engine"""
        Migration.__table__.create(self.main_engine, checkfirst=True)
        dbs = self.newSession()
        try:
            from_id = dbs.u.query(func.max(Migration.id)).scalar()
            if from_id == None:
                from_id = -1
            migration_files = sorted([f for f in os.listdir('migrations')])
            for file in migration_files:
                idx, name, *rest = file.split('_', maxsplit=1)
                idx = int(idx)
                name = name.removesuffix('.sql')
                if idx <= from_id:
                    continue
                with open(os.path.join('migrations', file), 'r') as file_ptr:
                    content = file_ptr.read()
                    print('applying migration - ', file)
                    connection = self.main_engine.raw_connection()
                    cursor = connection.cursor()
                    cursor.executescript(content)
                    cursor.close()
                    dbs.u.add(Migration(id=idx, name=name, date=utils.iso_date()))
                    dbs.commit()
        finally:
            dbs.close()
    
    def newSession(self) -> DbSession:
        """Creates new isolated session"""
        DBSession = sessionmaker(
            binds={
                Base: self.main_engine,
            },
            expire_on_commit=False,
        )
        return DbSession(DBSession())
