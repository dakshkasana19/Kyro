"""
Kyro — Supabase Database Manager

Initialises a singleton Supabase client and exposes
CRUD wrapper functions with error handling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.core.config import settings
from app.core.errors import DatabaseError
from app.core.logging import get_logger

logger = get_logger("db")

_client: Optional[Client] = None


def get_client() -> Client:
    """Return the initialised Supabase admin client (lazy singleton)."""
    global _client
    if _client is None:
        settings.supabase.validate()
        _client = create_client(settings.supabase.URL, settings.supabase.KEY)
        logger.info("Supabase admin client initialised for %s", settings.supabase.URL)
    return _client


def get_user_client(access_token: str) -> Client:
    """Create and return a Supabase client scoped to a specific user's JWT."""
    # We create a new client for each request to ensure isolation and RLS adherence.
    client = create_client(settings.supabase.URL, settings.supabase.KEY)
    client.postgrest.auth(access_token)
    return client


# ------------------------------------------------------------------
# Generic CRUD helpers
# ------------------------------------------------------------------

def insert_row(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a single row and return the created record."""
    try:
        response = get_client().table(table).insert(data).execute()
        if response.data:
            logger.debug("INSERT %s → %s", table, response.data[0].get("id"))
            return response.data[0]
        raise DatabaseError(f"Insert into '{table}' returned no data.")
    except DatabaseError:
        raise
    except Exception as exc:
        logger.exception("DB insert failed [table=%s]", table)
        raise DatabaseError(f"Failed to insert into '{table}': {exc}") from exc


def select_rows(
    table: str,
    columns: str = "*",
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Select rows with optional filters, ordering, and limit."""
    try:
        query = get_client().table(table).select(columns)
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        if order_by:
            desc = order_by.startswith("-")
            col = order_by.lstrip("-")
            query = query.order(col, desc=desc)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return response.data or []
    except Exception as exc:
        logger.exception("DB select failed [table=%s]", table)
        raise DatabaseError(f"Failed to select from '{table}': {exc}") from exc


def select_by_id(table: str, record_id: str, columns: str = "*") -> Optional[Dict[str, Any]]:
    """Fetch a single row by UUID primary key."""
    rows = select_rows(table, columns=columns, filters={"id": record_id}, limit=1)
    return rows[0] if rows else None


def update_row(table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a row by id and return the updated record."""
    try:
        response = (
            get_client()
            .table(table)
            .update(data)
            .eq("id", record_id)
            .execute()
        )
        if response.data:
            logger.debug("UPDATE %s id=%s", table, record_id)
            return response.data[0]
        raise DatabaseError(f"Update on '{table}' id={record_id} returned no data.")
    except DatabaseError:
        raise
    except Exception as exc:
        logger.exception("DB update failed [table=%s, id=%s]", table, record_id)
        raise DatabaseError(f"Failed to update '{table}': {exc}") from exc


def delete_row(table: str, record_id: str) -> bool:
    """Delete a row by id. Returns True on success."""
    try:
        get_client().table(table).delete().eq("id", record_id).execute()
        logger.debug("DELETE %s id=%s", table, record_id)
        return True
    except Exception as exc:
        logger.exception("DB delete failed [table=%s, id=%s]", table, record_id)
        raise DatabaseError(f"Failed to delete from '{table}': {exc}") from exc


def rpc(function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Call a Supabase RPC (Postgres function)."""
    try:
        response = get_client().rpc(function_name, params or {}).execute()
        return response.data
    except Exception as exc:
        logger.exception("RPC call failed [fn=%s]", function_name)
        raise DatabaseError(f"RPC '{function_name}' failed: {exc}") from exc
