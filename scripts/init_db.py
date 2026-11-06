"""Initialise the database (create all tables)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.database import Base, engine
Base.metadata.create_all(bind=engine)
print("Database initialised.")
