from typing import Dict, Any, List
from .base import BaseDomain
from .generic import GenericDomain
from .travel import TravelDomain
from .shopping import ShoppingDomain
from .study import StudyDomain
from .code import CodeDomain
from .entertainment import EntertainmentDomain

_DOMAINS = {
    "generic": GenericDomain(),
    "travel": TravelDomain(),
    "shopping": ShoppingDomain(),
    "study": StudyDomain(),
    "code": CodeDomain(),
    "entertainment": EntertainmentDomain()
}

def get_domain(name: str) -> BaseDomain:
    """Get domain instance by name."""
    return _DOMAINS.get(name.lower(), _DOMAINS["generic"])

def domain_exists(name: str) -> bool:
    """Check if domain exists."""
    return name.lower() in _DOMAINS

def list_domains() -> List[str]:
    """List all registered domains."""
    return list(_DOMAINS.keys())
