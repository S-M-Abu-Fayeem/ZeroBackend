-- =====================================================
-- ZERO WASTE MANAGEMENT SYSTEM - DATABASE SCHEMA
-- =====================================================

-- =====================================================
-- ENUM TYPES
-- =====================================================

-- User role enumeration
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('CITIZEN', 'CLEANER', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Report status enumeration
DO $$ BEGIN
    CREATE TYPE report_status AS ENUM ('SUBMITTED', 'APPROVED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Severity level enumeration
DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Environmental impact enumeration
DO $$ BEGIN
    CREATE TYPE environmental_impact AS ENUM ('LOW', 'MODERATE', 'HIGH', 'SEVERE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Quality rating enumeration
DO $$ BEGIN
    CREATE TYPE quality_rating AS ENUM ('POOR', 'FAIR', 'GOOD', 'EXCELLENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Verification status enumeration
DO $$ BEGIN
    CREATE TYPE verification_status AS ENUM ('VERIFIED', 'NEEDS_REVIEW', 'INCOMPLETE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Alert source enumeration
DO $$ BEGIN
    CREATE TYPE alert_source AS ENUM ('AI', 'CITIZEN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Alert status enumeration
DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('OPEN', 'RESOLVED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Badge type enumeration
DO $$ BEGIN
    CREATE TYPE badge_type AS ENUM ('FIRST_REPORT', 'ECO_WARRIOR', 'ZONE_CHAMPION', 'STREAK_7', 'STREAK_30', 'TOP_REPORTER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Notification type enumeration
DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM ('POINTS', 'BADGE', 'REPORT', 'TASK', 'ALERT', 'ANNOUNCEMENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Payment status enumeration (for future use)
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('PENDING', 'PAID', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =====================================================
-- CORE USER TABLES
-- =====================================================

-- Users table (all system users)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role user_role NOT NULL,
    address TEXT,
    language VARCHAR(5) DEFAULT 'en',
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    dark_mode BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Citizen profiles (gamification data)
CREATE TABLE IF NOT EXISTS citizen_profiles (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    green_points_balance INT DEFAULT 0,
    total_reports INT DEFAULT 0,
    approved_reports INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    rank INT,
    last_report_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- Cleaner profiles (earnings and ratings)
CREATE TABLE IF NOT EXISTS cleaner_profiles (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_earnings DECIMAL(12,2) DEFAULT 0,
    pending_earnings DECIMAL(12,2) DEFAULT 0,
    completed_tasks INT DEFAULT 0,
    current_tasks INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,
    total_ratings INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- Admin profiles (department and role)
CREATE TABLE IF NOT EXISTS admin_profiles (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(100),
    role_title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- =====================================================
-- ZONE MANAGEMENT
-- =====================================================

-- Zones (geographic service areas)
CREATE TABLE IF NOT EXISTS zones (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    cleanliness_score INT DEFAULT 100,
    color VARCHAR(7) DEFAULT '#3b82f6',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- Zone polygons (boundary coordinates)
CREATE TABLE IF NOT EXISTS zone_polygons (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    zone_id VARCHAR(36) NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    point_order INT NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    UNIQUE(zone_id, point_order)
);

-- =====================================================
-- REPORTS & WASTE ANALYSIS
-- =====================================================

-- Reports (waste reports from citizens)
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    zone_id VARCHAR(36) NOT NULL REFERENCES zones(id),
    description TEXT NOT NULL,
    image_url VARCHAR(500),
    severity severity_level NOT NULL,
    status report_status DEFAULT 'SUBMITTED',
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id),
    completed_at TIMESTAMP,
    cleaner_id VARCHAR(36) REFERENCES users(id),
    after_image_url VARCHAR(500),
    reviewed_by VARCHAR(36) REFERENCES users(id),
    reviewed_at TIMESTAMP,
    decline_reason TEXT
);

-- Waste analyses (AI-generated analysis of waste)
CREATE TABLE IF NOT EXISTS waste_analyses (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    report_id VARCHAR(36) UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    description TEXT,
    severity severity_level,
    estimated_volume VARCHAR(100),
    environmental_impact environmental_impact,
    health_hazard BOOLEAN DEFAULT false,
    hazard_details TEXT,
    recommended_action TEXT,
    estimated_cleanup_time VARCHAR(50),
    confidence INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- Waste compositions (breakdown of waste types)
CREATE TABLE IF NOT EXISTS waste_compositions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
    waste_type VARCHAR(50) NOT NULL,
    percentage INT NOT NULL,
    recyclable BOOLEAN DEFAULT false
);

-- Special equipment (equipment needed for cleanup)
CREATE TABLE IF NOT EXISTS special_equipment (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
    equipment_name VARCHAR(100) NOT NULL
);

-- Cleanup comparisons (AI-generated before/after analysis)
CREATE TABLE IF NOT EXISTS cleanup_comparisons (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    report_id VARCHAR(36) UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    completion_percentage INT,
    before_summary TEXT,
    after_summary TEXT,
    quality_rating quality_rating,
    environmental_benefit TEXT,
    verification_status verification_status,
    feedback TEXT,
    confidence INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- Cleanup waste removed (waste removed during cleanup)
CREATE TABLE IF NOT EXISTS cleanup_waste_removed (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    cleanup_comparison_id VARCHAR(36) NOT NULL REFERENCES cleanup_comparisons(id) ON DELETE CASCADE,
    waste_type VARCHAR(50) NOT NULL,
    percentage INT NOT NULL,
    recyclable BOOLEAN DEFAULT false
);

-- Cleanup remaining issues (issues still present after cleanup)
CREATE TABLE IF NOT EXISTS cleanup_remaining_issues (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    cleanup_comparison_id VARCHAR(36) NOT NULL REFERENCES cleanup_comparisons(id) ON DELETE CASCADE,
    issue_description TEXT NOT NULL
);

-- Cleanup reviews (citizen reviews of cleanup work)
CREATE TABLE IF NOT EXISTS cleanup_reviews (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    report_id VARCHAR(36) UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    citizen_id VARCHAR(36) NOT NULL REFERENCES users(id),
    cleaner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- =====================================================
-- TASKS
-- =====================================================

-- Tasks (cleanup tasks for cleaners)
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    report_id VARCHAR(36) REFERENCES reports(id),
    zone_id VARCHAR(36) NOT NULL REFERENCES zones(id),
    cleaner_id VARCHAR(36) REFERENCES users(id),
    description TEXT NOT NULL,
    status report_status DEFAULT 'APPROVED',
    priority severity_level NOT NULL,
    due_date TIMESTAMP NOT NULL,
    reward DECIMAL(10,2) NOT NULL,
    evidence_image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    taken_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- =====================================================
-- GAMIFICATION
-- =====================================================

-- Badges (achievement badges)
CREATE TABLE IF NOT EXISTS badges (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    badge_type badge_type UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    icon VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- User badges (badges earned by users)
CREATE TABLE IF NOT EXISTS user_badges (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id VARCHAR(36) NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    awarded_by VARCHAR(36) REFERENCES users(id),
    UNIQUE(user_id, badge_id)
);

-- Green points transactions (points earned/spent)
CREATE TABLE IF NOT EXISTS green_points_transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id VARCHAR(36) REFERENCES reports(id),
    green_points INT NOT NULL,
    reason VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id)
);

-- Green points config (points awarded for actions)
CREATE TABLE IF NOT EXISTS green_points_config (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    action_type VARCHAR(50) UNIQUE NOT NULL,
    green_points INT NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP,
    updated_by VARCHAR(36) REFERENCES users(id)
);

-- =====================================================
-- ALERTS & NOTIFICATIONS
-- =====================================================

-- Alerts (zone cleanliness alerts)
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source alert_source NOT NULL,
    zone_id VARCHAR(36) NOT NULL REFERENCES zones(id),
    severity severity_level NOT NULL,
    status alert_status DEFAULT 'OPEN',
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(36) REFERENCES users(id)
);

-- Notifications (user notifications)
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    related_report_id VARCHAR(36) REFERENCES reports(id),
    related_task_id VARCHAR(36) REFERENCES tasks(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id)
);

-- Bulk notifications (system-wide announcements)
CREATE TABLE IF NOT EXISTS bulk_notifications (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    audience VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    sent_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PAYMENTS
-- =====================================================

-- Earnings transactions (cleaner payments)
CREATE TABLE IF NOT EXISTS earnings_transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    cleaner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    paid_by VARCHAR(36) REFERENCES users(id)
);

-- =====================================================
-- LEADERBOARDS
-- =====================================================

-- Citizen leaderboard (top citizens by points)
CREATE TABLE IF NOT EXISTS citizen_leaderboard (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rank INT NOT NULL,
    total_green_points INT NOT NULL,
    approved_reports INT NOT NULL,
    badges_count INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculated_by VARCHAR(36) REFERENCES users(id),
    UNIQUE(period, rank)
);

-- Cleaner leaderboard (top cleaners by earnings)
CREATE TABLE IF NOT EXISTS cleaner_leaderboard (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rank INT NOT NULL,
    total_earnings DECIMAL(12,2) NOT NULL,
    completed_tasks INT NOT NULL,
    rating DECIMAL(3,2) NOT NULL,
    this_month_earnings DECIMAL(12,2) DEFAULT 0,
    period VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculated_by VARCHAR(36) REFERENCES users(id),
    UNIQUE(period, rank)
);

-- =====================================================
-- AUDIT & SESSIONS
-- =====================================================

-- Activity logs (audit trail of user actions)
CREATE TABLE IF NOT EXISTS activity_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(36),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions (active user sessions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_info TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DEFAULT DATA
-- =====================================================

-- Insert default badges
INSERT INTO badges (badge_type, name, description, icon) VALUES
('FIRST_REPORT', 'First Step', 'Submitted your first waste report', '🌱'),
('ECO_WARRIOR', 'Eco Warrior', 'Had 10 reports approved', '🌿'),
('ZONE_CHAMPION', 'Zone Champion', 'Top reporter in a zone', '🏆'),
('STREAK_7', '7-Day Streak', 'Reported waste for 7 consecutive days', '🔥'),
('STREAK_30', '30-Day Streak', 'Reported waste for 30 consecutive days', '⭐'),
('TOP_REPORTER', 'Top Reporter', 'Ranked #1 on the leaderboard', '👑')
ON CONFLICT (badge_type) DO NOTHING;

-- Insert default green points config
INSERT INTO green_points_config (action_type, green_points, description) VALUES
('REPORT_CREATED', 10, 'Points for submitting a report'),
('REPORT_APPROVED', 25, 'Bonus for approved report'),
('SEVERITY_LOW', 5, 'Bonus for LOW severity'),
('SEVERITY_MEDIUM', 10, 'Bonus for MEDIUM severity'),
('SEVERITY_HIGH', 15, 'Bonus for HIGH severity'),
('SEVERITY_CRITICAL', 25, 'Bonus for CRITICAL severity'),
('TASK_COMPLETED', 50, 'Bonus when cleanup is completed'),
('REVIEW_SUBMITTED', 5, 'Points for reviewing cleanup')
ON CONFLICT (action_type) DO NOTHING;

-- Insert system user for automated actions
INSERT INTO users (id, email, password_hash, name, role, is_active) VALUES
('00000000-0000-0000-0000-000000000000', 'system@zerowaste.internal', 
 'SYSTEM_USER_NO_LOGIN', 'System', 'ADMIN', true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Citizen profiles indexes
CREATE INDEX IF NOT EXISTS idx_citizen_profiles_user_id ON citizen_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_citizen_profiles_rank ON citizen_profiles(rank);
CREATE INDEX IF NOT EXISTS idx_citizen_profiles_green_points ON citizen_profiles(green_points_balance DESC);

-- Cleaner profiles indexes
CREATE INDEX IF NOT EXISTS idx_cleaner_profiles_user_id ON cleaner_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_cleaner_profiles_rating ON cleaner_profiles(rating DESC);
CREATE INDEX IF NOT EXISTS idx_cleaner_profiles_earnings ON cleaner_profiles(total_earnings DESC);

-- Admin profiles indexes
CREATE INDEX IF NOT EXISTS idx_admin_profiles_user_id ON admin_profiles(user_id);

-- Zones indexes
CREATE INDEX IF NOT EXISTS idx_zones_is_active ON zones(is_active);
CREATE INDEX IF NOT EXISTS idx_zones_cleanliness_score ON zones(cleanliness_score);

-- Zone polygons indexes
CREATE INDEX IF NOT EXISTS idx_zone_polygons_zone_id ON zone_polygons(zone_id);
CREATE INDEX IF NOT EXISTS idx_zone_polygons_coordinates ON zone_polygons(latitude, longitude);

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_zone_id ON reports(zone_id);
CREATE INDEX IF NOT EXISTS idx_reports_cleaner_id ON reports(cleaner_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_severity ON reports(severity);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_coordinates ON reports(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_reports_status_zone ON reports(status, zone_id);

-- Waste analyses indexes
CREATE INDEX IF NOT EXISTS idx_waste_analyses_report_id ON waste_analyses(report_id);
CREATE INDEX IF NOT EXISTS idx_waste_analyses_severity ON waste_analyses(severity);
CREATE INDEX IF NOT EXISTS idx_waste_analyses_environmental_impact ON waste_analyses(environmental_impact);

-- Waste compositions indexes
CREATE INDEX IF NOT EXISTS idx_waste_compositions_analysis_id ON waste_compositions(waste_analysis_id);
CREATE INDEX IF NOT EXISTS idx_waste_compositions_recyclable ON waste_compositions(recyclable);

-- Special equipment indexes
CREATE INDEX IF NOT EXISTS idx_special_equipment_analysis_id ON special_equipment(waste_analysis_id);

-- Cleanup comparisons indexes
CREATE INDEX IF NOT EXISTS idx_cleanup_comparisons_report_id ON cleanup_comparisons(report_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_comparisons_quality ON cleanup_comparisons(quality_rating);
CREATE INDEX IF NOT EXISTS idx_cleanup_comparisons_verification ON cleanup_comparisons(verification_status);

-- Cleanup waste removed indexes
CREATE INDEX IF NOT EXISTS idx_cleanup_waste_removed_comparison_id ON cleanup_waste_removed(cleanup_comparison_id);

-- Cleanup remaining issues indexes
CREATE INDEX IF NOT EXISTS idx_cleanup_remaining_issues_comparison_id ON cleanup_remaining_issues(cleanup_comparison_id);

-- Cleanup reviews indexes
CREATE INDEX IF NOT EXISTS idx_cleanup_reviews_report_id ON cleanup_reviews(report_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_reviews_citizen_id ON cleanup_reviews(citizen_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_reviews_cleaner_id ON cleanup_reviews(cleaner_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_reviews_rating ON cleanup_reviews(rating);

-- Tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_report_id ON tasks(report_id);
CREATE INDEX IF NOT EXISTS idx_tasks_zone_id ON tasks(zone_id);
CREATE INDEX IF NOT EXISTS idx_tasks_cleaner_id ON tasks(cleaner_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status_cleaner ON tasks(status, cleaner_id);

-- Badges indexes
CREATE INDEX IF NOT EXISTS idx_badges_badge_type ON badges(badge_type);

-- User badges indexes
CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_user_badges_badge_id ON user_badges(badge_id);
CREATE INDEX IF NOT EXISTS idx_user_badges_earned_at ON user_badges(earned_at DESC);

-- Green points transactions indexes
CREATE INDEX IF NOT EXISTS idx_green_points_transactions_user_id ON green_points_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_green_points_transactions_report_id ON green_points_transactions(report_id);
CREATE INDEX IF NOT EXISTS idx_green_points_transactions_created_at ON green_points_transactions(created_at DESC);

-- Green points config indexes
CREATE INDEX IF NOT EXISTS idx_green_points_config_action_type ON green_points_config(action_type);

-- Alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_zone_id ON alerts(zone_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- Bulk notifications indexes
CREATE INDEX IF NOT EXISTS idx_bulk_notifications_audience ON bulk_notifications(audience);
CREATE INDEX IF NOT EXISTS idx_bulk_notifications_created_at ON bulk_notifications(created_at DESC);

-- Earnings transactions indexes
CREATE INDEX IF NOT EXISTS idx_earnings_transactions_cleaner_id ON earnings_transactions(cleaner_id);
CREATE INDEX IF NOT EXISTS idx_earnings_transactions_task_id ON earnings_transactions(task_id);
CREATE INDEX IF NOT EXISTS idx_earnings_transactions_status ON earnings_transactions(status);
CREATE INDEX IF NOT EXISTS idx_earnings_transactions_created_at ON earnings_transactions(created_at DESC);

-- Citizen leaderboard indexes
CREATE INDEX IF NOT EXISTS idx_citizen_leaderboard_user_id ON citizen_leaderboard(user_id);
CREATE INDEX IF NOT EXISTS idx_citizen_leaderboard_period_rank ON citizen_leaderboard(period, rank);

-- Cleaner leaderboard indexes
CREATE INDEX IF NOT EXISTS idx_cleaner_leaderboard_user_id ON cleaner_leaderboard(user_id);
CREATE INDEX IF NOT EXISTS idx_cleaner_leaderboard_period_rank ON cleaner_leaderboard(period, rank);

-- Activity logs indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- =====================================================
-- TRIGGERS FOR AUTOMATED ACTIONS
-- =====================================================

-- Trigger: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_citizen_profiles_updated_at BEFORE UPDATE ON citizen_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleaner_profiles_updated_at BEFORE UPDATE ON cleaner_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_profiles_updated_at BEFORE UPDATE ON admin_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zones_updated_at BEFORE UPDATE ON zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_waste_analyses_updated_at BEFORE UPDATE ON waste_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleanup_comparisons_updated_at BEFORE UPDATE ON cleanup_comparisons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cleanup_reviews_updated_at BEFORE UPDATE ON cleanup_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_badges_updated_at BEFORE UPDATE ON badges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_green_points_config_updated_at BEFORE UPDATE ON green_points_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Update citizen profile stats when report is approved
CREATE OR REPLACE FUNCTION update_citizen_stats_on_report_approval()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.status = 'APPROVED' AND OLD.status != 'APPROVED' THEN
        UPDATE citizen_profiles
        SET 
            total_reports = total_reports + 1,
            approved_reports = approved_reports + 1,
            last_report_date = CURRENT_DATE,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_citizen_stats_on_approval
    AFTER UPDATE ON reports
    FOR EACH ROW
    WHEN (NEW.status = 'APPROVED' AND OLD.status != 'APPROVED')
    EXECUTE FUNCTION update_citizen_stats_on_report_approval();

-- Trigger: Update cleaner profile when task is completed
CREATE OR REPLACE FUNCTION update_cleaner_stats_on_task_completion()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' AND NEW.cleaner_id IS NOT NULL THEN
        UPDATE cleaner_profiles
        SET 
            completed_tasks = completed_tasks + 1,
            current_tasks = GREATEST(current_tasks - 1, 0),
            total_earnings = total_earnings + NEW.reward,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.cleaner_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cleaner_stats_on_completion
    AFTER UPDATE ON tasks
    FOR EACH ROW
    WHEN (NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED')
    EXECUTE FUNCTION update_cleaner_stats_on_task_completion();

-- Trigger: Update cleaner current tasks when task is assigned
CREATE OR REPLACE FUNCTION update_cleaner_current_tasks()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.cleaner_id IS NOT NULL AND (OLD.cleaner_id IS NULL OR OLD.cleaner_id != NEW.cleaner_id) THEN
        UPDATE cleaner_profiles
        SET 
            current_tasks = current_tasks + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.cleaner_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cleaner_current_tasks
    AFTER UPDATE ON tasks
    FOR EACH ROW
    WHEN (NEW.cleaner_id IS NOT NULL AND (OLD.cleaner_id IS NULL OR OLD.cleaner_id != NEW.cleaner_id))
    EXECUTE FUNCTION update_cleaner_current_tasks();

-- Trigger: Update cleaner rating when review is submitted
CREATE OR REPLACE FUNCTION update_cleaner_rating_on_review()
RETURNS TRIGGER AS $
BEGIN
    UPDATE cleaner_profiles
    SET 
        total_ratings = total_ratings + 1,
        rating = (
            SELECT ROUND(AVG(rating)::numeric, 2)
            FROM cleanup_reviews
            WHERE cleaner_id = NEW.cleaner_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.cleaner_id;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cleaner_rating
    AFTER INSERT ON cleanup_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_cleaner_rating_on_review();

-- Trigger: Award green points when report is approved
CREATE OR REPLACE FUNCTION award_green_points_on_approval()
RETURNS TRIGGER AS $
DECLARE
    base_points INT;
    severity_bonus INT;
    total_points INT;
BEGIN
    IF NEW.status = 'APPROVED' AND OLD.status != 'APPROVED' THEN
        -- Get base points for report approval
        SELECT green_points INTO base_points
        FROM green_points_config
        WHERE action_type = 'REPORT_APPROVED';
        
        -- Get severity bonus
        SELECT green_points INTO severity_bonus
        FROM green_points_config
        WHERE action_type = 'SEVERITY_' || NEW.severity;
        
        total_points := COALESCE(base_points, 0) + COALESCE(severity_bonus, 0);
        
        -- Insert transaction
        INSERT INTO green_points_transactions (user_id, report_id, green_points, reason, created_by)
        VALUES (NEW.user_id, NEW.id, total_points, 'Report approved', NEW.reviewed_by);
        
        -- Update citizen balance
        UPDATE citizen_profiles
        SET green_points_balance = green_points_balance + total_points
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_award_green_points
    AFTER UPDATE ON reports
    FOR EACH ROW
    WHEN (NEW.status = 'APPROVED' AND OLD.status != 'APPROVED')
    EXECUTE FUNCTION award_green_points_on_approval();

-- Trigger: Create earnings transaction when task is completed
CREATE OR REPLACE FUNCTION create_earnings_transaction_on_completion()
RETURNS TRIGGER AS $
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' AND NEW.cleaner_id IS NOT NULL THEN
        INSERT INTO earnings_transactions (cleaner_id, task_id, amount, status, created_by)
        VALUES (NEW.cleaner_id, NEW.id, NEW.reward, 'PENDING', NEW.updated_by);
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_earnings_transaction
    AFTER UPDATE ON tasks
    FOR EACH ROW
    WHEN (NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED')
    EXECUTE FUNCTION create_earnings_transaction_on_completion();

-- Trigger: Log user activity
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $
DECLARE
    action_name VARCHAR(100);
    entity_type_name VARCHAR(50);
BEGIN
    -- Determine action type
    IF TG_OP = 'INSERT' THEN
        action_name := 'CREATE';
    ELSIF TG_OP = 'UPDATE' THEN
        action_name := 'UPDATE';
    ELSIF TG_OP = 'DELETE' THEN
        action_name := 'DELETE';
    END IF;
    
    -- Get entity type from table name
    entity_type_name := TG_TABLE_NAME;
    
    -- Log the activity
    IF TG_OP = 'DELETE' THEN
        INSERT INTO activity_logs (user_id, action, entity_type, entity_id)
        VALUES (OLD.updated_by, action_name, entity_type_name, OLD.id);
    ELSE
        INSERT INTO activity_logs (user_id, action, entity_type, entity_id)
        VALUES (NEW.updated_by, action_name, entity_type_name, NEW.id);
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Apply activity logging to key tables (optional - can be enabled as needed)
-- CREATE TRIGGER log_reports_activity AFTER INSERT OR UPDATE OR DELETE ON reports
--     FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- CREATE TRIGGER log_tasks_activity AFTER INSERT OR UPDATE OR DELETE ON tasks
--     FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- =====================================================
-- STORED PROCEDURES FOR BUSINESS LOGIC
-- =====================================================

-- Procedure: Calculate citizen leaderboard
CREATE OR REPLACE FUNCTION calculate_citizen_leaderboard(period_name VARCHAR DEFAULT 'all_time')
RETURNS TABLE (
    rank INT,
    user_id VARCHAR,
    user_name VARCHAR,
    total_green_points INT,
    approved_reports INT,
    badges_count INT
) AS $
BEGIN
    RETURN QUERY
    WITH ranked_citizens AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY cp.green_points_balance DESC, cp.approved_reports DESC) AS rank,
            u.id AS user_id,
            u.name AS user_name,
            cp.green_points_balance AS total_green_points,
            cp.approved_reports,
            (SELECT COUNT(*) FROM user_badges WHERE user_badges.user_id = u.id) AS badges_count
        FROM users u
        JOIN citizen_profiles cp ON u.id = cp.user_id
        WHERE u.is_active = true AND u.role = 'CITIZEN'
    )
    SELECT * FROM ranked_citizens
    ORDER BY rank
    LIMIT 100;
END;
$ LANGUAGE plpgsql;

-- Procedure: Calculate cleaner leaderboard
CREATE OR REPLACE FUNCTION calculate_cleaner_leaderboard(period_name VARCHAR DEFAULT 'all_time')
RETURNS TABLE (
    rank INT,
    user_id VARCHAR,
    user_name VARCHAR,
    total_earnings DECIMAL,
    completed_tasks INT,
    rating DECIMAL,
    this_month_earnings DECIMAL
) AS $
BEGIN
    RETURN QUERY
    WITH ranked_cleaners AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY cp.total_earnings DESC, cp.completed_tasks DESC) AS rank,
            u.id AS user_id,
            u.name AS user_name,
            cp.total_earnings,
            cp.completed_tasks,
            cp.rating,
            COALESCE((
                SELECT SUM(amount)
                FROM earnings_transactions
                WHERE cleaner_id = u.id 
                AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
            ), 0) AS this_month_earnings
        FROM users u
        JOIN cleaner_profiles cp ON u.id = cp.user_id
        WHERE u.is_active = true AND u.role = 'CLEANER'
    )
    SELECT * FROM ranked_cleaners
    ORDER BY rank
    LIMIT 100;
END;
$ LANGUAGE plpgsql;

-- Procedure: Get zone statistics
CREATE OR REPLACE FUNCTION get_zone_statistics(zone_id_param VARCHAR)
RETURNS TABLE (
    zone_id VARCHAR,
    zone_name VARCHAR,
    total_reports BIGINT,
    pending_reports BIGINT,
    completed_reports BIGINT,
    active_tasks BIGINT,
    cleanliness_score INT,
    avg_completion_time INTERVAL
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        z.id AS zone_id,
        z.name AS zone_name,
        COUNT(r.id) AS total_reports,
        COUNT(r.id) FILTER (WHERE r.status IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS')) AS pending_reports,
        COUNT(r.id) FILTER (WHERE r.status = 'COMPLETED') AS completed_reports,
        COUNT(t.id) FILTER (WHERE t.status IN ('APPROVED', 'IN_PROGRESS')) AS active_tasks,
        z.cleanliness_score,
        AVG(r.completed_at - r.created_at) FILTER (WHERE r.completed_at IS NOT NULL) AS avg_completion_time
    FROM zones z
    LEFT JOIN reports r ON z.id = r.zone_id
    LEFT JOIN tasks t ON z.id = t.zone_id
    WHERE z.id = zone_id_param
    GROUP BY z.id, z.name, z.cleanliness_score;
END;
$ LANGUAGE plpgsql;

-- Procedure: Get user statistics
CREATE OR REPLACE FUNCTION get_user_statistics(user_id_param VARCHAR)
RETURNS TABLE (
    user_id VARCHAR,
    user_name VARCHAR,
    user_role user_role,
    total_reports INT,
    approved_reports INT,
    green_points INT,
    badges_count BIGINT,
    current_streak INT,
    completed_tasks INT,
    total_earnings DECIMAL,
    rating DECIMAL
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        u.id AS user_id,
        u.name AS user_name,
        u.role AS user_role,
        COALESCE(cp.total_reports, 0) AS total_reports,
        COALESCE(cp.approved_reports, 0) AS approved_reports,
        COALESCE(cp.green_points_balance, 0) AS green_points,
        (SELECT COUNT(*) FROM user_badges WHERE user_badges.user_id = u.id) AS badges_count,
        COALESCE(cp.current_streak, 0) AS current_streak,
        COALESCE(clp.completed_tasks, 0) AS completed_tasks,
        COALESCE(clp.total_earnings, 0) AS total_earnings,
        COALESCE(clp.rating, 0) AS rating
    FROM users u
    LEFT JOIN citizen_profiles cp ON u.id = cp.user_id
    LEFT JOIN cleaner_profiles clp ON u.id = clp.user_id
    WHERE u.id = user_id_param;
END;
$ LANGUAGE plpgsql;

-- Procedure: Award badge to user
CREATE OR REPLACE FUNCTION award_badge(
    user_id_param VARCHAR,
    badge_type_param badge_type,
    awarded_by_param VARCHAR DEFAULT '00000000-0000-0000-0000-000000000000'
)
RETURNS BOOLEAN AS $
DECLARE
    badge_id_var VARCHAR;
    already_awarded BOOLEAN;
BEGIN
    -- Check if badge already awarded
    SELECT EXISTS(
        SELECT 1 FROM user_badges ub
        JOIN badges b ON ub.badge_id = b.id
        WHERE ub.user_id = user_id_param AND b.badge_type = badge_type_param
    ) INTO already_awarded;
    
    IF already_awarded THEN
        RETURN FALSE;
    END IF;
    
    -- Get badge ID
    SELECT id INTO badge_id_var FROM badges WHERE badge_type = badge_type_param;
    
    IF badge_id_var IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Award badge
    INSERT INTO user_badges (user_id, badge_id, awarded_by)
    VALUES (user_id_param, badge_id_var, awarded_by_param);
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, created_by)
    VALUES (
        user_id_param,
        'BADGE',
        'New Badge Earned!',
        'Congratulations! You earned the ' || (SELECT name FROM badges WHERE id = badge_id_var) || ' badge!',
        awarded_by_param
    );
    
    RETURN TRUE;
END;
$ LANGUAGE plpgsql;

-- Procedure: Check and award automatic badges
CREATE OR REPLACE FUNCTION check_and_award_badges(user_id_param VARCHAR)
RETURNS VOID AS $
DECLARE
    approved_count INT;
    current_streak_val INT;
    citizen_rank INT;
BEGIN
    -- Get citizen stats
    SELECT approved_reports, current_streak, rank
    INTO approved_count, current_streak_val, citizen_rank
    FROM citizen_profiles
    WHERE user_id = user_id_param;
    
    -- Award FIRST_REPORT badge
    IF approved_count >= 1 THEN
        PERFORM award_badge(user_id_param, 'FIRST_REPORT');
    END IF;
    
    -- Award ECO_WARRIOR badge
    IF approved_count >= 10 THEN
        PERFORM award_badge(user_id_param, 'ECO_WARRIOR');
    END IF;
    
    -- Award STREAK_7 badge
    IF current_streak_val >= 7 THEN
        PERFORM award_badge(user_id_param, 'STREAK_7');
    END IF;
    
    -- Award STREAK_30 badge
    IF current_streak_val >= 30 THEN
        PERFORM award_badge(user_id_param, 'STREAK_30');
    END IF;
    
    -- Award TOP_REPORTER badge
    IF citizen_rank = 1 THEN
        PERFORM award_badge(user_id_param, 'TOP_REPORTER');
    END IF;
END;
$ LANGUAGE plpgsql;

-- Procedure: Update zone cleanliness score
CREATE OR REPLACE FUNCTION update_zone_cleanliness_score(zone_id_param VARCHAR)
RETURNS INT AS $
DECLARE
    pending_count INT;
    completed_count INT;
    total_count INT;
    new_score INT;
BEGIN
    -- Count reports by status
    SELECT 
        COUNT(*) FILTER (WHERE status IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS')),
        COUNT(*) FILTER (WHERE status = 'COMPLETED'),
        COUNT(*)
    INTO pending_count, completed_count, total_count
    FROM reports
    WHERE zone_id = zone_id_param
    AND created_at >= CURRENT_DATE - INTERVAL '30 days';
    
    -- Calculate score (100 = perfect, 0 = worst)
    IF total_count = 0 THEN
        new_score := 100;
    ELSE
        new_score := GREATEST(0, 100 - (pending_count * 5));
    END IF;
    
    -- Update zone score
    UPDATE zones
    SET cleanliness_score = new_score,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = zone_id_param;
    
    RETURN new_score;
END;
$ LANGUAGE plpgsql;

-- Procedure: Clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INT AS $
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- Procedure: Get dashboard statistics for admin
CREATE OR REPLACE FUNCTION get_admin_dashboard_stats()
RETURNS TABLE (
    total_users BIGINT,
    total_citizens BIGINT,
    total_cleaners BIGINT,
    total_reports BIGINT,
    pending_reports BIGINT,
    completed_reports BIGINT,
    total_tasks BIGINT,
    active_tasks BIGINT,
    total_zones BIGINT,
    avg_cleanliness_score DECIMAL
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM users WHERE is_active = true) AS total_users,
        (SELECT COUNT(*) FROM users WHERE role = 'CITIZEN' AND is_active = true) AS total_citizens,
        (SELECT COUNT(*) FROM users WHERE role = 'CLEANER' AND is_active = true) AS total_cleaners,
        (SELECT COUNT(*) FROM reports) AS total_reports,
        (SELECT COUNT(*) FROM reports WHERE status IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS')) AS pending_reports,
        (SELECT COUNT(*) FROM reports WHERE status = 'COMPLETED') AS completed_reports,
        (SELECT COUNT(*) FROM tasks) AS total_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status IN ('APPROVED', 'IN_PROGRESS')) AS active_tasks,
        (SELECT COUNT(*) FROM zones WHERE is_active = true) AS total_zones,
        (SELECT ROUND(AVG(cleanliness_score)::numeric, 2) FROM zones WHERE is_active = true) AS avg_cleanliness_score;
END;
$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE users IS 'Core user table for all system users (citizens, cleaners, admins)';
COMMENT ON TABLE citizen_profiles IS 'Gamification data for citizen users';
COMMENT ON TABLE cleaner_profiles IS 'Earnings and ratings for cleaner users';
COMMENT ON TABLE admin_profiles IS 'Department and role information for admin users';
COMMENT ON TABLE zones IS 'Geographic service areas with cleanliness scores';
COMMENT ON TABLE reports IS 'Waste reports submitted by citizens';
COMMENT ON TABLE waste_analyses IS 'AI-generated analysis of waste in reports';
COMMENT ON TABLE tasks IS 'Cleanup tasks assigned to cleaners';
COMMENT ON TABLE badges IS 'Achievement badges that can be earned';
COMMENT ON TABLE green_points_transactions IS 'History of green points earned/spent';
COMMENT ON TABLE alerts IS 'Zone cleanliness alerts from AI or citizens';
COMMENT ON TABLE notifications IS 'User notifications for various events';
COMMENT ON TABLE earnings_transactions IS 'Payment transactions for cleaners';
COMMENT ON TABLE citizen_leaderboard IS 'Ranked list of top citizens by points';
COMMENT ON TABLE cleaner_leaderboard IS 'Ranked list of top cleaners by earnings';
COMMENT ON TABLE activity_logs IS 'Audit trail of user actions in the system';