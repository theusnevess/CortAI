---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_5_f_006_infra_exposure_design_review
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design Review
artifact_type: wave_5_track_5_f_006_infra_exposure_design_review
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
track: Track 5 F-006 INFRA EXPOSURE
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

review_mode: documentation_only_design_review
reviewed_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design
review_verdict: PASS_WITH_MONITORING

F_006_INFRA_EXPOSURE_design_reviewed: true
F_006_INFRA_EXPOSURE_design_accepted: true
selected_design_accepted: local_only_default_bindings_with_profile_gated_internal_services
can_proceed_to_execution_authorization: true

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

# CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design Review

## 1. Purpose

This artifact reviews the Track 5 F-006 INFRA EXPOSURE design.

It accepts or rejects the selected design `local_only_default_bindings_with_profile_gated_internal_services`, candidate future patch scope, validation model, and closure criteria. It does not modify compose files, run Docker, start containers, inspect live ports, perform network scans, execute runtime, access credentials, read env values, call services, run tests, or declare production readiness.

## 2. Reviewed Artifact

```yaml
reviewed_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Design
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Design.md
  artifact_type: wave_5_track_5_f_006_infra_exposure_design
  selected_design: local_only_default_bindings_with_profile_gated_internal_services
  candidate_future_patch_scope:
    - docker-compose.yml
    - infra/nginx/default.conf
  execution_authorized: false
  compose_change_authorized: false
  infra_execution_authorized: false
  production_ready: false
```

## 3. Design Review Decision

```yaml
design_review_decision:
  review_verdict: PASS_WITH_MONITORING
  F_006_INFRA_EXPOSURE_design_reviewed: true
  F_006_INFRA_EXPOSURE_design_accepted: true
  selected_design_accepted: local_only_default_bindings_with_profile_gated_internal_services
  can_proceed_to_execution_authorization: true

  reason:
    - design_addresses_unqualified_host_port_publication
    - local_only_default_bindings_reduce_host_network_exposure
    - profile_gated_internal_services_preserve_dev_ergonomics_without_default_public_exposure
    - validation_model_avoids_infra_execution_by_default
    - production_ready_remains_false
```

## 4. Static Context Review

```yaml
static_context_review:
  files_read_by_design_artifact:
    - docker-compose.yml
    - infra/nginx/default.conf

  static_observations_accepted:
    docker_compose_file: docker-compose.yml
    services_with_host_port_publication:
      - api
      - read_api
      - edge
      - db
      - redis
      - minio
      - ollama
    nginx_exposure_controlled_by_compose_host_port_publication: true

  execution_performed_by_design_artifact: false
  env_values_read_by_design_artifact: false
  credentials_accessed_by_design_artifact: false
  result: PASS
```

## 5. Selected Design Review

```yaml
selected_design_review:
  selected_design: local_only_default_bindings_with_profile_gated_internal_services
  accepted: true

  accepted_principles:
    - host_published_ports_must_bind_explicitly_to_127_0_0_1_for_local_dev
    - internal_data_queue_storage_and_model_services_must_not_be_public_by_default
    - support_service_host_ports_should_be_profile_gated_or_removed_from_default_path
    - inter_container_access_should_use_internal_compose_networking
    - production_readiness_must_not_be_inferred_from_compose_hardening

  result: PASS_WITH_MONITORING
```

## 6. Candidate Future Patch Scope Review

```yaml
candidate_future_patch_scope_review:
  primary_candidate_file:
    - docker-compose.yml

  secondary_candidate_file:
    - infra/nginx/default.conf

  accepted_future_patch_constraints:
    - replace_unqualified_host_ports_with_127_0_0_1_bound_ports_where_host_access_is_required
    - remove_or_profile_gate_host_port_publication_for_db
    - remove_or_profile_gate_host_port_publication_for_redis
    - remove_or_profile_gate_host_port_publication_for_minio_api_and_console
    - remove_or_profile_gate_host_port_publication_for_ollama
    - preserve_internal_service_connectivity_through_compose_service_names

  code_change_authorized_by_this_review: false
  compose_change_authorized_by_this_review: false
  result: PASS
```

## 7. Future Validation Model Review

```yaml
future_validation_model_review:
  accepted_static_validation_model:
    - static_compose_source_assertions
    - yaml_parse_validation_if_available_without_service_start

  docker_compose_config_validation:
    allowed_now: false
    requires_separate_authorization: true

  forbidden_without_separate_authorization:
    - docker_compose_up
    - container_start
    - live_port_probe
    - network_scan
    - service_call
    - runtime_execution
    - credential_or_env_value_read

  result: PASS
```

## 8. Closure Criteria Review

```yaml
closure_criteria_review:
  accepted_closure_criteria:
    - no_internal_data_queue_storage_or_model_service_is_host_public_by_default
    - any_retained_host_port_is_explicitly_bound_to_127_0_0_1
    - debug_or_tooling_host_access_is_profile_gated_or_explicitly_documented
    - static_validation_confirms_no_bare_internal_service_port_publication
    - final_wave_5_retest_remains_required
    - production_ready_remains_false

  result: PASS
```

## 9. Non-Execution Review

```yaml
non_execution_review:
  review_mode: documentation_only_design_review
  code_changed_by_this_review: false
  compose_changed_by_this_review: false
  infra_changed_by_this_review: false
  tests_executed_by_this_review: false
  docker_compose_executed_by_this_review: false
  containers_started_by_this_review: false
  network_scan_executed_by_this_review: false
  runtime_executed_by_this_review: false
  external_calls_performed_by_this_review: false
  credentials_accessed_by_this_review: false
  production_ready_declared_by_this_review: false
  result: PASS
```

## 10. Guardrail Review

```yaml
guardrail_review:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  execution_authorized: false
  code_change_authorized: false
  compose_change_authorized: false
  infra_execution_authorized: false
  test_execution_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  result: PASS
```

## 11. Wave 5 Position After Review

```yaml
wave_5_position_after_review:
  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_2_F_004_CONFIG_HARDENING: remediated_with_monitoring_pending_final_wave_5_retest
  Track_3_F_005_DEPENDENCY_SECURITY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_4_F_003_SSRF_BLOCKER: remediated_with_monitoring_pending_final_wave_5_retest
  Track_5_F_006_INFRA_EXPOSURE: design_accepted_pending_execution_authorization

  security_gate_closed: false
  all_tracks_closed: false
  production_ready: false
```

## 12. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  F_006_INFRA_EXPOSURE_design_reviewed: true
  F_006_INFRA_EXPOSURE_design_accepted: true
  selected_design_accepted: local_only_default_bindings_with_profile_gated_internal_services
  can_proceed_to_execution_authorization: true

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

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_5_F_006_INFRA_EXPOSURE_Execution_Authorization.md
  purpose:
    - authorize_or_reject_controlled_compose_patch_scope
    - freeze_exact_files_and_validation_limits
    - preserve_no_patch_until_authorization_review
    - preserve_no_docker_compose_up_or_runtime_execution
```

## 14. Final Verdict

```yaml
final_verdict:
  review_verdict: PASS_WITH_MONITORING
  F_006_INFRA_EXPOSURE_design_reviewed: true
  F_006_INFRA_EXPOSURE_design_accepted: true
  selected_design_accepted: local_only_default_bindings_with_profile_gated_internal_services
  can_proceed_to_execution_authorization: true

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

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 5 F-006 INFRA EXPOSURE Execution Authorization
```
