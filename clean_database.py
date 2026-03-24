"""
Clean Database Script
This script removes all user data while keeping system configuration intact.
"""

from models import db_connection
from dotenv import load_dotenv

load_dotenv()

def clean_database():
    """Remove all user data from the database"""
    
    print("\n" + "="*70)
    print("CLEANING DATABASE - Removing all user data")
    print("="*70 + "\n")
    
    try:
        # Use autocommit mode to ensure each DELETE is committed immediately
        with db_connection.get_cursor(commit=True) as cursor:
            print("Cleaning user data in correct order...\n")
            
            # Delete data in correct order to respect foreign key constraints
            # Start with child tables first, then parent tables
            
            print("Step 1: Cleaning child tables...")
            child_tables = [
                ('user_sessions', 'User sessions'),
                ('activity_logs', 'Activity logs'),
                ('cleanup_remaining_issues', 'Cleanup remaining issues'),
                ('cleanup_waste_removed', 'Cleanup waste removed'),
                ('cleanup_comparisons', 'Cleanup comparisons'),
                ('special_equipment', 'Special equipment'),
                ('waste_compositions', 'Waste compositions'),
                ('waste_analyses', 'Waste analyses'),
                ('cleanup_reviews', 'Cleanup reviews'),
                ('earnings_transactions', 'Earnings transactions'),
                ('green_points_transactions', 'Green points transactions'),
                ('user_badges', 'User badges'),
                ('bulk_notifications', 'Bulk notifications'),
            ]
            
            for table, description in child_tables:
                try:
                    cursor.execute(f"DELETE FROM {table};")
                    print(f"  ✓ Cleaned {description}")
                except Exception as e:
                    print(f"  ⚠ Warning cleaning {description}: {str(e)}")
            
            print("\nStep 2: Cleaning notifications and alerts...")
            cursor.execute("DELETE FROM notifications;")
            print("  ✓ Cleaned Notifications")
            cursor.execute("DELETE FROM alerts;")
            print("  ✓ Cleaned Alerts")
            
            print("\nStep 3: Cleaning tasks...")
            cursor.execute("DELETE FROM tasks;")
            print("  ✓ Cleaned Tasks")
            
            print("\nStep 4: Cleaning reports...")
            cursor.execute("DELETE FROM reports;")
            print("  ✓ Cleaned Reports")
            
            print("\nStep 5: Cleaning zones...")
            cursor.execute("DELETE FROM zone_polygons;")
            print("  ✓ Cleaned Zone polygons")
            cursor.execute("DELETE FROM zones;")
            print("  ✓ Cleaned Zones")
            
            print("\nStep 6: Cleaning leaderboards...")
            cursor.execute("DELETE FROM citizen_leaderboard;")
            print("  ✓ Cleaned Citizen leaderboard")
            cursor.execute("DELETE FROM cleaner_leaderboard;")
            print("  ✓ Cleaned Cleaner leaderboard")
            
            print("\nStep 7: Cleaning profiles...")
            cursor.execute("DELETE FROM admin_profiles;")
            print("  ✓ Cleaned Admin profiles")
            cursor.execute("DELETE FROM cleaner_profiles;")
            print("  ✓ Cleaned Cleaner profiles")
            cursor.execute("DELETE FROM citizen_profiles;")
            print("  ✓ Cleaned Citizen profiles")
            
            print("\nStep 8: Cleaning users (except system user)...")
            cursor.execute("DELETE FROM users WHERE id != '00000000-0000-0000-0000-000000000000';")
            print("  ✓ Cleaned Users (kept system user)")
            
            print("\n" + "="*70)
            print("DATABASE CLEANED SUCCESSFULLY!")
            print("="*70)
            print("\nSystem configuration kept:")
            print("  ✓ Badges (6 system badges)")
            print("  ✓ Green points config (8 action types)")
            print("  ✓ System user (for automated actions)")
            print("  ✓ Database schema (tables, triggers, functions)")
            print("\nAll user data removed:")
            print("  ✓ All users (except system user)")
            print("  ✓ All profiles (citizen, cleaner, admin)")
            print("  ✓ All reports, tasks, and zones")
            print("  ✓ All notifications, transactions, and reviews")
            print("  ✓ All leaderboards, user badges, and activity logs")
            print("\nYou can now test the system with fresh data!")
            print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error cleaning database: {str(e)}")
        print("Rolling back changes...\n")
        raise


if __name__ == '__main__':
    # Confirm before cleaning
    print("\n⚠️  WARNING: This will delete ALL user data from the database!")
    print("System configuration (badges, points config) will be kept.\n")
    
    confirm = input("Are you sure you want to continue? Type 'YES' to confirm: ")
    
    if confirm == 'YES':
        db_connection.create_pool()
        try:
            clean_database()
        finally:
            db_connection.close_pool()
    else:
        print("\n❌ Database cleaning cancelled.\n")
