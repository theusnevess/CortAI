---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_5_f_006_infra_exposure_execution_authorization
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization
artifact_type: wave_5_track_5_f_006_infra_exposure_execution_authorization
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
track: Track 5 F-006 INFRA EXPOSURE
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

authorization_mode: controlled_compose_patch_execution_authorization_for_future_step
reviewed_design: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design Review
selected_design: local_only_default_bindings_with_profile_gated_internal_services

future_compose_patch_authorized_pending_review: true
future_static_validation_authorized_pending_review: true
execution_performed_now: false
code_change_authorized_now: false
compose_change_authorized_now: false
infra_execution_authorized_now: false
test_execution_authorized_now: false

runtime_integration_authorized: false
runtime_execution_authorized: false
external_call_authorized: false
credential_access_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization

## 1. Purpose

This artifact authorizes, for a future step only and pending review, a controlled compose hardening patch for Track 5 F-006 INFRA EXPOSURE.

It freezes the candidate files, allowed changes, validation boundaries, and forbidden actions before any patch is applied. It does not apply a patch now, run Docker, start containers, inspect live ports, perform network scans, execute runtime, access credentials, read env values, call services, or declare production readiness.

## 2. Authorization Basis

```yaml
authorization_basis:
  design_reviewed: true
  design_accepted: true
  selected_design: local_only_default_bindings_with_profile_gated_internal_services
  can_proceed_to_execution_authorization: true

  accepted_design_constraints:
    - host_published_ports_must_bind_explicitly_to_127_0_0_1_for_local_dev
    - internal_data_queue_storage_and_model_services_must_not_be_public_by_default
    - support_service_host_ports_should_be_profile_gated_or_removed_from_default_path
    - inter_container_access_should_use_internal_compose_networking
    - production_readiness_must_not_be_inferred_from_compose_hardening
```

## 3. Future Patch Scope

```yaml
future_patch_scope:
  future_patch_authorized_pending_review: true
  execution_performed_now: false

  allowed_modified_files:
    - docker-compose.yml

  allowed_read_only_reference_files:
    - infra/nginx/default.conf

  files_not_authorized_for_modification:
    - infra/nginx/default.conf
    - .env
    - backend/*
    - frontend/*
    - requirements_or_lock_files

  allowed_change_types:
    - bind_retained_host_ports_to_127_0_0_1
    - remove_or_profile_gate_default_host_ports_for_internal_services
    - preserve_inter_container_service_connectivity
    - add_comments_or_compose_profiles_only_if_needed_to_make_exposure_boundary_explicit
```

## 4. Exact Future Patch Constraints

```yaml
exact_future_patch_constraints:
  application_entry_surfaces:
    api:
      current_pattern: "8000:8000"
      future_allowed_pattern: "127.0.0.1:8000:8000"
    read_api:
      current_pattern: "8002:8000"
      future_allowed_pattern: "127.0.0.1:8002:8000"
    edge:
      current_pattern: "8001:8080"
      future_allowed_pattern: "127.0.0.1:8001:8080"

  internal_service_surfaces:
    db:
      current_pattern: "5432:5432"
      future_allowed_outcomes:
        - no_host_port_publication
        - profile_gated_host_port_bound_to_127_0_0_1
    redis:
      current_pattern: "6379:6379"
      future_allowed_outcomes:
        - no_host_port_publication
        - profile_gated_host_port_bound_to_127_0_0_1
    minio:
      current_patterns:
        - "9000:9000"
        - "9001:9001"
      future_allowed_outcomes:
        - no_default_host_port_publication
        - profile_gated_host_ports_bound_to_127_0_0_1
    ollama:
      current_pattern: "11435:11434"
      future_allowed_outcomes:
        - no_default_host_port_publication
        - tooling_profile_host_port_bound_to_127_0_0_1

  forbidden_patch_results:
    - any_internal_service_bare_host_port_publication
    - any_new_0_0_0_0_host_port_binding
    - any_runtime_start_command_change_unrelated_to_exposure_boundary
    - any_secret_or_env_value_change
```

## 5. Future Validation Authorization

```yaml
future_validation_authorization_pending_review:
  static_source_assertions_authorized_pending_review: true
  yaml_parse_validation_authorized_pending_review: true

  docker_compose_config_authorized: false
  docker_compose_up_authorized: false
  container_start_authorized: false
  live_port_probe_authorized: false
  network_scan_authorized: false
  service_call_authorized: false
  runtime_execution_authorized: false
  env_value_read_authorized: false
  credential_access_authorized: false

  expected_static_assertions:
    forbidden_default_patterns_absent:
      - '"5432:5432"'
      - '"6379:6379"'
      - '"9000:9000"'
      - '"9001:9001"'
      - '"11435:11434"'
    retained_host_ports_bound_to_localhost: true
```

## 6. Forbidden Actions Now

```yaml
forbidden_actions_now:
  apply_patch_now: false
  edit_docker_compose_now: false
  edit_infra_files_now: false
  run_static_assertions_now: false
  run_yaml_parser_now: false
  run_docker_compose_config_now: false
  run_docker_compose_up: false
  start_containers: false
  stop_containers: false
  inspect_live_ports: false
  perform_network_scan: false
  call_local_services: false
  execute_runtime: false
  read_env_values: false
  access_credentials: false
  run_tests: false
  declare_production_ready: false
```

## 7. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  future_compose_patch_authorized_pending_review: true
  future_static_validation_authorized_pending_review: true
  execution_performed_now: false

  code_change_authorized_now: false
  compose_change_authorized_now: false
  infra_execution_authorized_now: false
  test_execution_authorized_now: false
  docker_compose_execution_authorized: false
  network_scan_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false
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

## 9. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Execution_Authorization_Review.md
  purpose:
    - review_the_execution_authorization
    - accept_or_reject_future_compose_patch_scope
    - confirm_no_patch_or_infra_execution_has_occurred
    - decide_if_controlled_execution_can_proceed
```

## 10. Final Verdict

```yaml
final_verdict:
  future_compose_patch_authorized_pending_review: true
  future_static_validation_authorized_pending_review: true
  execution_performed_now: false

  allowed_modified_files:
    - docker-compose.yml

  code_change_authorized_now: false
  compose_change_authorized_now: false
  infra_execution_authorized_now: false
  docker_compose_execution_authorized: false
  network_scan_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization Review
```
