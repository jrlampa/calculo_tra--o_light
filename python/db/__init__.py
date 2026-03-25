"""
Database module initialization.
This module provides database connection and client management.
"""

from .supabase_client import get_supabase_client, SupabaseClient
from .pool import get_connection_pool, close_connection_pool

__all__ = [
    'get_supabase_client',
    'SupabaseClient', 
    'get_connection_pool',
    'close_connection_pool'
]