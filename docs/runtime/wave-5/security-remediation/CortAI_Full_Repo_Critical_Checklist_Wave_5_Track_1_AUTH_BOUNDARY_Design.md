---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_1_auth_boundary_design
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 1 AUTH BOUNDARY Design
artifact_type: wave_5_track_1_auth_boundary_design
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

design_mode: documentation_only_detailed_auth_boundary_design
security_track: F_001_F_002_AUTH_BOUNDARY
track_1_auth_boundary_design_created: true
track_1_auth_boundary_design_authorized_by_prior_review: true
track_1_execution_authorized: false
code_change_authorized: false
test_change_authorized: false
test_execution_authorized: false
runtime_integration_authorized: false
runtime_execution_authorized: false
external_call_authorized: false
credential_access_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 1 AUTH BOUNDARY Design

## 1. Purpose

This artifact creates the documentation-only detailed design for remediation Track 1: F-001/F-002 AUTH BOUNDARY.

It defines the target boundary model for the exposed control-plane surfaces. It does not implement the design and does not authorize code changes, tests, runtime execution, endpoint calls, external calls, credential access, or production readiness.

## 2. Authorization Lineage

```yaml
authorization_lineage:
  previous_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 1 AUTH BOUNDARY Authorization Review
  previous_artifact_path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_1_AUTH_BOUNDARY_Authorization_Review.md
  previous_review_verdict: PASS_WITH_MONITORING
  track_1_auth_boundary_design_authorized_for_future_step: true

  this_artifact:
    creates_design: true
    reviews_design: false
    authorizes_implementation: false
    authorizes_tests: false
    authorizes_runtime: false
```

## 3. Current Governed State

```yaml
current_state:
  system_state: SAFE_PRE_CROSSING
  hold_status: HOLD_CRITICAL_PRESERVED

  Wave_5_opened: true
  active_security_track: F_001_F_002_AUTH_BOUNDARY
  remediation_phase: documentation_only_design

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
```

## 4. Problem Definition

```yaml
problem_definition:
  problem_statement: control_plane_exposed_without_real_authentication

  core_issue:
    - operational_control_routes_are_mounted_without_real_auth_boundary
    - read_api_mounts_operator_mutation_routes
    - operator_identity_is_currently_supplied_by_client_controlled_payload
    - internal_maestro_gate_can_depend_on_client_controlled_header_when_enabled

  not_merely:
    - missing_token
    - missing_bearer_header
    - missing_request_field_validation

  boundary_failure_class:
    - public_data_plane_and_control_plane_not_sufficiently_separated
    - control_plane_identity_not_cryptographically_or_operationally_verified
    - internal_route_gate_not_equivalent_to_authentication

  operational_risk_if_runtime_enabled_later:
    - unauthenticated_pause_or_resume_rollout
    - unauthenticated_task_requeue
    - unauthenticated_event_index_rebuild
    - unauthenticated_alert_acknowledgement
    - header_forged_internal_maestro_execution_when_internal_gate_is_enabled
```

## 5. Current Surface Observations

```yaml
current_surface_observations:
  backend/app/api/v1/endpoints/operator_actions.py:
    router_dependency_present: false
    endpoint_dependency_present: false
    trusted_identity_source: payload.operator_id
    mutating_actions:
      - pause_rollout
      - resume_rollout
      - requeue_task
      - rebuild_event_index
      - ack_alert

  backend/app/main.py:
    operator_actions_mounted: true
    operator_actions_prefix: /api/v1/ops/actions
    internal_maestro_mounted: true
    public_app_context_contains_control_plane_routes: true

  backend/app/read_main.py:
    operator_actions_mounted: true
    operator_actions_prefix: /api/v1/ops/actions
    read_api_contains_mutating_control_plane_routes: true

  backend/app/api/v1/endpoints/internal_maestro.py:
    route_prefix: /internal
    current_gate: should_include_internal_status_request_gate
    current_gate_uses_client_controlled_header_when_feature_flag_enabled: true
    current_gate_is_not_real_authentication: true

  backend/app/observability/runtime_health.py:
    internal_gate_header: X-Internal-Status
    gate_is_visibility_or_feature_gate_not_auth_boundary: true
```

## 6. Selected Design

```yaml
selected_design:
  name: isolation_first_control_plane_auth_boundary
  design_status: selected_for_future_review

  design_layers:
    - route_exposure_boundary
    - verifiable_identity_boundary
    - authorization_scope_boundary
    - audit_identity_boundary
    - fail_closed_configuration_boundary

  governing_rule:
    - no_control_plane_route_may_be_reachable_from_public_or_read_context_without_real_authentication_or_real_isolation

  implementation_status:
    implementation_authorized_now: false
    code_change_authorized_now: false
    test_execution_authorized_now: false
```

## 7. Route Exposure Boundary Design

```yaml
route_exposure_boundary_design:
  read_api_boundary:
    required_future_state:
      - backend/app/read_main.py_must_not_mount_operator_actions_router
      - read_api_must_remain_read_only_for_observability_metrics_status
      - mutating_ops_actions_must_not_be_reachable_from_read_api_context

  public_api_boundary:
    required_future_state:
      - backend/app/main.py_must_not_expose_control_plane_routes_without_auth_dependency
      - operator_actions_router_may_only_be_mounted_with_router_or_app_level_auth_boundary
      - internal_maestro_router_may_only_be_mounted_with_internal_service_auth_boundary_or_real_process_network_isolation

  internal_route_boundary:
    required_future_state:
      - /internal/maestro/run_must_not_rely_on_X_Internal_Status_as_authentication
      - /internal/maestro/jobs_must_not_rely_on_X_Internal_Status_as_authentication
      - X_Internal_Status_may_remain_observability_visibility_context_only_if_not_used_as_auth

  design_constraint:
    - route_removal_or_route_auth_boundary_must_be_enforced_before_any_runtime_progression
```

## 8. Verifiable Identity Boundary Design

```yaml
verifiable_identity_boundary_design:
  proposed_future_module:
    path: backend/app/api/v1/dependencies/control_plane_auth.py
    status: proposed_for_future_implementation_only

  proposed_future_contracts:
    ControlPlaneIdentity:
      fields:
        - subject
        - scopes
        - auth_method
        - internal
      secret_fields_allowed: false

    ControlPlaneAuthError:
      behavior: fail_closed_without_secret_disclosure

  proposed_future_dependencies:
    require_control_plane_admin:
      purpose:
        - protect_operator_actions
        - provide_verified_operator_identity
      must_not_trust:
        - payload.operator_id
        - query.operator_id
        - client_controlled_identity_header_without_signature_or_token_verification

    require_internal_control_plane:
      purpose:
        - protect_internal_maestro
      must_not_trust:
        - X-Internal-Status_as_authentication
        - client_controlled_internal_header_without_verification

  credential_boundary:
    secret_values_in_design: forbidden
    env_value_read_by_design: forbidden
    future_secret_source_must_be_handled_by_separate_config_hardening_or_execution_authorization: true
```

## 9. Operator Action Identity Design

```yaml
operator_action_identity_design:
  current_state:
    operator_id_source: client_payload
    operator_id_trusted_for_audit: true

  required_future_state:
    trusted_operator_id_source: verified_ControlPlaneIdentity.subject
    payload_operator_id_status: untrusted_request_metadata_or_removed
    service_calls_must_receive_verified_operator_identity: true

  future_service_boundary_requirements:
    - OperatorActionService_methods_must_not_treat_payload_operator_id_as_verified_identity
    - audit_event_operator_id_must_come_from_verified_identity
    - request_reason_remains_user_supplied_but_not_identity_bearing
    - mutating_action_requires_authenticated_identity_before_service_call

  future_schema_options:
    option_A:
      description: remove_operator_id_from_mutating_payloads
      impact: breaking_API_change_for_control_plane_clients
    option_B:
      description: keep_operator_id_as_optional_display_or_assertion_field_but_never_trust_it
      impact: lower_client_breakage_but_requires_explicit_mismatch_handling

  preferred_design_direction: option_A_unless_backward_compatibility_is_required_by_later_review
```

## 10. Internal Maestro Boundary Design

```yaml
internal_maestro_boundary_design:
  current_state:
    route_prefix: /internal
    gate_function: should_include_internal_status
    gate_character: feature_visibility_gate
    gate_problem: client_controlled_header_can_open_route_when_feature_flag_enabled

  required_future_state:
    - internal_maestro_routes_require_require_internal_control_plane_dependency
    - X_Internal_Status_cannot_be_used_as_authentication
    - if_internal_maestro_remains_mounted_on_main_app_then_dependency_must_fail_closed
    - if_no_real_auth_is_available_then_internal_maestro_must_not_be_mounted_in_public_app_context

  demo_mode_constraint:
    - demo_query_parameter_must_not_weaken_auth_boundary
    - demo_mode_must_remain_behind_same_internal_control_plane_auth
```

## 11. Router Enforcement Shape

```yaml
router_enforcement_shape:
  operator_actions_router:
    acceptable_future_shapes:
      - APIRouter_dependencies_with_require_control_plane_admin
      - app.include_router_dependencies_with_require_control_plane_admin
    unacceptable_future_shapes:
      - endpoint_body_operator_id_only
      - header_presence_only
      - hidden_UI_only_control
      - docs_or_CORS_based_control

  internal_maestro_router:
    acceptable_future_shapes:
      - APIRouter_dependencies_with_require_internal_control_plane
      - app.include_router_dependencies_with_require_internal_control_plane
      - not_mounted_unless_running_in_real_internal_only_process_boundary
    unacceptable_future_shapes:
      - X_Internal_Status_header_only
      - EXPOSE_C1_HEALTH_STATUS_plus_header_as_auth
      - demo_parameter_as_safety_gate

  read_main:
    acceptable_future_shapes:
      - no_operator_actions_router_mount
      - no_internal_mutating_control_plane_router_mount
    unacceptable_future_shapes:
      - read_path_with_mutating_ops_actions
      - read_path_with_operator_console_mutation_target
```

## 12. Fail-Closed Design Requirements

```yaml
fail_closed_design_requirements:
  missing_auth_config:
    required_behavior: control_plane_routes_unavailable_or_401_403
    must_not_fallback_to: dev_secret_or_header_only_gate

  missing_request_auth:
    required_behavior: 401_or_403
    must_not_continue_to_service_layer: true

  invalid_request_auth:
    required_behavior: 401_or_403
    must_not_disclose_secret_or_config_state: true

  auth_dependency_error_handling:
    required_behavior:
      - generic_error_message
      - no_token_echo
      - no_secret_material_in_logs
      - no_connection_or_env_values_in_response
```

## 13. Future Implementation Plan Boundary

```yaml
future_implementation_plan_boundary:
  implementation_authorized_now: false

  likely_future_files_to_change_if_execution_is_later_authorized:
    existing_files:
      - backend/app/api/v1/endpoints/operator_actions.py
      - backend/app/api/v1/endpoints/internal_maestro.py
      - backend/app/main.py
      - backend/app/read_main.py
      - backend/app/ops/actions/service.py
      - backend/app/ops/actions/policy.py
      - backend/app/observability/runtime_health.py

    new_files_possible:
      - backend/app/api/v1/dependencies/control_plane_auth.py
      - backend/tests/test_operator_actions_auth_boundary.py
      - backend/tests/test_internal_maestro_auth_boundary.py
      - backend/tests/test_read_main_control_plane_boundary.py

  sequencing_if_later_authorized:
    1: add_verifiable_control_plane_auth_dependency_or_fail_closed_isolation
    2: remove_operator_actions_from_read_main
    3: enforce_operator_actions_auth_at_router_boundary
    4: derive_operator_identity_from_verified_identity_not_payload
    5: replace_internal_maestro_header_gate_with_internal_control_plane_dependency
    6: add_negative_auth_boundary_tests
    7: run_only_authorized_targeted_tests
```

## 14. Future Validation Model

```yaml
future_validation_model:
  validation_execution_authorized_now: false

  future_negative_tests:
    operator_actions:
      - POST_/api/v1/ops/actions/pause-rollout_without_auth_must_fail
      - POST_/api/v1/ops/actions/resume-rollout_without_auth_must_fail
      - POST_/api/v1/ops/actions/requeue-task_without_auth_must_fail
      - POST_/api/v1/ops/actions/rebuild-event-index_without_auth_must_fail
      - POST_/api/v1/ops/actions/ack-alert_without_auth_must_fail
      - forged_payload_operator_id_must_not_create_verified_identity

    internal_maestro:
      - POST_/internal/maestro/run_with_only_X_Internal_Status_must_fail
      - GET_/internal/maestro/jobs_job_id_with_only_X_Internal_Status_must_fail
      - demo_mode_query_must_not_bypass_auth

    read_main:
      - read_api_must_not_route_/api/v1/ops/actions_pause_rollout
      - read_api_must_not_route_/api/v1/ops/actions_requeue_task

  future_positive_tests:
    - verified_admin_identity_can_access_operator_action_only_with_required_scope
    - verified_internal_identity_can_access_internal_maestro_only_with_required_scope
    - verified_identity_subject_is_used_for_audit_operator_id

  future_static_checks:
    - no_operator_actions_router_mount_in_read_main
    - no_control_plane_router_mount_without_dependency
    - no_X_Internal_Status_as_auth_boundary
```

## 15. Acceptance Criteria For Future Remediation

```yaml
future_remediation_acceptance_criteria:
  auth_boundary:
    - zero_unauthenticated_control_plane_mutation_paths
    - zero_header_only_internal_auth_paths
    - zero_payload_operator_id_as_verified_identity_paths
    - read_api_has_no_mutating_operator_control_routes

  audit_boundary:
    - operator_action_audit_uses_verified_identity
    - audit_events_do_not_persist_secret_material
    - failed_auth_attempts_do_not_disclose_values

  runtime_boundary:
    - remediation_does_not_authorize_runtime_integration
    - remediation_does_not_authorize_runtime_execution
    - remediation_does_not_authorize_external_calls
    - remediation_does_not_declare_production_ready
```

## 16. Forbidden By This Design Artifact

```yaml
forbidden_by_this_artifact:
  implement_design: false
  create_auth_dependency: false
  modify_router_mounts: false
  modify_operator_actions: false
  modify_internal_maestro: false
  modify_ops_service: false
  modify_tests: false
  create_tests: false
  run_tests: false
  run_security_scan: false
  execute_runtime: false
  call_endpoints: false
  read_env_values: false
  read_dotenv: false
  access_credentials: false
  access_credential_values: false
  connect_database: false
  perform_external_calls: false
  declare_production_ready: false
```

## 17. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  track_1_auth_boundary_design_created: true
  track_1_auth_boundary_design_reviewed: false
  track_1_auth_boundary_design_accepted: false
  track_1_execution_authorized: false
  security_remediation_execution_authorized: false
  code_change_authorized: false
  test_change_authorized: false
  test_execution_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  credential_value_access_authorized: false
  env_value_read_authorized: false
  database_connection_authorized: false
  production_ready: false
```

## 18. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 1 AUTH BOUNDARY Design Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_1_AUTH_BOUNDARY_Design_Review.md
  purpose:
    - review_documentation_only_auth_boundary_design
    - accept_or_reject_selected_design
    - confirm_problem_is_control_plane_boundary_failure
    - confirm_no_implementation_or_execution_authorized
    - decide_whether_track_1_execution_authorization_can_be_considered
```

## 19. Final Verdict

```yaml
final_verdict:
  design_created: true
  design_mode: documentation_only_detailed_auth_boundary_design
  selected_design: isolation_first_control_plane_auth_boundary
  problem_statement: control_plane_exposed_without_real_authentication

  track_1_auth_boundary_design_reviewed: false
  track_1_auth_boundary_design_accepted: false
  track_1_execution_authorized: false
  code_change_authorized: false
  test_execution_authorized: false

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false
  credential_access_authorized: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 1 AUTH BOUNDARY Design Review
```
