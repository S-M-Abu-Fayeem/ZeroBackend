"""
ZERO WASTE MANAGEMENT - MOCK DATA GENERATOR
Generates comprehensive test data for all database tables
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt
from db_helper import DatabaseConnection, DatabaseConfig

load_dotenv()

# Database configuration
db_config = DatabaseConfig(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'zero_waste_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'password')
)
db_connection = DatabaseConnection(db_config, min_conn=2, max_conn=10)

# Sample data
DHAKA_ZONES = [
    "Dhanmondi", "Gulshan", "Banani", "Uttara", "Mirpur",
    "Mohammadpur", "Tejgaon", "Motijheel", "Old Dhaka", "Badda"
]

CITIZEN_NAMES = [
    "Rahim Ahmed", "Karim Hassan", "Fatima Khan", "Ayesha Rahman",
    "Shakib Islam", "Tamim Iqbal", "Mushfiqur Rahim", "Mahmudullah Riyad",
    "Taskin Ahmed", "Mustafizur Rahman", "Rubel Hossain", "Mehidy Hasan",
    "Liton Das", "Soumya Sarkar", "Sabbir Rahman"
]

CLEANER_NAMES = [
    "Abdul Karim", "Jamal Uddin", "Rafiq Mia", "Shamsul Haque",
    "Monir Hossain", "Kamal Ahmed", "Jalal Uddin", "Habib Rahman",
    "Aziz Mia", "Faruk Hossain"
]

ADMIN_NAMES = [
    "Dr. Nazrul Islam", "Eng. Farhan Ahmed", "Prof. Sultana Begum"
]

WASTE_TYPES = ["plastic", "organic", "paper", "metal", "glass", "electronic", "hazardous"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
REPORT_STATUSES = ["SUBMITTED", "APPROVED", "DECLINED", "IN_PROGRESS", "COMPLETED"]
TASK_STATUSES = ["APPROVED", "IN_PROGRESS", "COMPLETED"]

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def random_date(start_days_ago=90, end_days_ago=0):
    """Generate random datetime within range"""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)

def clear_all_data():
    """Clear all existing data from database"""
    print("\n" + "="*60)
    print("CLEARING ALL EXISTING DATA")
    print("="*60)
    
    tables = [
        "user_sessions", "activity_logs", "cleaner_leaderboard", "citizen_leaderboard",
        "earnings_transactions", "bulk_notifications", "notifications", "alerts",
        "green_points_config", "green_points_transactions", "user_badges",
        # Skip badges - they are needed by triggers
        "tasks", "cleanup_reviews", "cleanup_remaining_issues", "cleanup_waste_removed",
        "cleanup_comparisons", "special_equipment", "waste_compositions", "waste_analyses",
        "reports", "zone_polygons", "zones", "admin_profiles", "cleaner_profiles",
        "citizen_profiles", "users"
    ]
    
    with db_connection.get_cursor(commit=True) as cursor:
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  - Cleared {table}")
    
    print("\n[SUCCESS] All data cleared (badges preserved for triggers)")

def create_users():
    """Create users with different roles"""
    print("\n" + "="*60)
    print("CREATING USERS")
    print("="*60)
    
    users = []
    
    # Create citizens
    for i, name in enumerate(CITIZEN_NAMES, 1):
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, phone, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"citizen{i}@test.com",
                hash_password("password123"),
                name,
                f"01{random.randint(700000000, 799999999)}",
                "CITIZEN",
                True
            ))
            user_id = cursor.fetchone()['id']
            users.append(('CITIZEN', user_id, name))
            print(f"  - Created citizen: {name}")
    
    # Create cleaners
    for i, name in enumerate(CLEANER_NAMES, 1):
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, phone, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"cleaner{i}@test.com",
                hash_password("password123"),
                name,
                f"01{random.randint(700000000, 799999999)}",
                "CLEANER",
                True
            ))
            user_id = cursor.fetchone()['id']
            users.append(('CLEANER', user_id, name))
            print(f"  - Created cleaner: {name}")
    
    # Create admins
    for i, name in enumerate(ADMIN_NAMES, 1):
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, phone, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"admin{i}@test.com",
                hash_password("admin123"),
                name,
                f"01{random.randint(700000000, 799999999)}",
                "ADMIN",
                True
            ))
            user_id = cursor.fetchone()['id']
            users.append(('ADMIN', user_id, name))
            print(f"  - Created admin: {name}")
    
    print(f"\n[SUCCESS] Created {len(users)} users")
    return users

def update_profiles(users):
    """Update auto-created profiles with mock data"""
    print("\n" + "="*60)
    print("UPDATING PROFILES WITH MOCK DATA")
    print("="*60)
    
    for role, user_id, name in users:
        if role == 'CITIZEN':
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE citizen_profiles 
                    SET green_points_balance = %s, 
                        total_reports = %s, 
                        approved_reports = %s, 
                        current_streak = %s, 
                        longest_streak = %s
                    WHERE user_id = %s
                """, (random.randint(50, 500), random.randint(5, 30), random.randint(3, 25), 
                      random.randint(0, 10), random.randint(0, 15), user_id))
            print(f"  - Updated citizen profile: {name}")
        
        elif role == 'CLEANER':
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE cleaner_profiles 
                    SET total_earnings = %s, 
                        completed_tasks = %s, 
                        rating = %s, 
                        total_ratings = %s
                    WHERE user_id = %s
                """, (round(random.uniform(5000, 50000), 2), random.randint(10, 100), 
                      round(random.uniform(3.5, 5.0), 2), random.randint(5, 50), user_id))
            print(f"  - Updated cleaner profile: {name}")
        
        elif role == 'ADMIN':
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE admin_profiles 
                    SET department = %s, 
                        role_title = %s
                    WHERE user_id = %s
                """, (random.choice(["Operations", "Monitoring", "Management"]), 
                      random.choice(["Super Admin", "Zone Manager", "Monitor"]), user_id))
            print(f"  - Updated admin profile: {name}")
    
    print(f"\n[SUCCESS] Updated {len(users)} profiles")

def create_zones():
    """Create zones"""
    print("\n" + "="*60)
    print("CREATING ZONES")
    print("="*60)
    
    zones = []
    for zone_name in DHAKA_ZONES:
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO zones (name, description, cleanliness_score)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                zone_name,
                f"{zone_name} area of Dhaka city",
                random.randint(60, 95)
            ))
            zone_id = cursor.fetchone()['id']
            zones.append((zone_id, zone_name))
            print(f"  - Created zone: {zone_name}")
    
    print(f"\n[SUCCESS] Created {len(zones)} zones")
    return zones

def create_reports(users, zones):
    """Create waste reports"""
    print("\n" + "="*60)
    print("CREATING REPORTS")
    print("="*60)
    
    citizens = [u for u in users if u[0] == 'CITIZEN']
    reports = []
    
    for i in range(50):
        citizen = random.choice(citizens)
        zone = random.choice(zones)
        severity = random.choice(SEVERITIES)
        status = random.choice(REPORT_STATUSES)
        created_at = random_date(60, 0)
        
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO reports (user_id, zone_id, description, severity, status, 
                                   latitude, longitude, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                citizen[1],
                zone[0],
                f"Large amount of {random.choice(WASTE_TYPES)} waste found in {zone[1]} area. Immediate attention needed.",
                severity,
                status,
                round(random.uniform(23.7, 23.9), 6),
                round(random.uniform(90.3, 90.5), 6),
                f"https://example.com/images/report_{i+1}.jpg",
                created_at
            ))
            report_id = cursor.fetchone()['id']
            reports.append((report_id, status, created_at))
    
    print(f"\n[SUCCESS] Created {len(reports)} reports")
    return reports

def create_waste_analyses(reports):
    """Create AI waste analyses"""
    print("\n" + "="*60)
    print("CREATING WASTE ANALYSES")
    print("="*60)
    
    count = 0
    for report_id, status, created_at in reports:
        if status in ['APPROVED', 'IN_PROGRESS', 'COMPLETED']:
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO waste_analyses (report_id, description, severity, estimated_volume,
                                              environmental_impact, health_hazard, estimated_cleanup_time, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    report_id,
                    f"AI analysis of waste composition and severity",
                    random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                    f"{random.randint(10, 500)} kg",
                    random.choice(['LOW', 'MODERATE', 'HIGH', 'SEVERE']),
                    random.choice([True, False]),
                    f"{random.randint(30, 240)} minutes",
                    random.randint(75, 99)
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} waste analyses")

def create_tasks(reports, users, zones):
    """Create cleanup tasks"""
    print("\n" + "="*60)
    print("CREATING TASKS")
    print("="*60)
    
    cleaners = [u for u in users if u[0] == 'CLEANER']
    count = 0
    
    for report_id, status, created_at in reports:
        if status in ['APPROVED', 'IN_PROGRESS', 'COMPLETED']:
            cleaner = random.choice(cleaners)
            zone = random.choice(zones)
            task_status = 'COMPLETED' if status == 'COMPLETED' else status
            
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO tasks (report_id, zone_id, cleaner_id, description, status, priority,
                                     due_date, reward, created_at, taken_at, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    report_id,
                    zone[0],
                    cleaner[1] if task_status != 'APPROVED' else None,
                    f"Clean up waste in {zone[1]} area",
                    task_status,
                    random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                    created_at + timedelta(days=random.randint(1, 7)),
                    round(random.uniform(500, 5000), 2),
                    created_at,
                    created_at + timedelta(hours=random.randint(1, 24)) if task_status != 'APPROVED' else None,
                    created_at + timedelta(days=random.randint(1, 3)) if task_status == 'COMPLETED' else None
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} tasks")

def create_cleanup_reviews(reports, users):
    """Create cleanup reviews"""
    print("\n" + "="*60)
    print("CREATING CLEANUP REVIEWS")
    print("="*60)
    
    citizens = [u for u in users if u[0] == 'CITIZEN']
    cleaners = [u for u in users if u[0] == 'CLEANER']
    count = 0
    
    for report_id, status, created_at in reports:
        if status == 'COMPLETED':
            citizen = random.choice(citizens)
            cleaner = random.choice(cleaners)
            
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO cleanup_reviews (report_id, citizen_id, cleaner_id, rating, comment)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    report_id,
                    citizen[1],
                    cleaner[1],
                    random.randint(3, 5),
                    random.choice([
                        "Excellent work! Area is much cleaner now.",
                        "Good job, but some waste still remains.",
                        "Very satisfied with the cleanup.",
                        "Area looks great after cleanup!"
                    ])
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} cleanup reviews")

def create_badges_and_awards(users):
    """Award badges to users (badges already exist from schema)"""
    print("\n" + "="*60)
    print("AWARDING ADDITIONAL BADGES TO USERS")
    print("="*60)
    
    # Get existing badge IDs
    with db_connection.get_cursor() as cursor:
        cursor.execute("SELECT id FROM badges")
        badge_ids = [row['id'] for row in cursor.fetchall()]
    
    if not badge_ids:
        print("  [WARNING] No badges found in database. Run schema.sql first.")
        return
    
    print(f"  Found {len(badge_ids)} badges in database")
    
    # Award random badges to citizens (in addition to auto-awarded ones)
    citizens = [u for u in users if u[0] == 'CITIZEN']
    count = 0
    for citizen in citizens:
        num_badges = random.randint(0, 2)  # Award 0-2 additional badges
        awarded_badges = random.sample(badge_ids, min(num_badges, len(badge_ids)))
        for badge_id in awarded_badges:
            try:
                with db_connection.get_cursor(commit=True) as cursor:
                    cursor.execute("""
                        INSERT INTO user_badges (user_id, badge_id, earned_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, badge_id) DO NOTHING
                    """, (citizen[1], badge_id, random_date(30, 0)))
                    count += 1
            except:
                pass  # Skip if already awarded by trigger
    
    print(f"\n[SUCCESS] Awarded {count} additional badges to users")

def create_green_points_transactions(users):
    """Create green points transactions"""
    print("\n" + "="*60)
    print("CREATING GREEN POINTS TRANSACTIONS")
    print("="*60)
    
    citizens = [u for u in users if u[0] == 'CITIZEN']
    count = 0
    
    for citizen in citizens:
        num_transactions = random.randint(5, 15)
        for _ in range(num_transactions):
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO green_points_transactions (user_id, green_points, reason)
                    VALUES (%s, %s, %s)
                """, (
                    citizen[1],
                    random.randint(5, 50),
                    random.choice(['Report submitted', 'Report approved', 'Badge earned', 'Monthly bonus'])
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} green points transactions")

def create_earnings_transactions(users, zones):
    """Create earnings transactions for cleaners"""
    print("\n" + "="*60)
    print("CREATING EARNINGS TRANSACTIONS")
    print("="*60)
    
    cleaners = [u for u in users if u[0] == 'CLEANER']
    count = 0
    
    # First create some tasks to reference
    task_ids = []
    for cleaner in cleaners:
        num_tasks = random.randint(3, 8)
        for _ in range(num_tasks):
            zone = random.choice(zones)
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO tasks (zone_id, cleaner_id, description, status, priority, due_date, reward)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    zone[0],
                    cleaner[1],
                    f"Cleanup task in {zone[1]}",
                    'COMPLETED',
                    random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                    datetime.now() + timedelta(days=7),
                    round(random.uniform(500, 5000), 2)
                ))
                task_ids.append((cursor.fetchone()['id'], cleaner[1]))
    
    # Create earnings transactions
    for task_id, cleaner_id in task_ids:
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO earnings_transactions (cleaner_id, task_id, amount, status)
                VALUES (%s, %s, %s, %s)
            """, (
                cleaner_id,
                task_id,
                round(random.uniform(500, 5000), 2),
                random.choice(['PENDING', 'PENDING', 'PAID'])
            ))
            count += 1
    
    print(f"\n[SUCCESS] Created {count} earnings transactions")

def create_notifications(users):
    """Create notifications"""
    print("\n" + "="*60)
    print("CREATING NOTIFICATIONS")
    print("="*60)
    
    count = 0
    for role, user_id, name in users:
        num_notifications = random.randint(3, 10)
        for _ in range(num_notifications):
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO notifications (user_id, type, title, message, is_read)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    random.choice(['POINTS', 'BADGE', 'REPORT', 'TASK', 'ALERT', 'ANNOUNCEMENT']),
                    random.choice(['New Report', 'Task Assigned', 'Payment Received', 'Badge Earned']),
                    random.choice(['You have a new notification', 'Check your dashboard', 'Action required']),
                    random.choice([True, False])
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} notifications")

def create_alerts(zones):
    """Create zone alerts"""
    print("\n" + "="*60)
    print("CREATING ALERTS")
    print("="*60)
    
    count = 0
    for zone_id, zone_name in zones[:5]:  # Create alerts for first 5 zones
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO alerts (source, zone_id, severity, status, message)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                random.choice(['AI', 'CITIZEN']),
                zone_id,
                random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                random.choice(['OPEN', 'RESOLVED']),
                f"Cleanliness alert in {zone_name} area - attention needed"
            ))
            count += 1
    
    print(f"\n[SUCCESS] Created {count} alerts")

def create_leaderboards(users):
    """Create leaderboard entries"""
    print("\n" + "="*60)
    print("CREATING LEADERBOARDS")
    print("="*60)
    
    citizens = [u for u in users if u[0] == 'CITIZEN']
    cleaners = [u for u in users if u[0] == 'CLEANER']
    
    # Citizen leaderboard
    for period in ['weekly', 'monthly', 'all_time']:
        for rank, citizen in enumerate(citizens, 1):
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO citizen_leaderboard (user_id, period, rank, total_green_points,
                                                    approved_reports, badges_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    citizen[1],
                    period,
                    rank,
                    random.randint(50, 500),
                    random.randint(5, 30),
                    random.randint(0, 5)
                ))
    
    # Cleaner leaderboard
    for period in ['weekly', 'monthly', 'all_time']:
        for rank, cleaner in enumerate(cleaners, 1):
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO cleaner_leaderboard (user_id, period, rank, total_earnings,
                                                    completed_tasks, rating, this_month_earnings)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    cleaner[1],
                    period,
                    rank,
                    round(random.uniform(5000, 50000), 2),
                    random.randint(10, 100),
                    round(random.uniform(3.5, 5.0), 2),
                    round(random.uniform(1000, 10000), 2)
                ))
    
    print(f"\n[SUCCESS] Created leaderboard entries")

def create_activity_logs(users):
    """Create activity logs"""
    print("\n" + "="*60)
    print("CREATING ACTIVITY LOGS")
    print("="*60)
    
    actions = ['LOGIN', 'LOGOUT', 'CREATE_REPORT', 'UPDATE_PROFILE', 'COMPLETE_TASK', 'VIEW_DASHBOARD']
    count = 0
    
    for role, user_id, name in users:
        num_logs = random.randint(10, 30)
        for _ in range(num_logs):
            action = random.choice(actions)
            with db_connection.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO activity_logs (user_id, action, entity_type, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    action,
                    random.choice(['report', 'task', 'profile', 'zone', None]),
                    f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                        'Mozilla/5.0 (Android 13) Mobile Safari/537.36',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Safari/604.1'
                    ])
                ))
                count += 1
    
    print(f"\n[SUCCESS] Created {count} activity logs")

def verify_data():
    """Verify all mock data was inserted correctly"""
    print("\n" + "="*60)
    print("VERIFYING MOCK DATA")
    print("="*60)
    
    checks = [
        ("Users", "SELECT role, COUNT(*) as count FROM users GROUP BY role ORDER BY role"),
        ("Zones", "SELECT COUNT(*) as count FROM zones"),
        ("Reports", "SELECT status, COUNT(*) as count FROM reports GROUP BY status ORDER BY status"),
        ("Tasks", "SELECT COUNT(*) as count FROM tasks"),
        ("Waste Analyses", "SELECT COUNT(*) as count FROM waste_analyses"),
        ("Cleanup Reviews", "SELECT COUNT(*) as count FROM cleanup_reviews"),
        ("Badges", "SELECT COUNT(*) as count FROM badges"),
        ("User Badges", "SELECT COUNT(*) as count FROM user_badges"),
        ("Green Points Transactions", "SELECT COUNT(*) as count FROM green_points_transactions"),
        ("Earnings Transactions", "SELECT COUNT(*) as count FROM earnings_transactions"),
        ("Notifications", "SELECT COUNT(*) as count FROM notifications"),
        ("Alerts", "SELECT COUNT(*) as count FROM alerts"),
        ("Citizen Leaderboard", "SELECT COUNT(*) as count FROM citizen_leaderboard"),
        ("Cleaner Leaderboard", "SELECT COUNT(*) as count FROM cleaner_leaderboard"),
        ("Activity Logs", "SELECT COUNT(*) as count FROM activity_logs"),
    ]
    
    print("\nData Counts:\n")
    
    with db_connection.get_cursor() as cursor:
        for name, query in checks:
            cursor.execute(query)
            results = cursor.fetchall()
            
            if "GROUP BY" in query:
                print(f"  {name}:")
                for row in results:
                    print(f"    - {row['role'] if 'role' in row else row['status']}: {row['count']}")
            else:
                count = results[0]['count']
                print(f"  {name}: {count}")
    
    print("\n" + "="*60)
    print("TEST CREDENTIALS")
    print("="*60)
    print("\n  Citizens: citizen1@test.com (password: password123)")
    print("  Cleaners: cleaner1@test.com (password: password123)")
    print("  Admins:   admin1@test.com   (password: admin123)")
    print("\n" + "="*60)

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("ZERO WASTE MANAGEMENT - MOCK DATA GENERATOR")
    print("="*60)
    
    # Create connection pool
    if not db_connection.create_pool():
        print("\n[ERROR] Failed to create database connection pool")
        return
    
    try:
        # Ask for confirmation
        response = input("\nClear all existing data first? (yes/no): ").strip().lower()
        if response == 'yes':
            clear_all_data()
        
        # Generate mock data
        users = create_users()
        # Profiles are auto-created by database trigger
        update_profiles(users)  # Update with mock data
        zones = create_zones()
        reports = create_reports(users, zones)
        create_waste_analyses(reports)
        create_tasks(reports, users, zones)
        create_cleanup_reviews(reports, users)
        create_badges_and_awards(users)
        create_green_points_transactions(users)
        create_earnings_transactions(users, zones)
        create_notifications(users)
        create_alerts(zones)
        create_leaderboards(users)
        create_activity_logs(users)
        
        # Verify data
        verify_data()
        
        print("\n" + "="*60)
        print("[SUCCESS] MOCK DATA GENERATION COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_connection.close_pool()

if __name__ == "__main__":
    main()
