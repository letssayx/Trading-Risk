"""add_skills_and_rag_tables

Revision ID: bf05657c4fc1
Revises: b110b082b694
Create Date: 2026-06-28 21:02:54.094738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = 'bf05657c4fc1'
down_revision: Union[str, Sequence[str], None] = 'b110b082b694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # 2. Skills Registry
    op.create_table(
        'skills',
        sa.Column('skill_id', sa.Text(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workspace', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )

    op.create_table(
        'skill_steps',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_id', sa.Text(), sa.ForeignKey('skills.skill_id'), nullable=True),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('step_title', sa.Text(), nullable=True),
        sa.Column('step_content', sa.Text(), nullable=True),
        sa.Column('condition', sa.Text(), nullable=True),
    )

    # 3. Skills Knowledge + Examples (Vector DB)
    op.create_table(
        'skill_knowledge',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_id', sa.Text(), sa.ForeignKey('skills.skill_id'), nullable=True),
        sa.Column('knowledge_type', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE skill_knowledge ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    op.create_table(
        'skill_examples',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_id', sa.Text(), sa.ForeignKey('skills.skill_id'), nullable=True),
        sa.Column('market_context', JSONB, nullable=True),
        sa.Column('think_chain', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.SmallInteger(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE skill_examples ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    # 4. RAG Tables
    op.create_table(
        'veteran_annotations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('annotation_text', sa.Text(), nullable=False),
        sa.Column('market_context', JSONB, nullable=True),
        sa.Column('symbols', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('skill_id', sa.Text(), sa.ForeignKey('skills.skill_id'), nullable=True),
        sa.Column('was_correct', sa.Boolean(), nullable=True),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE veteran_annotations ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    op.create_table(
        'report_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('source_file', sa.Text(), nullable=True),
        sa.Column('report_date', sa.Date(), nullable=True),
        sa.Column('report_type', sa.Text(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE report_chunks ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    op.create_table(
        'regulatory_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('source_file', sa.Text(), nullable=True),
        sa.Column('doc_type', sa.Text(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE regulatory_chunks ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    op.create_table(
        'trade_reasoning',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('embedding', sa.Text(), nullable=True), # Temporary Text column, altered to vector(1024)
        sa.Column('skill_id', sa.Text(), sa.ForeignKey('skills.skill_id'), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('context_used', JSONB, nullable=True),
        sa.Column('think_chain', sa.Text(), nullable=True),
        sa.Column('final_answer', sa.Text(), nullable=True),
        sa.Column('user_rating', sa.SmallInteger(), nullable=True),
        sa.Column('correction', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
    )
    op.execute("ALTER TABLE trade_reasoning ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")

    # 5. Create HNSW Indexes
    op.execute("CREATE INDEX ON skill_knowledge USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX ON skill_examples USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX ON veteran_annotations USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX ON report_chunks USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX ON regulatory_chunks USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX ON trade_reasoning USING hnsw (embedding vector_cosine_ops);")

    # 6. Pre-populate skills table
    initial_skills = [
        {"skill_id": "oi_analysis", "name": "OI Analysis", "workspace": "DERIVATIVES"},
        {"skill_id": "rollover_analysis", "name": "Rollover Analysis", "workspace": "DERIVATIVES"},
        {"skill_id": "expiry_behaviour", "name": "Expiry Behaviour Analysis", "workspace": "DERIVATIVES"},
        {"skill_id": "options_analysis", "name": "Options Analysis", "workspace": "DERIVATIVES"},
        {"skill_id": "mwpl_analysis", "name": "MWPL Analysis", "workspace": "DERIVATIVES"},
        {"skill_id": "strategy_analysis", "name": "Strategy Analysis", "workspace": "DERIVATIVES"},

        {"skill_id": "pe_analysis", "name": "PE Analysis", "workspace": "FUNDAMENTAL"},
        {"skill_id": "peer_comparison", "name": "Peer Comparison Analysis", "workspace": "FUNDAMENTAL"},
        {"skill_id": "earnings_analysis", "name": "Earnings Analysis", "workspace": "FUNDAMENTAL"},

        {"skill_id": "technical_analysis", "name": "Technical Analysis", "workspace": "TECHNICAL"},
        {"skill_id": "fibonacci_analysis", "name": "Fibonacci Analysis", "workspace": "TECHNICAL"},
        {"skill_id": "historical_volatility", "name": "Historical Volatility Analysis", "workspace": "TECHNICAL"},
        {"skill_id": "beta_rsquared", "name": "Beta/R² Analysis", "workspace": "TECHNICAL"},

        {"skill_id": "risk_analysis", "name": "Risk Analysis", "workspace": "RISK"},
        {"skill_id": "black_swan", "name": "Black Swan Analysis", "workspace": "RISK"},

        {"skill_id": "macro_analysis", "name": "Macro Analysis", "workspace": "MACRO"},
        {"skill_id": "sectoral_analysis", "name": "Sectoral Analysis", "workspace": "MACRO"},
        {"skill_id": "thematic_analysis", "name": "Theme Analysis", "workspace": "MACRO"},

        {"skill_id": "commodity_analysis", "name": "Commodity Analysis", "workspace": "COMMODITY"},
        {"skill_id": "commodity_technical", "name": "Commodity Technical", "workspace": "COMMODITY"},
        {"skill_id": "commodity_fundamental", "name": "Commodity Fundamental", "workspace": "COMMODITY"},
        {"skill_id": "commodity_macro", "name": "Commodity Macro", "workspace": "COMMODITY"},

        {"skill_id": "special_situation", "name": "Special Situation Analysis", "workspace": "SPECIAL_SITUATION"},
        {"skill_id": "corporate_action", "name": "Corporate Action Research", "workspace": "SPECIAL_SITUATION"},
        {"skill_id": "corporate_research", "name": "Corporate Research & Analysis", "workspace": "SPECIAL_SITUATION"}
    ]

    for skill in initial_skills:
        op.execute(
            sa.text(
                "INSERT INTO skills (skill_id, name, workspace) VALUES (:skill_id, :name, :workspace)"
            ).bindparams(**skill)
        )

def downgrade() -> None:
    op.drop_table('trade_reasoning')
    op.drop_table('regulatory_chunks')
    op.drop_table('report_chunks')
    op.drop_table('veteran_annotations')
    op.drop_table('skill_examples')
    op.drop_table('skill_knowledge')
    op.drop_table('skill_steps')
    op.drop_table('skills')
