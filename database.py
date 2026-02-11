
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from config import settings

class DatabaseManager:
    """
    Manages PostgreSQL connection pool and provides context managers
    for database operations with automatic transaction handling
    """
    
    def __init__(self):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
    @contextmanager
    def get_cursor(self, commit=True):
        """
        Context manager for database operations
        Automatically commits on success, rolls back on error
        """
        conn = self.pool.getconn()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        self.pool.closeall()

# Global database manager instance
db_manager = DatabaseManager()