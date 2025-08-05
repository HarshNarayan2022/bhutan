from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False)
    age = Column(Integer, CheckConstraint("age > 0 AND age <= 150"))
    
    gender = Column(String(20), CheckConstraint(
        "gender IN ('Male', 'Female', 'Non-binary', 'Other', 'Prefer not to say')"
    ))

    city_region = Column(String(100))
    profession = Column(String(100))

    marital_status = Column(String(30), CheckConstraint(
        "marital_status IN ('Single', 'In relationship', 'Married', 'Divorced', 'Widowed', 'Other', 'Prefer not to say')"
    ))

    previous_mental_diagnosis = Column(Text, default="NA")
    ethnicity = Column(String(50))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)

    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())

