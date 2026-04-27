from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

# sqlite for testing ui without postgres dependency
engine = create_engine('sqlite:///turtle_test.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("Database sqlite initialized.")
