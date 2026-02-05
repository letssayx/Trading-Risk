from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

class LicenseStatus(Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    TAMPERED = "TAMPERED"

@dataclass(frozen=True, kw_only=True)
class License:
    """License file contract."""
    id: str
    client_name: str
    issued_at: datetime
    expires_at: datetime
    signature: str
    hardware_binding: Optional[str] = None # Hash of hardware ID if bound
    features: Dict[str, bool] = field(default_factory=dict)

@dataclass(frozen=True, kw_only=True)
class LicenseValidationResult:
    """Output of license check."""
    status: LicenseStatus
    message: str
    license_details: Optional[License] = None
