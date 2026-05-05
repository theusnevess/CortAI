---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_5_f_006_infra_exposure_design
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design
artifact_type: wave_5_track_5_f_006_infra_exposure_design
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
track: Track 5 F-006 INFRA EXPOSURE
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

design_mode: documentation_only_infra_exposure_hardening_design
reviewed_authorization: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Authorization Review
selected_design: local_only_default_bindings_with_profile_gated_internal_services

F_006_INFRA_EXPOSURE_design_created: true
F_006_INFRA_EXPOSURE_design_reviewed: false
execution_authorized: false
code_change_authorized: false
compose_change_authorized: false
infra_execution_authorized: false
test_execution_authorized: false

runtime_integration_authorized: false
runtime_execution_authorized: false
external_call_authorized: false
credential_access_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design

## 1. Purpose

This artifact defines the documentation-only design for Track 5 F-006 INFRA EXPOSURE remediation.

It identifies static infra exposure surfaces and defines a future hardening model. It does not modify compose files, run Docker, start containers, inspect live ports, perform network scans, execute runtime, access credentials, read env values, call services, or declare production readiness.

## 2. Static Context Reviewed

```yaml
static_context_reviewed:
  files_read:
    - docker-compose.yml
    - infra/nginx/default.conf

  files_not_read:
    - .env

  execution_performed: false
  docker_compose_executed: false
  containers_started: false
  live_port_probe_performed: false
  network_scan_performed: false
  env_values_read: false
  credentials_accessed: false
```

## 3. Problem Statement

```yaml
problem_statement:
  finding_id: F_006_INFRA_EXPOSURE
  problem: default_compose_host_port_publication_expands_local_attack_surface
  risk_class: infrastructure_attack_surface

  observed_static_surfaces:
    docker_compose_file: docker-compose.yml
    services_with_host_port_publication:
      - api
      - read_api
      - edge
      - db
      - redis
      - minio
      - ollama

  key_risk:
    - unqualified_compose_ports_bind_to_all_host_interfaces_by_default
    - data_and_support_services_are_host_reachable_when_compose_stack_is_started
    - dev_support_services_can_be_confused_with_operational_readiness
```

## 4. Static Exposure Inventory

```yaml
static_exposure_inventory:
  api:
    command_host: 0.0.0.0
    host_port_publication: "8000:8000"
    design_classification: application_entry_surface

  read_api:
    command_host: 0.0.0.0
    host_port_publication: "8002:8000"
    design_classification: application_read_entry_surface

  edge:
    host_port_publication: "8001:8080"
    design_classification: local_edge_entry_surface

  db:
    image: postgres:16-alpine
    host_port_publication: "5432:5432"
    design_classification: internal_data_service

  redis:
    image: redis:7-alpine
    host_port_publication: "6379:6379"
    design_classification: internal_queue_service

  minio:
    image: minio/minio:latest
    host_port_publication:
      - "9000:9000"
      - "9001:9001"
    design_classification: internal_object_storage_and_console

  ollama:
    image: ollama/ollama:latest
    host_port_publication: "11435:11434"
    design_classification: local_model_service

  edge_config:
    file: infra/nginx/default.conf
    listen_port_inside_container: 8080
    design_note: exposure_is_controlled_by_compose_host_port_publication
```

## 5. Selected Design

```yaml
selected_design:
  name: local_only_default_bindings_with_profile_gated_internal_services

  principles:
    - host_published_ports_must_bind_explicitly_to_127_0_0_1_for_local_dev
    - internal_data_queue_storage_and_model_services_must_not_be_public_by_default
    - support_service_host_ports_should_be_profile_gated_or_removed_from_default_path
    - inter_container_access_should_use_internal_compose_networking
    - production_readiness_must_not_be_inferred_from_compose_hardening

  default_hardening_model:
    application_entry_surfaces:
      api: bind_host_port_to_127_0_0_1_if_retained
      read_api: bind_host_port_to_127_0_0_1_if_retained
      edge: bind_host_port_to_127_0_0_1_if_retained

    internal_services:
      db: remove_default_host_port_or_bind_127_0_0_1_under_dev_profile
      redis: remove_default_host_port_or_bind_127_0_0_1_under_dev_profile
      minio: remove_default_host_ports_or_bind_127_0_0_1_under_dev_profile
      ollama: remove_default_host_port_or_bind_127_0_0_1_under_tooling_profile

    profiles:
      dev_local: explicit_local_development_entrypoints
      infra_debug: optional_host_access_to_internal_services
      model_tooling: optional_local_model_service_access
```

## 6. Candidate Future Patch Scope

```yaml
candidate_future_patch_scope:
  primary_candidate_file:
    - docker-compose.yml

  secondary_candidate_file:
    - infra/nginx/default.conf

  expected_primary_changes:
    - replace_unqualified_host_ports_with_127_0_0_1_bound_ports_where_host_access_is_required
    - remove_or_profile_gate_host_port_publication_for_db
    - remove_or_profile_gate_host_port_publication_for_redis
    - remove_or_profile_gate_host_port_publication_for_minio_api_and_console
    - remove_or_profile_gate_host_port_publication_for_ollama
    - preserve_internal_service_connectivity_through_compose_service_names

  expected_secondary_changes:
    - none_required_unless_future_review_identifies_edge_specific_exposure_controls

  explicit_non_scope:
    - no_kubernetes_or_cloud_infra_design
    - no_production_deployment_design
    - no_secret_or_env_value_changes
    - no_runtime_startup_changes
```

## 7. Future Patch Constraints

```yaml
future_patch_constraints:
  compose_host_binding:
    require_explicit_localhost_bind_for_any_retained_host_port: true
    disallow_bare_host_port_publication_for_internal_services: true

  internal_services:
    db_host_port_default_publication_allowed: false
    redis_host_port_default_publication_allowed: false
    minio_host_port_default_publication_allowed: false
    minio_console_default_publication_allowed: false
    ollama_host_port_default_publication_allowed: false

  runtime_authority:
    runtime_integration_authorized_by_future_patch: false
    runtime_execution_authorized_by_future_patch: false
    external_call_authorized_by_future_patch: false
    production_ready_authorized_by_future_patch: false
```

## 8. Future Validation Model

```yaml
future_validation_model:
  allowed_future_validation_after_execution_authorization:
    - static_compose_source_assertions
    - yaml_parse_validation_if_available_without_service_start
    - docker_compose_config_validation_only_if_separately_authorized

  static_assertion_candidates:
    forbidden_default_patterns:
      - '"5432:5432"'
      - '"6379:6379"'
      - '"9000:9000"'
      - '"9001:9001"'
      - '"11435:11434"'
    required_pattern_for_retained_host_ports:
      - '127.0.0.1:'

  forbidden_validation_methods_without_separate_authorization:
    - docker_compose_up
    - container_start
    - live_port_probe
    - network_scan
    - service_call
    - runtime_execution
    - credential_or_env_value_read
```

## 9. Closure Criteria

```yaml
closure_criteria:
  - no_internal_data_queue_storage_or_model_service_is_host_public_by_default
  - any_retained_host_port_is_explicitly_bound_to_127_0_0_1
  - debug_or_tooling_host_access_is_profile_gated_or_explicitly_documented
  - static_validation_confirms_no_bare_internal_service_port_publication
  - final_wave_5_retest_remains_required
  - production_ready_remains_false
```

## 10. Monitoring Requirements

```yaml
monitoring_requirements:
  - any_new_compose_service_with_ports_must_be_reviewed_for_localhost_binding
  - any_new_data_queue_storage_or_model_service_must_not_publish_host_ports_by_default
  - any_future_prod_compose_or_deployment_file_requires_separate_security_review
  - exposing_minio_console_or_ollama_requires_explicit_tooling_profile_or_separate_authorization
```

## 11. Forbidden Actions

```yaml
forbidden_actions:
  edit_compose_files_now: false
  edit_infra_files_now: false
  run_docker_compose: false
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

## 12. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  F_006_INFRA_EXPOSURE_design_created: true
  selected_design: local_only_default_bindings_with_profile_gated_internal_services
  execution_authorized: false
  code_change_authorized: false
  compose_change_authorized: false
  infra_execution_authorized: false
  test_execution_authorized: false
  docker_compose_execution_authorized: false
  network_scan_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false
```

## 13. Guardrail Preservation

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

## 14. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Design_Review.md
  purpose:
    - review_the_infra_exposure_hardening_design
    - accept_or_reject_selected_design
    - confirm_candidate_future_patch_scope
    - confirm_no_patch_or_infra_execution_was_authorized
    - decide_if_execution_authorization_can_be_created
```

## 15. Final Verdict

```yaml
final_verdict:
  F_006_INFRA_EXPOSURE_design_created: true
  selected_design: local_only_default_bindings_with_profile_gated_internal_services

  candidate_future_patch_scope:
    - docker-compose.yml
    - infra/nginx/default.conf

  execution_authorized: false
  code_change_authorized: false
  compose_change_authorized: false
  infra_execution_authorized: false
  test_execution_authorized: false

  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design Review
```
