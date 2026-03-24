"""
Database schema builders.

Thin compatibility module that re-exports split schema builder functions.
"""

from schema_tables import _create_tables
from schema_indexes import _create_indexes
from schema_triggers import _create_triggers
from schema_procedures import _create_procedures

__all__ = ['_create_tables', '_create_indexes', '_create_triggers', '_create_procedures']
