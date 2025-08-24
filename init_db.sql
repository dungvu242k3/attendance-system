CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    position TEXT,
    created_at TIMESTAMP(0) DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS face_embeddings_512 (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
    embedding vector(512) NOT NULL,
    filename TEXT,
    created_at TIMESTAMP(0) DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attendance_logs_512 (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE SET NULL,
    check_time TIMESTAMP(0) DEFAULT NOW(),
    status TEXT,
    image_path TEXT,
    check_type TEXT
);
