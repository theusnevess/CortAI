# ASSET_AGENT_DECISION_STANDARD_v1_0

## Objective

Define the mandatory decision standard for the Asset Agent.

The agent must:
- decide visual representation per segment
- ensure narrative alignment
- ensure system compatibility
- remain deterministic and auditable

---

## Core Principle

The Asset Agent does not select images.

It decides the visual representation of the narrative.

---

## Decision Unit

All decisions are made per segment:
- hook
- setup
- payoff

Never per video as a whole.

---

## Mandatory Decision Flow

For each segment, the agent must define:

1. Entity  
What is being shown?

2. Anomaly  
What is wrong or unusual?

3. Photographability  
Can this exist in the real world?

4. Source Decision  
- real (default)
- ai (exception)

5. Narrative Adequacy  
Does the asset fulfill the segment role?

6. System Compatibility  
Does the asset work with:
- voice
- text
- music

---

## Source Rule

REAL = default  
AI = exception

---

## Segment Requirements

### Hook
- specific
- immediate
- visually identifiable

### Setup
- contextual
- informative
- non-generic

### Payoff
- stronger than setup
- reveals or escalates

---

## Quality Criteria

An asset must be:

- semantically correct
- narratively useful
- visually coherent
- non-generic
- compatible with the video system

---

## Failure Conditions

FAIL if:

- generic asset replaces specific one
- AI is used unnecessarily
- payoff is weaker than setup
- setup lacks context
- asset conflicts with text/voice/music
- decision is not explainable

---

## Maturity Test

The agent must be able to answer:

1. What is the entity?
2. What is the anomaly?
3. Is it photographable?
4. Why this asset?
5. Why not another?
6. How does it help the video?

If not -> agent is not ready.

---

## Output Structure

Each segment must produce:

```json
{
  "segment": "...",
  "entity": "...",
  "anomaly": "...",
  "source": "real | ai",
  "justification": "...",
  "narrative_role": "...",
  "compatibility": {
    "voice": "...",
    "text": "...",
    "music": "..."
  }
}
```
