import sqlalchemy as sa

from models.db.base import Base

class Group(Base):
    __tablename__ = 'groups'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    lastReport = sa.Column(sa.Text, nullable=True)
    startReset = sa.Column(sa.Text, nullable=True)
