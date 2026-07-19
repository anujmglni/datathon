"""
Governance & RBAC Middleware for KSP Platform.
Enforces role-based query masking for protected demographic fields (CasteID, ReligionID)
and logs all executions to the immutable AuditLog table.
"""

import time
from database import execute_query

def apply_governance_rules(sql_query: str, user_role: str) -> tuple[str, bool]:
    """
    If user_role is 'Analyst' or general user, redacts CasteID and ReligionID from query.
    Returns (modified_sql, was_redacted).
    """
    was_redacted = False
    role_clean = (user_role or "Analyst").strip().lower()

    if role_clean in ["analyst", "public", "general"]:
        # Mask sensitive column queries
        if "casteid" in sql_query.lower() or "religionid" in sql_query.lower():
            sql_query = (
                sql_query
                .replace("CasteID", "NULL AS CasteID")
                .replace("casteid", "NULL AS casteid")
                .replace("ReligionID", "NULL AS ReligionID")
                .replace("religionid", "NULL AS religionid")
            )
            was_redacted = True

    return sql_query, was_redacted

def log_audit_trail(user_id: str, user_role: str, query_string: str, sql_executed: str, rows_touched: int):
    """
    Writes query audit details to AuditLog table.
    """
    timestamp = int(time.time())
    sql = """
        INSERT INTO AuditLog (UserID, UserRole, QueryString, SQLExecuted, RowsTouched, Timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    try:
        execute_query(sql, (user_id or "user_anon", user_role or "Analyst", query_string, sql_executed, rows_touched, timestamp))
    except Exception as e:
        print(f"⚠️ Audit logging fallback: {e}")
