---
artifact_id: cortai_full_repo_critical_checklist_wave_5_security_remediation_plan
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Security Remediation Plan
artifact_type: wave_5_security_remediation_plan
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

planning_mode: documentation_only_remediation_plan
execution_authorized: false
code_change_authorized: false
test_execution_authorized: false

runtime_integration_authorized: false
runtime_execution_authorized: false
external_call_authorized: false
production_ready: false

security_findings:
  critical: 0
  high: 4
  medium: 2

remediation_plan_defined: true
remediation_execution_defined_but_not_authorized: true
---

# CortAI Full Repo Critical Checklist Wave 5 Security Remediation Plan

## 1. Purpose

This artifact defines the complete remediation plan for all security findings identified by the Codex Security scan.

It defines remediation tracks, execution order, authorization sequence, validation strategy, and closure criteria. This artifact does not authorize execution, code changes, test execution, runtime progression, external calls, database usage, env reads, credential access, or production readiness.

## 2. Remediation Strategy Overview

```yaml
remediation_strategy:
  execution_model: staged_authorization
  approach: per_track_sequential_authorization

  constraints:
    - no_parallel_execution_initially
    - highest_risk_first
    - each_track_requires_review_before_execution
    - each_track_requires_post_validation_before_next

  first_track: F_001_F_002_AUTH_BOUNDARY
```

## 3. Remediation Order

```yaml
remediation_order:
  1: F_001_F_002_AUTH_BOUNDARY
  2: F_004_CONFIG_HARDENING
  3: F_005_DEPENDENCY_SECURITY
  4: F_003_SSRF_BLOCKER
  5: F_006_INFRA_EXPOSURE
```

## 4. Track 1: F-001 / F-002 AUTH BOUNDARY

### Objective

Eliminate unauthenticated operational control.

```yaml
track:
  id: F_001_F_002_AUTH_BOUNDARY
  priority: CRITICAL_BLOCKER

affected_surfaces:
  - backend/app/api/v1/endpoints/operator_actions.py
  - backend/app/api/v1/endpoints/internal_maestro.py
  - backend/app/main.py
  - backend/app/read_main.py
  - backend/app/ops/actions/policy.py
```

### Required Remediations

```yaml
remediation_actions:
  - enforce_authentication_dependency_at_router_level
  - remove_operator_id_as_identity_source
  - require_signed_or_token_based_identity
  - restrict_routes_to_internal_only_or_admin_scope
  - remove_header_based_authentication_gate
  - ensure_routes_not_exposed_on_public_app
```

### Validation Requirements

```yaml
validation_requirements:
  - unauthenticated_requests_must_fail
  - forged_headers_must_fail
  - missing_token_must_fail
  - operator_routes_inaccessible_from_public_context
```

### Closure Criteria

```yaml
closure_criteria:
  - zero_unauthenticated_mutation_paths
  - no_header_only_auth_remaining
  - all_operator_routes_protected_by_real_auth
```

## 5. Track 2: F-004 CONFIG HARDENING

### Objective

Remove credential-bearing fallbacks and enforce fail-closed behavior.

```yaml
track:
  id: F_004_CONFIG_HARDENING
  priority: CRITICAL_SECURITY

remediation_actions:
  - remove_default_connection_strings_from_code
  - require_env_variables_for_all_connections
  - implement_fail_closed_on_missing_config
  - move_examples_to_env_example_only
  - sanitize_error_messages

validation_requirements:
  - system_fails_without_env
  - no_connection_string_in_source
  - no_credentials_in_logs
```

## 6. Track 3: F-005 DEPENDENCY SECURITY

### Objective

Eliminate CVEs and enforce dependency control.

```yaml
track:
  id: F_005_DEPENDENCY_SECURITY
  priority: SUPPLY_CHAIN

remediation_actions:
  - upgrade_vulnerable_packages
  - pin_all_dependencies
  - regenerate_lock_state

validation_requirements:
  - pip_audit_returns_zero_high
  - all_dependencies_pinned
```

## 7. Track 4: F-003 SSRF BLOCKER

### Objective

Prevent future SSRF before enabling external calls.

```yaml
track:
  id: F_003_SSRF_BLOCKER
  priority: CONDITIONAL_CRITICAL

remediation_actions:
  - require_auth_on_video_endpoint
  - restrict_url_schemes
  - block_internal_ip_ranges
  - implement_allowlist
  - enforce_size_and_timeout_limits

constraint:
  - MUST_BE_COMPLETED_BEFORE_external_call_authorization
```

## 8. Track 5: F-006 INFRA EXPOSURE

### Objective

Reduce attack surface in local/dev infra.

```yaml
track:
  id: F_006_INFRA_EXPOSURE
  priority: HARDENING

remediation_actions:
  - bind_services_to_localhost
  - remove_default_public_ports
  - split_dev_and_prod_profiles
```

## 9. Authorization Sequence Model

```yaml
authorization_sequence:
  step_1:
    artifact: track_authorization
    allows: remediation_design_details

  step_2:
    artifact: track_execution_authorization
    allows: controlled_code_change

  step_3:
    artifact: track_validation_review
    allows: validation_execution

  step_4:
    artifact: track_closure_review
    allows: marking_track_closed
```

## 10. Global Constraints

```yaml
global_constraints:
  - no_runtime_execution_during_wave_5
  - no_external_calls_during_wave_5
  - no_database_usage_during_wave_5
  - no_env_reads_during_wave_5
  - no_credentials_access_during_wave_5
  - no_production_ready_declaration
```

## 11. Security Retest Requirement

```yaml
security_retest:
  required: true
  must_run_after_all_tracks_closed: true

  tools:
    - codex_security_scan
    - gitleaks
    - bandit
    - pip_audit

  expected_result:
    - zero_high_findings
    - zero_critical_findings
```

## 12. Failure Conditions

```yaml
failure_conditions:
  - any_track_executed_without_authorization
  - runtime_progression_during_remediation
  - credentials_exposed
  - auth_boundary_not_fully_closed
```

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 1 Authorization (F-001/F-002 AUTH BOUNDARY)
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_1_AUTH_BOUNDARY_Authorization.md
  purpose:
    - authorize_detailed_design_of_auth_fix
    - still_block_code_changes
```

## 14. Final Verdict

```yaml
final_verdict:
  remediation_plan_defined: true
  execution_authorized: false

  first_track: F_001_F_002_AUTH_BOUNDARY

  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
