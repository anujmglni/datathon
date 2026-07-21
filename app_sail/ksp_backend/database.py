"""
PostgreSQL Database Connection Manager for KSP Platform.
Supports PostgreSQL (via psycopg2) for Zoho Catalyst Cloud Scale Data Store
and standalone PostgreSQL instances (Supabase, Neon, AWS RDS, Local Postgres).
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
import getpass

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
                try:
                    _pg_pool = ThreadedConnectionPool(
                        1, 20,
                        host=PG_HOST,
                        port=PG_PORT,
                        user=PG_USER,
                        password=PG_PASSWORD,
                        database=PG_DATABASE,
                        connect_timeout=3
                    )
                except Exception:
                    # Fallback to local system user (macOS Homebrew Postgres)
                    sys_user = getpass.getuser()
                    _pg_pool = ThreadedConnectionPool(
                        1, 20,
                        host=PG_HOST,
                        port=PG_PORT,
                        user=sys_user,
                        database=PG_DATABASE,
                        connect_timeout=3
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
    
    # Ensure AuditLog table exists in SQLite
    conn.execute("""
        CREATE TABLE IF NOT EXISTS AuditLog (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID TEXT,
            UserRole TEXT,
            QueryString TEXT,
            SQLExecuted TEXT,
            RowsTouched INTEGER,
            Timestamp INTEGER
        );
    """)
    conn.commit()
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
                if params:
                    cur.execute(pg_sql, params)
                else:
                    cur.execute(pg_sql)
                if cur.description:  # SELECT query
                    results = [dict(r) for r in cur.fetchall()]
                else:  # INSERT / UPDATE query
                    conn.commit()
                    results = []
            return results
        else:
            # SQLite fallback: convert Postgres ILIKE to SQLite LIKE
            sqlite_sql = sql_query.replace(" ILIKE ", " LIKE ").replace(" ilike ", " LIKE ")
            cursor = conn.cursor()
            cursor.execute(sqlite_sql, params)
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
    import pandas as pd
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_data_dir = base_dir / "files" / "synthetic_data"

    if not synthetic_data_dir.exists():
        print(f"⚠️ Synthetic data directory not found at {synthetic_data_dir}")
        return

    conn, db_type = get_connection()
    if db_type != "postgresql":
        print("⚠️ Not connected to PostgreSQL. Seeding skipped.")
        release_connection(conn, db_type)
        return

    print("⚡ Seeding PostgreSQL database from synthetic CSV datasets...")
    from sqlalchemy import create_engine, text
    try:
        engine = create_engine(DATABASE_URL or f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}")
        # Test connection
        with engine.connect() as test_conn:
            pass
    except Exception:
        sys_user = getpass.getuser()
        engine = create_engine(f"postgresql://{sys_user}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    
    # Create auditlog table in PostgreSQL
    with engine.connect() as pconn:
        pconn.execute(text("""
            CREATE TABLE IF NOT EXISTS auditlog (
                logid SERIAL PRIMARY KEY,
                userid TEXT,
                userrole TEXT,
                querystring TEXT,
                sqlexecuted TEXT,
                rowstouched INTEGER,
                timestamp BIGINT
            );
        """))
        pconn.commit()

    for txt_file in SYNTHETIC_DATA_DIR.glob("*.txt"):
        table_name = txt_file.stem
        try:
            df = pd.read_csv(txt_file)
            df.columns = [c.lower() for c in df.columns]
            df.to_sql(table_name.lower(), engine, if_exists="replace", index=False)
            print(f"  Loaded table: {table_name:<25} ({len(df):>6} rows)")
        except Exception as e:
            print(f"  ❌ Error loading {table_name}: {e}")
            
    release_connection(conn, db_type)
    print("✅ PostgreSQL seeding complete.")
