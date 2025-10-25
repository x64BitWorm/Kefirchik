import json
from typing import Any
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from models.db.base import Base

class Spending(Base):
    __tablename__ = 'costs'
    messageId = sa.Column(sa.Integer, primary_key=True)
    groupId = sa.Column(sa.Integer, sa.ForeignKey('groups.id'), primary_key=True)
    isCompleted = sa.Column(sa.Boolean)
    telegramFromId = sa.Column(sa.String)
    costAmount = sa.Column(sa.Float)
    _debtors = sa.Column('debtors', sa.Text)
    desc = sa.Column(sa.Text)
    date = sa.Column(sa.Integer)

    @hybrid_property
    def debtors(self) -> dict[str, Any]:
        if self._debtors:
            return json.loads(self._debtors)
        return {}
    
    @debtors.setter
    def debtors(self, value: dict[str, Any]):
        self._debtors = json.dumps(value)

    @debtors.expression
    def debtors(cls):
        return cls._debtors

