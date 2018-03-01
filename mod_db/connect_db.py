from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base
from flask import Blueprint

db = Blueprint('mod_db', __name__)


def connect_db():

    # Connect to Database and create database session
    engine = create_engine('sqlite:///homeworkitems.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session
