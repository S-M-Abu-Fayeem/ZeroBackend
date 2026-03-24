# Zero Backend — Smart Waste Management System API

A Flask + PostgreSQL backend powering role-based workflows for citizens reporting waste, cleaners earning rewards, admins approving tasks, and superadmins managing system-wide operations. **All interactions are database-driven with explicit SQL**, normalized to 3NF, optimized with strategic indexes, and audited through triggers, procedures, and audit logs.

---

## System Architecture

- **Framework**: Flask 3 (Python 3.10+)
- **Database**: PostgreSQL 12+ with **3NF normalization**, ENUM types, foreign keys, 26+ strategic indexes, triggers, and stored procedures
- **Authentication**: JWT tokens (PyJWT) + bcrypt password hashing
- **Data Access**: Explicit SQL via db_helper.py; NO SQLAlchemy (intentional choice for control and auditability)
- **AI Integration**: HuggingFace/Groq waste analysis, image-to-image cleanup comparison
- **CORS**: Enabled for frontend on localhost:3000

---

## Deploy on Render (Backend + PostgreSQL)

This repository now includes a Render Blueprint file at [render.yaml](../render.yaml) that provisions:

- A managed PostgreSQL instance on Render
- A Python web service for this Flask backend
- Environment variable wiring from the Render database into the backend service

### 1. Push code to GitHub

Render deploys from your Git repository. Make sure your latest backend code is pushed.

### 2. Create services from Blueprint

1. Open Render Dashboard.
2. Click New > Blueprint.
3. Connect your GitHub repo.
4. Select this repository and deploy.

Render reads [render.yaml](../render.yaml) and creates:

- Database: zero-postgres
- Web service: zero-backend (rootDir: ZeroBackend)

### 3. Set required secret environment variables

In Render service settings for zero-backend, set:

- SUPERADMIN_PASSWORD (required by startup logic)

Optional secrets depending on features:

- HF_TOKEN (for HuggingFace-powered AI)
- GROQ_API_KEY (for Groq AI fallback)

### 4. Configure frontend origin for CORS

Set FRONTEND_ORIGINS to your deployed frontend URL. For multiple domains, use comma-separated values.

Example:

- https://your-frontend-domain.onrender.com
- https://your-frontend-domain.onrender.com,http://localhost:3000

### 5. Initialize database schema (first deploy)

Because this project intentionally runs schema setup explicitly, open a Render Shell on zero-backend and run:

```bash
python -c "from models import db_connection, setup_database; db_connection.create_pool(); setup_database(); db_connection.close_pool()"
```

Then restart the web service.

### 6. Verify deployment

- Health endpoint: GET /api/health
- API root endpoint: GET /

If health returns database disconnected, verify DB_* env vars and that the database service is running.

---

## Database Design — 3NF Relational Model

### Core Principle
All user roles, transactions, and workflows are implemented as **normalized relational entities** with proper primary/foreign keys, CHECK constraints, and business logic enforced at the database layer through **triggers** and **stored procedures**.

### Data Dictionary: 27 Tables

**USER MANAGEMENT**
- **users** [PK: id(UUID)]: Base user entity. All roles derive from this. Fields: email (UNIQUE), password_hash (bcrypt), name, phone, role ∈ {CITIZEN,CLEANER,ADMIN}, is_superadmin (bool), is_active (bool), avatar_url (nullable), dark_mode preference, created_at, updated_at, last_login_at, created_by/updated_by audit fields.
  - 1:1 → citizen_profiles | cleaner_profiles | admin_profiles (via user_id)
  - 1:N → reports (submitted by citizen)
  - 1:N → tasks (assigned cleaner via cleaner_id)
  - 1:N → user_sessions (multiple login sessions per user)
  - 1:N → green_points_transactions (for CITIZEN role earning)
  - 1:N → earnings_transactions (for CLEANER role)
  - 1:N → notifications (sent to each user)
  - 1:N → activity_logs (audit trail of actions)

- **citizen_profiles** [FK: user_id → users] [1:1]: Extended citizen data. Fields: green_points_balance (INT), total_reports (INT aggregated), approved_reports (INT aggregated), current_streak (INT days), longest_streak (INT days), badges_count (INT), reviews_given (INT), created_by/updated_by.

- **cleaner_profiles** [FK: user_id → users] [1:1]: Extended cleaner data. Fields: total_earnings (DECIMAL), pending_earnings (DECIMAL), completed_tasks (INT), current_tasks (INT), rating (DECIMAL(3,2) 0.0-5.0), total_reviews (INT), bank_account (nullable), created_by/updated_by.

- **admin_profiles** [FK: user_id → users] [1:1]: Extended admin data. Fields: role_title (VARCHAR), department (VARCHAR nullable), created_by/updated_by.

- **user_sessions** [PK: id] [FK: user_id → users]: JWT session tracking. Fields: token_hash (UNIQUE, bcrypt of JWT), device_info (JSON nullable), ip_address, created_at, expires_at, last_activity_at.

**ZONE MANAGEMENT**
- **zones** [PK: id(UUID)]: Geographic zones for waste reporting. Fields: name (UNIQUE), description (TEXT nullable), cleanliness_score (INT 0-100, computed), color (VARCHAR hex), is_active (bool), created_at, updated_at, created_by/updated_by.
  - 1:N → zone_polygons (polygon coordinates)
  - 1:N → reports (waste reports filed in zone)
  - 1:N → tasks (cleanup tasks in zone)
  - 1:N → alerts (zone-level alerts)

- **zone_polygons** [FK: zone_id → zones] [1:N]: Polygon vertices for zone boundaries. Fields: zone_id, point_order (INT, enforces sequence), latitude (DECIMAL(9,6)), longitude (DECIMAL(9,6)). UNIQUE(zone_id, point_order) ensures order. Used with ray-casting algorithm to detect point-in-zone.

**WASTE REPORTING**
- **reports** [PK: id(UUID)]: Citizen waste reports. Fields: user_id (FK citizen), zone_id (FK), description (TEXT), image_url (cloud storage path), severity ∈ {LOW,MEDIUM,HIGH,CRITICAL}, status ∈ {SUBMITTED,APPROVED,DECLINED,IN_PROGRESS,COMPLETED}, latitude/longitude (GPS coords), cleaner_id (FK nullable, assigned on approval), after_image_url (completion evidence), created_at, approved_at, completed_at, reviewed_at, decline_reason (TEXT nullable), created_by/updated_by audit.
  - 1:1 → waste_analyses (AI analysis result)
  - 1:1 → cleanup_comparisons (before/after AI comparison)
  - 1:1 → cleanup_reviews (citizen review of cleanup)
  - 1:N → green_points_transactions (earning history per action)
  - 1:N → notifications (to citizen on status change)

- **waste_analyses** [FK: report_id → reports] [1:1]: AI-generated waste analysis. Fields: report_id (UNIQUE), description (TEXT), severity (ENUM), estimated_volume (VARCHAR), environmental_impact ∈ {LOW,MODERATE,HIGH,SEVERE}, health_hazard (bool), hazard_details (TEXT nullable), recommended_action (TEXT), estimated_cleanup_time (VARCHAR), confidence (INT 0-100), created_at, created_by.
  - 1:N → waste_compositions (waste type breakdown)
  - 1:N → special_equipment (required cleanup equipment)

- **waste_compositions** [FK: waste_analysis_id → waste_analyses] [1:N]: Composition array from AI. Fields: id, waste_analysis_id, waste_type (VARCHAR), percentage (INT), recyclable (bool).

- **special_equipment** [FK: waste_analysis_id → waste_analyses] [1:N]: Equipment array from AI. Fields: id, waste_analysis_id, equipment_name (VARCHAR).

- **cleanup_comparisons** [FK: report_id → reports] [1:1]: AI-generated before/after comparison on task completion. Fields: report_id (UNIQUE), completion_percentage (INT 0-100), before_summary (TEXT), after_summary (TEXT), quality_rating ∈ {POOR,FAIR,GOOD,EXCELLENT}, environmental_benefit (TEXT), verification_status ∈ {VERIFIED,NEEDS_REVIEW,INCOMPLETE}, feedback (TEXT), confidence (INT 0-100), created_at.
  - 1:N → cleanup_waste_removed (waste removed breakdown)
  - 1:N → cleanup_remaining_issues (incomplete items)

- **cleanup_waste_removed** [FK: cleanup_comparison_id] [1:N]: What was removed per AI. Fields: id, cleanup_comparison_id, waste_type, percentage, recyclable.

- **cleanup_remaining_issues** [FK: cleanup_comparison_id] [1:N]: What was left behind per AI. Fields: id, cleanup_comparison_id, issue_description.

- **cleanup_reviews** [FK: report_id → reports] [1:1]: Citizen rating of cleanup quality. Fields: report_id (UNIQUE), citizen_id (FK), cleaner_id (FK), rating (INT 1-5), comment (TEXT nullable), created_at, created_by/updated_by.

**TASK LIFECYCLE**
- **tasks** [PK: id(UUID)]: Cleanup tasks manually created by admin or auto-spawned from approved reports. Fields: report_id (FK nullable, links to original report), zone_id (FK), cleaner_id (FK nullable, unassigned initially), description (TEXT), status ∈ {APPROVED,IN_PROGRESS,COMPLETED}, priority ∈ {LOW,MEDIUM,HIGH,CRITICAL}, due_date (TIMESTAMP), reward (DECIMAL BDT), evidence_image_url (completion photo), created_at, taken_at (when cleaner claimed), completed_at, created_by/updated_by.
  - 1:1 → earnings_transactions (payment for completion)

**GAMIFICATION**
- **badges** [PK: id(UUID)]: Badge template library. Fields: badge_type (UNIQUE varchar), name, description, icon (URL), category (earned_badges, milestones, special), created_at, created_by.
  - Examples: FIRST_REPORT, ECO_WARRIOR (10+ approved reports), ZONE_CHAMPION, STREAK_7, STREAK_30, PAYMENT_HERO (1000+ BDT earned)

- **user_badges** [PK: (user_id, badge_id)]: N:M junction, one row per user per earned badge. Fields: user_id (FK), badge_id (FK), earned_at (TIMESTAMP when unlocked), UNIQUE(user_id, badge_id) prevents duplicates.

- **green_points_transactions** [PK: id]: Points ledger for CITIZEN gamification. Fields: user_id (FK), report_id (FK nullable, which report triggered this), green_points (INT, signed, can be positive or negative forforfeit), reason ∈ {REPORT_CREATED,REPORT_APPROVED,REPORT_DECLINED_REFUND,TASK_COMPLETED,TASK_IN_PROGRESS,REVIEW_SUBMITTED}, created_at, created_by.

- **green_points_config** [PK: id]: Configuration table for point values (configurable without code changes). Fields: action_type (UNIQUE varchar), green_points (INT), description (VARCHAR), created_at, created_by.

- **citizen_leaderboard** [PK: (user_id, period)] [1:many denormalized]: Pre-computed ranks for performance. Fields: user_id (FK), rank (INT 1-...), total_green_points (INT), approved_reports (INT), badges_count (INT), period ∈ {all_time,week,month}, created_at. Recalculated periodically by cron job or admin trigger calling sp_recalculate_citizen_leaderboard(period).

- **cleaner_leaderboard** [PK: (user_id, period)] [1:many denormalized]: Pre-computed ranks. Fields: user_id (FK), rank (INT), total_earnings (DECIMAL), completed_tasks (INT), rating (DECIMAL 0-5), this_month_earnings (DECIMAL), period, created_at. Recalculated by sp_recalculate_cleaner_leaderboard(period).

**NOTIFICATIONS & ALERTS**
- **notifications** [PK: id(UUID)]: User notifications inbox. Fields: user_id (FK), type ∈ {POINTS,BADGE,REPORT,TASK,ALERT,ANNOUNCEMENT}, title (VARCHAR), message (TEXT), is_read (bool), related_report_id (FK nullable), related_task_id (FK nullable), created_at, created_by.
  - Index: (user_id, is_read DESC, created_at DESC) for unread notification feeds

- **bulk_notifications** [PK: id(UUID)]: Admin-sent broadcasts. Fields: audience ∈ {all,citizens,cleaners}, type, title, message, sent_by (FK admin), created_at.

- **alerts** [PK: id(UUID)]: System-generated or citizen-reported alerts. Fields: source ∈ {AI,CITIZEN}, zone_id (FK), severity ∈ {LOW,MEDIUM,HIGH,CRITICAL}, status ∈ {OPEN,RESOLVED}, message (TEXT), resolved_at (TIMESTAMP nullable), resolved_by (FK admin nullable), created_at, created_by.

**PAYMENTS & EARNINGS**
- **earnings_transactions** [PK: id(UUID)]: Cleaner payment ledger. Fields: cleaner_id (FK), task_id (FK UNIQUE), amount (DECIMAL 10,2 BDT), status ∈ {PENDING,PAID}, paid_at (TIMESTAMP nullable), created_at, created_by, paid_by (FK admin nullable). UNIQUE(task_id) ensures one payment per task. Index on (cleaner_id, status, created_at DESC) for payment query optimization.

**AUDIT & COMPLIANCE**
- **activity_logs** [PK: id(UUID)]: Superadmin audit trail. Fields: user_id (FK, who performed action), action (VARCHAR e.g., APPROVE_REPORT, DELETE_USER, BLOCK_USER), entity_type (VARCHAR e.g., reports, users), entity_id (UUID), details (JSONB, change payload), ip_address, user_agent, created_at.

---

## Strategic Indexes (26 Total)

**Performance Indexes for Query Optimization:**
1. idx_users_role_active ON users(role, is_active) — Staff lookups
2. idx_reports_status_created ON reports(status DESC, created_at DESC) — Pending/approved
3. idx_reports_user_created ON reports(user_id, created_at DESC) — Citizen timeline
4. idx_reports_zone_status ON reports(zone_id, status) — Zone metrics
5. idx_tasks_status_due ON tasks(status, due_date) — Available tasks
6. idx_tasks_cleaner_status ON tasks(cleaner_id, status) — Cleaner queue
7. idx_notifications_user_unread ON notifications(user_id, is_read DESC, created_at DESC) — Fast unread fetch
8. idx_citizen_profiles_points_reports ON citizen_profiles(green_points_balance DESC, approved_reports DESC) — Leaderboard sort
9. idx_cleaner_profiles_earnings_tasks ON cleaner_profiles(total_earnings DESC, completed_tasks DESC) — Cleaner leaderboard
10. idx_earnings_cleaner_status ON earnings_transactions(cleaner_id, status, created_at DESC) — Payment queries
11. idx_green_points_user_created ON green_points_transactions(user_id, created_at DESC) — Points history
12. idx_cleanup_reviews_cleaner ON cleanup_reviews(cleaner_id, created_at DESC) — Cleaner review feed
13. idx_alerts_status_created ON alerts(status, created_at DESC) — Active alerts view
14. idx_zone_polygons_by_zone ON zone_polygons(zone_id, point_order) — Polygon boundary queries
15. idx_waste_composition_analysis ON waste_compositions(waste_analysis_id) — Composition lookups
16. idx_special_equipment_analysis ON special_equipment(waste_analysis_id) — Equipment lookups

**Uniqueness & Correctness:**

17. idx_users_email_unique ON users(email) UNIQUE — Login lookups, prevent duplicates
18. idx_earnings_task_unique ON earnings_transactions(task_id) UNIQUE — One payment per task
19. idx_user_badges_unique ON user_badges(user_id, badge_id) UNIQUE — Badge earned once per user
20. idx_sessions_token_unique ON user_sessions(token_hash) UNIQUE — JWT token verification
21. idx_badges_type_unique ON badges(badge_type) UNIQUE — Template lookups
22. idx_citizen_leaderboard_unique ON citizen_leaderboard(period, rank) UNIQUE — One #1 per period
23. idx_cleaner_leaderboard_unique ON cleaner_leaderboard(period, rank) UNIQUE — One #1 per period
24. idx_zone_polygons_unique ON zone_polygons(zone_id, point_order) UNIQUE — Polygon ordering
25. idx_green_points_config_unique ON green_points_config(action_type) UNIQUE — Config lookups
26. idx_zone_name_unique ON zones(name) UNIQUE — Zone name uniqueness

---

## Triggers & Stored Procedures (22 Triggers + 15 Procedures)

**Automatic Timestamp Maintenance (1 per table):**
- UPDATE triggers on: users, citizen_profiles, cleaner_profiles, admin_profiles, zones, reports, tasks, waste_analyses, cleanup_comparisons, cleanup_reviews, notifications, badges, alerts, earnings_transactions — All set updated_at = NOW() on UPDATE.

**User Lifecycle Automation:**
- 	rg_create_user_profile() AFTER INSERT ON users — Automatically creates citizen_profiles | cleaner_profiles | admin_profiles row based on user.role.

**Report State Machine (5 triggers):**
- 	rg_report_created() AFTER INSERT ON reports — Calls notification creation, triggers recalculate_zone_cleanliness().
- 	rg_report_approved() AFTER UPDATE ON reports (status = 'APPROVED') — Awards citizen green_points, optionally creates task.
- 	rg_report_declined() AFTER UPDATE ON reports (status = 'DECLINED') — Refunds any points (if provisional), notifies citizen.
- 	rg_report_completed() AFTER UPDATE ON reports (status = 'COMPLETED') — Marks cleaner as completed, triggers cleanup_comparisons if AI evidence provided.
- 	rg_cleanup_verified() AFTER UPDATE ON cleanup_comparisons (verification_status = 'VERIFIED') — Finalizes cleaner payment.

**Task Lifecycle (2 triggers):**
- 	rg_task_taken() AFTER UPDATE ON tasks (status = 'IN_PROGRESS') — Sets taken_at timestamp, increments cleaner current_tasks.
- 	rg_task_completed() AFTER UPDATE ON tasks (status = 'COMPLETED') — Creates earnings_transaction row, decrements cleaner current_tasks.

**Review & Rating (2 triggers):**
- 	rg_cleanup_review_submitted() AFTER INSERT ON cleanup_reviews — Awards citizen review bonus points, recalculates cleaner average rating.
- 	rg_cleaner_rating_updated() AFTER UPDATE ON cleaner_profiles (rating changed) — Logs to activity_logs.

**Gamification (3 triggers):**
- 	rg_badge_earned() AFTER INSERT ON user_badges — Increments citizen_profiles.badges_count, creates notification.
- 	rg_streak_updated() AFTER UPDATE ON citizen_profiles (current_streak changed) — Log to activity_logs, check for streak badges.
- 	rg_zone_alert_on_cleanliness_drop() AFTER UPDATE ON zones (cleanliness_score drops below threshold) — Creates alert.

**Stored Procedures (15 total):**
1. update_citizen_streak(user_id UUID) — Recalculates 7-day and 30-day action streaks from green_points_transactions timestamps.
2. check_eco_warrior_badge(user_id UUID) — Award ECOWARRIOR badge if approved_reports ≥ 10.
3. ward_badge_if_not_exists(user_id UUID, badge_type VARCHAR) — Idempotent badge grant (insert ignored if exists).
4. ecalculate_zone_cleanliness(zone_id UUID) — Recalculates zone.cleanliness_score from recent 30-day approved reports in zone.
5. sp_register_user(email, password_hash, name, phone, role) RETURNS UUID — Atomically creates users row + profile row.
6. sp_submit_report(user_id, zone_id, description, severity, image_url, latitude, longitude, ai_analysis JSONB) RETURNS UUID — Wraps report insert + waste_analyses.
7. sp_approve_report(report_id, green_points_reward, create_task BOOL) — Sets status=APPROVED, awards points, optionally creates task.
8. sp_decline_report(report_id, reason) — Sets status=DECLINED, refunds points if applicable, notifies citizen.
9. sp_take_task(task_id, cleaner_id) — Returns error if already taken; sets cleaner_id, status=IN_PROGRESS, taken_at=NOW().
10. sp_complete_task(task_id, evidence_image_url, notes) — Sets status=COMPLETED, completed_at=NOW(), creates earnings_transaction.
11. sp_create_zone(name, description, color, polygon_points JSONB) RETURNS UUID — Atomically creates zones + zone_polygons rows.
12. sp_recalculate_citizen_leaderboard(period VARCHAR) — Truncates citizen_leaderboard for period, recalculates ranks from citizen_profiles/green_points_transactions.
13. sp_recalculate_cleaner_leaderboard(period VARCHAR) — Truncates cleaner_leaderboard for period, recalculates ranks from cleaner_profiles/earnings_transactions.
14. sp_send_bulk_notification(audience, type, title, message, sent_by_admin_id) — Inserts one notification row per recipient (broadcast).
15. sp_process_payment(payment_ids UUID[], action VARCHAR, reason VARCHAR) — Batch updates earnings_transactions status (PENDING→PAID or REJECT).

---

## API Endpoints Overview (96 Total)

### Authentication (4 endpoints)
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout

### Citizen (22 endpoints)
- POST/GET /api/citizen/reports
- GET /api/citizen/reports/<id>
- PUT/DELETE /api/citizen/reports/<id>
- POST /api/citizen/reports/<id>/review
- GET /api/citizen/profile
- PUT /api/citizen/profile
- GET /api/citizen/stats
- GET /api/citizen/badges
- GET /api/citizen/points
- GET /api/citizen/leaderboard
- GET /api/citizen/notifications
- POST /api/citizen/password/change
- POST /api/citizen/data/download
- DELETE /api/citizen/account

### Cleaner (18 endpoints)
- GET /api/cleaner/tasks/available
- POST /api/cleaner/tasks/<id>/take
- GET /api/cleaner/tasks
- POST /api/cleaner/tasks/<id>/complete
- GET /api/cleaner/earnings
- GET /api/cleaner/payments/summary
- POST /api/cleaner/payments/withdraw
- GET /api/cleaner/payments/history
- GET /api/cleaner/profile
- PUT /api/cleaner/profile
- GET /api/cleaner/leaderboard
- GET /api/cleaner/notifications
- ... (similar endpoints as citizen)

### Admin (28 endpoints)
- GET /api/admin/reports
- GET /api/admin/reports/pending
- GET /api/admin/reports/<id>/reward-suggestion
- POST/PUT /api/admin/reports/<id>/approve
- POST /api/admin/reports/<id>/decline
- POST /api/admin/reports/<id>/reopen
- GET/POST /api/admin/tasks
- PUT/DELETE /api/admin/tasks/<id>
- GET/POST /api/admin/zones
- PUT/DELETE /api/admin/zones/<id>
- GET /api/admin/zones/<id>/stats
- GET /api/admin/payments/pending
- POST /api/admin/payments/process
- GET /api/admin/payments/summary
- POST /api/admin/payments/top-up
- ... (and more admin-specific endpoints)

### Superadmin (8 endpoints)
- GET /api/superadmin/dashboard
- GET /api/superadmin/users
- POST /api/superadmin/users/<id>/block
- POST /api/superadmin/users/<id>/unblock
- DELETE /api/superadmin/users/<id>
- GET /api/superadmin/activity-logs
- POST /api/superadmin/actions/<id>/revert

### AI Services (3 endpoints)
- POST /api/ai/analyze-waste
- POST /api/ai/compare-cleanup
- POST /api/ai/analyze-report/<id>

### Leaderboards (3 endpoints)
- GET /api/leaderboards/citizens
- GET /api/leaderboards/cleaners
- POST /api/admin/leaderboards/recalculate

### Shared (5 endpoints)
- GET /api/zones
- GET /api/zones/by-location
- GET /api/zones/<id>/stats
- GET /api/reports/<id>
- GET /api/tasks/<id>

### Health (1 endpoint)
- GET /api/health

---

## Running the Backend

### Prerequisites
```
Python 3.10+
PostgreSQL 12+
pip (Python package manager)
```

### Environment Setup
```ash
cd ZeroBackend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zero_db
DB_USER=postgres
DB_PASSWORD=your_password
SECRET_KEY=your_secret_key_here_min_32_chars
SUPERADMIN_PASSWORD=strong_password_here
SUPERADMIN_EMAIL=superadmin@zero.local
SUPERADMIN_NAME=Super Admin
SUPERADMIN_RESET_PASSWORD=false
DB_MIN_CONN=2
DB_MAX_CONN=10
RERUN_MIGRATIONS=false
HUGGINGFACE_API_KEY=optional_for_ai
GROQ_API_KEY=optional_for_ai
```

### Database Initialization
```ash
python app.py
```

### Verify Installation
```ash
curl http://localhost:5000/api/health
```

---

## Deployment

- Update DB_* for production database
- Set strong SECRET_KEY (use secrets.token_urlsafe(32))
- Update CORS origins to production frontend URL
- Enable HTTPS (Flask behind reverse proxy)
- Monitor /api/health with uptime service
- Automated PostgreSQL backups

---
