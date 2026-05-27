"""Core manifest data structures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Capability:
    """A single agent capability with an optional feature flag."""

    name: str
    feature_flag: str | None = None

    def __str__(self) -> str:
        if self.feature_flag:
            return f"{self.name}[{self.feature_flag}]"
        return self.name


@dataclass(frozen=True)
class TrustProfile:
    """Trust scoring parameters for the agent."""

    initial_score: float = 0.5
    decay_rate: float = 25.0
    params: tuple[bool, ...] = (False,) * 12

    def __post_init__(self) -> None:
        if not 0.0 <= self.initial_score <= 1.0:
            raise ValueError(f"initial_score must be in [0, 1], got {self.initial_score}")
        if not 0.0 <= self.decay_rate <= 100.0:
            raise ValueError(f"decay_rate must be in [0, 100], got {self.decay_rate}")
        if len(self.params) != 12:
            raise ValueError(f"params must have exactly 12 entries, got {len(self.params)}")


@dataclass(frozen=True)
class Duty:
    """A role assignment with conflict-of-interest tracking."""

    role: str
    conflict_with: tuple[str, ...] = ()

    def conflicts(self, other_role: str) -> bool:
        return other_role.lower() in {c.lower() for c in self.conflict_with}


@dataclass(frozen=True)
class Autonomy:
    """Autonomy level and approval gates."""

    level: int = 0
    requires_approval_for: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.level <= 10:
            raise ValueError(f"level must be in [0, 10], got {self.level}")


@dataclass(frozen=True)
class Dependency:
    """A dependency on another agent or package, with optional version constraint."""

    name: str
    version_range: str | None = None  # PEP 440-style, e.g. ">=1.0,<3.0"

    def __str__(self) -> str:
        if self.version_range:
            return f"{self.name}{self.version_range}"
        return self.name


@dataclass(frozen=True)
class ConfigField:
    """A single configuration schema field."""

    key: str
    type: str = "string"
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass(frozen=True)
class AgentManifest:
    """Declarative specification of an agent's identity, capabilities, and constraints."""

    name: str
    version: str
    description: str = ""
    capabilities: tuple[Capability, ...] = ()
    trust_profile: TrustProfile = field(default_factory=TrustProfile)
    dependencies: tuple[Dependency, ...] = ()
    config_schema: tuple[ConfigField, ...] = ()
    equipment: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    duties: tuple[Duty, ...] = ()
    compliance: tuple[str, ...] = ()
    autonomy: Autonomy = field(default_factory=Autonomy)

    # ---- convenience helpers ----

    def capability_names(self) -> set[str]:
        return {c.name for c in self.capabilities}

    def dependency_names(self) -> set[str]:
        return {d.name for d in self.dependencies}

    def duty_for(self, role: str) -> Duty | None:
        role_lower = role.lower()
        for d in self.duties:
            if d.role.lower() == role_lower:
                return d
        return None

    def check_duty_conflict(self, action: str) -> tuple[bool, str]:
        """Return (allowed, reason) for *action* against duty conflict rules."""
        action_lower = action.lower()
        for duty in self.duties:
            role_lower = duty.role.lower()
            if action_lower == role_lower or role_lower in action_lower:
                for conflict in duty.conflict_with:
                    if conflict.lower() in action_lower:
                        return False, f'Action "{action}" conflicts with duty role "{duty.role}"'
        return True, "No duty conflicts detected"

    # ---- serialization ----

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": [
                {"name": c.name, "feature_flag": c.feature_flag} if c.feature_flag else c.name
                for c in self.capabilities
            ],
            "trust_profile": {
                "initial_score": self.trust_profile.initial_score,
                "decay_rate": self.trust_profile.decay_rate,
                "params": list(self.trust_profile.params),
            },
            "dependencies": [
                {"name": d.name, "version_range": d.version_range}
                if d.version_range
                else d.name
                for d in self.dependencies
            ],
            "config_schema": [
                {
                    "key": f.key,
                    "type": f.type,
                    "required": f.required,
                    "default": f.default,
                    "description": f.description,
                }
                for f in self.config_schema
            ],
            "equipment": list(self.equipment),
            "skills": list(self.skills),
            "rules": list(self.rules),
            "duties": [
                {"role": duty.role, "conflict_with": list(duty.conflict_with)}
                for duty in self.duties
            ],
            "compliance": list(self.compliance),
            "autonomy": {
                "level": self.autonomy.level,
                "requires_approval_for": list(self.autonomy.requires_approval_for),
            },
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentManifest:
        caps = []
        for c in data.get("capabilities", []):
            if isinstance(c, str):
                caps.append(Capability(name=c))
            elif isinstance(c, dict):
                caps.append(Capability(name=c["name"], feature_flag=c.get("feature_flag")))

        deps = []
        for d in data.get("dependencies", []):
            if isinstance(d, str):
                deps.append(Dependency(name=d))
            elif isinstance(d, dict):
                deps.append(Dependency(name=d["name"], version_range=d.get("version_range")))

        fields = []
        for f in data.get("config_schema", []):
            fields.append(
                ConfigField(
                    key=f["key"],
                    type=f.get("type", "string"),
                    required=f.get("required", True),
                    default=f.get("default"),
                    description=f.get("description", ""),
                )
            )

        tp_data = data.get("trust_profile", {})
        trust_profile = TrustProfile(
            initial_score=tp_data.get("initial_score", 0.5),
            decay_rate=tp_data.get("decay_rate", 25.0),
            params=tuple(tp_data.get("params", [False] * 12)),
        )

        duties = []
        for duty in data.get("duties", []):
            if isinstance(duty, dict):
                duties.append(
                    Duty(role=duty["role"], conflict_with=tuple(duty.get("conflict_with", [])))
                )

        auto_data = data.get("autonomy", {})
        autonomy = Autonomy(
            level=auto_data.get("level", 0),
            requires_approval_for=tuple(auto_data.get("requires_approval_for", [])),
        )

        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            capabilities=tuple(caps),
            trust_profile=trust_profile,
            dependencies=tuple(deps),
            config_schema=tuple(fields),
            equipment=tuple(data.get("equipment", [])),
            skills=tuple(data.get("skills", [])),
            rules=tuple(data.get("rules", [])),
            duties=tuple(duties),
            compliance=tuple(data.get("compliance", [])),
            autonomy=autonomy,
        )

    @classmethod
    def from_json(cls, json_str: str) -> AgentManifest:
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, path: str) -> AgentManifest:
        with open(path) as f:
            return cls.from_json(f.read())
