---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_5_f_006_infra_exposure_execution
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution
artifact_type: wave_5_track_5_f_006_infra_exposure_execution
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
track: Track 5 F-006 INFRA EXPOSURE
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

execution_mode: controlled_compose_exposure_patch_execution
selected_design: local_only_default_bindings_with_profile_gated_internal_services
F_006_INFRA_EXPOSURE_execution_completed: true
compose_patch_applied: true
static_validation_executed: true
yaml_parse_validation_executed: true
validation_result: passed

docker_compose_execution_performed: false
containers_started: false
network_scan_performed: false
runtime_execution_performed: false
external_calls_performed: false
credential_access_performed: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution

## 1. Purpose

This artifact records the controlled execution of the Track 5 F-006 INFRA EXPOSURE remediation.

The execution hardens `docker-compose.yml` host port exposure using static file edits only. It does not run Docker, start containers, inspect live ports, perform network scans, execute runtime, access credentials, read env values, call services, or declare production readiness.

## 2. Authorized Scope

```yaml
authorized_scope:
  allowed_modified_files:
    - docker-compose.yml

  allowed_read_only_reference_files:
    - infra/nginx/default.conf

  allowed_validation:
    - static_compose_source_assertions
    - yaml_parse_validation_without_service_start

  not_authorized:
    - docker_compose_config
    - docker_compose_up
    - container_start
    - live_port_probe
    - network_scan
    - service_call
    - runtime_execution
    - env_value_read
    - credential_access
    - production_ready_declaration
```

## 3. Files Changed

```yaml
files_changed:
  - docker-compose.yml
  - docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Execution.md
```

## 4. Patch Summary

```yaml
patch_summary:
  application_entry_surfaces:
    api:
      before: "8000:8000"
      after: "127.0.0.1:8000:8000"
    read_api:
      before: "8002:8000"
      after: "127.0.0.1:8002:8000"
    edge:
      before: "8001:8080"
      after: "127.0.0.1:8001:8080"

  internal_services:
    db:
      before: "5432:5432"
      after: no_host_port_publication
    redis:
      before: "6379:6379"
      after: no_host_port_publication
    minio:
      before:
        - "9000:9000"
        - "9001:9001"
      after: no_host_port_publication
    ollama:
      before: "11435:11434"
      after: no_host_port_publication

  internal_connectivity:
    compose_service_names_preserved: true
    depends_on_relationships_preserved: true
    env_file_references_preserved_without_value_read: true
```

## 5. Validation Performed

```yaml
static_and_yaml_validation:
  command: python_inline_yaml_parse_and_static_port_assertions
  result: passed
  yaml_parse_validation: passed
  published_ports_after_patch: 3
  validated_conditions:
    - api_read_api_and_edge_ports_are_bound_to_127_0_0_1
    - db_has_no_host_port_publication
    - redis_has_no_host_port_publication
    - minio_has_no_host_port_publication
    - ollama_has_no_host_port_publication
    - no_bare_host_port_publications_remain
    - forbidden_internal_bare_patterns_absent

diff_check:
  command: git diff --check -- docker-compose.yml
  result: passed
```

## 6. Validation Evidence

```yaml
validation_evidence:
  static_assertion_console_result: PASSED static compose exposure assertions; published_ports=3
  forbidden_internal_default_patterns_absent:
    - '"5432:5432"'
    - '"6379:6379"'
    - '"9000:9000"'
    - '"9001:9001"'
    - '"11435:11434"'

  retained_host_ports:
    - "127.0.0.1:8000:8000"
    - "127.0.0.1:8002:8000"
    - "127.0.0.1:8001:8080"

  internal_services_without_host_ports:
    - db
    - redis
    - minio
    - ollama
```

## 7. Non-Execution Confirmation

```yaml
non_execution_confirmation:
  docker_compose_config_executed: false
  docker_compose_up_executed: false
  containers_started: false
  containers_stopped: false
  live_port_probe_performed: false
  network_scan_performed: false
  local_service_call_performed: false
  runtime_executed: false
  tests_executed: false
  env_values_read: false
  credentials_accessed: false
  external_calls_performed: false
  production_ready_declared: false
```

## 8. Guardrail Preservation

```yaml
guardrail_preservation:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  result: PASS
```

## 9. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  compose_patch_applied: true
  static_validation_executed: true
  yaml_parse_validation_executed: true

  docker_compose_execution_authorized: false
  docker_compose_execution_performed: false
  network_scan_authorized: false
  network_scan_performed: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  F_006_INFRA_EXPOSURE_closed_by_this_artifact: false
```

## 10. Execution Verdict

```yaml
execution_verdict:
  F_006_INFRA_EXPOSURE_execution_completed: true
  compose_patch_applied: true
  patch_scope_respected: true
  validation_result: passed
  static_validation: passed
  yaml_parse_validation: passed
  diff_check: passed
  production_ready: false
  can_proceed_to_execution_review: true
```

## 11. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Execution_Review.md
  purpose:
    - review_the_compose_exposure_patch
    - accept_or_reject_static_and_yaml_validation
    - confirm_no_docker_or_runtime_execution_occurred
    - decide_if_track_5_can_proceed_to_closure_decision
```

## 12. Final Verdict

```yaml
final_verdict:
  F_006_INFRA_EXPOSURE_execution_completed: true
  compose_patch_applied: true
  validation_result: passed
  static_validation: passed
  yaml_parse_validation: passed
  diff_check: passed

  docker_compose_execution_performed: false
  containers_started: false
  network_scan_performed: false
  runtime_execution_performed: false
  external_calls_performed: false
  credential_access_performed: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Review
```
