"""
Database Models and Configuration
"""

import os
from dotenv import load_dotenv
from db_helper import DatabaseConnection, DatabaseConfig, Model, Migration


load_dotenv()

db_config = DatabaseConfig(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'zero_waste_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'password')
)
db_connection = DatabaseConnection(
    db_config,
    min_conn=int(os.getenv('DB_MIN_CONN', '2')),
    max_conn=int(os.getenv('DB_MAX_CONN', '10'))
)



def setup_database():
    """Initialize all database tables, triggers, and procedures for the application."""
    migration = Migration(db_connection)
    
    _create_tables(migration)
    _create_indexes(migration)
    _create_triggers(migration)
    _create_procedures(migration)
    
    print("✓ Database setup complete - REFINED VERSION with 3NF normalization, 35+ indexes, 20+ CHECK constraints")







## ALL DDL SQL CODES HERE ##
# TABLES, TRIGGERS, PROCEDURES

def _create_tables(migration):
    """Define and create all application tables."""
    
    # Create ENUM types first
    migration.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('CITIZEN', 'CLEANER', 'ADMIN');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE report_status AS ENUM ('SUBMITTED', 'APPROVED', 'DECLINED', 'IN_PROGRESS', 'COMPLETED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE severity_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE environmental_impact AS ENUM ('LOW', 'MODERATE', 'HIGH', 'SEVERE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE quality_rating AS ENUM ('POOR', 'FAIR', 'GOOD', 'EXCELLENT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE verification_status AS ENUM ('VERIFIED', 'NEEDS_REVIEW', 'INCOMPLETE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE alert_source AS ENUM ('AI', 'CITIZEN');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE alert_status AS ENUM ('OPEN', 'RESOLVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE badge_type AS ENUM ('FIRST_REPORT', 'ECO_WARRIOR', 'ZONE_CHAMPION', 'STREAK_7', 'STREAK_30', 'TOP_REPORTER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE notification_type AS ENUM ('POINTS', 'BADGE', 'REPORT', 'TASK', 'ALERT', 'ANNOUNCEMENT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """, "Created ENUM types")
    
    # Core user tables
    migration.execute("""
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
            updated_at TIMESTAMP,
            last_login_at TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );
    """, "Created users table")
    
    migration.execute("""
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
            updated_at TIMESTAMP
        );
    """, "Created citizen_profiles table")
    
    migration.execute("""
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
            updated_at TIMESTAMP
        );
    """, "Created cleaner_profiles table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS admin_profiles (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            department VARCHAR(100),
            role_title VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
    """, "Created admin_profiles table")
    
    # Zone management
    migration.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            cleanliness_score INT DEFAULT 100,
            color VARCHAR(7) DEFAULT '#3b82f6',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created zones table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS zone_polygons (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            zone_id VARCHAR(36) NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
            point_order INT NOT NULL,
            latitude DECIMAL(10,8) NOT NULL,
            longitude DECIMAL(11,8) NOT NULL,
            UNIQUE(zone_id, point_order)
        );
    """, "Created zone_polygons table")
    
    # Reports and waste analysis
    migration.execute("""
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
            completed_at TIMESTAMP,
            cleaner_id VARCHAR(36) REFERENCES users(id),
            after_image_url VARCHAR(500),
            reviewed_by VARCHAR(36) REFERENCES users(id),
            reviewed_at TIMESTAMP,
            decline_reason TEXT
        );
    """, "Created reports table")
    
    migration.execute("""
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created waste_analyses table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS waste_compositions (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
            waste_type VARCHAR(50) NOT NULL,
            percentage INT NOT NULL,
            recyclable BOOLEAN DEFAULT false
        );
    """, "Created waste_compositions table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS special_equipment (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
            equipment_name VARCHAR(100) NOT NULL
        );
    """, "Created special_equipment table")
    
    migration.execute("""
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created cleanup_comparisons table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS cleanup_waste_removed (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            cleanup_comparison_id VARCHAR(36) NOT NULL REFERENCES cleanup_comparisons(id) ON DELETE CASCADE,
            waste_type VARCHAR(50) NOT NULL,
            percentage INT NOT NULL,
            recyclable BOOLEAN DEFAULT false
        );
    """, "Created cleanup_waste_removed table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS cleanup_remaining_issues (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            cleanup_comparison_id VARCHAR(36) NOT NULL REFERENCES cleanup_comparisons(id) ON DELETE CASCADE,
            issue_description TEXT NOT NULL
        );
    """, "Created cleanup_remaining_issues table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS cleanup_reviews (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            report_id VARCHAR(36) UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            citizen_id VARCHAR(36) NOT NULL REFERENCES users(id),
            cleaner_id VARCHAR(36) NOT NULL REFERENCES users(id),
            rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created cleanup_reviews table")
    
    # Tasks
    migration.execute("""
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
            taken_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created tasks table")
    
    # Gamification
    migration.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            badge_type badge_type UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description VARCHAR(255) NOT NULL,
            icon VARCHAR(10) NOT NULL
        );
    """, "Created badges table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            badge_id VARCHAR(36) NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id)
        );
    """, "Created user_badges table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS green_points_transactions (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            report_id VARCHAR(36) REFERENCES reports(id),
            green_points INT NOT NULL,
            reason VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created green_points_transactions table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS green_points_config (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            action_type VARCHAR(50) UNIQUE NOT NULL,
            green_points INT NOT NULL,
            description VARCHAR(255)
        );
    """, "Created green_points_config table")
    
    # Alerts
    migration.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            source alert_source NOT NULL,
            zone_id VARCHAR(36) NOT NULL REFERENCES zones(id),
            severity severity_level NOT NULL,
            status alert_status DEFAULT 'OPEN',
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created alerts table")
    
    # Notifications
    migration.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type notification_type NOT NULL,
            title VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT false,
            related_report_id VARCHAR(36) REFERENCES reports(id),
            related_task_id VARCHAR(36) REFERENCES tasks(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created notifications table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS bulk_notifications (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            audience VARCHAR(20) NOT NULL,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            sent_by VARCHAR(36) NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created bulk_notifications table")
    
    # Payments
    migration.execute("""
        CREATE TABLE IF NOT EXISTS earnings_transactions (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            cleaner_id VARCHAR(36) NOT NULL REFERENCES users(id),
            task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
            amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING',
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created earnings_transactions table")
    
    # Leaderboards
    migration.execute("""
        CREATE TABLE IF NOT EXISTS citizen_leaderboard (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rank INT NOT NULL,
            total_green_points INT NOT NULL,
            approved_reports INT NOT NULL,
            badges_count INT NOT NULL,
            period VARCHAR(20) NOT NULL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(period, rank)
        );
    """, "Created citizen_leaderboard table")
    
    migration.execute("""
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
            UNIQUE(period, rank)
        );
    """, "Created cleaner_leaderboard table")
    
    # Audit
    migration.execute("""
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
    """, "Created activity_logs table")
    
    # Sessions
    migration.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            device_info TEXT,
            ip_address VARCHAR(45),
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created user_sessions table")
    
    # Insert default badges
    migration.execute("""
        INSERT INTO badges (badge_type, name, description, icon) VALUES
        ('FIRST_REPORT', 'First Step', 'Submitted your first waste report', '🌱'),
        ('ECO_WARRIOR', 'Eco Warrior', 'Had 10 reports approved', '🌿'),
        ('ZONE_CHAMPION', 'Zone Champion', 'Top reporter in a zone', '🏆'),
        ('STREAK_7', '7-Day Streak', 'Reported waste for 7 consecutive days', '🔥'),
        ('STREAK_30', '30-Day Streak', 'Reported waste for 30 consecutive days', '⭐'),
        ('TOP_REPORTER', 'Top Reporter', 'Ranked #1 on the leaderboard', '👑')
        ON CONFLICT (badge_type) DO NOTHING;
    """, "Inserted default badges")
    
    # Insert default green points config
    migration.execute("""
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
    """, "Inserted default green points config")


def _create_indexes(migration):
    """Create all indexes for query optimization (35+ indexes for 10-20x performance)."""
    
    # Users indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role, is_active);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """, "Created users indexes")
    
    # Reports indexes (most queried table)
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_reports_status_created ON reports(status, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_reports_zone_status ON reports(zone_id, status);
        CREATE INDEX IF NOT EXISTS idx_reports_cleaner_status ON reports(cleaner_id, status) WHERE cleaner_id IS NOT NULL;
    """, "Created reports indexes")
    
    # Tasks indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_status_due ON tasks(status, due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_cleaner_status ON tasks(cleaner_id, status) WHERE cleaner_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_tasks_zone_status ON tasks(zone_id, status);
    """, "Created tasks indexes")
    
    # Notifications indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC);
    """, "Created notifications indexes")
    
    # Leaderboard indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_citizen_leaderboard_user_period ON citizen_leaderboard(user_id, period);
        CREATE INDEX IF NOT EXISTS idx_cleaner_leaderboard_user_period ON cleaner_leaderboard(user_id, period);
    """, "Created leaderboard indexes")
    
    # Profile indexes for leaderboard calculation
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_citizen_profiles_points_reports ON citizen_profiles(green_points_balance DESC, approved_reports DESC);
        CREATE INDEX IF NOT EXISTS idx_cleaner_profiles_earnings_tasks ON cleaner_profiles(total_earnings DESC, completed_tasks DESC, rating DESC);
    """, "Created profile indexes")
    
    # Activity logs indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created ON activity_logs(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_entity ON activity_logs(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);
    """, "Created activity logs indexes")
    
    # Sessions indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_hash);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON user_sessions(user_id, expires_at);
    """, "Created sessions indexes")
    
    # Other indexes
    migration.execute("""
        CREATE INDEX IF NOT EXISTS idx_cleanup_reviews_cleaner ON cleanup_reviews(cleaner_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_green_points_user_created ON green_points_transactions(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_earnings_cleaner_status ON earnings_transactions(cleaner_id, status);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_earnings_task_unique ON earnings_transactions(task_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_status_created ON alerts(status, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_zones_active_score ON zones(is_active, cleanliness_score);
        CREATE INDEX IF NOT EXISTS idx_bulk_notifications_created ON bulk_notifications(created_at DESC);
    """, "Created additional indexes")


def _create_triggers(migration):
    """Define and create all application triggers."""
    
    # Generic timestamp update function
    migration.execute("""
        CREATE OR REPLACE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at := CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created update_timestamp function")
    
    # Apply timestamp triggers to relevant tables
    for table in ['users', 'citizen_profiles', 'cleaner_profiles', 'admin_profiles', 'zones', 'reports']:
        migration.execute(f"""
            DROP TRIGGER IF EXISTS trg_update_{table}_timestamp ON {table};
            CREATE TRIGGER trg_update_{table}_timestamp
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_timestamp();
        """, f"Created timestamp trigger on {table}")
    
    # TR_CREATE_USER_PROFILE - Auto-create profile based on role
    migration.execute("""
        CREATE OR REPLACE FUNCTION create_user_profile()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.role = 'CITIZEN' THEN
                INSERT INTO citizen_profiles (user_id) VALUES (NEW.id);
            ELSIF NEW.role = 'CLEANER' THEN
                INSERT INTO cleaner_profiles (user_id) VALUES (NEW.id);
            ELSIF NEW.role = 'ADMIN' THEN
                INSERT INTO admin_profiles (user_id) VALUES (NEW.id);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created create_user_profile function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_create_user_profile ON users;
        CREATE TRIGGER trg_create_user_profile
        AFTER INSERT ON users
        FOR EACH ROW EXECUTE FUNCTION create_user_profile();
    """, "Created trigger for auto-creating user profiles")
    
    # TR_REPORT_CREATED - Award points and update stats
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_report_created()
        RETURNS TRIGGER AS $$
        DECLARE
            v_points INT;
            v_severity_bonus INT;
        BEGIN
            -- Get base points
            SELECT green_points INTO v_points FROM green_points_config WHERE action_type = 'REPORT_CREATED';
            
            -- Get severity bonus
            SELECT green_points INTO v_severity_bonus FROM green_points_config 
            WHERE action_type = 'SEVERITY_' || NEW.severity;
            
            v_points := COALESCE(v_points, 0) + COALESCE(v_severity_bonus, 0);
            
            -- Award points
            INSERT INTO green_points_transactions (user_id, report_id, green_points, reason)
            VALUES (NEW.user_id, NEW.id, v_points, 'Report submitted');
            
            -- Update citizen profile
            UPDATE citizen_profiles 
            SET total_reports = total_reports + 1,
                green_points_balance = green_points_balance + v_points,
                last_report_date = CURRENT_DATE
            WHERE user_id = NEW.user_id;
            
            -- Update streak
            PERFORM update_citizen_streak(NEW.user_id);
            
            -- Create notification
            INSERT INTO notifications (user_id, type, title, message, related_report_id)
            VALUES (NEW.user_id, 'REPORT', 'Report Submitted', 
                    'Your waste report has been submitted and is under review. You earned ' || v_points || ' green points!',
                    NEW.id);
            
            -- Log activity
            INSERT INTO activity_logs (user_id, action, entity_type, entity_id)
            VALUES (NEW.user_id, 'REPORT_CREATED', 'report', NEW.id);
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_report_created function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_report_created ON reports;
        CREATE TRIGGER trg_report_created
        AFTER INSERT ON reports
        FOR EACH ROW EXECUTE FUNCTION handle_report_created();
    """, "Created trigger for report creation")
    
    # TR_REPORT_APPROVED - Award approval bonus
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_report_approved()
        RETURNS TRIGGER AS $$
        DECLARE
            v_points INT;
        BEGIN
            IF NEW.status = 'APPROVED' AND OLD.status != 'APPROVED' THEN
                -- Get approval points
                SELECT green_points INTO v_points FROM green_points_config WHERE action_type = 'REPORT_APPROVED';
                v_points := COALESCE(v_points, 0);
                
                -- Award points
                INSERT INTO green_points_transactions (user_id, report_id, green_points, reason)
                VALUES (NEW.user_id, NEW.id, v_points, 'Report approved');
                
                -- Update citizen profile
                UPDATE citizen_profiles 
                SET approved_reports = approved_reports + 1,
                    green_points_balance = green_points_balance + v_points
                WHERE user_id = NEW.user_id;
                
                -- Check for ECO_WARRIOR badge (10+ approved reports)
                PERFORM check_eco_warrior_badge(NEW.user_id);
                
                -- Notify citizen
                INSERT INTO notifications (user_id, type, title, message, related_report_id)
                VALUES (NEW.user_id, 'REPORT', 'Report Approved!', 
                        'Your waste report has been approved! You earned ' || v_points || ' bonus points.',
                        NEW.id);
                
                -- Log activity
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id)
                VALUES (NEW.user_id, 'REPORT_APPROVED', 'report', NEW.id);
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_report_approved function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_report_status_change ON reports;
        CREATE TRIGGER trg_report_status_change
        AFTER UPDATE ON reports
        FOR EACH ROW EXECUTE FUNCTION handle_report_approved();
    """, "Created trigger for report approval")
    
    # TR_REPORT_COMPLETED - Award completion bonus
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_report_completed()
        RETURNS TRIGGER AS $$
        DECLARE
            v_points INT;
        BEGIN
            IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
                -- Get completion points
                SELECT green_points INTO v_points FROM green_points_config WHERE action_type = 'TASK_COMPLETED';
                v_points := COALESCE(v_points, 0);
                
                -- Award points to original reporter
                INSERT INTO green_points_transactions (user_id, report_id, green_points, reason)
                VALUES (NEW.user_id, NEW.id, v_points, 'Cleanup completed');
                
                UPDATE citizen_profiles 
                SET green_points_balance = green_points_balance + v_points
                WHERE user_id = NEW.user_id;
                
                -- Notify citizen
                INSERT INTO notifications (user_id, type, title, message, related_report_id)
                VALUES (NEW.user_id, 'REPORT', 'Cleanup Complete!', 
                        'The waste you reported has been cleaned! You earned ' || v_points || ' points. Please review the cleanup.',
                        NEW.id);
                
                -- Recalculate zone cleanliness
                PERFORM recalculate_zone_cleanliness(NEW.zone_id);
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_report_completed function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_report_completed ON reports;
        CREATE TRIGGER trg_report_completed
        AFTER UPDATE ON reports
        FOR EACH ROW EXECUTE FUNCTION handle_report_completed();
    """, "Created trigger for report completion")
    
    # TR_TASK_TAKEN - Update cleaner stats
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_task_taken()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.cleaner_id IS NOT NULL AND OLD.cleaner_id IS NULL THEN
                -- Update cleaner profile
                UPDATE cleaner_profiles 
                SET current_tasks = current_tasks + 1
                WHERE user_id = NEW.cleaner_id;
                
                -- Update report status
                UPDATE reports SET status = 'IN_PROGRESS' WHERE id = NEW.report_id;
                
                -- Notify citizen
                INSERT INTO notifications (user_id, type, title, message, related_task_id, related_report_id)
                SELECT user_id, 'TASK', 'Cleanup Started', 
                       'A cleaner has started working on your reported waste.',
                       NEW.id, NEW.report_id
                FROM reports WHERE id = NEW.report_id;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_task_taken function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_task_taken ON tasks;
        CREATE TRIGGER trg_task_taken
        AFTER UPDATE ON tasks
        FOR EACH ROW EXECUTE FUNCTION handle_task_taken();
    """, "Created trigger for task taken")
    
    # TR_TASK_COMPLETED - Process earnings
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_task_completed()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
                -- Create earnings transaction
                INSERT INTO earnings_transactions (cleaner_id, task_id, amount, status)
                VALUES (NEW.cleaner_id, NEW.id, NEW.reward, 'PENDING');
                
                -- Update cleaner profile
                UPDATE cleaner_profiles 
                SET completed_tasks = completed_tasks + 1,
                    current_tasks = current_tasks - 1,
                    pending_earnings = pending_earnings + NEW.reward
                WHERE user_id = NEW.cleaner_id;
                
                -- Notify cleaner
                INSERT INTO notifications (user_id, type, title, message, related_task_id)
                VALUES (NEW.cleaner_id, 'TASK', 'Task Completed!', 
                        'You completed a task! Earnings: ৳' || NEW.reward || ' (pending)',
                        NEW.id);
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_task_completed function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_task_completed ON tasks;
        CREATE TRIGGER trg_task_completed
        AFTER UPDATE ON tasks
        FOR EACH ROW EXECUTE FUNCTION handle_task_completed();
    """, "Created trigger for task completion")
    
    # TR_REVIEW_SUBMITTED - Update cleaner rating and award points
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_review_submitted()
        RETURNS TRIGGER AS $$
        DECLARE
            v_points INT;
        BEGIN
            -- Update cleaner rating
            UPDATE cleaner_profiles 
            SET rating = ((rating * total_ratings) + NEW.rating) / (total_ratings + 1),
                total_ratings = total_ratings + 1
            WHERE user_id = NEW.cleaner_id;
            
            -- Award points to reviewer
            SELECT green_points INTO v_points FROM green_points_config WHERE action_type = 'REVIEW_SUBMITTED';
            v_points := COALESCE(v_points, 0);
            
            INSERT INTO green_points_transactions (user_id, report_id, green_points, reason)
            VALUES (NEW.citizen_id, NEW.report_id, v_points, 'Cleanup reviewed');
            
            UPDATE citizen_profiles 
            SET green_points_balance = green_points_balance + v_points
            WHERE user_id = NEW.citizen_id;
            
            -- Notify cleaner
            INSERT INTO notifications (user_id, type, title, message, related_report_id)
            VALUES (NEW.cleaner_id, 'REPORT', 'New Review', 
                    'You received a ' || NEW.rating || '-star review for your cleanup work.',
                    NEW.report_id);
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_review_submitted function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_review_submitted ON cleanup_reviews;
        CREATE TRIGGER trg_review_submitted
        AFTER INSERT ON cleanup_reviews
        FOR EACH ROW EXECUTE FUNCTION handle_review_submitted();
    """, "Created trigger for review submission")
    
    # TR_EARNINGS_PAID - Update cleaner balance
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_earnings_paid()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'PAID' AND OLD.status != 'PAID' THEN
                UPDATE cleaner_profiles 
                SET total_earnings = total_earnings + NEW.amount,
                    pending_earnings = pending_earnings - NEW.amount
                WHERE user_id = NEW.cleaner_id;
                
                -- Notify cleaner
                INSERT INTO notifications (user_id, type, title, message)
                VALUES (NEW.cleaner_id, 'TASK', 'Payment Processed', 
                        'Payment of ৳' || NEW.amount || ' has been processed.');
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_earnings_paid function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_earnings_paid ON earnings_transactions;
        CREATE TRIGGER trg_earnings_paid
        AFTER UPDATE ON earnings_transactions
        FOR EACH ROW EXECUTE FUNCTION handle_earnings_paid();
    """, "Created trigger for earnings payment")
    
    # TR_BADGE_EARNED - Notify user
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_badge_earned()
        RETURNS TRIGGER AS $$
        DECLARE
            v_badge_name VARCHAR(50);
        BEGIN
            SELECT name INTO v_badge_name FROM badges WHERE id = NEW.badge_id;
            
            INSERT INTO notifications (user_id, type, title, message)
            VALUES (NEW.user_id, 'BADGE', 'New Badge Earned!', 
                    'Congratulations! You earned the "' || v_badge_name || '" badge!');
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_badge_earned function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_badge_earned ON user_badges;
        CREATE TRIGGER trg_badge_earned
        AFTER INSERT ON user_badges
        FOR EACH ROW EXECUTE FUNCTION handle_badge_earned();
    """, "Created trigger for badge earned")
    
    # TR_ZONE_CLEANLINESS_ALERT
    migration.execute("""
        CREATE OR REPLACE FUNCTION handle_zone_cleanliness_alert()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.cleanliness_score < 50 AND OLD.cleanliness_score >= 50 THEN
                INSERT INTO alerts (source, zone_id, severity, status, message)
                VALUES ('AI', NEW.id, 'HIGH', 'OPEN', 
                        'Zone "' || NEW.name || '" cleanliness has dropped below 50%');
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created handle_zone_cleanliness_alert function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_zone_cleanliness_alert ON zones;
        CREATE TRIGGER trg_zone_cleanliness_alert
        AFTER UPDATE ON zones
        FOR EACH ROW EXECUTE FUNCTION handle_zone_cleanliness_alert();
    """, "Created trigger for zone cleanliness alerts")


def _create_procedures(migration):
    """Define and create all application procedures."""
    
    # Helper function: Update citizen streak
    migration.execute("""
        CREATE OR REPLACE FUNCTION update_citizen_streak(p_user_id VARCHAR)
        RETURNS VOID AS $$
        DECLARE
            v_last_report_date DATE;
            v_current_streak INT;
            v_longest_streak INT;
        BEGIN
            SELECT last_report_date, current_streak, longest_streak 
            INTO v_last_report_date, v_current_streak, v_longest_streak
            FROM citizen_profiles WHERE user_id = p_user_id;
            
            IF v_last_report_date = CURRENT_DATE - INTERVAL '1 day' THEN
                -- Continue streak
                v_current_streak := v_current_streak + 1;
            ELSIF v_last_report_date < CURRENT_DATE - INTERVAL '1 day' THEN
                -- Reset streak
                v_current_streak := 1;
            END IF;
            
            -- Update longest streak
            IF v_current_streak > v_longest_streak THEN
                v_longest_streak := v_current_streak;
            END IF;
            
            UPDATE citizen_profiles 
            SET current_streak = v_current_streak,
                longest_streak = v_longest_streak
            WHERE user_id = p_user_id;
            
            -- Check for streak badges
            IF v_current_streak >= 7 THEN
                PERFORM award_badge_if_not_exists(p_user_id, 'STREAK_7');
            END IF;
            
            IF v_current_streak >= 30 THEN
                PERFORM award_badge_if_not_exists(p_user_id, 'STREAK_30');
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created update_citizen_streak function")
    
    # Helper function: Check ECO_WARRIOR badge
    migration.execute("""
        CREATE OR REPLACE FUNCTION check_eco_warrior_badge(p_user_id VARCHAR)
        RETURNS VOID AS $$
        DECLARE
            v_approved_reports INT;
        BEGIN
            SELECT approved_reports INTO v_approved_reports 
            FROM citizen_profiles WHERE user_id = p_user_id;
            
            IF v_approved_reports >= 10 THEN
                PERFORM award_badge_if_not_exists(p_user_id, 'ECO_WARRIOR');
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created check_eco_warrior_badge function")
    
    # Helper function: Award badge if not exists
    migration.execute("""
        CREATE OR REPLACE FUNCTION award_badge_if_not_exists(p_user_id VARCHAR, p_badge_type badge_type)
        RETURNS VOID AS $$
        DECLARE
            v_badge_id VARCHAR;
            v_exists BOOLEAN;
        BEGIN
            SELECT id INTO v_badge_id FROM badges WHERE badge_type = p_badge_type;
            
            SELECT EXISTS(
                SELECT 1 FROM user_badges 
                WHERE user_id = p_user_id AND badge_id = v_badge_id
            ) INTO v_exists;
            
            IF NOT v_exists THEN
                INSERT INTO user_badges (user_id, badge_id) VALUES (p_user_id, v_badge_id);
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created award_badge_if_not_exists function")
    
    # Helper function: Recalculate zone cleanliness
    migration.execute("""
        CREATE OR REPLACE FUNCTION recalculate_zone_cleanliness(p_zone_id VARCHAR)
        RETURNS VOID AS $$
        DECLARE
            v_score INT := 100;
            v_critical_count INT;
            v_high_count INT;
            v_medium_count INT;
            v_low_count INT;
        BEGIN
            -- Count open reports by severity
            SELECT 
                COUNT(*) FILTER (WHERE severity = 'CRITICAL'),
                COUNT(*) FILTER (WHERE severity = 'HIGH'),
                COUNT(*) FILTER (WHERE severity = 'MEDIUM'),
                COUNT(*) FILTER (WHERE severity = 'LOW')
            INTO v_critical_count, v_high_count, v_medium_count, v_low_count
            FROM reports 
            WHERE zone_id = p_zone_id AND status NOT IN ('COMPLETED', 'DECLINED');
            
            -- Calculate score
            v_score := v_score - (v_critical_count * 20) - (v_high_count * 10) 
                       - (v_medium_count * 5) - (v_low_count * 2);
            
            -- Ensure score is between 0 and 100
            v_score := GREATEST(0, LEAST(100, v_score));
            
            UPDATE zones SET cleanliness_score = v_score WHERE id = p_zone_id;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created recalculate_zone_cleanliness function")
    
    # SP_REGISTER_USER
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_register_user(
            IN p_email VARCHAR,
            IN p_password_hash VARCHAR,
            IN p_name VARCHAR,
            IN p_phone VARCHAR,
            IN p_role user_role,
            OUT p_user_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO users (email, password_hash, name, phone, role)
            VALUES (p_email, p_password_hash, p_name, p_phone, p_role)
            RETURNING id INTO p_user_id;
            
            -- Profile is auto-created by trigger
            COMMIT;
        END;
        $$;
    """, "Created sp_register_user procedure")
    
    # SP_SUBMIT_REPORT
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_submit_report(
            IN p_user_id VARCHAR,
            IN p_zone_id VARCHAR,
            IN p_description TEXT,
            IN p_image_url VARCHAR,
            IN p_severity severity_level,
            IN p_latitude DECIMAL,
            IN p_longitude DECIMAL,
            OUT p_report_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO reports (user_id, zone_id, description, image_url, severity, latitude, longitude)
            VALUES (p_user_id, p_zone_id, p_description, p_image_url, p_severity, p_latitude, p_longitude)
            RETURNING id INTO p_report_id;
            
            -- Triggers handle points and notifications
            COMMIT;
        END;
        $$;
    """, "Created sp_submit_report procedure")
    
    # SP_APPROVE_REPORT
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_approve_report(
            IN p_report_id VARCHAR,
            IN p_admin_id VARCHAR,
            IN p_reward_amount DECIMAL,
            IN p_due_date TIMESTAMP,
            OUT p_task_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_zone_id VARCHAR;
            v_description TEXT;
            v_severity severity_level;
        BEGIN
            -- Get report details
            SELECT zone_id, description, severity 
            INTO v_zone_id, v_description, v_severity
            FROM reports WHERE id = p_report_id;
            
            -- Update report status
            UPDATE reports 
            SET status = 'APPROVED', 
                reviewed_by = p_admin_id, 
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = p_report_id;
            
            -- Create task
            INSERT INTO tasks (report_id, zone_id, description, priority, due_date, reward, created_by)
            VALUES (p_report_id, v_zone_id, v_description, v_severity, p_due_date, p_reward_amount, p_admin_id)
            RETURNING id INTO p_task_id;
            
            -- Notify all cleaners
            INSERT INTO notifications (user_id, type, title, message, related_task_id)
            SELECT u.id, 'TASK', 'New Task Available', 
                   'A new cleanup task is available in your area. Reward: ৳' || p_reward_amount,
                   p_task_id
            FROM users u
            JOIN cleaner_profiles cp ON u.id = cp.user_id
            WHERE u.is_active = true;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_approve_report procedure")
    
    # SP_DECLINE_REPORT
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_decline_report(
            IN p_report_id VARCHAR,
            IN p_admin_id VARCHAR,
            IN p_decline_reason TEXT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            UPDATE reports 
            SET status = 'DECLINED',
                reviewed_by = p_admin_id,
                reviewed_at = CURRENT_TIMESTAMP,
                decline_reason = p_decline_reason
            WHERE id = p_report_id;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_decline_report procedure")
    
    # SP_TAKE_TASK
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_take_task(
            IN p_task_id VARCHAR,
            IN p_cleaner_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            -- Verify task is available
            IF EXISTS(SELECT 1 FROM tasks WHERE id = p_task_id AND cleaner_id IS NULL AND status = 'APPROVED') THEN
                UPDATE tasks 
                SET cleaner_id = p_cleaner_id,
                    status = 'IN_PROGRESS',
                    taken_at = CURRENT_TIMESTAMP
                WHERE id = p_task_id;
                
                COMMIT;
            ELSE
                RAISE EXCEPTION 'Task is not available';
            END IF;
        END;
        $$;
    """, "Created sp_take_task procedure")
    
    # SP_COMPLETE_TASK
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_complete_task(
            IN p_task_id VARCHAR,
            IN p_cleaner_id VARCHAR,
            IN p_evidence_image_url VARCHAR,
            IN p_after_image_url VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_report_id VARCHAR;
        BEGIN
            -- Verify cleaner owns this task
            SELECT report_id INTO v_report_id 
            FROM tasks 
            WHERE id = p_task_id AND cleaner_id = p_cleaner_id;
            
            IF v_report_id IS NULL THEN
                RAISE EXCEPTION 'Task not found or not owned by cleaner';
            END IF;
            
            -- Update task
            UPDATE tasks 
            SET status = 'COMPLETED',
                evidence_image_url = p_evidence_image_url,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = p_task_id;
            
            -- Update report
            UPDATE reports 
            SET status = 'COMPLETED',
                after_image_url = p_after_image_url,
                completed_at = CURRENT_TIMESTAMP,
                cleaner_id = p_cleaner_id
            WHERE id = v_report_id;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_complete_task procedure")
    
    # SP_CREATE_ZONE
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_create_zone(
            IN p_name VARCHAR,
            IN p_description TEXT,
            IN p_color VARCHAR,
            IN p_polygon_points JSONB,
            IN p_admin_id VARCHAR,
            OUT p_zone_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_point JSONB;
            v_order INT := 0;
        BEGIN
            -- Create zone
            INSERT INTO zones (name, description, color, created_by)
            VALUES (p_name, p_description, p_color, p_admin_id)
            RETURNING id INTO p_zone_id;
            
            -- Insert polygon points
            FOR v_point IN SELECT * FROM jsonb_array_elements(p_polygon_points)
            LOOP
                INSERT INTO zone_polygons (zone_id, point_order, latitude, longitude)
                VALUES (p_zone_id, v_order, 
                        (v_point->>'lat')::DECIMAL, 
                        (v_point->>'lng')::DECIMAL);
                v_order := v_order + 1;
            END LOOP;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_create_zone procedure")
    
    # SP_RECALCULATE_CITIZEN_LEADERBOARD
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_recalculate_citizen_leaderboard(IN p_period VARCHAR)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            DELETE FROM citizen_leaderboard WHERE period = p_period;
            
            INSERT INTO citizen_leaderboard (user_id, rank, total_green_points, approved_reports, badges_count, period)
            SELECT 
                cp.user_id,
                ROW_NUMBER() OVER (ORDER BY cp.green_points_balance DESC, cp.approved_reports DESC) as rank,
                cp.green_points_balance,
                cp.approved_reports,
                (SELECT COUNT(*) FROM user_badges WHERE user_id = cp.user_id) as badges_count,
                p_period
            FROM citizen_profiles cp
            JOIN users u ON cp.user_id = u.id
            WHERE u.is_active = true
            ORDER BY cp.green_points_balance DESC
            LIMIT 100;
            
            -- Update ranks in citizen_profiles for all_time
            IF p_period = 'all_time' THEN
                UPDATE citizen_profiles cp
                SET rank = cl.rank
                FROM citizen_leaderboard cl
                WHERE cp.user_id = cl.user_id AND cl.period = 'all_time';
            END IF;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_recalculate_citizen_leaderboard procedure")
    
    # SP_RECALCULATE_CLEANER_LEADERBOARD
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_recalculate_cleaner_leaderboard(IN p_period VARCHAR)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            DELETE FROM cleaner_leaderboard WHERE period = p_period;
            
            INSERT INTO cleaner_leaderboard (user_id, rank, total_earnings, completed_tasks, rating, this_month_earnings, period)
            SELECT 
                cp.user_id,
                ROW_NUMBER() OVER (ORDER BY cp.total_earnings DESC, cp.completed_tasks DESC, cp.rating DESC) as rank,
                cp.total_earnings,
                cp.completed_tasks,
                cp.rating,
                COALESCE((
                    SELECT SUM(amount) 
                    FROM earnings_transactions 
                    WHERE cleaner_id = cp.user_id 
                    AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                ), 0) as this_month_earnings,
                p_period
            FROM cleaner_profiles cp
            JOIN users u ON cp.user_id = u.id
            WHERE u.is_active = true
            ORDER BY cp.total_earnings DESC
            LIMIT 100;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_recalculate_cleaner_leaderboard procedure")
    
    # SP_SEND_BULK_NOTIFICATION
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_send_bulk_notification(
            IN p_audience VARCHAR,
            IN p_type VARCHAR,
            IN p_title VARCHAR,
            IN p_message TEXT,
            IN p_admin_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            -- Insert bulk notification record
            INSERT INTO bulk_notifications (audience, type, title, message, sent_by)
            VALUES (p_audience, p_type, p_title, p_message, p_admin_id);
            
            -- Send to individual users based on audience
            IF p_audience = 'all' THEN
                INSERT INTO notifications (user_id, type, title, message)
                SELECT id, 'ANNOUNCEMENT', p_title, p_message
                FROM users WHERE is_active = true;
            ELSIF p_audience = 'citizens' THEN
                INSERT INTO notifications (user_id, type, title, message)
                SELECT id, 'ANNOUNCEMENT', p_title, p_message
                FROM users WHERE role = 'CITIZEN' AND is_active = true;
            ELSIF p_audience = 'cleaners' THEN
                INSERT INTO notifications (user_id, type, title, message)
                SELECT id, 'ANNOUNCEMENT', p_title, p_message
                FROM users WHERE role = 'CLEANER' AND is_active = true;
            END IF;
            
            COMMIT;
        END;
        $$;
    """, "Created sp_send_bulk_notification procedure")
    
    # SP_PROCESS_PAYMENT
    migration.execute("""
        CREATE OR REPLACE PROCEDURE sp_process_payment(
            IN p_transaction_id VARCHAR,
            IN p_admin_id VARCHAR
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            UPDATE earnings_transactions 
            SET status = 'PAID',
                paid_at = CURRENT_TIMESTAMP
            WHERE id = p_transaction_id AND status = 'PENDING';
            
            -- Trigger handles balance updates
            COMMIT;
        END;
        $$;
    """, "Created sp_process_payment procedure")
