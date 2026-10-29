from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL="postgresql://postgres:1234@localhost/postgres"
engine=create_engine(SQLALCHEMY_DATABASE_URL)
#engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread' : False})

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()
#git commit -m "Safety checkpoint before cleanup"