---
artifact_id: cortai_master_gate_lane_4_l4_collect_002_remediation_plan
artifact_name: CortAI Master Gate Lane 4 L4-COLLECT-002 Remediation Plan
artifact_type: master_gate_lane_4_l4_collect_002_remediation_plan
system: CortAI
date: 2026-05-12
lane: Master Audit Gate Lane 4 Test Collection Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_l4_collect_002_remediation_plan
reviewed_authorization_review: CortAI Master Gate Lane 4 L4-COLLECT-002 Remediation Authorization Review
triggering_finding: L4-COLLECT-002
root_cause_classification_defined: true
remediation_target: app_main_worker_import_boundary
preferred_strategy: defer_or_localize_execute_action_worker_import

code_patch_authorized: false
pytest_collection_execution_authorized: false
test_execution_authorized: false
env_value_read_authorized: false
database_usage_authorized: false
docker_execution_authorized: false
runtime_execution_authorized: false
production_ready: false
---

# CortAI Master Gate Lane 4 L4-COLLECT-002 Remediation Plan

## 1. Purpose

This artifact defines the documentation-only remediation plan for `L4-COLLECT-002`.

It classifies the residual collection blocker, defines the preferred remediation strategy, identifies future patch-scope candidates, and defines future validation requirements. It does not authorize code patches, pytest collection execution, test execution, Docker execution, runtime execution, database usage, environment value reads, credential access, external calls, or production readiness.

## 2. Triggering Finding

```yaml
triggering_finding:
  id: L4-COLLECT-002
  title: app_main_imports_worker_execute_action_during_collection
  source_artifact: CortAI Master Gate Lane 4 Post Boundary Patch Pytest Collection Validation Execution Review
  accepted: true
  severity_for_master_gate: blocking

  current_blocker:
    file: backend/app/main.py
    statement: from app.worker import execute_action
    effect: app_main_imports_worker_during_pytest_collection

  observed_failure:
    error: RuntimeConfigError_missing_REDIS_URL
    import_path:
      - app.main
      - app.worker
      - app.config.runtime.require_worker_broker_url
```

## 3. Root Cause Classification

```yaml
root_cause_classification:
  root_cause_classification_defined: true
  class: app_import_time_dependency_on_worker_runtime_configuration

  current_runtime_coupling:
    app_main:
      imports: app.worker.execute_action
      purpose: observe_endpoint_executor_callback

    app_worker:
      module_load_behavior:
        - imports_require_worker_broker_url
        - evaluates_REDIS_URL_at_module_load
        - constructs_celery_app_with_required_broker_config

  why_collection_fails:
    - pytest_collect_only_imports_app_main
    - app_main_imports_app_worker_before_any_endpoint_is_called
    - app_worker_requires_REDIS_URL_at_import_time
    - REDIS_URL_is_absent_in_collect_only_environment
    - fail_closed_runtime_config_blocks_collection

  security_interpretation:
    - worker_fail_closed_behavior_is_correct_for_worker_runtime
    - app_main_collection_should_not_import_worker_runtime_configuration
    - execute_action_is_currently_worker_free_business_callback_logic
    - remediation_should_move_or_defer_the_callback_boundary_not_weaken_worker_config

  result: BLOCKING_COLLECTION_BOUNDARY_FINDING
```

## 4. Strategy Options

```yaml
strategy_options:
  option_a_extract_worker_free_execute_action_boundary:
    description: move_execute_action_logic_to_worker_independent_module_and_import_that_from_app_main
    likely_future_files:
      - backend/app/main.py
      - backend/app/worker.py
      - backend/app/action_executor.py
    strengths:
      - app_main_can_collect_without_importing_worker
      - worker_can_reuse_or_reexport_same_callback_if_needed
      - require_worker_broker_url_remains_fail_closed_in_worker
      - behavior_of_execute_action_can_remain_stable
    risks:
      - new_file_requires_explicit_future_patch_scope
      - worker_reexport_strategy_must_avoid_runtime_semantic_drift

  option_b_localize_execute_action_in_app_main:
    description: define_execute_action_callback_in_app_main_if_only_used_by_observe_endpoint
    likely_future_files:
      - backend/app/main.py
    strengths:
      - smallest_patch_scope
      - avoids_worker_import_during_collection
      - no_worker_config_change
    risks:
      - may_duplicate_semantics_if_worker_execute_action_is_later_used_elsewhere
      - less_reusable_than_dedicated_worker_free_module

  option_c_lazy_import_worker_execute_action_inside_observe:
    description: import_execute_action_inside_observe_endpoint_only
    status: acceptable_only_if_observe_is_runtime_worker_dependent
    strengths:
      - removes_collection_time_worker_import
      - minimal_code_movement
    risks:
      - observe_endpoint_would_still_require_REDIS_URL_when_called
      - may incorrectly bind cognitive_cycle_action_callback_to_worker_runtime_config

  option_d_weaken_worker_runtime_config:
    status: rejected
    reason:
      - would_regress_fail_closed_runtime_configuration
      - would_weaken_Wave_5_config_hardening
      - would_mask_missing_REDIS_URL_in_real_worker_runtime
```

## 5. Preferred Strategy

```yaml
preferred_strategy:
  id: defer_or_localize_execute_action_worker_import
  recommended_primary_path: extract_worker_free_execute_action_boundary
  recommended_fallback_path: localize_execute_action_in_app_main

  required_properties:
    - app_main_import_must_not_import_app_worker
    - pytest_collection_must_not_require_REDIS_URL
    - app_worker_must_still_require_REDIS_URL_when_imported_for_worker_runtime
    - observe_endpoint_callback_behavior_must_remain_stable
    - no_default_REDIS_URL_may_be_added
    - no_env_value_read_may_be_introduced

  forbidden_properties:
    - weakening_require_worker_broker_url
    - moving_worker_runtime_config_into_app_main
    - adding_dummy_REDIS_URL_to_source
    - starting_redis_or_database_for_collection
    - treating_collection_success_as_runtime_authorization
```

## 6. Future Patch Scope Model

```yaml
future_patch_scope_model:
  patch_not_authorized_by_this_plan: true

  primary_candidate_files:
    - backend/app/main.py

  conditional_candidate_files_if_extracting_shared_callback:
    - backend/app/worker.py
    - backend/app/action_executor.py

  forbidden_without_separate_authorization:
    - backend/app/config/runtime.py
    - backend/app/tasks/collector_tasks.py
    - backend/tests/conftest.py
    - any_env_file
    - docker-compose.yml

  scope_rules_for_future_authorization:
    - exact_files_must_be_frozen_before_patch
    - prefer_removing_app_main_import_time_dependency_on_worker
    - preserve_worker_runtime_fail_closed_semantics
    - preserve_observe_endpoint_contract
    - do_not_expand_to_pytest_collection_execution_without_separate_authorization
```

## 7. Future Validation Strategy

```yaml
future_validation_strategy:
  validation_not_authorized_by_this_plan: true

  static_validation_after_future_patch:
    - git_diff_check_for_allowed_files
    - py_compile_changed_python_files
    - scan_app_main_for_from_app_worker_import
    - scan_for_default_REDIS_URL_introduction
    - scan_runtime_config_for_require_worker_broker_url_preservation
    - scan_worker_for_require_worker_broker_url_preservation
    - affected_file_diff_review

  future_collect_only_validation_after_separate_authorization:
    - python -m pytest backend/tests --collect-only -q
    - python -m pytest tests --collect-only -q

  expected_future_collect_only_result:
    backend_tests_collect_only_exit_code: 0
    tests_collect_only_exit_code: 0
    RuntimeConfigError_missing_REDIS_URL: absent
    import_mismatch_errors: absent

  explicitly_not_authorized_now:
    - code_patch
    - pytest_collection_execution
    - test_execution
    - docker_execution
    - runtime_execution
    - database_usage
    - env_value_read
```

## 8. Closure Criteria

```yaml
closure_criteria:
  L4_COLLECT_002_closure_requires:
    - future_patch_execution_reviewed_and_accepted
    - app_main_no_longer_imports_app_worker_during_collection
    - worker_runtime_fail_closed_semantics_confirmed_preserved
    - future_collect_only_validation_reviewed_and_accepted
    - no_RuntimeConfigError_missing_REDIS_URL_during_collection

  lane_4_overall_closure_requires:
    - L4_COLLECT_001_and_L4_COLLECT_002_resolved_or_formally_dispositioned
    - original_collection_blockers_confirmed_resolved
    - backend_tests_collect_only_passes
    - tests_collect_only_passes
    - lane_5_DB_dependent_test_boundary_not_conflated_with_collection_validation

  master_gate_closure_by_this_plan: false
```

## 9. Non-Authorization Confirmation

```yaml
non_authorization_confirmation:
  code_patch_authorized: false
  pytest_collection_execution_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  database_usage_authorized: false
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  env_value_read_authorized: false
  production_ready: false

  result: PASS
```

## 10. Master Gate Status

```yaml
master_gate_status:
  Master_Gate: HOLD_PENDING_REMEDIATION
  lane_4_L4_COLLECT_002_remediation_plan_created: true
  lane_4_closure_ready: false
  master_gate_closed_by_this_plan: false

  remaining_master_gate_lanes:
    - lane_4_test_collection_remediation
    - lane_5_DB_dependent_test_boundary
```

## 11. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Master Gate Lane 4 L4-COLLECT-002 Remediation Plan Review
  path: docs/runtime/master-audit-gate/CortAI_Master_Gate_Lane_4_L4_COLLECT_002_Remediation_Plan_Review.md
  purpose:
    - accept_or_reject_L4_COLLECT_002_root_cause_classification
    - accept_or_reject_preferred_strategy
    - decide_if_future_patch_authorization_can_be_created
    - preserve_no_execution_until_separate_authorization
```

## 12. Final Verdict

```yaml
final_verdict:
  triggering_finding: L4-COLLECT-002
  root_cause_classification_defined: true
  remediation_target: app_main_worker_import_boundary
  preferred_strategy: defer_or_localize_execute_action_worker_import

  code_patch_authorized: false
  pytest_collection_execution_authorized: false
  test_execution_authorized: false
  env_value_read_authorized: false
  database_usage_authorized: false
  docker_execution_authorized: false
  runtime_execution_authorized: false
  production_ready: false

  worker_runtime_fail_closed_semantics_preserved: true
  do_not_weaken_require_worker_broker_url: true
  do_not_add_default_REDIS_URL: true

  Master_Gate: HOLD_PENDING_REMEDIATION
  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Master Gate Lane 4 L4-COLLECT-002 Remediation Plan Review
```
