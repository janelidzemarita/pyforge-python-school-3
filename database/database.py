import os
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for model definitions
Base = declarative_base()


# Function to initialize the database (create tables)
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except IntegrityError:
        print("Database already exists.")
