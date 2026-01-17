# ZeroBackend - Developer Guide

> **Internal documentation for development team. Not for public use.**

This guide explains the backend architecture so you understand how components connect and where to add new features.

---

## 📁 Project Structure

```
ZeroBackend/
├── db_helper.py          # Database library (reusable utilities)
├── models.py             # Database config + schema migrations
├── app.py                # Flask app entry point
├── citizen.py            # Citizens feature routes
├── cleaner.py            # Cleaners feature routes
├── admin.py              # Admin feature routes
├── .env                  # Environment variables (not in git)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🔄 How Components Connect

### **Layer 1: db_helper.py** (Library)
**Purpose:** Generic database utilities that any project can use.

**What it provides:**
- `DatabaseConfig` — stores connection credentials
- `DatabaseConnection` — manages connection pool (not a single connection, but multiple reusable ones)
- `QueryBuilder` — generates parameterized SQL for SELECT, INSERT, UPDATE, DELETE
- `Model` — CRUD operations helper (`find_all()`, `find_by_id()`, `create()`, `update()`, `delete()`)
- `Migration` — executes DDL statements (CREATE TABLE, triggers, procedures)

**Key concept:** `db_helper.py` is a **library**. It has no business logic. It's just tools.

```python
# Example: db_helper provides the tools
migration.execute(sql, "Creating users table")
model.find_by_id(user_id)
```

---

### **Layer 2: models.py** (Configuration + Schema)
**Purpose:** Sets up database connection and defines all schema (tables, triggers, procedures).

**What happens here:**

1. **Load environment variables** from `.env`
   ```python
   host = config('DB_HOST', default='localhost')
   port = config('DB_PORT', default=5432, cast=int)
   ```

2. **Create database connection** using `DatabaseConfig` from `db_helper.py`
   ```python
   db_config = DatabaseConfig(host=host, port=port, ...)
   db_connection = DatabaseConnection(db_config, min_conn=2, max_conn=10)
   ```

3. **Define all schema migrations** (tables, triggers, procedures) in helper functions:
   - `_create_tables()` — All your tables (users, citizens, cleaners, admins, bookings, etc.)
   - `_create_triggers()` — All your triggers (updated_at timestamps, validations, etc.)
   - `_create_procedures()` — All your stored procedures (business logic in database)

4. **Export models** for use in routes
   ```python
   users_model = Model(db_connection, 'users')
   citizens_model = Model(db_connection, 'citizens')
   cleaners_model = Model(db_connection, 'cleaners')
   ```

**Key concept:** `models.py` glues `db_helper` library to your app and defines your schema.

---

### **Layer 3: app.py** (Flask Entry Point)
**Purpose:** Main Flask app. Registers blueprints. Defines error handlers.

**What happens here:**

1. Create Flask app
2. Import blueprints from `citizen.py`, `cleaner.py`, `admin.py`
3. Register blueprints with URL prefixes
4. Define global error handlers (404, 500)
5. Cleanup on shutdown

```python
from flask import Flask
from citizen import citizen_bp
from cleaner import cleaner_bp
from admin import admin_bp

app = Flask(__name__)
app.register_blueprint(citizen_bp, url_prefix='/api/citizens')
app.register_blueprint(cleaner_bp, url_prefix='/api/cleaners')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Key concept:** `app.py` is minimal and clean. It only registers blueprints.

---

### **Layer 4: citizen.py, cleaner.py, admin.py** (Feature Routes)
**Purpose:** Feature-specific route handlers. Each file contains routes for one entity.

**Structure:**
```python
from flask import Blueprint, jsonify, request
from models import citizens_model  # Import model from models.py

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.route('/', methods=['GET'])
def get_citizens():
    """Get all citizens"""
    citizens = citizens_model.find_all()
    return jsonify({"data": citizens})

@citizen_bp.route('/<int:id>', methods=['GET'])
def get_citizen(id):
    """Get a specific citizen"""
    citizen = citizens_model.find_by_id(id)
    return jsonify({"data": citizen})

@citizen_bp.route('/', methods=['POST'])
def create_citizen():
    """Create a new citizen"""
    data = request.get_json()
    new_citizen = citizens_model.create(data)
    return jsonify({"data": new_citizen}), 201

@citizen_bp.route('/<int:id>', methods=['PUT'])
def update_citizen(id):
    """Update a citizen"""
    data = request.get_json()
    updated = citizens_model.update(data, {'id': id})
    return jsonify({"data": updated})

@citizen_bp.route('/<int:id>', methods=['DELETE'])
def delete_citizen(id):
    """Delete a citizen"""
    citizens_model.delete({'id': id})
    return jsonify({"message": "Deleted"})
```

**Key concept:** Each feature file is independent. It imports models from `models.py` and uses them to serve HTTP requests.

---

## 🔗 Data Flow Example

**Request comes in:** `GET /api/citizens/1`

1. **app.py** catches the request and routes to `citizen.py`
2. **citizen.py** calls `citizens_model.find_by_id(1)` from `models.py`
3. **models.py** has the model instance connected to `db_connection`
4. **Model (from db_helper.py)** uses `QueryBuilder` to build SQL: `SELECT * FROM citizens WHERE id = %s`
5. **DatabaseConnection (from db_helper.py)** gets a connection from the pool and executes the query
6. **Result** returns to `citizen.py`, which formats it as JSON and sends back to client

```
HTTP Request
    ↓
app.py (route handler)
    ↓
citizen.py (@citizen_bp.route)
    ↓
citizens_model.find_by_id() [from models.py]
    ↓
QueryBuilder.select() [from db_helper.py]
    ↓
DatabaseConnection.get_cursor() [from db_helper.py]
    ↓
PostgreSQL
    ↓
HTTP Response (JSON)
```

---

## 📋 Adding New Features

### **1. Add a new table to the database**
Edit `models.py` → `_create_tables()`:

```python
def _create_tables(migration):
    """Define and create all application tables."""
    migration.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created users table")
    
    migration.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            citizen_id INT NOT NULL REFERENCES citizens(id),
            cleaner_id INT NOT NULL REFERENCES cleaners(id),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created bookings table")  # ← Add here
```

### **2. Create a model instance in models.py**
```python
# After connection setup
bookings_model = Model(db_connection, 'bookings')
```

### **3. Create a new feature file (e.g., booking.py)**
```python
from flask import Blueprint, jsonify, request
from models import bookings_model

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/', methods=['GET'])
def get_bookings():
    bookings = bookings_model.find_all()
    return jsonify({"data": bookings})

# ... more routes
```

### **4. Register in app.py**
```python
from booking import booking_bp

app.register_blueprint(booking_bp, url_prefix='/api/bookings')
```

---

## 🔧 Configuration

### **.env file** (create this locally)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flask_api_db
DB_USER=postgres
DB_PASSWORD=password

DB_MIN_CONN=2
DB_MAX_CONN=10

RERUN_MIGRATIONS=false
```

**Why?** Credentials should not be in version control. `.env` is in `.gitignore`.

---

## 🚀 Setup & Run

### **1. Install dependencies**
```bash
pip install -r requirements.txt
```

### **2. Create `.env` file**
Copy the template above and add your database credentials.

### **3. Create database tables (first time only)**
Set `RERUN_MIGRATIONS=true` in `.env`, then run the app:
```bash
python app.py
```
After tables are created, set `RERUN_MIGRATIONS=false` to avoid rerunning migrations on every startup.

### **4. Run the app**
```bash
python app.py
```

App runs at `http://127.0.0.1:5000`

---

## 💡 Key Principles

| Component | Role | Owns What |
|-----------|------|-----------|
| `db_helper.py` | Reusable library | Generic DB utilities (no business logic) |
| `models.py` | Config + schema | Database connection, all tables/triggers/procedures |
| `app.py` | Entry point | Flask setup, blueprint registration |
| `citizen.py, cleaner.py, admin.py` | Feature handlers | Routes + business logic for each entity |

---

## ❓ Common Questions

**Q: Where do I add validation logic?**  
A: In the route handler (citizen.py, cleaner.py, etc.) before calling the model.

**Q: Where do I add complex queries?**  
A: Use `Model.execute_raw()` in the route handler, or add a stored procedure in `models.py` and call it from the route.

**Q: What if I need to query multiple tables?**  
A: Use joins in `Model.execute_raw()` in your route handler.

**Q: Should I modify db_helper.py?**  
A: Only if you're adding generic utilities that all features can use. Otherwise, add logic to routes or create stored procedures in `models.py`.


---

Happy coding! 🚀
