from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
#from datetime import datetime
from typing import Optional
import os
import uuid

# Database configuration
DATABASE_URL = os.getenv("SUPABASE_DB_URI")
print(f"Connecting to database at {DATABASE_URL}")


# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the UserProfile model
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    age = Column(Integer)
    gender = Column(String(20))
    city_region = Column(String(100))
    profession = Column(String(100))
    marital_status = Column(String(30))
    previous_mental_diagnosis = Column(Text, default='NA')
    ethnicity = Column(String(50))
    #created_at = Column(DateTime(timezone=True), server_default=func.now())
    #updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserProfile(id='{self.id}', name='{self.name}', age={self.age})>"
    
    def to_dict(self):
        """Convert the model instance to a dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'city_region': self.city_region,
            'profession': self.profession,
            'marital_status': self.marital_status,
            'previous_mental_diagnosis': self.previous_mental_diagnosis,
            'ethnicity': self.ethnicity,
            #'created_at': self.created_at.isoformat() if self.created_at else None,
            #'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Database operations class
class UserProfileRepository:
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Fetch a single user profile by ID
        
        Args:
            user_id (str): The user ID to search for
            
        Returns:
            UserProfile or None: The user profile if found, None otherwise
        """
        try:
            user = self.session.query(UserProfile).filter(UserProfile.id == user_id).first()
            return user
        except Exception as e:
            print(f"Error fetching user by ID {user_id}: {e}")
            self.session.rollback()
            return None
    

def get_user_profile(user_id: str) -> Optional[dict]:
    """
    Retrieve a user profile by ID
    
    Args:
        user_id (str): The user ID to search for
        
    Returns:
        dict or None: User profile data as a dictionary, or None if not found
    """
    with UserProfileRepository() as repo:
        user = repo.get_user_by_id(user_id)
        return user.to_dict() if user else None
        

