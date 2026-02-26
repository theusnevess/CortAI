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
