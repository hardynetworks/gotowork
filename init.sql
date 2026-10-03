-- ============================================
-- Crew Scheduler Database Initialization
-- ============================================

-- Create extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- ROLES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name) VALUES 
    ('admin'),
    ('manager')
ON CONFLICT (name) DO NOTHING;

-- ==========================================
-- USERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed admin user
INSERT INTO users (email, password_hash, name, role_id)
SELECT 
    'admin@crew-scheduler.com',
    'hashed_password_here',
    'Administrator',
    r.id
FROM roles r
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- ==========================================
-- CREW MEMBERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS crew_members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    skill_level VARCHAR(50) DEFAULT 'general',
    specializations TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- SHIFT TYPES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS shift_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default shift types
INSERT INTO shift_types (name, start_time, end_time) VALUES 
    ('morning', 6, 14),
    ('evening', 14, 22),
    ('night', 22, 6)
ON CONFLICT DO NOTHING;

-- ==========================================
-- SHIFTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS shifts (
    id SERIAL PRIMARY KEY,
    shift_type_id INTEGER REFERENCES shift_types(id) ON DELETE CASCADE NOT NULL,
    location VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- CREW MEMBER SHIFT RELATIONSHIP
-- ==========================================
CREATE TABLE IF NOT EXISTS crew_member_shift (
    crew_member_id INTEGER REFERENCES crew_members(id) ON DELETE CASCADE,
    shift_id INTEGER REFERENCES shifts(id) ON DELETE CASCADE,
    PRIMARY KEY (crew_member_id, shift_id)
);

-- ==========================================
-- SCHEDULES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    location_id INTEGER REFERENCES shifts(id),
    status VARCHAR(20) DEFAULT 'draft',
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- SCHEDULE ASSIGNMENTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS schedule_assignments (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE CASCADE NOT NULL,
    crew_member_id INTEGER REFERENCES crew_members(id) ON DELETE CASCADE NOT NULL,
    shift_id INTEGER REFERENCES shifts(id) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schedule_id, crew_member_id, shift_id)
);

-- ==========================================
-- CONSTRAINTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS constraints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    value NUMERIC,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed default constraints (removed ON CONFLICT - will cause errors in older PG versions)
INSERT INTO constraints (name, description, value, enabled, priority) VALUES 
    ('max_weekly_hours', 'Maximum weekly hours per crew member', 40.0, TRUE, 1),
    ('min_break_minutes', 'Minimum break duration in minutes', 30.0, TRUE, 2),
    ('max_consecutive_days', 'Maximum consecutive work days', 5.0, TRUE, 1);

-- ==========================================
-- SCHEDULING LOGS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS scheduling_logs (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id),
    action VARCHAR(50) NOT NULL,
    details TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_schedules_period ON schedules(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_crew_members_active ON crew_members(is_active);
CREATE INDEX IF NOT EXISTS idx_shifts_date ON shifts(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_assignments_schedule ON schedule_assignments(schedule_id);

-- ==========================================
-- VIEWS FOR REPORTING
-- ==========================================
CREATE OR REPLACE VIEW view_crew_workload AS
SELECT 
    cm.id,
    cm.name,
    cm.email,
    COUNT(sa.schedule_id) as total_shifts,
    SUM(st.start_time + st.end_time - 2 * 60) as estimated_hours
FROM crew_members cm
LEFT JOIN schedule_assignments sa ON cm.id = sa.crew_member_id
LEFT JOIN shifts s ON sa.shift_id = s.id
LEFT JOIN shift_types st ON s.shift_type_id = st.id
WHERE cm.is_active = TRUE
GROUP BY cm.id;

CREATE OR REPLACE VIEW view_shift_coverage AS
SELECT 
    sh.name as location,
    COUNT(DISTINCT sc.crew_member_id) as crew_count,
    st.name as shift_type
FROM shifts sh
LEFT JOIN schedule_assignments sa ON sh.id = sa.shift_id
LEFT JOIN crew_members cm ON sa.crew_member_id = cm.id
LEFT JOIN schedule_assignments sc ON sh.id = sc.shift_id
LEFT JOIN shift_types st ON sh.shift_type_id = st.id
GROUP BY sh.id, st.name;

COMMENT ON VIEW view_crew_workload IS 'Shows workload distribution across all crew members';
COMMENT ON VIEW view_shift_coverage IS 'Shows coverage statistics by location and shift type';