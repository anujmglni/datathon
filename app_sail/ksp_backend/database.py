"""
PostgreSQL Database Connection Manager for KSP Platform.
Supports PostgreSQL (via psycopg2) for Zoho Catalyst Cloud Scale Data Store
and standalone PostgreSQL instances (Supabase, Neon, AWS RDS, Local Postgres).
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_DATA_DIR = BASE_DIR / "files" / "synthetic_data"

# Environment Variables for PostgreSQL Configuration
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "postgres")
PG_DATABASE = os.environ.get("PG_DATABASE", "ksp_db")
DATABASE_URL = os.environ.get("DATABASE_URL", None)

_pg_pool = None

def get_pg_pool():
    """
    Returns a thread-safe PostgreSQL connection pool.
    """
    global _pg_pool
    if _pg_pool is None or _pg_pool.closed:
        try:
            if DATABASE_URL:
                _pg_pool = ThreadedConnectionPool(1, 20, dsn=DATABASE_URL)
            else:
                _pg_pool = ThreadedConnectionPool(
                    1, 20,
                    host=PG_HOST,
                    port=PG_PORT,
                    user=PG_USER,
                    password=PG_PASSWORD,
                    database=PG_DATABASE,
                    connect_timeout=5
                )
            print("✅ PostgreSQL Threaded Connection Pool initialized.")
        except Exception as e:
            print(f"⚠️ Could not connect to PostgreSQL ({e}). Falling back to local SQLite engine...")
            return None
    return _pg_pool

def get_connection():
    """
    Obtains a PostgreSQL connection from the pool, or falls back to local SQLite.
    """
    pool = get_pg_pool()
    if pool:
        conn = pool.getconn()
        return conn, "postgresql"
    
    # Fallback SQLite for seamless local testing without Postgres daemon
    import sqlite3
    sqlite_path = Path(__file__).resolve().parent / "ksp_local.db"
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"

def release_connection(conn, db_type):
    if db_type == "postgresql" and _pg_pool:
        _pg_pool.putconn(conn)
    elif db_type == "sqlite":
        conn.close()

def execute_query(sql_query: str, params: tuple = ()) -> list[dict]:
    """
    Executes a SQL query against PostgreSQL (or SQLite fallback) and returns rows as dictionaries.
    """
    conn, db_type = get_connection()
    try:
        if db_type == "postgresql":
            # Convert SQLite placeholder ? to Postgres %s if needed
            pg_sql = sql_query.replace("?", "%s")
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(pg_sql, params)
                if cur.description:  # SELECT query
                    results = [dict(r) for r in cur.fetchall()]
                else:  # INSERT / UPDATE query
                    conn.commit()
                    results = []
            return results
        else:
            # SQLite fallback
            cursor = conn.cursor()
            cursor.execute(sql_query, params)
            if cursor.description:
                results = [dict(r) for r in cursor.fetchall()]
            else:
                conn.commit()
                results = []
            return results
    finally:
        release_connection(conn, db_type)

def seed_synthetic_data_to_postgres():
    """
    Seeds local CSV synthetic datasets into PostgreSQL.
    """
    if not SYNTHETIC_DATA_DIR.exists():
        print(f"⚠️ Synthetic data directory not found at {SYNTHETIC_DATA_DIR}")
        return

    conn, db_type = get_connection()
    if db_type != "postgresql":
        print("⚠️ Not connected to PostgreSQL. Seeding skipped.")
        release_connection(conn, db_type)
        return

    print("⚡ Seeding PostgreSQL database from synthetic CSV datasets...")
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL or f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    
    for txt_file in SYNTHETIC_DATA_DIR.glob("*.txt"):
        table_name = txt_file.stem
        try:
            df = pd.read_csv(txt_file)
            df.to_sql(table_name.lower(), engine, if_exists="replace", index=False)
            print(f"  Loaded table: {table_name:<25} ({len(df):>6} rows)")
        except Exception as e:
            print(f"  ❌ Error loading {table_name}: {e}")
            
    release_connection(conn, db_type)
    print("✅ PostgreSQL seeding complete.")
