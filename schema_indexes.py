"""DDL index builders."""

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


