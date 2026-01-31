try:
    # Try psycopg3 first (for Python 3.12+)
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
    PSYCOPG_VERSION = 3
except ImportError:
    # Fall back to psycopg2 (for Python < 3.12)
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2

from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple

class DatabaseConfig:
    """Holds connection configuration details for establishing PostgreSQL connections."""

    def __init__(self, host="localhost", port=5432, database="mydb",
                 user="postgres", password="password"):
        """Initialize config values for the database connection."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def get_cursor_string(self):
        """Return a connection string compatible with psycopg2 cursor usage."""
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"
        

class DatabaseConnection:
    """Manages lifecycle of a PostgreSQL connection pool and cursor access."""

    def __init__(self, config: DatabaseConfig, min_conn=1, max_conn=10):
        """Store configuration and pool sizing before pool creation."""
        self.config = config
        self.connection_pool = None
        self.min_conn = min_conn
        self.max_conn = max_conn

    def create_pool(self):
        """Create a connection pool with configured bounds; returns True on success."""
        try:
            if PSYCOPG_VERSION == 3:
                # psycopg3 connection string
                conninfo = f"host={self.config.host} port={self.config.port} dbname={self.config.database} user={self.config.user} password={self.config.password}"
                self.connection_pool = ConnectionPool(
                    conninfo=conninfo,
                    min_size=self.min_conn,
                    max_size=self.max_conn
                )
            else:
                # psycopg2 connection pool
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    self.min_conn,
                    self.max_conn,
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password
                )
            print(f"Connection pool created successfully (psycopg{PSYCOPG_VERSION})")
            return True
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            return False

    @contextmanager
    def get_cursor(self, commit=False):
        """Yield a cursor from the pool; commit or rollback based on execution outcome."""
        if PSYCOPG_VERSION == 3:
            # psycopg3 uses connection context manager
            with self.connection_pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    try:
                        yield cursor
                        if commit:
                            connection.commit()
                    except Exception as e:
                        connection.rollback()
                        print(f"Error during database operation: {e}")
                        raise e
        else:
            # psycopg2 manual connection management
            connection = self.connection_pool.getconn()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error during database operation: {e}")
                raise e
            finally:
                cursor.close()
                self.connection_pool.putconn(connection)
    
    def close_pool(self):
        """Close all connections in the pool if it has been initialized."""
        if self.connection_pool:
            if PSYCOPG_VERSION == 3:
                self.connection_pool.close()
            else:
                self.connection_pool.closeall()
            print("Connection pool closed")

class QueryBuilder:
    """Provides helper methods to build parameterized SQL queries."""

    @staticmethod
    def select(table, columns=None, where=None, order_by=None, limit=None):
        """Construct a SELECT statement with optional columns, filters, ordering, and limit."""
        col_str = "*" if not columns else ", ".join(columns)
        query = f"SELECT {col_str} FROM {table}"
        params = []
        if where:
            conditions = []
            for key,value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        return query, params

    @staticmethod
    def insert(table, data):
        """Construct an INSERT statement returning the inserted row."""
        columns = list(data.keys())
        values = list(data.values())
        col_str = ", ".join(columns)
        placeholders = ", ".join(["%s"]*len(columns))
        query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) RETURNING *"
        return query, values

    @staticmethod
    def update(table, data, where):
        """Construct an UPDATE statement with filters, returning the updated row."""
        set_parts = []
        params = []
        for key, value in data.items():
            set_parts.append(f"{key} = %s")
            params.append(value)
        
        query = f"UPDATE {table} SET  {', '.join(set_parts)}"
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        query += " RETURNING *"
        return query, params

    @staticmethod
    def delete(table, where):
        """Construct a DELETE statement with filters, returning the deleted row."""
        params = []
        query = f"DELETE FROM {table}"
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        query += " RETURNING *"
        return query, params
    
class Model:
    """Lightweight base model offering CRUD helpers tied to a specific table."""

    def __init__(self, db_connection, table_name):
        """Bind the model to a database connection and target table."""
        self.db = db_connection
        self.table_name = table_name
        self.query_builder = QueryBuilder()

    def find_all(self, where=None, order_by=None,limit=None):
        """Fetch multiple rows with optional filters, ordering, and limit."""
        query, params = self.query_builder.select(
            self.table, where=where, order_by=order_by, limit=limit
        )

        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def find_by_id(self, id_value, id_column="id"):
        """Fetch a single row by primary key or specified identifier column."""
        query, params = self.query_builder.select(
            self.table_name, where={id_column: id_value}
        )
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def create(self, data):
        """Insert a new record and return the inserted row."""
        query, params = self.query_builder.insert(self.table, data)
        with self.db.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def update(self, data, where):
        """Update matching records and return the updated row."""
        query, params = self.query_builder.update(self.table, data, where)
        with self.db.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def delete(self, where):
        """Delete matching records and return the deleted row."""
        query, params = self.query_builder.delete(self.table, where)
        with self.db.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def execute_raw(self, query, params=None, commit=False):
        """Execute arbitrary SQL with optional parameters; returns fetched rows when available."""
        with self.deb.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or [])
            try:
                return cursor.fetchall()
            except:
                return []

class Migration:
    """Provides generic helpers to execute schema migrations (DDL/DML operations)."""

    def __init__(self, db_connection):
        """Store the shared database connection for migration operations."""
        self.db = db_connection
    
    def execute(self, sql, description):
        """Execute arbitrary SQL; log success or exception. Useful for all DDL/schema work."""
        try:
            with self.db.get_cursor(commit=True) as cursor:
                cursor.execute(sql)
            msg = description if description else "Migration executed"
            print(f"✓ {msg}")
        except Exception as e:
            print(f"✗ Error: {e}")
            raise





# Example usage:
if __name__ == "__main__":
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="testdb",
        user="testuser",
        password="testpassword"
    )
    db = DatabaseConnection(config)
    if db.create_pool():
        migration = Migration(db)
        migration.create_users_table()
        user_model = Model(db, "users")
        new_user = user_model.create({
            "name": "John Doe", 
            "email": "john@email.com"
        })
        print(f"Created User: {new_user}")
        all_users = user_model.find_all()
        print(f"All Users: {all_users}")

        first_user = user_model.find_by_id(new_user['id'])
        print(f"First User: {first_user}")

        updated_user = user_model.update(
            {"name": "Jane Doe"},
            {"id": new_user['id']}
        )
        print(f"Updated User: {updated_user}")

        db.close_pool()
