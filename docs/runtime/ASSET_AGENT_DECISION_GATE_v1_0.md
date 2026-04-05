# ASSET_AGENT_DECISION_GATE_v1_0

## A. Decision Integrity

For each segment:

- [ ] entity defined correctly
- [ ] anomaly defined
- [ ] photographability evaluated
- [ ] source decision coherent (`real` vs `ai`)
- [ ] justification present

---

## B. Narrative Alignment

- [ ] hook is specific and strong
- [ ] setup is not generic
- [ ] setup contextualizes correctly
- [ ] payoff is stronger than setup
- [ ] payoff reveals or intensifies

---

## C. Source Discipline

- [ ] REAL used as default
- [ ] AI used only when necessary
- [ ] AI does not replace adequate real assets
- [ ] source decision is explainable

---

## D. System Compatibility

- [ ] image is legible with text
- [ ] does not conflict with voice
- [ ] respects narrative rhythm
- [ ] does not overload the frame

---

## E. Visual Quality

- [ ] not generic
- [ ] not placeholder
- [ ] adequate to tone
- [ ] coherent with setting

---

## F. Fail Conditions

FAIL automatically if any:

- [ ] generic hook
- [ ] generic setup without context
- [ ] weak payoff
- [ ] AI used unnecessarily
- [ ] unexplained decision

---

## G. Final Verdict

```json
{
  "verdict": "GO | HOLD | NO-GO",
  "decision_integrity": "high | medium | low",
  "narrative_alignment": "high | medium | low",
  "source_discipline": "high | medium | low",
  "system_compatibility": "high | medium | low",
  "main_failures": []
}
```
