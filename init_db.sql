CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    position TEXT,
    created_at TIMESTAMP(0) DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS face_embeddings(
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
    employee_code TEXT NOT NULL,
    embedding vector(512) NOT NULL,
    filename TEXT,
    created_at TIMESTAMP(0) DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'check_type_enum') THEN
        CREATE TYPE check_type_enum AS ENUM ('checkin', 'checkout');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS attendance_logs(
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE SET NULL,
    employee_code TEXT NOT NULL,
    check_time TIMESTAMP(0) DEFAULT NOW(),
    check_type check_type_enum NOT NULL,
    image_path TEXT,
    work_status TEXT,                    
    created_at TIMESTAMP(0) DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_employee_code_time 
ON attendance_logs(employee_code, check_time);


CREATE OR REPLACE FUNCTION update_employee_code_in_logs()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE attendance_logs
  SET employee_code = NEW.employee_code
  WHERE employee_id = NEW.id;

  UPDATE face_embeddings
  SET employee_code = NEW.employee_code
  WHERE employee_id = NEW.id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_employee_code
AFTER UPDATE OF employee_code ON employees
FOR EACH ROW
EXECUTE FUNCTION update_employee_code_in_logs();
