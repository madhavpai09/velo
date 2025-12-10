import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.connections import engine
from database.models import Base

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")

if __name__ == "__main__":
    init_db()
