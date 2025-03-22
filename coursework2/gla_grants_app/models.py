from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from gla_grants_app import db

class Grant(db.Model):
    """Model representing GLA grant data"""
    __tablename__ = 'grants'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    amount_awarded: Mapped[float] = mapped_column(Float)
    funding_org_department: Mapped[str] = mapped_column(Text)
    recipient_org_name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    award_date: Mapped[str] = mapped_column(Text)
    
    # Relationship to application submissions
    applications = relationship("GrantApplication", back_populates="grant")

class User(db.Model):
    """Model representing users of the application"""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Relationship to application submissions
    applications = relationship("GrantApplication", back_populates="user")

class GrantApplication(db.Model):
    """Model representing grant applications submitted by users"""
    __tablename__ = 'grant_applications'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    grant_id: Mapped[Optional[int]] = mapped_column(ForeignKey('grants.id'))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    date_submitted: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships to parent tables
    user = relationship("User", back_populates="applications")
    grant = relationship("Grant", back_populates="applications")