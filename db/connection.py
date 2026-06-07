"""Nuke Asset Browser — PostgreSQL connection pool.

Manages a pool of database connections with **lazy initialisation**
and **graceful degradation** — if PostgreSQL is unreachable the
application continues to work (using the JSON fallback).

Usage::

    from asset_browser.db.connection import pg_pool

    if pg_pool.available:
        rows = pg_pool.fetch_all("SELECT * FROM browser.drafts")
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Optional

import psycopg2
from psycopg2 import pool as _pg_pool
from psycopg2.extras import RealDictCursor

from asset_browser.utils.config import config
from asset_browser.utils.logger import get_logger

logger = get_logger(__name__)


class PgPool:
    """PostgreSQL connection pool (``SimpleConnectionPool``).

    The pool is **not** created at instantiation time — call
    :meth:`ensure_connected` to establish connections, or rely on
    the automatic first-use initialisation in :meth:`fetch_all` /
    :meth:`execute`.
    """

    def __init__(self) -> None:
        self._pool: _pg_pool.SimpleConnectionPool | None = None
        self._available: bool = False
        self._min_conn = 1
        self._max_conn = 5

    # ── Public interface ────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """``True`` if the pool has been successfully connected."""
        return self._available

    def ensure_connected(self) -> bool:
        """Try to establish the connection pool.

        Returns ``True`` if the pool is now available.  Safe to call
        repeatedly — subsequent calls are no-ops if already connected.
        """
        if self._available:
            return True
        return self._connect()

    def disconnect(self) -> None:
        """Close all connections and reset the pool."""
        if self._pool is not None:
            try:
                self._pool.closeall()
            except Exception:
                pass
        self._pool = None
        self._available = False
        logger.info("PG pool disconnected")

    @contextmanager
    def _get_conn(self) -> Generator[Any, None, None]:
        """Yield a connection from the pool (context manager).

        Yields:
            A psycopg2 connection, or ``None`` if the pool is down.
        """
        if not self.ensure_connected():
            yield None
            return

        conn = None
        try:
            conn = self._pool.getconn()  # type: ignore[union-attr]
            yield conn
        except Exception as exc:
            logger.error("Failed to get PG connection: %s", exc)
            yield None
        finally:
            if conn is not None:
                self._pool.putconn(conn)  # type: ignore[union-attr]

    def fetch_all(
        self,
        query: str,
        params: tuple | dict | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return all result rows as dicts.

        Args:
            query: SQL query with ``%(name)s`` or ``%s`` placeholders.
            params: Query parameters.

        Returns:
            List of row dicts.  Empty if pool is unavailable.
        """
        with self._get_conn() as conn:
            if conn is None:
                return []
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    conn.commit()  # commit for write-capable queries (INSERT…RETURNING etc.)
                    return [dict(r) for r in rows]
            except Exception as exc:
                conn.rollback()
                logger.error("PG fetch_all failed: %s", exc)
                return []

    def fetch_one(
        self,
        query: str,
        params: tuple | dict | None = None,
    ) -> Optional[dict[str, Any]]:
        """Execute a SELECT and return the first row, or ``None``.

        Args:
            query: SQL query.
            params: Query parameters.

        Returns:
            A row dict, or ``None`` if no result or pool unavailable.
        """
        rows = self.fetch_all(query, params)
        return rows[0] if rows else None

    def execute(
        self,
        query: str,
        params: tuple | dict | None = None,
    ) -> int:
        """Execute an INSERT / UPDATE / DELETE / DDL statement.

        Args:
            query: SQL statement with placeholders.
            params: Query parameters.

        Returns:
            Number of rows affected (or 0 for DDL), or ``-1`` on failure.
        """
        with self._get_conn() as conn:
            if conn is None:
                return -1
            try:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit()
                    return cur.rowcount if cur.rowcount >= 0 else 0
            except Exception as exc:
                conn.rollback()
                logger.error("PG execute failed: %s", exc)
                return -1

    def execute_many(
        self,
        query: str,
        params_list: list[tuple | dict],
    ) -> int:
        """Execute the same query with multiple parameter sets.

        Args:
            query: SQL statement.
            params_list: List of parameter tuples/dicts.

        Returns:
            Number of rows affected, or ``-1`` on failure.
        """
        with self._get_conn() as conn:
            if conn is None:
                return -1
            try:
                with conn.cursor() as cur:
                    psycopg2.extras.execute_batch(cur, query, params_list)
                    conn.commit()
                    return cur.rowcount
            except Exception as exc:
                conn.rollback()
                logger.error("PG execute_many failed: %s", exc)
                return -1

    # ── Internal ────────────────────────────────────────────────────────

    def _connect(self) -> bool:
        """Create the connection pool.

        Returns ``True`` on success.  Logs and sets ``_available = False``
        on failure — never raises.
        """
        try:
            self._pool = _pg_pool.SimpleConnectionPool(
                self._min_conn,
                self._max_conn,
                host=config.pg_host,
                port=config.pg_port,
                dbname=config.pg_database,
                user=config.pg_user or None,
                password=config.pg_password or None,
                connect_timeout=3,
            )
            self._available = True
            logger.info(
                "PG pool ready — %s:%d/%s",
                config.pg_host, config.pg_port, config.pg_database,
            )
            return True
        except Exception as exc:
            logger.warning("PG pool unavailable: %s", exc)
            self._available = False
            return False


# ── Module-level singleton ──────────────────────────────────────────────
pg_pool = PgPool()
