from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("ProblemNote", back_populates="user", cascade="all, delete-orphan")
    review_logs = relationship("ReviewLog", back_populates="user", cascade="all, delete-orphan")
    ai_hints = relationship("AiHint", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="owner", cascade="all, delete-orphan")

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    leetcode_id = Column(Integer, index=True, nullable=True)
    title = Column(String, nullable=False)
    title_cn = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    difficulty = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    examples = Column(Text, nullable=True)
    constraints_text = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    stage = Column(String, nullable=True, index=True)
    source = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    key_pattern = Column(Text, nullable=True)
    starter_code = Column(Text, nullable=True)
    recommended_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    progress = relationship("Progress", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")
    notes = relationship("ProblemNote", back_populates="problem", cascade="all, delete-orphan")
    review_logs = relationship("ReviewLog", back_populates="problem", cascade="all, delete-orphan")
    ai_hints = relationship("AiHint", back_populates="problem", cascade="all, delete-orphan")

class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_progress_user_problem"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    status = Column(String, default="Not Started", index=True)
    attempts = Column(Integer, default=0)
    solved_count = Column(Integer, default=0)
    first_solved_at = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)
    last_review_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    mastery_level = Column(Integer, default=0)
    confidence = Column(Integer, default=0)
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    user = relationship("User", back_populates="progress")
    problem = relationship("Problem", back_populates="progress")

class ProblemNote(Base):
    __tablename__ = "problem_notes"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_problem_notes_user_problem"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    idea = Column(Text, default="")
    key_points = Column(Text, default="")
    complexity = Column(Text, default="")
    pitfalls = Column(Text, default="")
    summary = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="notes")
    problem = relationship("Problem", back_populates="notes")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    language = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String, nullable=False, index=True)
    runtime_ms = Column(Integer, nullable=True)
    memory_mb = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    fail_reason = Column(String, nullable=True)
    is_best = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")

class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    review_type = Column(String, default="Manual")
    result = Column(String, default="")
    notes = Column(Text, default="")
    prev_mastery_level = Column(Integer, default=0)
    new_mastery_level = Column(Integer, default=0)
    review_interval_days = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="review_logs")
    problem = relationship("Problem", back_populates="review_logs")

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_system = Column(Boolean, default=False, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    language = Column(String, nullable=False, index=True)
    code = Column(Text, nullable=False)
    explanation = Column(Text, default="")
    tags = Column(Text, default="[]")
    usage_scenario = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="templates")

class AiHint(Base):
    __tablename__ = "ai_hints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True)
    hint_type = Column(String, nullable=False)
    prompt = Column(Text, default="")
    response = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="ai_hints")
    problem = relationship("Problem", back_populates="ai_hints")
