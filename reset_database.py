"""
Reset Database Script
This script completely drops and recreates the database schema.
WARNING: This will delete EVERYTHING including system configuration.
"""

from models import db_connection, setup_database
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    """Drop all tables and recreate the database schema"""
    
    print("\n" + "="*70)
    print("RESETTING DATABASE - Dropping and recreating all tables")
    print("="*70 + "\n")
    
    try:
        with db_connection.get_cursor(commit=True) as cursor:
            print("Dropping all tables, functions, and triggers...")
            
            # Drop all tables in correct order (reverse of creation)
            tables = [
                'bulk_notifications',
                'activity_logs',
                'alerts',
                'cleanup_reviews',
                'earnings_transactions',
                'green_points_transactions',
                'notifications',
                'user_badges',
                'badges',
                'green_points_config',
                'zone_polygons',
                'zones',
                'tasks',
                'reports',
                'citizen_leaderboard',
                'cleaner_leaderboard',
                'admin_profiles',
                'cleaner_profiles',
                'citizen_profiles',
                'users',
            ]
            
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"✓ Dropped table: {table}")
            
            # Drop sequences
            sequences = [
                'reports_id_seq',
                'tasks_id_seq',
                'zones_id_seq',
                'notifications_id_seq',
                'alerts_id_seq',
            ]
            
            for seq in sequences:
                cursor.execute(f"DROP SEQUENCE IF EXISTS {seq} CASCADE;")
                print(f"✓ Dropped sequence: {seq}")
            
            # Drop functions and procedures
            print("\nDropping functions and procedures...")
            cursor.execute("""
                DO $$ 
                DECLARE 
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT proname, oidvectortypes(proargtypes) as args
                              FROM pg_proc INNER JOIN pg_namespace ns ON (pg_proc.pronamespace = ns.oid)
                              WHERE ns.nspname = 'public' AND proname LIKE 'sp_%') 
                    LOOP
                        EXECUTE 'DROP PROCEDURE IF EXISTS ' || r.proname || '(' || r.args || ') CASCADE';
                    END LOOP;
                    
                    FOR r IN (SELECT proname, oidvectortypes(proargtypes) as args
                              FROM pg_proc INNER JOIN pg_namespace ns ON (pg_proc.pronamespace = ns.oid)
                              WHERE ns.nspname = 'public' AND proname LIKE 'fn_%') 
                    LOOP
                        EXECUTE 'DROP FUNCTION IF EXISTS ' || r.proname || '(' || r.args || ') CASCADE';
                    END LOOP;
                END $$;
            """)
            print("✓ Dropped all functions and procedures")
            
        print("\n" + "="*70)
        print("DATABASE DROPPED SUCCESSFULLY!")
        print("="*70 + "\n")
        
        # Recreate database schema
        print("Recreating database schema...\n")
        setup_database()
        
        print("\n" + "="*70)
        print("DATABASE RESET COMPLETE!")
        print("="*70)
        print("\nThe database has been completely reset with:")
        print("  ✓ Fresh schema")
        print("  ✓ System configuration (badges, points config)")
        print("  ✓ System user")
        print("  ✓ All triggers and functions")
        print("\nNo user data - ready for testing!")
        print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error resetting database: {str(e)}")
        print("Rolling back changes...\n")
        raise


if __name__ == '__main__':
    # Confirm before resetting
    print("\n⚠️  WARNING: This will COMPLETELY RESET the database!")
    print("ALL data including system configuration will be deleted and recreated.\n")
    
    confirm = input("Are you sure you want to continue? Type 'RESET' to confirm: ")
    
    if confirm == 'RESET':
        db_connection.create_pool()
        try:
            reset_database()
        finally:
            db_connection.close_pool()
    else:
        print("\n❌ Database reset cancelled.\n")
