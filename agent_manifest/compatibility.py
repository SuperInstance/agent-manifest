"""Compatibility checking between manifests — versions, capabilities, feature flags."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import AbstractSet

from .manifest import AgentManifest, Capability


@dataclass
class CompatibilityResult:
    """Result of comparing two manifests for compatibility."""

    compatible: bool
    issues: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)
    extra_capabilities: list[str] = field(default_factory=list)
    feature_flag_diffs: dict[str, tuple[str | None, str | None]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.compatible


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a simple semver-like version string into a comparable tuple."""
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


class CompatibilityChecker:
    """Compare two manifests for forward/backward compatibility."""

    def __init__(
        self,
        *,
        strict_versions: bool = False,
        require_all_capabilities: bool = True,
        ignore_feature_flags: bool = False,
        allowed_compliance_tags: AbstractSet[str] | None = None,
    ) -> None:
        self.strict_versions = strict_versions
        self.require_all_capabilities = require_all_capabilities
        self.ignore_feature_flags = ignore_feature_flags
        self.allowed_compliance = allowed_compliance_tags

    def check(self, source: AgentManifest, target: AgentManifest) -> CompatibilityResult:
        """Check if *source* is compatible with *target*.

        Typical use: source is a dependency requirement, target is the actual available version.
        """
        issues: list[str] = []
        missing: list[str] = []
        extra: list[str] = []
        flag_diffs: dict[str, tuple[str | None, str | None]] = {}

        # -- version compatibility --
        sv = _parse_version(source.version)
        tv = _parse_version(target.version)
        if self.strict_versions and sv != tv:
            issues.append(f"Version mismatch: source={source.version}, target={target.version}")
        elif tv < sv:
            issues.append(
                f"Target version ({target.version}) is older than source ({source.version})"
            )

        # -- capability comparison --
        source_caps = {c.name: c for c in source.capabilities}
        target_caps = {c.name: c for c in target.capabilities}

        for name, cap in source_caps.items():
            if name not in target_caps:
                missing.append(name)
            elif not self.ignore_feature_flags:
                src_flag = cap.feature_flag
                tgt_flag = target_caps[name].feature_flag
                src_flag = cap.feature_flag
                tgt_flag = target_caps[name].feature_flag
                if src_flag != tgt_flag:
                    flag_diffs[name] = (src_flag, tgt_flag)
                    issues.append(
                        f'Capability "{name}" feature flag mismatch: source={src_flag!r}, target={tgt_flag!r}'
                    )

        if self.require_all_capabilities and missing:
            issues.append(
                f"Missing capabilities: {', '.join(missing)}"
            )

        if not self.require_all_capabilities:
            for name in target_caps:
                if name not in source_caps:
                    extra.append(name)

        # -- compliance tags --
        if self.allowed_compliance is not None:
            for tag in source.compliance:
                if tag not in self.allowed_compliance:
                    issues.append(f"Source has unrecognized compliance tag: {tag}")
            for tag in target.compliance:
                if tag not in self.allowed_compliance:
                    issues.append(f"Target has unrecognized compliance tag: {tag}")

        compatible = len(issues) == 0
        return CompatibilityResult(
            compatible=compatible,
            issues=issues,
            missing_capabilities=missing,
            extra_capabilities=extra,
            feature_flag_diffs=flag_diffs,
        )

    @staticmethod
    def capability_diff(
        source: AgentManifest, target: AgentManifest
    ) -> tuple[set[str], set[str], set[str]]:
        """Return (shared, only_in_source, only_in_target) capability name sets."""
        s = source.capability_names()
        t = target.capability_names()
        return s & t, s - t, t - s
