from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, SmallInteger, Date, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from backend.infrastructure.db import Base

class Skill(Base):
    __tablename__ = "skills"

    skill_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    workspace = Column(Text)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SkillStep(Base):
    __tablename__ = "skill_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Text, ForeignKey('skills.skill_id'))
    step_number = Column(Integer)
    step_title = Column(Text)
    step_content = Column(Text)
    condition = Column(Text)

class SkillKnowledge(Base):
    __tablename__ = "skill_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Text, ForeignKey('skills.skill_id'))
    knowledge_type = Column(Text)
    title = Column(Text)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=1)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SkillExample(Base):
    __tablename__ = "skill_examples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Text, ForeignKey('skills.skill_id'))
    market_context = Column(JSONB)
    think_chain = Column(Text)
    answer = Column(Text)
    quality_score = Column(SmallInteger)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VeteranAnnotation(Base):
    __tablename__ = "veteran_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding = Column(Vector(1024))
    annotation_text = Column(Text, nullable=False)
    market_context = Column(JSONB)
    symbols = Column(ARRAY(Text))
    skill_id = Column(Text, ForeignKey('skills.skill_id'))
    was_correct = Column(Boolean)
    outcome_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ReportChunk(Base):
    __tablename__ = "report_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding = Column(Vector(1024))
    chunk_text = Column(Text, nullable=False)
    source_file = Column(Text)
    report_date = Column(Date)
    report_type = Column(Text)
    page_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RegulatoryChunk(Base):
    __tablename__ = "regulatory_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding = Column(Vector(1024))
    chunk_text = Column(Text, nullable=False)
    source_file = Column(Text)
    doc_type = Column(Text)
    effective_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TradeReasoning(Base):
    __tablename__ = "trade_reasoning"

    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding = Column(Vector(1024))
    skill_id = Column(Text, ForeignKey('skills.skill_id'))
    query = Column(Text)
    context_used = Column(JSONB)
    think_chain = Column(Text)
    final_answer = Column(Text)
    user_rating = Column(SmallInteger)
    correction = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
