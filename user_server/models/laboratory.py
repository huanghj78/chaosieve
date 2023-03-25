from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
import sys
print(sys.path)

Base = declarative_base()


class Laboratory(Base):
    __tablename__ = "laboratory"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    create_at = Column(String(50), unique=True)
    nodes = Column(String(120), unique=True)

    def __init__(self, name=None, create_at=None, nodes=nodes):
        self.name = name
        self.create_at = create_at
        self.nodes = nodes.join(',')

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, create_at={self.create_at!r}, nodes={self.nodes!r})"


engine = create_engine('mysql+pymysql://root:dr3645DRG@localhost:3306/chaos')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
lab = Laboratory("lab1", "1 mins ago", "11111")
db_session.add(lab)
db_session.commit()
db_session.remove()
