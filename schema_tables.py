"""DDL table builders."""

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
            avatar_url TEXT,
            role user_role NOT NULL,
            address TEXT,
            language VARCHAR(5) DEFAULT 'en',
            email_notifications BOOLEAN DEFAULT true,
            push_notifications BOOLEAN DEFAULT true,
            notify_report_updates BOOLEAN DEFAULT true,
            notify_news_updates BOOLEAN DEFAULT false,
            is_superadmin BOOLEAN DEFAULT false,
            dark_mode BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id),
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
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
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
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created cleaner_profiles table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS admin_profiles (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_title VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
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
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
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
            image_url TEXT,
            severity severity_level NOT NULL,
            status report_status DEFAULT 'SUBMITTED',
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id),
            completed_at TIMESTAMP,
            cleaner_id VARCHAR(36) REFERENCES users(id),
            after_image_url TEXT,
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
            estimated_volume TEXT,
            environmental_impact environmental_impact,
            health_hazard BOOLEAN DEFAULT false,
            hazard_details TEXT,
            recommended_action TEXT,
            estimated_cleanup_time TEXT,
            confidence INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created waste_analyses table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS waste_compositions (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
            waste_type TEXT NOT NULL,
            percentage INT NOT NULL,
            recyclable BOOLEAN DEFAULT false
        );
    """, "Created waste_compositions table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS special_equipment (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            waste_analysis_id VARCHAR(36) NOT NULL REFERENCES waste_analyses(id) ON DELETE CASCADE,
            equipment_name TEXT NOT NULL
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created cleanup_comparisons table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS cleanup_waste_removed (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            cleanup_comparison_id VARCHAR(36) NOT NULL REFERENCES cleanup_comparisons(id) ON DELETE CASCADE,
            waste_type TEXT NOT NULL,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
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
            evidence_image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            taken_at TIMESTAMP,
            completed_at TIMESTAMP,
            updated_at TIMESTAMP,
            updated_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created tasks table")
    
    # Gamification
    migration.execute("""
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
    """, "Created badges table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            badge_id VARCHAR(36) NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            awarded_by VARCHAR(36) REFERENCES users(id),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id)
        );
    """, "Created green_points_transactions table")
    
    migration.execute("""
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
            created_by VARCHAR(36) REFERENCES users(id),
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id),
            paid_by VARCHAR(36) REFERENCES users(id)
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
            calculated_by VARCHAR(36) REFERENCES users(id),
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
            calculated_by VARCHAR(36) REFERENCES users(id),
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
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            table_name VARCHAR(100) NOT NULL,
            record_id VARCHAR(36) NOT NULL,
            action VARCHAR(50) NOT NULL,
            changed_by VARCHAR(36),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            old_data JSONB,
            new_data JSONB
        );
    """, "Created audit_log table")
    
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
        ('FIRST_REPORT', 'First Step', 'Submitted your first waste report', 'ðŸŒ±'),
        ('ECO_WARRIOR', 'Eco Warrior', 'Had 10 reports approved', 'ðŸŒ¿'),
        ('ZONE_CHAMPION', 'Zone Champion', 'Top reporter in a zone', 'ðŸ†'),
        ('STREAK_7', '7-Day Streak', 'Reported waste for 7 consecutive days', 'ðŸ”¥'),
        ('STREAK_30', '30-Day Streak', 'Reported waste for 30 consecutive days', 'â­'),
        ('TOP_REPORTER', 'Top Reporter', 'Ranked #1 on the leaderboard', 'ðŸ‘‘')
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
    
    # Insert system user for automated actions
    migration.execute("""
        INSERT INTO users (id, email, password_hash, name, role, is_active) VALUES
        ('00000000-0000-0000-0000-000000000000', 'system@zerowaste.internal', 
         'SYSTEM_USER_NO_LOGIN', 'System', 'ADMIN', true)
        ON CONFLICT (id) DO NOTHING;
    """, "Created system user for automated actions")


