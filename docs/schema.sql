-- Users & Licensing
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_config (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- Audit Trail
CREATE TABLE gemini_audit (
    audit_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    prompt TEXT NOT NULL,
    generated_python TEXT,
    result_summary TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE data_ingestion_log (
    upload_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    file_name VARCHAR(255),
    record_count INTEGER,
    status VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Persistence
CREATE TABLE trade_ideas (
    idea_id VARCHAR(50) PRIMARY KEY, -- UUID
    user_id INTEGER REFERENCES users(user_id),
    instrument_symbol VARCHAR(50),
    direction VARCHAR(10),
    rationale_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dashboard_templates (
    template_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analysis_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    trade_idea_id VARCHAR(50) REFERENCES trade_ideas(idea_id),
    report_metadata JSONB,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
