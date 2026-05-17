---
artifact_id: cortai_master_gate_lane_4_test_collection_remediation_plan
artifact_name: CortAI Master Gate Lane 4 Test Collection Remediation Plan
artifact_type: master_gate_lane_4_test_collection_remediation_plan
system: CortAI
date: 2026-05-12
lane: Master Audit Gate Lane 4 Test Collection Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_test_collection_remediation_plan
reviewed_authorization_review: CortAI Master Gate Lane 4 Test Collection Remediation Authorization Review
test_collection_root_cause_classification_defined: true

future_test_fix_authorized: false
test_execution_authorized: false
pytest_collection_execution_authorized: false
docker_execution_authorized: false
runtime_execution_authorized: false
production_ready: false
---

# CortAI Master Gate Lane 4 Test Collection Remediation Plan

## 1. Purpose

This artifact defines the Lane 4 Test Collection Remediation Plan.

It classifies root causes for the Master Gate test collection blockers and defines a minimal future remediation strategy. It does not authorize test fixes, code patches, test execution, pytest collection execution, Docker execution, runtime execution, database usage, external calls, credential access, or production readiness.

## 2. Current Master Gate State

```yaml
current_master_gate_state:
  Master_Gate: HOLD_PENDING_REMEDIATION
  lane_2_secret_findings_disposition: closed_with_monitoring
  lane_3_dependency_scope_decision: closed_with_monitoring

  current_lane: lane_4_test_collection_remediation

  remaining_master_gate_lanes:
    - lane_4_test_collection_remediation
    - lane_5_DB_dependent_test_boundary

  test_fix_authorized: false
  test_execution_authorized: false
  pytest_collection_execution_authorized: false
  docker_execution_authorized: false
  runtime_execution_authorized: false
  production_ready: false
```

## 3. Root Cause Classification

```yaml
root_cause_classification:
  backend_tests_test_collector_smoke_contract:
    file: backend/tests/test_collector_smoke_contract.py
    observed_issue: pytest_skip_used_during_collection_without_allow_module_level
    root_cause:
      - _resolve_good_urls_is_called_during_pytest_parametrize_collection
      - unresolved_smoke_asset_stack_calls_pytest_skip_before_test_runtime
      - skip_is_not_marked_allow_module_level
    classification: collection_time_environment_probe_with_invalid_module_level_skip
    risk: collection_blocker

  backend_tests_test_p2b1_synthetic:
    file: backend/tests/test_p2b1_synthetic.py
    observed_issue: import_error_sessionlocal_from_app_cognitive_metrics
    root_cause:
      - test_imports_SessionLocal_symbol_that_app_cognitive_metrics_does_not_export
      - app_cognitive_metrics_uses_private_lazy_sessionmaker_boundary
      - test_crosses_internal_session_boundary_without_adapter
    classification: test_import_boundary_mismatch
    risk: collection_blocker

  tests_collection_import_mismatch:
    observed_issue: duplicate_top_level_vs_nested_test_module_basenames
    root_cause:
      - pytest_imports_duplicate_basenames_as_top_level_modules
      - later_collection_detects_same_module_name_from_different_file_path
      - duplicate_files_exist_between_top_level_tests_and_nested_domain_test_directories
    classification: duplicate_test_module_basename_import_collision
    risk: collection_blocker
```

## 4. Duplicate Module Inventory

```yaml
duplicate_test_module_inventory:
  duplicate_basenames_detected:
    - test_analysis_research_layer_d34_unittest.py
    - test_content_pipeline_d27_unittest.py
    - test_content_template_library_d36_unittest.py
    - test_data_consistency_checker_d38_unittest.py
    - test_offline_simulation_engine_d37_unittest.py
    - test_platform_safety_d28_unittest.py
    - test_screen_text_adapter_unittest.py
    - test_script_generation_unittest.py

  affected_path_pairs:
    - top_level: tests/test_analysis_research_layer_d34_unittest.py
      nested: tests/content/test_analysis_research_layer_d34_unittest.py
    - top_level: tests/test_content_pipeline_d27_unittest.py
      nested: tests/content/test_content_pipeline_d27_unittest.py
    - top_level: tests/test_content_template_library_d36_unittest.py
      nested: tests/content/test_content_template_library_d36_unittest.py
    - top_level: tests/test_data_consistency_checker_d38_unittest.py
      nested: tests/runtime/operations/test_data_consistency_checker_d38_unittest.py
    - top_level: tests/test_offline_simulation_engine_d37_unittest.py
      nested: tests/runtime/operations/test_offline_simulation_engine_d37_unittest.py
    - top_level: tests/test_platform_safety_d28_unittest.py
      nested: tests/runtime/operations/test_platform_safety_d28_unittest.py
    - top_level: tests/test_screen_text_adapter_unittest.py
      nested: tests/agents/video_qc/test_screen_text_adapter_unittest.py
    - top_level: tests/test_script_generation_unittest.py
      nested: tests/agents/script/test_script_generation_unittest.py

  result: DUPLICATE_BASENAME_COLLISIONS_REQUIRE_FUTURE_RESOLUTION
```

## 5. Recommended Remediation Strategy

```yaml
recommended_remediation_strategy:
  - module_level_skip_fix_for_test_collector_smoke_contract
  - import_boundary_fix_for_test_p2b1_synthetic
  - duplicate_test_module_name_resolution_strategy

preferred_future_fixes:
  test_collector_smoke_contract:
    preferred_fix: avoid_invalid_collection_time_skip
    candidate_actions:
      - move_environment_resolution_out_of_parametrize_collection_if_possible
      - or_use_pytest_skip_allow_module_level_true_if_module_level_skip_is_intended
    minimal_future_patch_scope:
      - backend/tests/test_collector_smoke_contract.py

  test_p2b1_synthetic:
    preferred_fix: align_test_session_boundary_with_app_cognitive_metrics
    candidate_actions:
      - replace_missing_SessionLocal_import_with_explicit_test_local_sessionmaker_adapter
      - avoid_production_behavior_change_if_test_only_adapter_is_sufficient
    minimal_future_patch_scope:
      - backend/tests/test_p2b1_synthetic.py

  duplicate_test_module_name_resolution:
    preferred_fix: eliminate_duplicate_import_module_basenames_without_changing_test_intent
    candidate_actions:
      - rename_duplicate_nested_or_top_level_test_files_to_unique_contextual_basenames
      - avoid_global_pytest_import_mode_change_unless_renaming_is_rejected
      - preserve_test_contents_and_assertion_semantics
    minimal_future_patch_scope:
      - tests/content/test_analysis_research_layer_d34_unittest.py
      - tests/content/test_content_pipeline_d27_unittest.py
      - tests/content/test_content_template_library_d36_unittest.py
      - tests/runtime/operations/test_data_consistency_checker_d38_unittest.py
      - tests/runtime/operations/test_offline_simulation_engine_d37_unittest.py
      - tests/runtime/operations/test_platform_safety_d28_unittest.py
      - tests/agents/video_qc/test_screen_text_adapter_unittest.py
      - tests/agents/script/test_script_generation_unittest.py
```

## 6. Future Patch Scope Model

```yaml
future_patch_scope_model:
  patch_not_authorized_now: true

  primary_future_patch_scope:
    - backend/tests/test_collector_smoke_contract.py
    - backend/tests/test_p2b1_synthetic.py

  duplicate_name_future_scope:
    type: file_rename_or_collection_strategy_decision_required
    candidate_files:
      - tests/content/test_analysis_research_layer_d34_unittest.py
      - tests/content/test_content_pipeline_d27_unittest.py
      - tests/content/test_content_template_library_d36_unittest.py
      - tests/runtime/operations/test_data_consistency_checker_d38_unittest.py
      - tests/runtime/operations/test_offline_simulation_engine_d37_unittest.py
      - tests/runtime/operations/test_platform_safety_d28_unittest.py
      - tests/agents/video_qc/test_screen_text_adapter_unittest.py
      - tests/agents/script/test_script_generation_unittest.py

  forbidden_without_separate_authorization:
    - production_code_behavior_change
    - runtime_execution_change
    - database_boundary_change
    - broad_pytest_configuration_change
    - deleting_tests_without_replacement
    - weakening_test_assertions
```

## 7. Future Validation Strategy

```yaml
future_validation_strategy:
  static_validation_after_future_patch:
    - git_diff_check_for_allowed_files
    - duplicate_test_basename_inventory_check
    - import_statement_check_for_test_p2b1_synthetic
    - pytest_skip_boundary_check_for_test_collector_smoke_contract

  collection_validation_after_future_authorization:
    - pytest_collect_only_for_backend_tests
    - pytest_collect_only_for_tests_tree

  targeted_execution_after_separate_authorization_if_needed:
    - targeted_test_execution_for_fixed_files

  not_authorized_now:
    - test_execution
    - pytest_collection_execution
    - docker_execution
    - database_usage
    - runtime_execution
```

## 8. Escalation Rules

```yaml
escalation_rules:
  must_escalate_if:
    - p2b1_fix_requires_production_app_cognitive_metrics_API_change
    - collector_smoke_fix_requires_external_network_or_runtime_stack
    - duplicate_name_fix_requires_deleting_tests
    - duplicate_name_fix_requires_global_pytest_import_mode_change
    - collection_validation_requires_database_or_runtime_start

  escalation_result:
    - pause_lane_4_execution
    - create_separate_authorization_artifact
    - do_not_resolve_under_current_plan
```

## 9. Closure Criteria For Lane 4

```yaml
lane_4_closure_criteria:
  required_before_closure:
    - test_collection_remediation_plan_review_accepted
    - future_patch_authorization_review_accepted
    - controlled_patch_execution_completed
    - static_validation_passed
    - authorized_pytest_collection_validation_passed
    - no_runtime_or_production_authority_created

  closure_mode_if_successful: close_lane_4_with_monitoring
```

## 10. Non-Authorization Preservation

```yaml
non_authorization_preservation:
  future_test_fix_authorized: false
  test_fix_authorized: false
  code_patch_authorized: false
  test_file_patch_authorized: false
  test_execution_authorized: false
  pytest_collection_execution_authorized: false
  docker_execution_authorized: false
  database_usage_authorized: false
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  result: PASS
```

## 11. Guardrail Preservation

```yaml
guardrails:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved
  Master_Gate: HOLD_PENDING_REMEDIATION

  lane_2_secret_findings_disposition: closed_with_monitoring
  lane_3_dependency_scope_decision: closed_with_monitoring

  remaining_master_gate_lanes:
    - lane_4_test_collection_remediation
    - lane_5_DB_dependent_test_boundary

  production_ready: false
  runtime_execution_authorized: false

  result: PASS
```

## 12. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Master Gate Lane 4 Test Collection Remediation Plan Review
  path: docs/runtime/master-audit-gate/CortAI_Master_Gate_Lane_4_Test_Collection_Remediation_Plan_Review.md
  purpose:
    - accept_or_reject_root_cause_classification
    - accept_or_reject_recommended_remediation_strategy
    - decide_if_future_patch_execution_authorization_can_be_created
```

## 13. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_test_collection_remediation_plan
  test_collection_root_cause_classification_defined: true

  recommended_remediation_strategy:
    - module_level_skip_fix_for_test_collector_smoke_contract
    - import_boundary_fix_for_test_p2b1_synthetic
    - duplicate_test_module_name_resolution_strategy

  future_test_fix_authorized: false
  test_execution_authorized: false
  pytest_collection_execution_authorized: false
  docker_execution_authorized: false
  runtime_execution_authorized: false
  production_ready: false

  Master_Gate: HOLD_PENDING_REMEDIATION
  remaining_master_gate_lanes:
    - lane_4_test_collection_remediation
    - lane_5_DB_dependent_test_boundary

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Master Gate Lane 4 Test Collection Remediation Plan Review
```
