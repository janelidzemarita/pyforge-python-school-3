from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:password@localhost:5432/myMoleculeDB"

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for model definitions
Base = declarative_base()


# Function to initialize the database (create tables)
def init_db():
    Base.metadata.create_all(bind=engine)
