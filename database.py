"""
Database models and utilities for SQLite.
Handles user authentication, session history, and usage tracking.
"""
import logging
from datetime import datetime, date
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from config import settings
import bcrypt

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """User model for authentication and subscription management."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("OptimizationSession", back_populates="user")


class OptimizationSession(Base):
    """Model for tracking optimization sessions."""
    __tablename__ = "optimization_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    original_prompt = Column(Text, nullable=False)
    prompt_type = Column(String(50), nullable=False)  # creative, technical, etc.
    optimized_prompt = Column(Text, nullable=True)
    sample_output = Column(Text, nullable=True)
    quality_score = Column(Integer, nullable=True)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class DailyUsage(Base):
    """Model for tracking daily usage limits."""
    __tablename__ = "daily_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    date = Column(Date, default=date.today, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Unique constraint on user_id and date
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class Database:
    """Database management class."""
    
    def __init__(self):
        """Initialize database connection."""
        self.engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def create_user(
        self,
        email: str,
        username: str,
        password: str
    ) -> Optional[User]:
        """Create a new user."""
        db = self.get_session()
        try:
            # Check if user exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                return None
            
            # Hash password
            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create user
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user."""
        db = self.get_session()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user or not user.is_active:
                return None
            
            if bcrypt.checkpw(
                password.encode('utf-8'),
                user.hashed_password.encode('utf-8')
            ):
                return user
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
        finally:
            db.close()
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        db = self.get_session()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    def check_usage_limit(self, user_id: Optional[int]) -> bool:
        """Check if user has reached daily usage limit."""
        db = self.get_session()
        try:
            # For anonymous users (user_id is None), use free tier limit
            if user_id is None:
                daily_limit = settings.free_tier_daily_limit
                today = date.today()
                usage = db.query(DailyUsage).filter(
                    DailyUsage.user_id.is_(None),
                    DailyUsage.date == today
                ).first()
            else:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False  # User doesn't exist
                
                is_premium = user.is_premium if user else False
                daily_limit = (
                    settings.paid_tier_daily_limit if is_premium
                    else settings.free_tier_daily_limit
                )
                
                today = date.today()
                usage = db.query(DailyUsage).filter(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date == today
                ).first()
            
            if not usage:
                return True  # No usage today, within limit
            
            # Check if usage is less than limit (not <=)
            return usage.usage_count < daily_limit
        except SQLAlchemyError as e:
            logger.error(f"Error checking usage limit: {str(e)}")
            return False  # Fail closed - deny if we can't verify
        finally:
            db.close()
    
    def increment_usage(self, user_id: Optional[int]):
        """Increment daily usage count."""
        db = self.get_session()
        try:
            today = date.today()
            if user_id is None:
                usage = db.query(DailyUsage).filter(
                    DailyUsage.user_id.is_(None),
                    DailyUsage.date == today
                ).first()
            else:
                usage = db.query(DailyUsage).filter(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date == today
                ).first()
            
            if not usage:
                usage = DailyUsage(user_id=user_id, date=today, usage_count=0)
                db.add(usage)
            
            usage.usage_count += 1
            db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error incrementing usage: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def save_session(
        self,
        user_id: Optional[int],
        original_prompt: str,
        prompt_type: str,
        optimized_prompt: Optional[str] = None,
        sample_output: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> Optional[OptimizationSession]:
        """Save an optimization session."""
        db = self.get_session()
        try:
            session = OptimizationSession(
                user_id=user_id,
                original_prompt=original_prompt,
                prompt_type=prompt_type,
                optimized_prompt=optimized_prompt,
                sample_output=sample_output,
                quality_score=quality_score
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error saving session: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_user_sessions(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[OptimizationSession]:
        """Get recent optimization sessions for a user."""
        db = self.get_session()
        try:
            return db.query(OptimizationSession).filter(
                OptimizationSession.user_id == user_id
            ).order_by(
                OptimizationSession.created_at.desc()
            ).limit(limit).all()
        finally:
            db.close()


# Global database instance
db = Database()
