import sqlalchemy as sa

from models.db.base import Base

class Migration(Base):
    __tablename__ = 'migrations'
    id = sa.Column(sa.Integer, primary_key=True, unique=True)
    name = sa.Column(sa.Text)
    date = sa.Column(sa.Text(23))
