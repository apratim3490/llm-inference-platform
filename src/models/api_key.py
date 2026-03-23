"""
API Key Data Model

Frozen dataclass representing an API key with its tier and limits.
Stored in Redis (hashed), looked up on every request.
"""
from dataclasses import dataclass

from src.models.enums import Tier


@dataclass(frozen = True)
class APIKey:
    key_hash: str
    name: str
    tier: Tier
    rpm_limit: int
    tpm_limit: int
    is_active: bool = True

TIER_LIMITS = {
    Tier.FREE: {"rpm": 10, "tpm": 10000},
    Tier.PRO: {"rpm": 50, "tpm": 100000},
    Tier.ADMIN: {"rpm": 300, "tpm": 1000000}
}

