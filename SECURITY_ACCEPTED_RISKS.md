# Security Accepted Risks

## CVE-2024-23342 / GHSA-wj6h-64fc-37mp

- Package: `ecdsa` (python-ecdsa)
- Current Version: `0.19.1`
- Advisory: https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp
- Status: No fix planned upstream

### Nature of the issue

Timing side-channel vulnerability in ECDSA operations (signing / key generation / ECDH)
in a pure-Python implementation.

### Impact Assessment (Project Context)

- The project does **not** use python-ecdsa for:
  - signing operations
  - key generation
  - ECDH
- Only verification paths (if any) are exercised.
- No direct exposure of private keys via this library is part of the runtime model.

### Mitigation

- Avoid runtime use of:
  - `SigningKey.sign_digest()`
  - ECDH operations
  - key generation via python-ecdsa
- Keep dependency scanning strict for all other findings.
- Monitor upstream and dependency chain changes.
- Re-evaluate immediately if the JWT/auth stack changes.

### Risk Classification

- Operational risk: Low
- Cryptographic misuse risk: Low (given current usage model)

### Review Deadline

Re-evaluate in 90 days or on JWT/auth stack change (whichever happens first).

### Owner

Engineering / Security

---

## Bandit Low Findings (Exception Handling / Defensive Parsing)

- Tool: `bandit`
- Current Result: `15` findings
- Severity Profile:
  - `Low`: 15
  - `Medium`: 0
  - `High`: 0

### Nature of the issue

Residual findings are concentrated in:

- `try/except continue` during JSONL parsing of operational logs
- `try/except pass` in defensive fallback paths for status/runtime introspection

Representative locations:

- `backend/app/api/v1/endpoints/metrics.py`
- `backend/app/api/v1/endpoints/status.py`
- `backend/app/cognitive/cognitive_loop_runner.py`
- `backend/app/cognitive_metrics.py`
- `backend/app/cognitive_runs.py`
- `backend/app/core/executor/cognitive_executor.py`
- `backend/app/observations.py`
- `backend/app/tasks/collector_tasks.py`

### Impact Assessment (Project Context)

- These paths are not introducing command execution, credential exposure, or unsafe deserialization.
- The patterns are used to keep operational parsing and fallback telemetry resilient when encountering malformed lines, absent runtime attributes, or best-effort persistence failures.
- Current audit status confirms:
  - `pip-audit`: no known vulnerabilities found
  - `bandit`: no `Medium` or `High` findings remain
  - full test suite: green

### Mitigation

- Keep these code paths under test and observability.
- Prefer explicit exception narrowing in future refactors when touching these modules.
- Do not expand these patterns into auth, payment, secrets, or external-input validation paths.
- Re-evaluate immediately if one of these locations becomes part of a security-sensitive flow.

### Risk Classification

- Operational risk: Low
- Exploitability in current architecture: Low

### Review Deadline

Re-evaluate in 90 days or on the next security hardening slice affecting parsing/runtime fallback code.

### Owner

Engineering / Security
