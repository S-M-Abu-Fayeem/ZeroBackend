"""DDL stored procedure builders."""

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
                   'A new cleanup task is available in your area. Reward: à§³' || p_reward_amount,
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


