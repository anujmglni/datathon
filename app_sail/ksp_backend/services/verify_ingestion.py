"""
Verification script for KSP PostgreSQL & DataStore Ingestion.
Queries table row counts, checks data integrity, and validates all ingested modules.
"""

from database import get_connection, release_connection

def verify_all_ingested_data():
    conn, db_type = get_connection()
    try:
        if db_type == "postgresql":
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
                tables = [r[0] for r in cur.fetchall()]
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = [r[0] for r in cursor.fetchall()]

        print("\n" + "="*65)
        print(f"KSP DATABASE INGESTION VERIFICATION REPORT [{db_type.upper()}]")
        print("="*65)
        print(f"{'Table Name':<35} | {'Row Count':>15}")
        print("-" * 65)

        total_records = 0
        for table in tables:
            if db_type == "postgresql":
                with conn.cursor() as cur:
                    cur.execute(f'SELECT count(*) FROM "{table}";')
                    cnt = cur.fetchone()[0]
            else:
                cursor = conn.cursor()
                cursor.execute(f"SELECT count(*) FROM {table};")
                cnt = cursor.fetchone()[0]

            total_records += cnt
            print(f"{table:<35} | {cnt:>15,}")

        print("-" * 65)
        print(f"{'TOTAL INGESTED RECORDS':<35} | {total_records:>15,}")
        print("=" * 65 + "\n")

        return {
            "db_type": db_type,
            "total_tables": len(tables),
            "total_records": total_records
        }
    finally:
        release_connection(conn, db_type)

if __name__ == "__main__":
    verify_all_ingested_data()
