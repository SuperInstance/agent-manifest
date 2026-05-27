# Agent Manifest

Standard agent identity for the Cocapn fleet — repo-as-agent.

## What It Is

A `agent.json` file at repo root that defines who an agent is, what it can do, and what constraints it operates under. Combined with `SOUL.md` for personality/values, this forms the complete agent identity.

This repo provides both a **TypeScript** reference implementation (`agent-manifest.ts`) and a full **Python library** (`agent_manifest/`).

## The Manifest

```json
{
  "name": "studylog-ai",
  "version": "2.0.0",
  "description": "Your AI study companion",
  "capabilities": ["tutoring", "quizzing", "flashcards", "progress-tracking"],
  "trust_profile": { "initial_score": 0.5, "params": [true, false, true, false, true, false, true, false, true, false, true, false] },
  "equipment": ["crystal-graph", "session-tracker"],
  "skills": ["socratic-method", "spaced-repetition"],
  "rules": ["MUST ALWAYS explain reasoning", "MUST NEVER give direct answers without hints"],
  "duties": [{ "role": "tutor", "conflict_with": ["grader"] }],
  "compliance": ["EU-AI-ACT"],
  "autonomy": { "level": 3, "requires_approval_for": ["delete", "deploy"] }
}
```

## Python Library

### Installation

```bash
pip install -e .
```

### Quick Start

```python
from agent_manifest import ManifestBuilder, ManifestValidator

# Build a manifest with the fluent API
manifest = (
    ManifestBuilder()
    .name("studylog-ai")
    .version("2.0.0")
    .description("Your AI study companion")
    .capability("tutoring")
    .capability("quizzing", feature_flag="beta")
    .dependency("math-engine", version_range=">=2.0")
    .duty("tutor", conflicts_with=["grader"])
    .rule("Always explain reasoning")
    .config_field("model", type="string", default="gpt-4")
    .trust(initial_score=0.7, decay_rate=30.0)
    .autonomy_level(3, requires_approval_for=["delete", "deploy"])
    .compliance("EU-AI-ACT")
    .build()
)

# Validate it
result = ManifestValidator().validate(manifest)
assert result.valid
print(manifest.to_json())
```

### Validation

```python
from agent_manifest import ManifestValidator

validator = ManifestValidator(
    require_description=True,
    require_capabilities=False,
    allowed_compliance={"EU-AI-ACT", "SOC2"},
)
result = validator.validate(manifest)
print(result.valid)      # True/False
print(result.errors)     # List of error strings
print(result.warnings)   # List of warning strings
```

### Dependency Resolution

```python
from agent_manifest import DependencyResolver

# Define a dependency graph: agent -> set of dependencies
graph = {
    "study-agent": {"math-engine", "session-store"},
    "math-engine": {" numeral-lib"},
    "session-store": set(),
    "numeral-lib": set(),
}

resolver = DependencyResolver(graph)
result = resolver.resolve()

print(result.ok)           # True if no conflicts/cycles
print(result.order)        # Topological order (deps first)
print(result.cycles)       # List of circular dependency chains
print(result.conflicts)    # Version conflicts if version_map provided
```

### Compatibility Checking

```python
from agent_manifest import CompatibilityChecker

checker = CompatibilityChecker(
    strict_versions=False,
    require_all_capabilities=True,
)
result = checker.check(source_manifest, target_manifest)
print(result.compatible)            # True/False
print(result.missing_capabilities)  # Caps in source but not target
print(result.feature_flag_diffs)    # Flag mismatches
```

### Serialization

```python
# JSON round-trip
json_str = manifest.to_json()
restored = AgentManifest.from_json(json_str)

# Dict conversion
data = manifest.to_dict()
restored = AgentManifest.from_dict(data)

# Load from file
manifest = AgentManifest.load("agent.json")
```

### Duty Conflict Detection

```python
allowed, reason = manifest.check_duty_conflict("grade-student")
if not allowed:
    print(f"Blocked: {reason}")
```

## API Reference

| Module | Class | Purpose |
|--------|-------|---------|
| `manifest` | `AgentManifest` | Core manifest dataclass with serialization |
| `manifest` | `Capability`, `Duty`, `Autonomy`, `TrustProfile`, `Dependency`, `ConfigField` | Component dataclasses |
| `validator` | `ManifestValidator` | Schema validation, semantic checks |
| `resolver` | `DependencyResolver` | Topological sort, cycle/conflict detection |
| `compatibility` | `CompatibilityChecker` | Compare manifests for compatibility |
| `builder` | `ManifestBuilder` | Fluent API for constructing manifests |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## Integration

- **fleet-identity**: Fleet-wide agent discovery
- **governance-equipment**: Policy evaluation uses duties/rules
- **increments-trust**: Trust profile drives autonomy levels
- **ues-protocol**: Manifest published via DISCOVERY events

## From the RA Ideation Library

This module implements RA Action 4 (Repository-as-Agent Identity) from the CheetahClaws Reverse-Actualization Ideation Library. The insight: "clone a repo, get an agent."

---

<i>Built with [Cocapn](https://github.com/Lucineer/cocapn-ai).</i>

Superinstance & Lucineer (DiGennaro et al.)
