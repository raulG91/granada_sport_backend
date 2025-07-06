import os
from sqlmodel import SQLModel,create_engine, Session
from fastapi import Depends
from typing import Annotated

DB_URL = os.getenv("DATABASE_URL")
#DB_URL ="mysql+pymysql://root@localhost/granada_sport"


if DB_URL is None:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DB_URL, echo=True, future=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("Database and tables created successfully.")

def getSession():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session,Depends(getSession)]
