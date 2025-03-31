"""
Database models for the GLA Grants application.

This module defines the SQLAlchemy ORM models that represent the
database schema for the GLA Grants application, including User and
GrantApplication models.
"""
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from coursework2.gla_grants_app import db

class User(db.Model):
    """
    Model representing users of the application.
    
    Attributes:
        id: Primary key for the user.
        username: Unique username for the user.
        password: Hashed password for the user.
        is_admin: Boolean flag indicating if the user has admin privileges.
        applications: Relationship to application submissions.
    """
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    applications = relationship("GrantApplication", back_populates="user")

class GrantApplication(db.Model):
    """
    Model representing grant applications submitted by users.
    
    Attributes:
        id: Primary key for the application.
        user_id: Foreign key to the user who submitted the application.
        title: Title of the grant application.
        description: Detailed description of the grant application.
        category: Category of the grant application.
        question: Specific question posed by the applicant.
        comment: Optional admin feedback on the application.
        date_submitted: Date when the application was submitted.
        user: Relationship to the user who submitted the application.
    """
    __tablename__ = 'grant_applications'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    date_submitted: Mapped[str] = mapped_column(Text, nullable=False)
    
    user = relationship("User", back_populates="applications")