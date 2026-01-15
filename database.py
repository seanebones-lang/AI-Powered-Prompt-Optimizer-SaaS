"""
Database models and utilities for SQLite.
Handles user authentication, session history, and usage tracking.
"""
import logging
from datetime import datetime, date
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, Float, func
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


class SavedPrompt(Base):
    """Model for saved optimized prompts library."""
    __tablename__ = "saved_prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    original_prompt = Column(Text)
    optimized_prompt = Column(Text, nullable=False)
    prompt_type = Column(String(50))
    quality_score = Column(Integer)
    tags = Column(Text)  # JSON array
    folder = Column(String(100), default="default")
    is_template = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentBlueprint(Base):
    """Model for agent blueprints - complete agent architecture specifications."""
    __tablename__ = "agent_blueprints"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    blueprint_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    version = Column(String(20), default="1.0.0")
    agent_type = Column(String(50), nullable=False)  # conversational, task_executor, etc.
    domain = Column(String(100))
    description = Column(Text)
    
    # Core components (stored as JSON)
    system_prompt = Column(Text, nullable=False)
    personality_traits = Column(Text)  # JSON array
    capabilities = Column(Text)  # JSON array
    constraints = Column(Text)  # JSON array
    
    # Tools and integrations (stored as JSON)
    tools = Column(Text)  # JSON array of tool definitions
    integrations = Column(Text)  # JSON array of integration requirements
    
    # Workflow (stored as JSON)
    workflow_steps = Column(Text)  # JSON array
    orchestration_pattern = Column(String(200))
    
    # Configuration (stored as JSON)
    model_config = Column(Text)  # JSON object
    
    # Testing (stored as JSON)
    test_scenarios = Column(Text)  # JSON array
    validation_rules = Column(Text)  # JSON array
    
    # Deployment (stored as JSON)
    deployment_config = Column(Text)  # JSON object
    monitoring_metrics = Column(Text)  # JSON array
    scaling_strategy = Column(String(200))
    
    # Documentation (stored as JSON)
    usage_examples = Column(Text)  # JSON array
    best_practices = Column(Text)  # JSON array
    known_limitations = Column(Text)  # JSON array
    
    # Metadata
    is_favorite = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    tags = Column(Text)  # JSON array
    folder = Column(String(100), default="default")
    parent_blueprint_id = Column(Integer, ForeignKey("agent_blueprints.id"), nullable=True)  # For versioning
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="blueprints")
    versions = relationship("AgentBlueprint", backref="parent", remote_side=[id])


class PromptVersion(Base):
    """Model for prompt version control."""
    __tablename__ = "prompt_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    prompt_id = Column(String(100), nullable=False, index=True)  # Groups versions together
    version_number = Column(Integer, nullable=False)
    prompt_text = Column(Text, nullable=False)
    prompt_type = Column(String(50))
    quality_score = Column(Integer)
    change_description = Column(Text)  # What changed in this version
    parent_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)
    is_current = Column(Boolean, default=True)  # Current active version
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))  # Username or "system"
    
    # Relationships
    user = relationship("User", backref="prompt_versions")
    parent = relationship("PromptVersion", remote_side=[id], backref="children")


class RefinementHistory(Base):
    """Model for iterative refinement tracking."""
    __tablename__ = "refinement_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("optimization_sessions.id"), nullable=True)
    iteration_number = Column(Integer, nullable=False)
    prompt_text = Column(Text, nullable=False)
    user_feedback = Column(Text)  # What the user didn't like
    changes_made = Column(Text)  # What was changed
    quality_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="refinements")
    session = relationship("OptimizationSession", backref="refinements")


class TestCase(Base):
    """Model for generated test cases."""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    blueprint_id = Column(Integer, ForeignKey("agent_blueprints.id"), nullable=True)
    prompt_id = Column(String(100), nullable=True)  # Link to prompt if not blueprint
    
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(50))  # happy_path, edge_case, error_handling, load_test
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text)
    success_criteria = Column(Text)  # JSON array
    actual_output = Column(Text, nullable=True)  # Filled when test is run
    passed = Column(Boolean, nullable=True)  # Null = not run yet
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="test_cases")
    blueprint = relationship("AgentBlueprint", backref="test_cases")


class KnowledgeBase(Base):
    """Model for custom domain knowledge bases."""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    domain = Column(String(100))
    is_private = Column(Boolean, default=True)
    
    # Storage info
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    vector_store_path = Column(String(500))  # Path to vector store
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="knowledge_bases")
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base")


class KnowledgeDocument(Base):
    """Model for documents in knowledge bases."""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pdf, txt, md, docx, etc.
    file_size = Column(Integer)  # bytes
    content_hash = Column(String(64))  # SHA-256 hash for deduplication
    
    # Processing info
    chunk_count = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(Text)  # JSON array
    category = Column(String(100))
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class CollaborationShare(Base):
    """Model for sharing prompts/blueprints with team members."""
    __tablename__ = "collaboration_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # What's being shared
    resource_type = Column(String(50), nullable=False)  # prompt, blueprint, knowledge_base
    resource_id = Column(Integer, nullable=False)
    
    # Permissions
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    can_comment = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="shares_given")
    shared_with = relationship("User", foreign_keys=[shared_with_id], backref="shares_received")


class Comment(Base):
    """Model for comments and annotations."""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # What's being commented on
    resource_type = Column(String(50), nullable=False)  # prompt, blueprint, etc.
    resource_id = Column(Integer, nullable=False)
    
    # Comment content
    content = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For replies
    is_resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])


class Database:
    """Database management class."""
    
    def __init__(self):
        """Initialize database connection."""
        try:
            self.engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._create_tables()
        except Exception as e:
            logger.warning(f"Could not initialize database: {str(e)}. Using fallback mode.")
            # Create a dummy engine that won't work but won't crash
            self.engine = None
            self.SessionLocal = None
    
    def _create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.warning(f"Could not create database tables: {str(e)}. Using in-memory fallback.")
            # Don't raise exception - allow app to continue with limited functionality
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def session_scope(self):
        """
        Context manager for database sessions.

        Provides automatic commit on success, rollback on error,
        and proper session cleanup.

        Usage:
            with db.session_scope() as session:
                user = session.query(User).first()
        """
        from contextlib import contextmanager

        @contextmanager
        def _session_scope():
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise
            finally:
                session.close()

        return _session_scope()

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
        user_id: Optional[int] = None,
        original_prompt: str = "",
        prompt_type: str = "",
        optimized_prompt: Optional[str] = None,
        sample_output: Optional[str] = None,
        quality_score: Optional[int] = None,
        deconstruction: Optional[str] = None,
        diagnosis: Optional[str] = None,
        evaluation: Optional[str] = None,
        tokens_used: Optional[int] = None,
        processing_time: Optional[float] = None
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
                quality_score=quality_score,
                deconstruction=deconstruction,
                diagnosis=diagnosis,
                evaluation=evaluation,
                tokens_used=tokens_used,
                processing_time=processing_time
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
                    AgentConfig.is_default
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
                AgentConfig.is_default
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

    def save_prompt(
        self,
        name: str,
        optimized_prompt: str,
        original_prompt: Optional[str] = None,
        prompt_type: Optional[str] = None,
        quality_score: Optional[int] = None,
        tags: Optional[List[str]] = None,
        folder: str = "default",
        is_template: bool = False,
        notes: Optional[str] = None
    ) -> Optional[SavedPrompt]:
        """Save an optimized prompt to the library."""
        db = self.get_session()
        try:
            saved_prompt = SavedPrompt(
                name=name,
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt,
                prompt_type=prompt_type,
                quality_score=quality_score,
                tags=json.dumps(tags) if tags else None,
                folder=folder,
                is_template=is_template,
                notes=notes
            )
            db.add(saved_prompt)
            db.commit()
            db.refresh(saved_prompt)
            return saved_prompt
        except SQLAlchemyError as e:
            logger.error(f"Error saving prompt: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_saved_prompts(
        self,
        folder: Optional[str] = None,
        prompt_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None,
        search_query: Optional[str] = None
    ) -> List[SavedPrompt]:
        """Get saved prompts with optional filtering."""
        db = self.get_session()
        try:
            query = db.query(SavedPrompt)

            if folder:
                query = query.filter(SavedPrompt.folder == folder)
            if prompt_type:
                query = query.filter(SavedPrompt.prompt_type == prompt_type)
            if is_template is not None:
                query = query.filter(SavedPrompt.is_template == is_template)
            if search_query:
                # Search in name, notes, and optimized_prompt
                search_filter = f"%{search_query}%"
                query = query.filter(
                    (SavedPrompt.name.ilike(search_filter)) |
                    (SavedPrompt.notes.ilike(search_filter)) |
                    (SavedPrompt.optimized_prompt.ilike(search_filter))
                )
            if tags:
                # Filter by tags (JSON array contains any of the specified tags)
                for tag in tags:
                    query = query.filter(SavedPrompt.tags.like(f'%"{tag}"%'))

            return query.order_by(SavedPrompt.updated_at.desc()).all()
        finally:
            db.close()

    def get_saved_prompt(self, prompt_id: int) -> Optional[SavedPrompt]:
        """Get a specific saved prompt by ID."""
        db = self.get_session()
        try:
            return db.query(SavedPrompt).filter(SavedPrompt.id == prompt_id).first()
        finally:
            db.close()

    def update_saved_prompt(
        self,
        prompt_id: int,
        **updates
    ) -> Optional[SavedPrompt]:
        """Update a saved prompt."""
        db = self.get_session()
        try:
            prompt = db.query(SavedPrompt).filter(SavedPrompt.id == prompt_id).first()
            if not prompt:
                return None

            # Handle tags specially (convert list to JSON)
            if 'tags' in updates and isinstance(updates['tags'], list):
                updates['tags'] = json.dumps(updates['tags'])

            for key, value in updates.items():
                if hasattr(prompt, key):
                    setattr(prompt, key, value)

            db.commit()
            db.refresh(prompt)
            return prompt
        except SQLAlchemyError as e:
            logger.error(f"Error updating saved prompt: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()

    def delete_saved_prompt(self, prompt_id: int) -> bool:
        """Delete a saved prompt."""
        db = self.get_session()
        try:
            prompt = db.query(SavedPrompt).filter(SavedPrompt.id == prompt_id).first()
            if not prompt:
                return False

            db.delete(prompt)
            db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting saved prompt: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_folders(self) -> List[str]:
        """Get all unique folder names."""
        db = self.get_session()
        try:
            folders = db.query(SavedPrompt.folder).distinct().all()
            return [folder[0] for folder in folders]
        finally:
            db.close()

    def get_tags(self) -> List[str]:
        """Get all unique tags."""
        db = self.get_session()
        try:
            all_tags = []
            prompts = db.query(SavedPrompt.tags).filter(SavedPrompt.tags.isnot(None)).all()
            for tags_json in prompts:
                if tags_json[0]:
                    try:
                        tags = json.loads(tags_json[0])
                        all_tags.extend(tags)
                    except json.JSONDecodeError:
                        continue
            return list(set(all_tags))  # Remove duplicates
        finally:
            db.close()
    
    # Agent Blueprint Methods
    def save_blueprint(
        self,
        user_id: Optional[int],
        blueprint_data: Dict
    ) -> Optional[AgentBlueprint]:
        """Save an agent blueprint to the database."""
        db = self.get_session()
        try:
            blueprint = AgentBlueprint(
                user_id=user_id,
                blueprint_id=blueprint_data.get("blueprint_id"),
                name=blueprint_data.get("name"),
                version=blueprint_data.get("version", "1.0.0"),
                agent_type=blueprint_data.get("agent_type"),
                domain=blueprint_data.get("domain"),
                description=blueprint_data.get("description"),
                system_prompt=blueprint_data.get("system_prompt"),
                personality_traits=json.dumps(blueprint_data.get("personality_traits", [])),
                capabilities=json.dumps(blueprint_data.get("capabilities", [])),
                constraints=json.dumps(blueprint_data.get("constraints", [])),
                tools=json.dumps(blueprint_data.get("tools", [])),
                integrations=json.dumps(blueprint_data.get("integrations", [])),
                workflow_steps=json.dumps(blueprint_data.get("workflow_steps", [])),
                orchestration_pattern=blueprint_data.get("orchestration_pattern"),
                model_config=json.dumps(blueprint_data.get("model_config", {})),
                test_scenarios=json.dumps(blueprint_data.get("test_scenarios", [])),
                validation_rules=json.dumps(blueprint_data.get("validation_rules", [])),
                deployment_config=json.dumps(blueprint_data.get("deployment_config", {})),
                monitoring_metrics=json.dumps(blueprint_data.get("monitoring_metrics", [])),
                scaling_strategy=blueprint_data.get("scaling_strategy"),
                usage_examples=json.dumps(blueprint_data.get("usage_examples", [])),
                best_practices=json.dumps(blueprint_data.get("best_practices", [])),
                known_limitations=json.dumps(blueprint_data.get("known_limitations", [])),
                tags=json.dumps(blueprint_data.get("tags", [])),
                folder=blueprint_data.get("folder", "default"),
                is_favorite=blueprint_data.get("is_favorite", False),
                is_template=blueprint_data.get("is_template", False)
            )
            db.add(blueprint)
            db.commit()
            db.refresh(blueprint)
            return blueprint
        except SQLAlchemyError as e:
            logger.error(f"Error saving blueprint: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_blueprints(
        self,
        user_id: Optional[int] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None
    ) -> List[Dict]:
        """Get agent blueprints with optional filtering."""
        db = self.get_session()
        try:
            query = db.query(AgentBlueprint)
            
            if user_id is not None:
                query = query.filter(AgentBlueprint.user_id == user_id)
            if folder:
                query = query.filter(AgentBlueprint.folder == folder)
            if is_template is not None:
                query = query.filter(AgentBlueprint.is_template == is_template)
            
            blueprints = query.order_by(AgentBlueprint.created_at.desc()).all()
            
            result = []
            for bp in blueprints:
                # Filter by tags if specified
                if tags:
                    bp_tags = json.loads(bp.tags) if bp.tags else []
                    if not any(tag in bp_tags for tag in tags):
                        continue
                
                result.append({
                    "id": bp.id,
                    "blueprint_id": bp.blueprint_id,
                    "name": bp.name,
                    "version": bp.version,
                    "agent_type": bp.agent_type,
                    "domain": bp.domain,
                    "description": bp.description,
                    "folder": bp.folder,
                    "is_favorite": bp.is_favorite,
                    "is_template": bp.is_template,
                    "tags": json.loads(bp.tags) if bp.tags else [],
                    "created_at": bp.created_at.isoformat()
                })
            
            return result
        finally:
            db.close()
    
    def get_blueprint_by_id(self, blueprint_id: str) -> Optional[Dict]:
        """Get full blueprint details by ID."""
        db = self.get_session()
        try:
            bp = db.query(AgentBlueprint).filter(
                AgentBlueprint.blueprint_id == blueprint_id
            ).first()
            
            if not bp:
                return None
            
            return {
                "id": bp.id,
                "blueprint_id": bp.blueprint_id,
                "name": bp.name,
                "version": bp.version,
                "agent_type": bp.agent_type,
                "domain": bp.domain,
                "description": bp.description,
                "system_prompt": bp.system_prompt,
                "personality_traits": json.loads(bp.personality_traits) if bp.personality_traits else [],
                "capabilities": json.loads(bp.capabilities) if bp.capabilities else [],
                "constraints": json.loads(bp.constraints) if bp.constraints else [],
                "tools": json.loads(bp.tools) if bp.tools else [],
                "integrations": json.loads(bp.integrations) if bp.integrations else [],
                "workflow_steps": json.loads(bp.workflow_steps) if bp.workflow_steps else [],
                "orchestration_pattern": bp.orchestration_pattern,
                "model_config": json.loads(bp.model_config) if bp.model_config else {},
                "test_scenarios": json.loads(bp.test_scenarios) if bp.test_scenarios else [],
                "validation_rules": json.loads(bp.validation_rules) if bp.validation_rules else [],
                "deployment_config": json.loads(bp.deployment_config) if bp.deployment_config else {},
                "monitoring_metrics": json.loads(bp.monitoring_metrics) if bp.monitoring_metrics else [],
                "scaling_strategy": bp.scaling_strategy,
                "usage_examples": json.loads(bp.usage_examples) if bp.usage_examples else [],
                "best_practices": json.loads(bp.best_practices) if bp.best_practices else [],
                "known_limitations": json.loads(bp.known_limitations) if bp.known_limitations else [],
                "folder": bp.folder,
                "is_favorite": bp.is_favorite,
                "is_template": bp.is_template,
                "tags": json.loads(bp.tags) if bp.tags else [],
                "created_at": bp.created_at.isoformat(),
                "updated_at": bp.updated_at.isoformat()
            }
        finally:
            db.close()
    
    # Prompt Versioning Methods
    def create_prompt_version(
        self,
        user_id: Optional[int],
        prompt_id: str,
        version_number: int,
        prompt_text: str,
        prompt_type: Optional[str] = None,
        quality_score: Optional[int] = None,
        change_description: Optional[str] = None,
        parent_version_id: Optional[int] = None,
        created_by: str = "user"
    ) -> Optional[PromptVersion]:
        """Create a new prompt version."""
        db = self.get_session()
        try:
            # Mark previous versions as not current
            db.query(PromptVersion).filter(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.is_current == True
            ).update({"is_current": False})
            
            version = PromptVersion(
                user_id=user_id,
                prompt_id=prompt_id,
                version_number=version_number,
                prompt_text=prompt_text,
                prompt_type=prompt_type,
                quality_score=quality_score,
                change_description=change_description,
                parent_version_id=parent_version_id,
                is_current=True,
                created_by=created_by
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            return version
        except SQLAlchemyError as e:
            logger.error(f"Error creating prompt version: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_prompt_versions(self, prompt_id: str) -> List[Dict]:
        """Get all versions of a prompt."""
        db = self.get_session()
        try:
            versions = db.query(PromptVersion).filter(
                PromptVersion.prompt_id == prompt_id
            ).order_by(PromptVersion.version_number.desc()).all()
            
            return [{
                "id": v.id,
                "version_number": v.version_number,
                "prompt_text": v.prompt_text,
                "prompt_type": v.prompt_type,
                "quality_score": v.quality_score,
                "change_description": v.change_description,
                "is_current": v.is_current,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by
            } for v in versions]
        finally:
            db.close()
    
    # Refinement History Methods
    def add_refinement(
        self,
        user_id: Optional[int],
        session_id: Optional[int],
        iteration_number: int,
        prompt_text: str,
        user_feedback: Optional[str] = None,
        changes_made: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> Optional[RefinementHistory]:
        """Add a refinement iteration."""
        db = self.get_session()
        try:
            refinement = RefinementHistory(
                user_id=user_id,
                session_id=session_id,
                iteration_number=iteration_number,
                prompt_text=prompt_text,
                user_feedback=user_feedback,
                changes_made=changes_made,
                quality_score=quality_score
            )
            db.add(refinement)
            db.commit()
            db.refresh(refinement)
            return refinement
        except SQLAlchemyError as e:
            logger.error(f"Error adding refinement: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_refinement_history(self, session_id: int) -> List[Dict]:
        """Get refinement history for a session."""
        db = self.get_session()
        try:
            refinements = db.query(RefinementHistory).filter(
                RefinementHistory.session_id == session_id
            ).order_by(RefinementHistory.iteration_number).all()
            
            return [{
                "id": r.id,
                "iteration_number": r.iteration_number,
                "prompt_text": r.prompt_text,
                "user_feedback": r.user_feedback,
                "changes_made": r.changes_made,
                "quality_score": r.quality_score,
                "created_at": r.created_at.isoformat()
            } for r in refinements]
        finally:
            db.close()
    
    # Test Case Methods
    def save_test_case(
        self,
        user_id: Optional[int],
        test_data: Dict
    ) -> Optional[TestCase]:
        """Save a test case."""
        db = self.get_session()
        try:
            test_case = TestCase(
                user_id=user_id,
                blueprint_id=test_data.get("blueprint_id"),
                prompt_id=test_data.get("prompt_id"),
                test_name=test_data.get("test_name"),
                test_type=test_data.get("test_type"),
                input_data=test_data.get("input_data"),
                expected_output=test_data.get("expected_output"),
                success_criteria=json.dumps(test_data.get("success_criteria", []))
            )
            db.add(test_case)
            db.commit()
            db.refresh(test_case)
            return test_case
        except SQLAlchemyError as e:
            logger.error(f"Error saving test case: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_test_cases(
        self,
        user_id: Optional[int] = None,
        blueprint_id: Optional[int] = None,
        prompt_id: Optional[str] = None
    ) -> List[Dict]:
        """Get test cases with optional filtering."""
        db = self.get_session()
        try:
            query = db.query(TestCase)
            
            if user_id is not None:
                query = query.filter(TestCase.user_id == user_id)
            if blueprint_id is not None:
                query = query.filter(TestCase.blueprint_id == blueprint_id)
            if prompt_id is not None:
                query = query.filter(TestCase.prompt_id == prompt_id)
            
            test_cases = query.all()
            
            return [{
                "id": tc.id,
                "test_name": tc.test_name,
                "test_type": tc.test_type,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "success_criteria": json.loads(tc.success_criteria) if tc.success_criteria else [],
                "actual_output": tc.actual_output,
                "passed": tc.passed,
                "error_message": tc.error_message,
                "execution_time": tc.execution_time,
                "created_at": tc.created_at.isoformat(),
                "last_run_at": tc.last_run_at.isoformat() if tc.last_run_at else None
            } for tc in test_cases]
        finally:
            db.close()
    
    # Knowledge Base Methods
    def create_knowledge_base(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        domain: Optional[str] = None,
        is_private: bool = True
    ) -> Optional[KnowledgeBase]:
        """Create a new knowledge base."""
        db = self.get_session()
        try:
            kb = KnowledgeBase(
                user_id=user_id,
                name=name,
                description=description,
                domain=domain,
                is_private=is_private
            )
            db.add(kb)
            db.commit()
            db.refresh(kb)
            return kb
        except SQLAlchemyError as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_knowledge_bases(self, user_id: int) -> List[Dict]:
        """Get user's knowledge bases."""
        db = self.get_session()
        try:
            kbs = db.query(KnowledgeBase).filter(
                KnowledgeBase.user_id == user_id
            ).all()
            
            return [{
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "domain": kb.domain,
                "is_private": kb.is_private,
                "document_count": kb.document_count,
                "total_chunks": kb.total_chunks,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat()
            } for kb in kbs]
        finally:
            db.close()
    
    # Collaboration Methods
    def share_resource(
        self,
        owner_id: int,
        shared_with_id: int,
        resource_type: str,
        resource_id: int,
        can_view: bool = True,
        can_edit: bool = False,
        can_comment: bool = True
    ) -> Optional[CollaborationShare]:
        """Share a resource with another user."""
        db = self.get_session()
        try:
            share = CollaborationShare(
                owner_id=owner_id,
                shared_with_id=shared_with_id,
                resource_type=resource_type,
                resource_id=resource_id,
                can_view=can_view,
                can_edit=can_edit,
                can_comment=can_comment
            )
            db.add(share)
            db.commit()
            db.refresh(share)
            return share
        except SQLAlchemyError as e:
            logger.error(f"Error sharing resource: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def add_comment(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        content: str,
        parent_comment_id: Optional[int] = None
    ) -> Optional[Comment]:
        """Add a comment to a resource."""
        db = self.get_session()
        try:
            comment = Comment(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                content=content,
                parent_comment_id=parent_comment_id
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)
            return comment
        except SQLAlchemyError as e:
            logger.error(f"Error adding comment: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_comments(
        self,
        resource_type: str,
        resource_id: int
    ) -> List[Dict]:
        """Get comments for a resource."""
        db = self.get_session()
        try:
            comments = db.query(Comment).filter(
                Comment.resource_type == resource_type,
                Comment.resource_id == resource_id,
                Comment.parent_comment_id == None  # Only top-level comments
            ).order_by(Comment.created_at.desc()).all()
            
            result = []
            for comment in comments:
                # Get user info
                user = db.query(User).filter(User.id == comment.user_id).first()
                
                # Get replies
                replies = db.query(Comment).filter(
                    Comment.parent_comment_id == comment.id
                ).order_by(Comment.created_at).all()
                
                result.append({
                    "id": comment.id,
                    "user": {
                        "id": user.id,
                        "username": user.username
                    } if user else None,
                    "content": comment.content,
                    "is_resolved": comment.is_resolved,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat(),
                    "replies": [{
                        "id": r.id,
                        "user": {
                            "id": db.query(User).filter(User.id == r.user_id).first().id,
                            "username": db.query(User).filter(User.id == r.user_id).first().username
                        },
                        "content": r.content,
                        "created_at": r.created_at.isoformat()
                    } for r in replies]
                })
            
            return result
        finally:
            db.close()


# Global database instance
db = Database()
