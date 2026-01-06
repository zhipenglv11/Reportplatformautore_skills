-- backend/database/init_sqlite.sql
CREATE TABLE IF NOT EXISTS professional_data (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    run_id TEXT,
    test_item TEXT NOT NULL,
    test_result REAL, -- nullable
    test_unit TEXT, -- nullable
    record_code TEXT,
    test_location_text TEXT,
    design_strength_grade TEXT,
    strength_estimated_mpa REAL,
    carbonation_depth_avg_mm REAL,
    test_date TEXT,
    casting_date TEXT,
    test_value_json TEXT,
    component_type TEXT,
    location TEXT,
    evidence_refs TEXT NOT NULL,
    raw_result TEXT NOT NULL,
    confirmed_result TEXT,
    result_version INTEGER NOT NULL DEFAULT 1,
    source_prompt_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    raw_hash TEXT,
    input_fingerprint TEXT,
    confirmed_by TEXT,
    confirmed_at TIMESTAMP,
    source_hash TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_id ON professional_data(project_id);
CREATE INDEX IF NOT EXISTS idx_professional_data_project_node_time ON professional_data(project_id, node_id, created_at);
CREATE INDEX IF NOT EXISTS idx_professional_data_project_time ON professional_data(project_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_professional_data_dedup
ON professional_data(input_fingerprint);

CREATE TABLE IF NOT EXISTS run_log (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    node_id TEXT,
    record_id TEXT,
    status TEXT NOT NULL,
    stage TEXT,
    prompt_version TEXT,
    schema_version TEXT,
    input_file_hashes TEXT,
    skill_steps TEXT,
    llm_usage TEXT,
    total_cost REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_project_id_log ON run_log(project_id);
CREATE INDEX IF NOT EXISTS idx_run_log_project_node_time ON run_log(project_id, node_id, created_at);
CREATE INDEX IF NOT EXISTS idx_status ON run_log(status);
