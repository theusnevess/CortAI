# Script Agent Payoff Intelligence Upgrade Plan

## 1. Executive Summary

The current Script Agent is operational, integrated, and already capable of producing strong hooks and workable setups. The main product weakness now is not general script generation. It is payoff density.

Current observed state:
- hooks are often strong enough to secure early attention
- setups usually sustain tension adequately
- payoffs can still land as semantically weak, abstract, or insufficiently concrete
- the system prompt already asks for a concrete reveal, but the enforcement is weak
- current validation rejects only a narrow set of abstract payoff terms

This plan does not redesign the Script Agent.

It upgrades one specific layer:
- payoff intensity

Objective:
- move the Script Agent from "three-block generator with weak payoff enforcement" to "three-block generator with materially stronger payoff closure"

This is a product-quality upgrade, not a pipeline-governance upgrade.

## 2. Current State Diagnosis

Grounded in current implementation:

- `backend/app/creative/agents/script/service.py`
  - builds `ScriptGenerationContext`
  - calls structured generation
  - adapts hook/setup/payoff through `ScreenTextAdapterService`
  - falls back to deterministic contextual scripts on generation failure

- `backend/app/content/script_gen/service.py`
  - prompt already contains explicit payoff guidance:
    - concrete unsettling closure
    - specific enough to visualize instantly
    - observable reveal, not abstract mystery
  - `_validate_payload(...)` only enforces:
    - distinct blocks
    - block length bounds
    - anti-cliche phrases
    - a small weak-payoff term blacklist

What is implemented:
- payoff intent exists in prompt language
- weak payoff blacklist exists
- deterministic fallback payloads already tend to be more concrete than some live generations

What is missing:
- no explicit payoff scoring inside script generation
- no structured check for reveal concreteness
- no check that payoff resolves the promise introduced by hook/setup
- no distinction between:
  - interesting final line
  - strong final reveal
- no repair pass when payoff is weak but not invalid

Most honest label:
- payoff guidance exists
- payoff intelligence is still shallow

## 3. Product Problem To Solve

The failure mode is specific:

- hook creates a strong anomaly
- setup sustains tension
- payoff ends in a vague or low-impact reveal

Typical weak payoff patterns:
- abstract mystery statements
- weak semantic closure
- insufficiently visualizable ending
- conceptually interesting but emotionally flat final line
- reveal lacks concrete object, place, person, number, timestamp, warning, or observable anomaly

This is not a system reliability problem.
This is a closure-strength problem.

## 4. Target State

After this upgrade, the Script Agent should:

- produce payoffs that are more concrete by default
- reject or repair weak payoff closures before finalizing the script
- preserve current hook/setup strengths
- remain deterministic in fallback and validation behavior
- improve downstream product quality without requiring a redesign of Voice, Asset, Editor, or QC

This phase is successful if:
- weak abstract payoffs are meaningfully reduced
- stronger reveal-style payoffs become more common
- downstream QC HOLDs caused by weak payoff landing materially decrease in controlled validation

## 5. Scope

Allowed:
- strengthen prompt instructions for payoff construction
- add deterministic payoff validation heuristics
- add a narrow payoff repair layer
- improve fallback payload quality
- add unit/integration validation around payoff intensity

Out of scope:
- redesigning the Script Agent end to end
- changing Voice logic
- changing Editor logic
- changing QC thresholds
- adding a large narrative ontology
- introducing a new model orchestration layer

## 6. Root Cause In Current Code

The current code already says the right thing in the prompt, but does not enforce it strongly enough.

Current gap by layer:

### Prompt layer

Strength:
- already instructs concrete payoff closure

Weakness:
- instructions are advisory only
- there is no structured preference for:
  - room numbers
  - names
  - timestamps
  - documents
  - warnings
  - physical evidence
  - impossible system states

### Validation layer

Strength:
- blocks must be distinct
- cliches are partially filtered

Weakness:
- only a narrow blacklist of weak payoff terms is used
- a payoff can still be weak while avoiding blacklist words

### Recovery layer

Strength:
- deterministic fallback exists

Weakness:
- there is no intermediate repair path:
  - weak but parse-valid payoff goes through unchanged

## 7. Upgrade Strategy

The correct move is not "generate more creatively."

The correct move is:
- make payoff strength explicit
- make weakness detectable
- repair weak payoffs deterministically when possible

Recommended implementation order:

1. strengthen prompt constraints
2. add payoff-intensity validation
3. add deterministic payoff repair
4. strengthen fallback payloads
5. validate on controlled payoff cases

## 8. Prompt Upgrade Plan

File:
- `backend/app/content/script_gen/service.py`

Current prompt already asks for a concrete reveal.

vNext prompt should add stronger payoff-specific requirements:

- payoff must contain at least one concrete reveal anchor
- payoff should preferably name one of:
  - room number
  - name
  - timestamp
  - device
  - document
  - warning text
  - sealed place
  - impossible state
- payoff must convert mystery into visible evidence, not just continued vagueness

Recommended additions:

- "The payoff must reveal one concrete, observable fact."
- "Prefer a payoff containing a named room, number, date, warning, file, tape, key, voice, body, floor, station, or sealed location."
- "Do not end only on a broad eerie concept such as empty room, strange feeling, unanswered mystery, or unknown presence."
- "The payoff must make the viewer picture the final reveal instantly."

Important:
- keep this as prompt reinforcement, not the only defense

## 9. Payoff Validation Plan

File:
- `backend/app/content/script_gen/service.py`

Add a narrow deterministic payoff validator inside `_validate_payload(...)`.

### 9.1 New signal families

Recommended heuristic checks:

- concrete evidence presence
- specificity strength
- visualizability strength
- closure strength

### 9.2 Concrete evidence heuristic

Reward or require payoff presence of at least one concrete anchor type:

- number or room marker
- proper-name-like token
- device/object evidence
- place evidence
- timestamp/date evidence
- explicit system anomaly

Examples of acceptable anchors:
- `ROOM 312`
- `03:14`
- `WARNING PANEL`
- `TAPE`
- `LOCK`
- `BADGE`
- `ELEVATOR`
- `ARCHIVE`
- `DOOR`
- `INTERCOM`

### 9.3 Weak payoff patterns to penalize

Expand beyond current blacklist.

New weak-pattern examples:
- "empty room" with no stronger qualifier
- "something answered"
- "nobody understood why"
- "it was never explained"
- "someone was there"
- "something was waiting"
- "the room was wrong"

Important:
- do not overfit to phrase-level only
- use pattern families, not brittle exact strings

### 9.4 Closure-strength rule

The payoff should:
- resolve the promise introduced by hook/setup
- add a final concrete escalation or reveal

Reject or repair if the payoff:
- merely restates tension
- remains purely atmospheric
- ends without evidence

## 10. Payoff Repair Layer Plan

This is the highest-value addition.

When payload is parse-valid but payoff is weak:
- do not immediately accept it
- run a deterministic payoff repair step

### 10.1 Repair input

Use:
- topic
- hook
- setup
- payoff
- narrative mode
- niche

### 10.2 Repair objective

Transform weak payoff into:
- more concrete
- more visual
- more final

without changing overall premise

### 10.3 Repair method

Minimum-change deterministic approach:

- build a candidate payoff from the topic and existing anomaly
- preserve emotional tone
- inject one stronger reveal anchor

Examples:

Weak:
- `The caller whispered the number of an empty room.`

Stronger repaired variants:
- `The caller whispered Room 312, sealed since 1997.`
- `The caller named Room 312, a room removed from the floorplan.`
- `The last whisper matched a room listed as non-existent.`

### 10.4 Repair safety rule

If repair cannot confidently produce a stronger payoff:
- fall back to deterministic contextual payload

## 11. Fallback Payload Upgrade Plan

File:
- `backend/app/content/script_gen/service.py`

Current fallback payloads are often already better than weak live payoffs.
Still, they can be tightened further.

Upgrade rule:
- every fallback payoff should contain a concrete reveal anchor

Preferred patterns:
- room number
- date
- sealed object
- impossible physical condition
- named file/tape/witness

This matters because fallback quality defines the floor.

## 12. Contract Surface

No major contract expansion is needed.

Keep:
- `ScriptPlan`
- `StructuredScriptPayload`
- `ScriptGenerationResponse`

Optional narrow addition:
- internal payoff validation trace in `raw_output`-side diagnostics or provider trace

Recommendation:
- avoid adding new public Script contracts in this phase

## 13. File-Level Implementation Surface

Required:
- `backend/app/content/script_gen/service.py`
  - prompt strengthening
  - weak-payoff detection
  - payoff repair step
  - stronger fallback payloads

Likely touched:
- `backend/app/creative/agents/script/service.py`
  - only if a post-generation payoff-repair hook is cleaner at agent layer

Tests:
- `tests/test_script_agent_phase2_unittest.py`
- likely add:
  - `tests/test_script_payoff_intensity_unittest.py`
  - or extend existing script generation tests

Optional validation scripts:
- dedicated payoff audit runner in `tests/run_*.py`

## 14. Migration Strategy

This upgrade should be introduced safely:

1. strengthen validation and repair behind deterministic logic
2. preserve current behavior when payoff is already strong
3. only intervene on weak payoffs
4. keep public output contracts unchanged

Backward compatibility requirement:
- existing consumers of `ScriptPlan` must not break

## 15. Validation Plan

### 15.1 Unit tests

Add tests proving:

- strong payoff passes unchanged
- weak payoff is rejected or repaired
- repair is deterministic
- fallback payoff is concrete
- abstract endings are filtered more reliably

Required case families:

- strong_hook + strong_setup + weak_payoff
- strong_hook + strong_setup + concrete_payoff
- generic eerie payoff
- specific room/number payoff
- specific document/tape/date payoff

### 15.2 Integration tests

Add integration checks proving:

- repaired payoff reaches `ScriptPlan`
- downstream `Asset` gets more concrete payoff material
- same input produces same repaired payoff

### 15.3 Product validation

Create a focused gate:

- `SCRIPT_AGENT_PAYOFF_INTELLIGENCE_VALIDATION_GATE`

Expected artifacts:
- `OUT/audit/script_agent_payoff_intelligence_validation/block_summary.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/final_verdict.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/payoff_examples.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/execution_batch.json`
- `OUT/audit/script_agent_payoff_intelligence_validation/metrics.json`

### 15.4 Success signals

The gate should show:

- fewer weak abstract payoffs
- stronger concrete reveal frequency
- improved payoff examples on controlled cases
- no regression in hook/setup quality

## 16. Success Criteria

This upgrade is successful if:

1. weak abstract payoffs are caught more reliably
2. weak payoffs are repaired or replaced deterministically
3. concrete reveal anchors become materially more common
4. current hook strength does not regress
5. downstream inputs become more visually actionable
6. no contract breakage occurs

## 17. Risks And Mitigations

### Risk 1: Overcorrection into formulaic payoffs

Mitigation:
- use a small set of anchor families
- do not force the same payoff template everywhere

### Risk 2: Validator becomes too brittle

Mitigation:
- use coarse heuristics
- combine weak-pattern detection with positive evidence checks

### Risk 3: Repair changes premise too aggressively

Mitigation:
- constrain repair to preserve original anomaly and topic
- prefer minimal semantic lift, not rewrite

### Risk 4: Hooks or setups degrade because prompt becomes too payoff-heavy

Mitigation:
- add payoff instructions without weakening hook/setup instructions
- validate all three blocks in regression tests

## 18. Next Correct Move After This Upgrade

If this payoff upgrade works, the next correct move is:

- strengthen `Asset` payoff evidence selection to mirror the stronger reveal

After that:
- re-run end-to-end QC product checks
- only then consider a dedicated pre-QC payoff scoring layer

The order matters:

1. fix generation quality first
2. then fix reveal visualization
3. then decide whether extra scoring is still needed

## 19. Final Implementation Principle

Do not solve this with more abstract narrative language.

Solve it by making the payoff:
- more concrete
- more visual
- more final

The success condition is simple:

- the last line should land harder
- and the system should do that consistently
