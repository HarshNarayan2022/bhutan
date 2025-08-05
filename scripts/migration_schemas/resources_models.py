import yaml
from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    Date,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import os
from backend.app.core.deps import EMBEDDING_DIM as embedding_dim
from sqlalchemy import UniqueConstraint

Base = declarative_base()


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    phone = Column(String)
    website = Column(String)
    address = Column(String)
    operation_hours = Column(String)
    category = Column(String)  # e.g., "mental_health", "addiction", etc.
    type = Column(String, nullable=False)  # e.g., "helpline", "organization"
    source = Column(String)

    __table_args__ = (
        UniqueConstraint("name", name="uq_resource_name"),
    )

class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, unique=True)
    title = Column(String, nullable=False, unique=True)
    author = Column(String)
    source = Column(String)
    published_date = Column(Date)
    topic = Column(String)

    chunks = relationship("ArticleChunk", back_populates="article")

class ArticleChunk(Base):
    __tablename__ = "article_chunks"

    chunk_id = Column(String, primary_key=True, unique=True)
    doc_id = Column(String, ForeignKey("articles.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(embedding_dim))
    keywords = Column(Text) 

    article = relationship("Article", back_populates="chunks")                    

  
  