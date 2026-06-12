from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

class DbCard(Base):
    __tablename__ = "inventory"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    set_name    = Column(String, nullable=False)
    num         = Column(String, nullable=False)
    lot_name    = Column(String, nullable=True, default="Main Lot")
    slab_grade  = Column(String, nullable=True)
    cost_paid   = Column(Float, nullable=True)
    collectr    = Column(Float, nullable=True)
    raw         = Column(Float, nullable=True)
    psa_8       = Column(Float, nullable=True)
    psa_9       = Column(Float, nullable=True)
    psa_10      = Column(Float, nullable=True)
    tcgplayer   = Column(Float, nullable=True)
    url         = Column(String, nullable=True)
    last_updated = Column(String, nullable=True)

# Sticker is an alias kept for backward compat
DbCard.sticker = DbCard.cost_paid

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
