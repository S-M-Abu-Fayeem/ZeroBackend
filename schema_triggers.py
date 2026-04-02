"""DDL trigger builders."""

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
            
            -- Update streak (must be BEFORE updating last_report_date)
            PERFORM update_citizen_streak(NEW.user_id);
            
            -- Update citizen profile
            UPDATE citizen_profiles 
            SET total_reports = total_reports + 1,
                green_points_balance = green_points_balance + v_points,
                last_report_date = CURRENT_DATE
            WHERE user_id = NEW.user_id;
            
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
                        'You completed a task! Earnings: à§³' || NEW.reward || ' (pending)',
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
                        'Payment of à§³' || NEW.amount || ' has been processed.');
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



