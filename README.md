# Agent Manifest

Standard agent identity for the Cocapn fleet — repo-as-agent.

## What It Is

A `agent.json` file at repo root that defines who an agent is, what it can do, and what constraints it operates under. Combined with `SOUL.md` for personality/values, this forms the complete agent identity.

## The Manifest

```json
{
  "name": "studylog-ai",
  "version": "2.0.0",
  "description": "Your AI study companion",
  "capabilities": ["tutoring", "quizzing", "flashcards", "progress-tracking"],
  "trust_profile": { "initial_score": 0.5, "params": ["consistency", "competence", "transparency"] },
  "equipment": ["crystal-graph", "session-tracker"],
  "skills": ["socratic-method", "spaced-repetition"],
  "rules": ["MUST ALWAYS explain reasoning", "MUST NEVER give direct answers without hints"],
  "duties": { "role": "tutor", "conflict_with": ["grader"] },
  "compliance": ["EU-AI-ACT"],
  "autonomy": { "level": 3, "requires_approval_for": ["delete", "deploy"] }
}
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
