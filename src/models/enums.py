"""
Enumerations

Shared enums used across the application.
"""

from enum import Enum


class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ADMIN = "admin"


# TODO: Phase 3 - Priority enum (P0, P1, P2)
# TODO: Phase 6 - CircuitState enum (closed, open, half_open)
