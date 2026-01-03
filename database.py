"""
Database models and utilities for SQLite.
Handles user authentication, session history, and usage tracking.
"""
import logging
from datetime import datetime, date
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, Float, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from config import settings
import bcrypt
import json

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
    api_key = Column(String(255), unique=True, nullable=True, index=True)  # For API access
    
    # Relationships
    sessions = relationship("OptimizationSession", back_populates="user")
    agent_configs = relationship("AgentConfig", back_populates="user")
    batch_jobs = relationship("BatchJob", back_populates="user")
    ab_tests = relationship("ABTest", back_populates="user")


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
    deconstruction = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    evaluation = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    agent_config_id = Column(Integer, ForeignKey("agent_configs.id"), nullable=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    agent_config = relationship("AgentConfig", back_populates="sessions")
    ab_test = relationship("ABTest", back_populates="sessions")


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


class AgentConfig(Base):
    """Model for custom agent configurations (premium feature)."""
    __tablename__ = "agent_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config_json = Column(Text, nullable=False)  # JSON string with agent settings
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="agent_configs")
    sessions = relationship("OptimizationSession", back_populates="agent_config")


class BatchJob(Base):
    """Model for batch optimization jobs."""
    __tablename__ = "batch_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(200), nullable=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    total_prompts = Column(Integer, default=0)
    completed_prompts = Column(Integer, default=0)
    failed_prompts = Column(Integer, default=0)
    prompts_json = Column(Text, nullable=False)  # JSON array of prompts
    results_json = Column(Text, nullable=True)  # JSON array of results
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="batch_jobs")


class ABTest(Base):
    """Model for A/B testing prompt variants."""
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(200), nullable=False)
    original_prompt = Column(Text, nullable=False)
    variant_a = Column(Text, nullable=True)
    variant_b = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, completed, paused
    variant_a_score = Column(Float, nullable=True)
    variant_b_score = Column(Float, nullable=True)
    variant_a_responses = Column(Integer, default=0)
    variant_b_responses = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="ab_tests")
    sessions = relationship("OptimizationSession", back_populates="ab_test")


class AnalyticsEvent(Base):
    """Model for analytics events tracking."""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)  # optimization, export, api_call, etc.
    event_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


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
        # Beta mode: No usage limits
        return True
    
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
    
    def generate_api_key(self, user_id: int) -> Optional[str]:
        """Generate a unique API key for a user."""
        import secrets
        db = self.get_session()
        try:
            api_key = f"pk_{secrets.token_urlsafe(32)}"
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.api_key = api_key
                db.commit()
                return api_key
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error generating API key: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        db = self.get_session()
        try:
            return db.query(User).filter(User.api_key == api_key).first()
        finally:
            db.close()
    
    def create_agent_config(
        self,
        user_id: int,
        name: str,
        config_json: str,
        description: Optional[str] = None,
        is_default: bool = False
    ) -> Optional[AgentConfig]:
        """Create a custom agent configuration."""
        db = self.get_session()
        try:
            # If setting as default, unset other defaults
            if is_default:
                db.query(AgentConfig).filter(
                    AgentConfig.user_id == user_id,
                    AgentConfig.is_default == True
                ).update({"is_default": False})
            
            config = AgentConfig(
                user_id=user_id,
                name=name,
                description=description,
                config_json=config_json,
                is_default=is_default
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
        except SQLAlchemyError as e:
            logger.error(f"Error creating agent config: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_agent_configs(self, user_id: int) -> List[AgentConfig]:
        """Get all agent configurations for a user."""
        db = self.get_session()
        try:
            return db.query(AgentConfig).filter(
                AgentConfig.user_id == user_id
            ).order_by(AgentConfig.is_default.desc(), AgentConfig.created_at.desc()).all()
        finally:
            db.close()
    
    def get_default_agent_config(self, user_id: int) -> Optional[AgentConfig]:
        """Get default agent configuration for a user."""
        db = self.get_session()
        try:
            return db.query(AgentConfig).filter(
                AgentConfig.user_id == user_id,
                AgentConfig.is_default == True
            ).first()
        finally:
            db.close()
    
    def create_batch_job(
        self,
        user_id: Optional[int],
        prompts_json: str,
        name: Optional[str] = None
    ) -> Optional[BatchJob]:
        """Create a batch optimization job."""
        db = self.get_session()
        try:
            prompts = json.loads(prompts_json)
            job = BatchJob(
                user_id=user_id,
                name=name or f"Batch Job {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                prompts_json=prompts_json,
                total_prompts=len(prompts),
                status="pending"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        except (SQLAlchemyError, json.JSONDecodeError) as e:
            logger.error(f"Error creating batch job: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def update_batch_job(
        self,
        job_id: int,
        status: Optional[str] = None,
        completed_prompts: Optional[int] = None,
        failed_prompts: Optional[int] = None,
        results_json: Optional[str] = None
    ) -> Optional[BatchJob]:
        """Update a batch job."""
        db = self.get_session()
        try:
            job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
            if not job:
                return None
            
            if status:
                job.status = status
            if completed_prompts is not None:
                job.completed_prompts = completed_prompts
            if failed_prompts is not None:
                job.failed_prompts = failed_prompts
            if results_json:
                job.results_json = results_json
            if status == "completed":
                job.completed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(job)
            return job
        except SQLAlchemyError as e:
            logger.error(f"Error updating batch job: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def create_ab_test(
        self,
        user_id: Optional[int],
        name: str,
        original_prompt: str,
        variant_a: Optional[str] = None,
        variant_b: Optional[str] = None
    ) -> Optional[ABTest]:
        """Create an A/B test."""
        db = self.get_session()
        try:
            ab_test = ABTest(
                user_id=user_id,
                name=name,
                original_prompt=original_prompt,
                variant_a=variant_a,
                variant_b=variant_b,
                status="active"
            )
            db.add(ab_test)
            db.commit()
            db.refresh(ab_test)
            return ab_test
        except SQLAlchemyError as e:
            logger.error(f"Error creating A/B test: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def update_ab_test_results(
        self,
        ab_test_id: int,
        variant: str,  # 'a' or 'b'
        score: float
    ) -> Optional[ABTest]:
        """Update A/B test results."""
        db = self.get_session()
        try:
            ab_test = db.query(ABTest).filter(ABTest.id == ab_test_id).first()
            if not ab_test:
                return None
            
            if variant == 'a':
                ab_test.variant_a_score = score
                ab_test.variant_a_responses += 1
            elif variant == 'b':
                ab_test.variant_b_score = score
                ab_test.variant_b_responses += 1
            
            db.commit()
            db.refresh(ab_test)
            return ab_test
        except SQLAlchemyError as e:
            logger.error(f"Error updating A/B test: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def log_analytics_event(
        self,
        user_id: Optional[int],
        event_type: str,
        event_data: Optional[Dict] = None
    ):
        """Log an analytics event."""
        db = self.get_session()
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=json.dumps(event_data) if event_data else None
            )
            db.add(event)
            db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error logging analytics event: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def get_analytics_data(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get analytics data for dashboard."""
        db = self.get_session()
        try:
            query = db.query(AnalyticsEvent)
            if user_id:
                query = query.filter(AnalyticsEvent.user_id == user_id)
            if start_date:
                query = query.filter(AnalyticsEvent.created_at >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                query = query.filter(AnalyticsEvent.created_at <= datetime.combine(end_date, datetime.max.time()))
            
            events = query.all()
            
            # Aggregate data
            total_optimizations = db.query(OptimizationSession).filter(
                OptimizationSession.user_id == user_id if user_id else True
            ).count()
            
            avg_quality_score = db.query(
                func.avg(OptimizationSession.quality_score)
            ).filter(
                OptimizationSession.user_id == user_id if user_id else True,
                OptimizationSession.quality_score.isnot(None)
            ).scalar() or 0
            
            return {
                "total_events": len(events),
                "total_optimizations": total_optimizations,
                "avg_quality_score": round(float(avg_quality_score), 2),
                "events_by_type": {}
            }
        finally:
            db.close()


# Global database instance
db = Database()
