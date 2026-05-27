"""agent-manifest — Declarative agent manifests for Python."""

from .manifest import AgentManifest, Capability, TrustProfile, Duty, Autonomy
from .validator import ManifestValidator
from .resolver import DependencyResolver
from .compatibility import CompatibilityChecker
from .builder import ManifestBuilder

__all__ = [
    "AgentManifest",
    "Capability",
    "TrustProfile",
    "Duty",
    "Autonomy",
    "ManifestValidator",
    "DependencyResolver",
    "CompatibilityChecker",
    "ManifestBuilder",
]
__version__ = "0.1.0"
