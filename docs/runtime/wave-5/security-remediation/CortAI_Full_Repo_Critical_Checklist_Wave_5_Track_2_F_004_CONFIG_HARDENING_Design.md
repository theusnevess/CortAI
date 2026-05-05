---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_2_f_004_config_hardening_design
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Design
artifact_type: wave_5_track_2_f_004_config_hardening_design
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

design_mode: documentation_only_config_hardening_design
security_track: F_004_CONFIG_HARDENING
reviewed_authorization: CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Authorization Review
problem_statement: credential_bearing_configuration_fallbacks_and_fail_open_defaults
selected_design: centralized_fail_closed_redacted_config_boundary

track_2_config_hardening_design_created: true
track_2_config_hardening_design_reviewed: false
track_2_config_hardening_design_accepted: false
track_2_execution_authorized: false
code_change_authorized: false
test_change_authorized: false
test_execution_authorized: false
static_scan_authorized: false
secret_scan_authorized: false
env_value_read_authorized: false
credential_access_authorized: false
credential_value_access_authorized: false
runtime_integration_authorized: false
runtime_execution_authorized: false
external_call_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Design

## 1. Purpose

This artifact creates the documentation-only design for Track 2: F-004 CONFIG HARDENING.

It defines the target configuration hardening model for credential-bearing fallbacks and fail-open defaults. It does not implement the design and does not authorize code changes, tests, scans, env value reads, credential access, runtime execution, external calls, or production readiness.

## 2. Authorization Lineage

```yaml
authorization_lineage:
  authorization_review:
    name: CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Authorization Review
    path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_2_F_004_CONFIG_HARDENING_Authorization_Review.md
    review_verdict: PASS_WITH_MONITORING
    track_2_config_hardening_design_authorized_for_future_step: true
    can_proceed_to_track_2_config_hardening_design_artifact: true

  this_artifact:
    creates_design: true
    reviews_design: false
    authorizes_implementation: false
    authorizes_tests: false
    authorizes_scans: false
    authorizes_env_value_read: false
```

## 3. Current Governed State

```yaml
current_state:
  system_state: SAFE_PRE_CROSSING
  hold_status: HOLD_CRITICAL_PRESERVED

  Wave_5_opened: true
  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  active_security_track: F_004_CONFIG_HARDENING
  current_step: track_2_config_hardening_design

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  credential_value_access_authorized: false
  env_value_read_authorized: false
```

## 4. Problem Definition

```yaml
problem_definition:
  finding_id: F_004
  problem_statement: credential_bearing_configuration_fallbacks_and_fail_open_defaults

  issue_class:
    - credential_bearing_connection_strings_in_source
    - default_database_or_redis_urls_mask_missing_runtime_configuration
    - source_defaults_can_look_like_real_credentials
    - missing_required_config_can_be_treated_as_usable_config
    - config_errors_can_accidentally_disclose_secret_or_connection_values

  not_merely:
    - developer_convenience_cleanup
    - naming_standardization
    - local_environment_preference

  required_security_direction:
    - centralize_required_config_loading
    - remove_credential_bearing_fallbacks_from_source
    - fail_closed_on_missing_required_runtime_config
    - keep_test_config_explicit_and_non_secret
    - redact_secret_or_connection_values_from_errors_logs_and_artifacts
```

## 5. Frozen Surfaces For Design

```yaml
frozen_surfaces_for_design:
  database_config_surfaces:
    - backend/app/db/session.py
    - backend/alembic/env.py
    - backend/app/cognitive_runs.py
    - backend/app/cognitive_metrics.py
    - backend/app/observations.py
    - backend/app/publish_receipts.py
    - backend/app/agents/collector/observability.py

  worker_and_task_config_surfaces:
    - backend/app/worker.py
    - backend/app/tasks/collector_tasks.py

  adjacent_secret_default_surfaces_for_review_only:
    - backend/app/observability/event_query/query_service.py

  future_new_file_candidates:
    - backend/app/config/runtime.py
    - backend/tests/test_config_hardening.py

  code_change_authorized_now: false
```

## 6. Selected Design

```yaml
selected_design:
  name: centralized_fail_closed_redacted_config_boundary
  design_status: selected_for_future_review

  design_layers:
    - centralized_required_config_loader
    - typed_runtime_config_contract
    - fail_closed_missing_config_behavior
    - redacted_error_and_logging_boundary
    - explicit_test_only_config_boundary
    - migration_and_worker_config_alignment

  governing_rule:
    - runtime_connection_values_must_come_from_explicit_runtime_configuration_or_fail_closed
    - source_code_must_not_provide_credential_bearing_connection_string_fallbacks
    - documentation_may_reference_env_var_names_but_must_not_store_values

  implementation_status:
    implementation_authorized_now: false
    code_change_authorized_now: false
    test_execution_authorized_now: false
```

## 7. Centralized Config Boundary Design

```yaml
centralized_config_boundary_design:
  proposed_future_module:
    path: backend/app/config/runtime.py
    status: proposed_for_future_implementation_only

  proposed_future_contracts:
    RuntimeConfigError:
      behavior:
        - fail_closed
        - message_contains_env_var_name_only
        - message_does_not_contain_env_value
        - message_does_not_contain_connection_string

    RuntimeDatabaseConfig:
      required_fields:
        - database_url
      secret_value_repr: redacted

    RuntimeRedisConfig:
      required_fields:
        - redis_url_or_broker_url
      secret_value_repr: redacted

    RuntimeCursorSigningConfig:
      conditional_fields:
        - cursor_signature_secret_required_when_cursor_enforcement_enabled
      secret_value_repr: redacted

  proposed_future_helpers:
    require_env_var:
      input: env_var_name
      output: raw_value_to_caller_only
      failure: RuntimeConfigError_with_name_only
      logging: no_value_logging

    redact_config_value:
      input: possible_secret_or_connection_string
      output: redacted_marker
      use: errors_logs_debug_payloads

  design_constraint:
    - future_documentation_steps_may_not_read_env_values
    - future_execution_step_may_reference_env_var_names_without_disclosing_values
```

## 8. Database Config Design

```yaml
database_config_design:
  target_surfaces:
    - backend/app/db/session.py
    - backend/alembic/env.py
    - backend/app/cognitive_runs.py
    - backend/app/cognitive_metrics.py
    - backend/app/observations.py
    - backend/app/publish_receipts.py
    - backend/app/agents/collector/observability.py

  required_future_state:
    - no_default_postgresql_connection_string_in_source
    - DATABASE_URL_or_explicit_test_config_required_before_database_engine_creation
    - async_and_sync_database_url_conversion_must_preserve_secret_non_disclosure
    - alembic_must_fail_closed_if_required_database_config_is_missing
    - error_messages_must_reference_DATABASE_URL_name_only

  test_boundary:
    - TEST_DATABASE_URL_may_be_used_only_in_test_context
    - test_values_must_be_non_secret_or_fixture_scoped
    - test_config_must_not_become_runtime_fallback
```

## 9. Worker And Task Config Design

```yaml
worker_and_task_config_design:
  target_surfaces:
    - backend/app/worker.py
    - backend/app/tasks/collector_tasks.py

  required_future_state:
    - broker_or_redis_connection_config_must_be_explicit
    - missing_worker_connection_config_must_fail_closed
    - worker_defaults_must_not_contain_credential_bearing_urls
    - local_dev_examples_must_move_to_non_secret_example_files_or_docs

  runtime_boundary:
    - config_hardening_does_not_authorize_worker_runtime_execution
    - config_hardening_does_not_authorize_queue_or_broker_connection
```

## 10. Adjacent Secret Default Design

```yaml
adjacent_secret_default_design:
  target_surface:
    - backend/app/observability/event_query/query_service.py

  issue_context:
    - cursor_signing_default_secret_is_adjacent_to_F_004
    - secret_default_removal_may_be_required_if_cursor_signature_enforcement_is_enabled

  required_future_state:
    - no_production_secret_default
    - enforcement_enabled_requires_explicit_secret
    - disabled_enforcement_must_not_emit_signed_cursors_with_dev_secret

  track_boundary:
    - this_surface_is_adjacent_review_context
    - exact_patch_scope_requires_execution_authorization_review
```

## 11. Redaction Boundary Design

```yaml
redaction_boundary_design:
  sensitive_value_classes:
    - database_url
    - redis_url
    - broker_url
    - connection_string
    - cursor_signing_secret
    - token
    - password

  required_future_behavior:
    - exceptions_include_env_var_name_but_not_env_value
    - logs_include_config_key_but_not_config_value
    - artifacts_include_env_var_name_but_not_secret_value
    - test_failure_output_must_not_print_real_connection_strings

  allowed_representations:
    - DATABASE_URL
    - REDIS_URL
    - CORTAI_CONTROL_PLANE_TOKEN
    - CORTAI_INTERNAL_CONTROL_PLANE_TOKEN
    - CURSOR_SIGNATURE_SECRET
    - "<redacted>"
    - "<required>"
    - "<test-only-placeholder>"

  forbidden_representations:
    - real_connection_string
    - realistic_password_bearing_connection_string
    - token_value
    - secret_value
```

## 12. Future Implementation Plan Boundary

```yaml
future_implementation_plan_boundary:
  implementation_authorized_now: false

  likely_future_files_to_change_if_execution_is_later_authorized:
    existing_files:
      - backend/app/db/session.py
      - backend/alembic/env.py
      - backend/app/cognitive_runs.py
      - backend/app/cognitive_metrics.py
      - backend/app/observations.py
      - backend/app/publish_receipts.py
      - backend/app/agents/collector/observability.py
      - backend/app/worker.py
      - backend/app/tasks/collector_tasks.py
      - backend/app/observability/event_query/query_service.py

    new_files_possible:
      - backend/app/config/runtime.py
      - backend/tests/test_config_hardening.py

  sequencing_if_later_authorized:
    1: add_centralized_config_loader_with_redacted_errors
    2: remove_database_url_fallbacks_from_database_surfaces
    3: align_alembic_with_required_database_config
    4: remove_worker_or_task_connection_fallbacks
    5: address_adjacent_cursor_secret_default_if_in_scope
    6: add_targeted_config_hardening_tests
    7: run_only_authorized_targeted_tests_or_static_assertions
```

## 13. Future Validation Model

```yaml
future_validation_model:
  validation_execution_authorized_now: false
  static_scan_authorized_now: false
  secret_scan_authorized_now: false

  future_validation_requirements:
    static_assertions:
      - no_credential_bearing_postgresql_fallbacks_in_source
      - no_credential_bearing_redis_or_broker_fallbacks_in_source
      - no_dev_secret_fallback_when_enforcement_enabled

    targeted_unit_tests:
      - missing_DATABASE_URL_fails_closed_without_value_disclosure
      - missing_worker_broker_config_fails_closed_without_value_disclosure
      - config_error_repr_redacts_values
      - test_only_placeholders_are_not_runtime_defaults

    migration_boundary_tests:
      - alembic_missing_database_config_fails_closed
      - alembic_error_mentions_DATABASE_URL_name_only

  validation_not_authorized_now:
    - run_pytest
    - run_gitleaks
    - run_bandit
    - run_codex_security_scan
    - run_pip_audit
    - read_env_values
    - connect_database
```

## 14. Acceptance Criteria For Future Remediation

```yaml
future_remediation_acceptance_criteria:
  config_hardening:
    - zero_credential_bearing_connection_string_fallbacks_in_runtime_source
    - required_runtime_config_fails_closed_when_missing
    - central_config_errors_are_redacted
    - alembic_does_not_hide_missing_database_config_with_default_url
    - worker_or_task_connection_config_does_not_hide_missing_runtime_config

  secret_boundary:
    - no_secret_values_in_artifacts
    - no_secret_values_in_logs
    - no_secret_values_in_test_output
    - env_var_names_only_are_documented

  governance_boundary:
    - remediation_does_not_authorize_runtime_integration
    - remediation_does_not_authorize_runtime_execution
    - remediation_does_not_authorize_external_calls
    - remediation_does_not_declare_production_ready
```

## 15. Forbidden By This Design Artifact

```yaml
forbidden_by_this_artifact:
  implement_design: false
  modify_code: false
  modify_tests: false
  run_tests: false
  run_static_scan: false
  run_secret_scan: false
  run_security_scan: false
  read_env_values: false
  read_dotenv: false
  access_credentials: false
  access_credential_values: false
  connect_database: false
  execute_runtime: false
  call_endpoints: false
  perform_external_calls: false
  declare_production_ready: false
```

## 16. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  track_2_config_hardening_design_created: true
  track_2_config_hardening_design_reviewed: false
  track_2_config_hardening_design_accepted: false
  track_2_execution_authorized: false
  code_change_authorized: false
  test_change_authorized: false
  test_execution_authorized: false
  static_scan_authorized: false
  secret_scan_authorized: false
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

## 17. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Design Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_2_F_004_CONFIG_HARDENING_Design_Review.md
  purpose:
    - review_documentation_only_config_hardening_design
    - accept_or_reject_selected_design
    - confirm_no_patch_tests_scans_or_env_reads_were_authorized
    - decide_whether_track_2_execution_authorization_can_be_considered
```

## 18. Final Verdict

```yaml
final_verdict:
  design_created: true
  design_mode: documentation_only_config_hardening_design
  selected_design: centralized_fail_closed_redacted_config_boundary
  problem_statement: credential_bearing_configuration_fallbacks_and_fail_open_defaults

  track_2_config_hardening_design_reviewed: false
  track_2_config_hardening_design_accepted: false
  track_2_execution_authorized: false
  code_change_authorized: false
  test_execution_authorized: false
  static_scan_authorized: false
  secret_scan_authorized: false
  env_value_read_authorized: false
  credential_access_authorized: false

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  external_call_authorized: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 2 F-004 CONFIG HARDENING Design Review
```
