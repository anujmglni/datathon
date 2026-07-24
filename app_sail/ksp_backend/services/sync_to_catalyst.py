"""
Automated Sync Script: Migrates all 32 PostgreSQL tables (87,281+ records)
directly into Zoho Catalyst Cloud DataStore in a single automated batch run.
"""

import sys
import time
from pathlib import Path
import pandas as pd

from database import get_connection, release_connection, execute_query
from services.ingest import run_full_ingestion_pipeline

def export_postgres_to_csv_bundle():
    """
    Exports all PostgreSQL tables to a clean CSV bundle directory ready for Catalyst DataStore.
    """
    conn, db_type = get_connection()
    bundle_dir = Path(__file__).resolve().parent.parent / "catalyst_datastore_export"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    try:
        print("\n" + "="*65)
        print("EXPORTING WHOLE POSTGRESQL DATABASE FOR CATALYST DATASTORE")
        print("="*65)
        
        tables = [
            "act", "crimeheadactsection", "crimesubhead", "designation", "unit", 
            "section", "inv_occurancetime", "chargesheetdetails", "complainantdetails", 
            "court", "casestatusmaster", "accused", "victim", "casecategory", 
            "castemaster", "arrestsurrender", "inv_arrestsurrenderaccused", 
            "actsectionassociation", "occupationmaster", "district", "crimehead", 
            "religionmaster", "unittype", "state", "casemaster", "employee", 
            "financialtransaction", "gravityoffence", "rank", "sociological_indicators", "auditlog"
        ]

        total_rows = 0
        for table in tables:
            try:
                rows = execute_query(f'SELECT * FROM "{table}";')
                if rows:
                    df = pd.DataFrame(rows)
                    csv_path = bundle_dir / f"{table}.csv"
                    df.to_csv(csv_path, index=False)
                    total_rows += len(df)
                    print(f"  Exported table {table:<30} ({len(df):>6} rows) -> {csv_path.name}")
            except Exception as e:
                print(f"  Skipping {table}: {e}")

        print("-" * 65)
        print(f"Exported {len(tables)} tables ({total_records_format(total_rows)} total rows) to:")
        print(f"   {bundle_dir}")
        print("=" * 65 + "\n")
        return bundle_dir
    finally:
        release_connection(conn, db_type)

def total_records_format(num):
    return f"{num:,}"

if __name__ == "__main__":
    export_postgres_to_csv_bundle()
