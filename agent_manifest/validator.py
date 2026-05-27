"""Manifest validation — schema checks, version constraints, semantic rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import AbstractSet

from .manifest import AgentManifest


@dataclass
class ValidationResult:
    """Result of validating a manifest."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


class ManifestValidator:
    """Validates AgentManifest instances for structural and semantic correctness."""

    SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$")

    def __init__(
        self,
        *,
        require_description: bool = True,
        require_capabilities: bool = False,
        allowed_compliance: AbstractSet[str] | None = None,
        max_name_length: int = 128,
    ) -> None:
        self.require_description = require_description
        self.require_capabilities = require_capabilities
        self.allowed_compliance = allowed_compliance
        self.max_name_length = max_name_length

    def validate(self, manifest: AgentManifest) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # -- name --
        if not manifest.name or not manifest.name.strip():
            errors.append("name is required and must be non-empty")
        elif len(manifest.name) > self.max_name_length:
            errors.append(f"name exceeds max length ({self.max_name_length})")
        if " " in manifest.name:
            warnings.append("name contains spaces — consider hyphens or underscores")

        # -- version --
        if not manifest.version:
            errors.append("version is required")
        elif not self.SEMVER_RE.match(manifest.version):
            errors.append(
                f'version "{manifest.version}" is not valid semver (expected x.y.z with optional pre-release/build)'
            )

        # -- description --
        if self.require_description and not manifest.description.strip():
            errors.append("description is required")

        # -- capabilities --
        if self.require_capabilities and not manifest.capabilities:
            errors.append("at least one capability is required")
        seen_caps: set[str] = set()
        for cap in manifest.capabilities:
            if cap.name in seen_caps:
                errors.append(f'duplicate capability "{cap.name}"')
            seen_caps.add(cap.name)

        # -- trust profile --
        tp = manifest.trust_profile
        if not 0.0 <= tp.initial_score <= 1.0:
            errors.append(f"trust_profile.initial_score must be in [0, 1], got {tp.initial_score}")
        if not 0.0 <= tp.decay_rate <= 100.0:
            errors.append(f"trust_profile.decay_rate must be in [0, 100], got {tp.decay_rate}")
        if len(tp.params) != 12:
            errors.append(f"trust_profile.params must have exactly 12 entries, got {len(tp.params)}")

        # -- autonomy --
        auto = manifest.autonomy
        if not 0 <= auto.level <= 10:
            errors.append(f"autonomy.level must be in [0, 10], got {auto.level}")

        # -- duties --
        seen_roles: set[str] = set()
        for i, duty in enumerate(manifest.duties):
            if not duty.role.strip():
                errors.append(f"duty[{i}]: role is required")
            if duty.role.lower() in seen_roles:
                errors.append(f'duplicate duty role "{duty.role}"')
            seen_roles.add(duty.role.lower())
            for conflict in duty.conflict_with:
                if conflict.lower() == duty.role.lower():
                    errors.append(f'duty "{duty.role}" conflicts with itself')

        # -- dependencies --
        seen_deps: set[str] = set()
        for dep in manifest.dependencies:
            if dep.name in seen_deps:
                errors.append(f'duplicate dependency "{dep.name}"')
            seen_deps.add(dep.name)

        # -- compliance --
        if self.allowed_compliance is not None:
            for tag in manifest.compliance:
                if tag not in self.allowed_compliance:
                    warnings.append(f'unknown compliance tag "{tag}"')

        # -- config schema --
        seen_keys: set[str] = set()
        for cf in manifest.config_schema:
            if cf.key in seen_keys:
                errors.append(f'duplicate config key "{cf.key}"')
            seen_keys.add(cf.key)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
