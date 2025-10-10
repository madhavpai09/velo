import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://Mini_Uber_user:password@localhost/Mini_Uber"
)

# Create engine with error handling
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    def create_tables():
        """Create all database tables"""
        try:
            from database.models import RideRequestDB
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
        except Exception as e:
            print(f" Could not create database tables: {e}")
            print(" We will store this data in Postgres once connection is established")
            
except Exception as e:
    print(f" Database connection failed: {e}")
    print(" Running without database - will print data instead")
    
    # Mock functions for when database is not available
    def get_db():
        return None
        
    def create_tables():
        print("We will store this data in Postgres once connection is established")
