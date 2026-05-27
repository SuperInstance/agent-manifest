"""Fluent builder API for constructing AgentManifest instances."""

from __future__ import annotations

from .manifest import (
    AgentManifest,
    Autonomy,
    Capability,
    ConfigField,
    Dependency,
    Duty,
    TrustProfile,
)


class ManifestBuilder:
    """Fluent builder for :class:`AgentManifest`.

    Usage::

        manifest = (
            ManifestBuilder()
            .name("my-agent")
            .version("1.0.0")
            .description("Does cool stuff")
            .capability("tutoring")
            .capability("quizzing", feature_flag="beta")
            .dependency("math-engine", version_range=">=2.0")
            .duty("tutor", conflicts_with=["grader"])
            .rule("Always explain reasoning")
            .config_field("model", type="string", default="gpt-4")
            .trust(initial_score=0.7, decay_rate=30.0)
            .autonomy_level(5, requires_approval_for=["delete"])
            .build()
        )
    """

    def __init__(self) -> None:
        self._name: str = ""
        self._version: str = "0.1.0"
        self._description: str = ""
        self._capabilities: list[Capability] = []
        self._dependencies: list[Dependency] = []
        self._config_fields: list[ConfigField] = []
        self._equipment: list[str] = []
        self._skills: list[str] = []
        self._rules: list[str] = []
        self._duties: list[Duty] = []
        self._compliance: list[str] = []
        self._trust_profile: TrustProfile | None = None
        self._autonomy: Autonomy | None = None

    def name(self, value: str) -> ManifestBuilder:
        self._name = value
        return self

    def version(self, value: str) -> ManifestBuilder:
        self._version = value
        return self

    def description(self, value: str) -> ManifestBuilder:
        self._description = value
        return self

    def capability(self, name: str, *, feature_flag: str | None = None) -> ManifestBuilder:
        self._capabilities.append(Capability(name=name, feature_flag=feature_flag))
        return self

    def dependency(self, name: str, *, version_range: str | None = None) -> ManifestBuilder:
        self._dependencies.append(Dependency(name=name, version_range=version_range))
        return self

    def config_field(
        self,
        key: str,
        *,
        type: str = "string",
        required: bool = True,
        default: object = None,
        description: str = "",
    ) -> ManifestBuilder:
        self._config_fields.append(
            ConfigField(key=key, type=type, required=required, default=default, description=description)
        )
        return self

    def equipment(self, *names: str) -> ManifestBuilder:
        self._equipment.extend(names)
        return self

    def skill(self, *names: str) -> ManifestBuilder:
        self._skills.extend(names)
        return self

    def rule(self, *rules: str) -> ManifestBuilder:
        self._rules.extend(rules)
        return self

    def duty(self, role: str, *, conflicts_with: list[str] | tuple[str, ...] | None = None) -> ManifestBuilder:
        self._duties.append(Duty(role=role, conflict_with=tuple(conflicts_with or ())))
        return self

    def compliance(self, *tags: str) -> ManifestBuilder:
        self._compliance.extend(tags)
        return self

    def trust(
        self,
        *,
        initial_score: float = 0.5,
        decay_rate: float = 25.0,
        params: tuple[bool, ...] | list[bool] | None = None,
    ) -> ManifestBuilder:
        self._trust_profile = TrustProfile(
            initial_score=initial_score,
            decay_rate=decay_rate,
            params=tuple(params) if params else (False,) * 12,
        )
        return self

    def autonomy_level(
        self,
        level: int,
        *,
        requires_approval_for: list[str] | tuple[str, ...] | None = None,
    ) -> ManifestBuilder:
        self._autonomy = Autonomy(
            level=level,
            requires_approval_for=tuple(requires_approval_for or ()),
        )
        return self

    def build(self) -> AgentManifest:
        return AgentManifest(
            name=self._name,
            version=self._version,
            description=self._description,
            capabilities=tuple(self._capabilities),
            dependencies=tuple(self._dependencies),
            config_schema=tuple(self._config_fields),
            equipment=tuple(self._equipment),
            skills=tuple(self._skills),
            rules=tuple(self._rules),
            duties=tuple(self._duties),
            compliance=tuple(self._compliance),
            trust_profile=self._trust_profile or TrustProfile(),
            autonomy=self._autonomy or Autonomy(),
        )
