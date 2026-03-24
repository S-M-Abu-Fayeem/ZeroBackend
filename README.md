# Zero Waste Management System - Backend

**Internal Developer Documentation**

This README is for backend developers setting up and working on this project. It covers project setup, architecture, file responsibilities, and how to extend the system.

---

## 📋 Quick Navigation

- [Project Setup](#-project-setup) - Get the project running on your machine
- [Project Architecture](#-project-architecture) - Understand the tech stack and design
- [File Responsibilities](#-file-responsibilities) - What each file does
- [Database Design](#-database-design) - Tables, triggers, procedures
- [Development Workflow](#-development-workflow) - Daily development tasks
- [Adding New Features](#-adding-new-features) - How to extend the system
- [Testing & Debugging](#-testing--debugging) - Common issues and solutions

---

## 🚀 Project Setup

### Prerequisites
- **PostgreSQL 12+** installed and running
- **Python 3.10+** (tested with 3.12, 3.13)
- **pip** package manager

### Step 1: Install Dependencies

```bash
cd ZeroBackend
pip install -r requirements.txt
```

**What gets installed:**
- `Flask` - Web framework
- `Flask-CORS` - Cross-origin resource sharing
- `psycopg2-binary` or `psycopg[binary]` - PostgreSQL adapter
- `psycopg-pool` - Connection pooling (Python 3.12+)
- `python-dotenv` - Environment variables
- `PyJWT` - JWT tokens
- `bcrypt` - Password hashing

### Step 2: Create Database User and Database

Open PostgreSQL command line:
```bash
psql -U postgres
```

Run these commands:
```sql
CREATE USER zero_user WITH PASSWORD 'zero_pass000';
CREATE DATABASE zero_db OWNER zero_user;
GRANT ALL PRIVILEGES ON DATABASE zero_db TO zero_user;
\c zero_db;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zero_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zero_user;
\q
```

### Step 3: Configure Environment

Copy the example file:
```bash
copy .env.example .env
```

Edit `.env`:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zero_db
DB_USER=zero_user
DB_PASSWORD=zero_pass000
SECRET_KEY=change-this-to-random-string-in-production
FLASK_ENV=development
FLASK_DEBUG=True
```

### Step 4: Initialize Database

Run the Python migrations in `models.py`:
```bash
python app.py
```

`app.py` calls `setup_database()` from `models.py` when `RERUN_MIGRATIONS=true` (default).

This creates:
- 25 tables
- 11 ENUM types
- 77 indexes
- 20 triggers
- 17 stored procedures
- 6 default badges

### Step 5: Load Test Data

```bash
python mock.py
```

Type `yes` when prompted. This creates:
- 28 users (15 citizens, 10 cleaners, 3 admins)
- 10 zones
- 50 reports
- Tasks, reviews, transactions, etc.

**Test credentials:**
- Citizens: `citizen1@test.com` / `password123`
- Cleaners: `cleaner1@test.com` / `password123`
- Admins: `admin1@test.com` / `admin123`

### Step 6: Start Server

```bash
python app.py
```

Server runs at `http://localhost:5000`

**Test it:**
```bash
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"email\":\"citizen1@test.com\",\"password\":\"password123\"}"
```

---

## 🏗️ Project Architecture

### Tech Stack
- **Backend:** Flask (Python)
- **Database:** PostgreSQL 12+
- **Auth:** JWT tokens
- **Password:** bcrypt hashing
- **DB Driver:** psycopg2 (Python <3.12) or psycopg3 (Python ≥3.12) - auto-detected

### Design Patterns

**1. Database-First Design**
- Business logic in triggers and stored procedures
- Keeps application code clean
- Ensures consistency across all clients

**2. Context Manager Pattern**
```python
with db_connection.get_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO ...")
    # Auto-commits on success, auto-rollbacks on error
```

**3. Dictionary-Based Rows**
```python
row = cursor.fetchone()
user_id = row['id']  # NOT row[0]
```

**4. Role-Based Access**
- `@token_required` - Needs valid JWT
- `@role_required('ADMIN')` - Needs specific role
- Roles: CITIZEN, CLEANER, ADMIN

---

## 📁 File Responsibilities

### Application Files

**`app.py`** - Main Entry Point
- Starts Flask server
- Registers API blueprints
- Configures CORS
- Initializes database pool
- **Run this to start the server**

**`auth.py`** - Authentication
- JWT token generation/validation
- Password hashing
- Login/register endpoints
- Decorators: `@token_required`, `@role_required`
- **Modify to change auth logic**

**`citizen.py`** - Citizen Endpoints
- `/api/citizen/profile` - Profile management
- `/api/citizen/stats` - User statistics
- **Add citizen features here**

**`cleaner.py`** - Cleaner Endpoints
- `/api/cleaner/profile` - Profile management
- `/api/cleaner/stats` - Earnings/tasks
- **Add cleaner features here**

**`admin.py`** - Admin Endpoints
- `/api/admin/users` - User management
- `/api/admin/profile` - Admin profile
- `/api/admin/stats` - System stats
- **Add admin features here**

### Database Files

**`db_helper.py`** - Database Utilities
- `DatabaseConfig` - Connection config
- `DatabaseConnection` - Pool management with context managers
- `QueryBuilder` - SQL query helpers
- `Model` - Base model class
- `Migration` - Schema utilities
- **Auto-detects Python version for driver**

**`models.py`** - Database Schema & Migrations ⭐
- **PRIMARY SCHEMA FILE**
- Defines all tables, indexes, triggers, procedures
- **Modify this for schema changes**

**`deliverables/schema.sql`** - SQL Export (Reference)
- Optional SQL deliverable snapshot
- Not used by runtime initialization

**Schema Checks**
- Use `psql` inspection commands (`\dt`, `\d <table>`, counts)
- Use API health endpoint `GET /api/health`

**`mock.py`** - Test Data Generator
- Generates realistic test data
- Includes verification
- **Run after schema changes**

### Config Files

**`.env`** - Environment Variables (DO NOT COMMIT)
- Database credentials
- JWT secret
- **Each developer has their own**

**`.env.example`** - Template
- Example environment file
- **Update when adding new vars**

**`requirements.txt`** - Dependencies
- Python packages
- **Update when adding packages**

**`.gitignore`** - Git Ignore
- Excludes .env, __pycache__, etc.

---

## 🗄️ Database Design

### Tables (25 Total)

**Core Users (4)**
- `users` - All users (email, password, role)
- `citizen_profiles` - Points, reports, streaks
- `cleaner_profiles` - Earnings, ratings
- `admin_profiles` - Department, role

**Zones (2)**
- `zones` - Service areas
- `zone_polygons` - Map boundaries

**Reports & Analysis (8)**
- `reports` - Waste reports
- `waste_analyses` - AI analysis
- `waste_compositions` - Waste breakdown
- `special_equipment` - Equipment needed
- `cleanup_comparisons` - Before/after
- `cleanup_waste_removed` - Waste removed
- `cleanup_remaining_issues` - Remaining issues
- `cleanup_reviews` - Citizen reviews

**Tasks (1)**
- `tasks` - Cleanup tasks

**Gamification (4)**
- `badges` - Achievement badges
- `user_badges` - Earned badges
- `green_points_transactions` - Points
- `green_points_config` - Point rules

**Notifications (3)**
- `alerts` - Zone alerts
- `notifications` - User notifications
- `bulk_notifications` - Announcements

**Payments (1)**
- `earnings_transactions` - Cleaner payments

**Leaderboards & Audit (4)**
- `citizen_leaderboard` - Top citizens
- `cleaner_leaderboard` - Top cleaners
- `activity_logs` - Audit trail
- `user_sessions` - Active sessions

### Key Features

**Automated Triggers (20)**
- Auto-create profiles on user registration
- Auto-award points on report submission/approval
- Auto-update stats on actions
- Auto-create earnings on task completion
- Auto-update ratings on reviews
- Auto-send notifications on badge awards

**Why triggers?** They ensure business logic always runs, even if you forget to call it.

**Stored Procedures (17)**
```sql
-- Leaderboards
SELECT * FROM calculate_citizen_leaderboard() LIMIT 10;
SELECT * FROM calculate_cleaner_leaderboard() LIMIT 10;

-- Statistics
SELECT * FROM get_zone_statistics('zone-id');
SELECT * FROM get_user_statistics('user-id');
SELECT * FROM get_admin_dashboard_stats();

-- Badges
SELECT award_badge('user-id', 'ECO_WARRIOR');
SELECT check_and_award_badges('user-id');

-- Maintenance
SELECT update_zone_cleanliness_score('zone-id');
SELECT cleanup_expired_sessions();
```

**Performance Indexes (77)**
- 10-20x faster queries
- Status + timestamp indexes
- Foreign key indexes
- Partial indexes for unread items

**Data Integrity**
- 38 foreign keys with CASCADE
- 11 ENUM types
- CHECK constraints
- NOT NULL constraints

### Database Connection Pattern

**ALWAYS use context managers:**

```python
# ✅ CORRECT
with db_connection.get_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO users ...")
    user_id = cursor.fetchone()['id']

# ❌ WRONG
cursor = db_connection.get_cursor()  # Returns context manager, not cursor!
```

**Dictionary access:**

```python
# ✅ CORRECT
row = cursor.fetchone()
user_id = row['id']
email = row['email']

# ❌ WRONG
user_id = row[0]  # Don't use tuple indexing
```

---

## 💻 Development Workflow

### Daily Development

1. Start PostgreSQL
2. Activate virtual environment (if using)
3. Run server: `python app.py`
4. Test changes

### Making Database Changes

1. Edit `models.py` (`_create_tables`, `_create_indexes`, `_create_triggers`, `_create_procedures`)
2. Drop and recreate database:
   ```bash
   psql -U postgres -c "DROP DATABASE zero_db;"
   psql -U postgres -c "CREATE DATABASE zero_db OWNER zero_user;"
    python app.py
   ```
3. Reload test data: `python mock.py`
4. Test changes

### Making API Changes

1. Edit appropriate file (`citizen.py`, `cleaner.py`, `admin.py`)
2. Add endpoint:
   ```python
   @citizen_bp.route('/api/citizen/new-feature', methods=['GET'])
   @token_required
   def new_feature(current_user):
       return jsonify({'message': 'Success'}), 200
   ```
3. Restart server (auto-reloads in debug mode)
4. Test endpoint

### Common Queries

**Get user with profile:**
```python
with db_connection.get_cursor() as cursor:
    cursor.execute("""
        SELECT u.*, cp.green_points_balance, cp.total_reports
        FROM users u
        LEFT JOIN citizen_profiles cp ON u.id = cp.user_id
        WHERE u.id = %s
    """, (user_id,))
    user = cursor.fetchone()
```

**Insert with RETURNING:**
```python
with db_connection.get_cursor(commit=True) as cursor:
    cursor.execute("""
        INSERT INTO reports (user_id, zone_id, description, severity, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (user_id, zone_id, description, severity, 'SUBMITTED'))
    new_report = cursor.fetchone()
    report_id = new_report['id']
```

**Call stored procedure:**
```python
with db_connection.get_cursor() as cursor:
    cursor.execute("SELECT * FROM calculate_citizen_leaderboard() LIMIT 10")
    leaderboard = cursor.fetchall()
```

---

## 🔧 Adding New Features

### Add New API Endpoint

**Example: Get citizen's reports**

Edit `citizen.py`:
```python
@citizen_bp.route('/api/citizen/reports', methods=['GET'])
@token_required
def get_my_reports(current_user):
    """Get all reports by current citizen"""
    try:
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT r.*, z.name as zone_name
                FROM reports r
                JOIN zones z ON r.zone_id = z.id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
            """, (current_user['id'],))
            reports = cursor.fetchall()
        
        return jsonify({
            'reports': reports,
            'count': len(reports)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Test:
```bash
curl http://localhost:5000/api/citizen/reports -H "Authorization: Bearer TOKEN"
```

### Add New Table

Edit `models.py` inside `_create_tables(migration)`:
```sql
CREATE TABLE IF NOT EXISTS new_table (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_new_table_user ON new_table(user_id);
```

Recreate database (see workflow above).

Update `mock.py` to generate test data.

### Add New Trigger

Edit `models.py` inside `_create_triggers(migration)`:
```sql
CREATE OR REPLACE FUNCTION my_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- Your logic
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER my_trigger
AFTER INSERT ON my_table
FOR EACH ROW EXECUTE FUNCTION my_trigger_function();
```

Recreate database and test.

### Add New Stored Procedure

Edit `models.py` inside `_create_procedures(migration)`:
```sql
CREATE OR REPLACE FUNCTION my_procedure(p_user_id VARCHAR)
RETURNS TABLE(result_column VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT column FROM table WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;
```

Call from Python:
```python
with db_connection.get_cursor() as cursor:
    cursor.execute("SELECT * FROM my_procedure(%s)", (user_id,))
    results = cursor.fetchall()
```

---

## 🧪 Testing & Debugging

### Test API with curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"citizen1@test.com","password":"password123"}'

# Get profile (use token from login)
curl http://localhost:5000/api/citizen/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Debug Database

```bash
# Check tables
psql -U zero_user -d zero_db -c "\dt"

# Check table structure
psql -U zero_user -d zero_db -c "\d users"

# Check data
psql -U zero_user -d zero_db -c "SELECT COUNT(*) FROM users;"

# Quick health check
curl http://localhost:5000/api/health
```

### Common Issues

**"relation does not exist"**
→ Run `python app.py` with `RERUN_MIGRATIONS=true`

**"column does not exist"**
→ Check column name in schema

**"duplicate key violates unique constraint"**
→ Triggers might auto-create data (e.g., profiles)

**"null value violates not-null constraint"**
→ Check required fields, triggers need certain data

**"Token is invalid"**
→ Login again for new token

**"Permission denied"**
→ Check user has correct role

### Complete Reset

```bash
# Drop database
psql -U postgres -c "DROP DATABASE zero_db;"

# Recreate
psql -U postgres -c "CREATE DATABASE zero_db OWNER zero_user;"

# Grant permissions
psql -U postgres -d zero_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zero_user;"
psql -U postgres -d zero_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zero_user;"

# Run migrations
python app.py

# Load data
python mock.py
```

---

## 📚 Useful Commands

### PostgreSQL

```bash
# Connect
psql -U zero_user -d zero_db

# List tables
\dt

# Describe table
\d table_name

# List functions
\df

# List triggers
SELECT * FROM pg_trigger;

# Exit
\q
```

### Python Virtual Environment

```bash
# Create
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Deactivate
deactivate
```

---

## 🎯 Best Practices

1. ✅ Always use context managers for database
2. ✅ Never commit `.env` to git
3. ✅ Test with mock data first
4. ✅ Use stored procedures for complex queries
5. ✅ Let triggers handle business logic
6. ✅ Add indexes for frequent queries
7. ✅ Use ENUM types for categories
8. ✅ Document your code
9. ✅ Test endpoints after changes
10. ✅ Keep `models.py` as source of truth

---

## 🐛 Getting Help

1. Check this README
2. Check error logs in terminal
3. Verify database with `psql` checks and `GET /api/health`
4. Check test data with `mock.py`
5. Review documentation files
6. Ask team members

---

**Project Status:** Production Ready  
**Last Updated:** January 2026

**Happy coding!** 🚀
