from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True, kw_only=True)
class User:
    """System user entity."""
    id: str
    username: str
    full_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
