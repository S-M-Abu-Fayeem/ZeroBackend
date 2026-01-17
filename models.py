"""
Database Models and Configuration
==================================
This module handles database setup, configuration, and model initialization.
"""

import os
from dotenv import load_dotenv
from db_helper import DatabaseConnection, DatabaseConfig, Model, Migration


load_dotenv()

db_config = DatabaseConfig(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'flask_api_db'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'password')
)
db_connection = DatabaseConnection(
    db_config,
    min_conn=int(os.getenv('DB_MIN_CONN', '2')),
    max_conn=int(os.getenv('DB_MAX_CONN', '10'))
)



def setup_database():
    """Initialize all database tables, triggers, and procedures for the application."""
    migration = Migration(db_connection)
    
    _create_tables(migration)
    _create_triggers(migration)
    _create_procedures(migration)
    
    print("✓ Database setup complete")







## ALL DDL SQL CODES HERE ##
# TABLES, TRIGGERS, PROCEDURES

def _create_tables(migration):
    """Define and create all application tables."""
    migration.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """, "Created users table")


def _create_triggers(migration):
    """Define and create all application triggers."""
    migration.execute("""
        CREATE OR REPLACE FUNCTION update_users_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at := CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """, "Created update_users_timestamp function")
    
    migration.execute("""
        DROP TRIGGER IF EXISTS trg_update_users_timestamp ON users;
        CREATE TRIGGER trg_update_users_timestamp
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_users_timestamp();
    """, "Created trigger trg_update_users_timestamp on users table")


def _create_procedures(migration):
    """Define and create all application procedures."""
    migration.execute("""
        CREATE OR REPLACE PROCEDURE add_user(IN p_name TEXT, IN p_email TEXT)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO users(name, email) VALUES (p_name, p_email);
            COMMIT;
        END;
        $$;
    """, "Created procedure add_user")
