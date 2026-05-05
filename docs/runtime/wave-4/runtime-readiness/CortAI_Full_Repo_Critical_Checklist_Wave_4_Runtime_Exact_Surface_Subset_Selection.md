---
artifact_id: cortai_full_repo_critical_checklist_wave_4_runtime_exact_surface_subset_selection
artifact_name: CortAI Full Repo Critical Checklist Wave 4 Runtime Exact Surface Subset Selection
artifact_type: wave_4_runtime_exact_surface_subset_selection
system: CortAI
date: 2026-05-02
lane: Wave 4 Runtime Readiness
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

selection_mode: documentation_reference_only_subset_selection
runtime_exact_surface_subset_selection_created: true
selected_surfaces_reference_only: true
runtime_integration_authorized: false
runtime_wiring_authorized: false
runtime_execution_authorized: false

wave_4_operational_start_authorized: false
code_authorized: false
tests_authorized: false
test_execution_authorized: false
fixture_change_authorized: false
external_call_authorized: false
credential_access_authorized: false
credential_value_access_authorized: false
env_value_read_authorized: false
request_transformation_authorized: false
transport_payload_authorized: false
publisher_external_client_authorized: false
upload_authorized: false
scheduling_authorized: false
publishing_authorized: false
production_ready: false

F_003_fixture_conflict_status: parallel_debt_track_carried
F_003_fixture_debt_carried_forward: true
F_003_fixture_debt_resolved: false
F_003_closed: false
---

# CortAI Full Repo Critical Checklist Wave 4 Runtime Exact Surface Subset Selection

## 1. Purpose

This artifact selects exact candidate runtime surfaces as documentation-only reference surfaces for future authorization planning.

The selected surfaces remain reference-only. This artifact does not authorize runtime integration, runtime wiring, runtime execution, external calls, credential access, request transformation, transport payload creation, publishing, scheduling, production readiness, code changes, tests, fixture changes, debt resolution, or F-003 unrestricted closure.

## 2. Source Artifacts Reviewed

```yaml
source_artifacts_reviewed:
  - docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Exact_Surface_Subset_Selection_Authorization.md
  - docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Exact_Surface_Subset_Selection_Authorization_Review.md
  - docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Surface_Inventory.md
  - docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Surface_Inventory_Review.md
  - docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Integration_Authorization_Decision.md
```

## 3. Current State

```yaml
current_state:
  runtime_exact_surface_subset_selection_authorization_reviewed: true
  runtime_exact_surface_subset_selection_authorization_accepted: true
  can_proceed_to_runtime_exact_surface_subset_selection_artifact: true
  runtime_exact_surface_subset_selected_by_prior_review: false

  runtime_integration_authorized: false
  runtime_wiring_authorized: false
  runtime_execution_authorized: false
  wave_4_operational_start_authorized: false
  production_ready: false

  external_call_authorized: false
  credential_access_authorized: false
  request_transformation_authorized: false
  transport_payload_authorized: false

  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  F_003_fixture_conflict_status: parallel_debt_track_carried
  F_003_fixture_debt_carried_forward: true
  F_003_fixture_debt_resolved: false
  F_003_closed: false
```

## 4. Selection Rationale

```yaml
selection_rationale:
  strategy: conservative_runtime_authorization_planning_subset
  reason:
    - prioritize_lowest_runtime_authority_surfaces_before_external_provider_surfaces
    - avoid_selecting_surfaces_with_direct_external_call_or_credential_dependencies_for_initial_runtime_integration_planning
    - keep_external_boundary_provider_surfaces_unselected_until_dependency_decisions_are_ready
    - preserve_DEBT_F003_FIXTURE_as_parallel_debt
```

## 5. Selected Surfaces

```yaml
selected_surfaces_reference_only:
  account_health_fail_closed_surface:
    file: backend/app/creative/agents/account_health/service.py
    selection_status: selected_for_future_runtime_integration_authorization_planning
    boundary_categories:
      - runtime_entrypoint_boundary
      - validation_release_boundary
    dependency_decisions_required:
      external_call_dependency_decision: false
      credential_dependency_decision: false
      request_transformation_dependency_decision: false
      transport_payload_dependency_decision: false
      runtime_wiring_separation_decision: true
      validation_authorization_decision: true
      DEBT_F003_FIXTURE_impact_decision: true
    reference_only: true
    runtime_integration_authorized: false
    runtime_wiring_authorized: false
    runtime_execution_authorized: false

  status_policy_projection_surface:
    file: backend/app/api/v1/endpoints/status.py
    selection_status: selected_for_dependency_review_only_not_for_runtime_execution
    boundary_categories:
      - runtime_entrypoint_boundary
      - external_call_boundary
      - credential_boundary
      - request_transformation_boundary
      - transport_payload_boundary
      - validation_release_boundary
    dependency_decisions_required:
      external_call_dependency_decision: true
      credential_dependency_decision: true
      request_transformation_dependency_decision: true
      transport_payload_dependency_decision: true
      runtime_wiring_separation_decision: true
      validation_authorization_decision: true
      DEBT_F003_FIXTURE_impact_decision: true
    reference_only: true
    runtime_integration_authorized: false
    runtime_wiring_authorized: false
    runtime_execution_authorized: false
```

## 6. Unselected Surfaces

```yaml
unselected_surfaces_reference_only:
  script_generation_provider_surface:
    file: backend/app/content/script_gen/service.py
    reason: direct_external_provider_credential_request_and_transport_dependencies_require_separate_dependency_decisions_first

  trend_collection_surface:
    file: backend/app/creative/agents/trend_analysis/collectors.py
    reason: external_collector_dependency_requires_separate_external_call_decision_first

  asset_provider_ingestor_surfaces:
    files:
      - backend/app/assets/unsplash_ingestor.py
      - backend/app/assets/pixabay_ingestor.py
      - backend/app/assets/pexels_ingestor.py
    reason: provider_http_and_credential_dependencies_require_separate_dependency_decisions_first

  shared_asset_ingestion_helper_surface:
    file: backend/app/assets/ingestion_common.py
    reason: arbitrary_url_fetch_and_download_boundaries_require_separate_external_call_decision_first

  local_provider_comfyui_surface:
    file: backend/app/assets/comfyui_image_service.py
    reason: local_provider_runtime_wiring_and_transport_dependencies_require_separate_runtime_wiring_decision_first

  collector_downloader_surface:
    file: backend/app/agents/collector/service.py
    reason: downloader_upload_cookie_and_external_dependencies_require_separate_dependency_decisions_first
```

## 7. Dependency Decision Matrix

```yaml
dependency_decision_matrix:
  selected_surface_count: 2
  unselected_surface_groups_count: 6

  selected_surfaces_require_before_any_runtime_integration_authorization:
    account_health_fail_closed_surface:
      - runtime_wiring_separation_decision
      - validation_authorization_decision
      - DEBT_F003_FIXTURE_impact_decision

    status_policy_projection_surface:
      - external_call_dependency_decision
      - credential_dependency_decision
      - request_transformation_dependency_decision
      - transport_payload_dependency_decision
      - runtime_wiring_separation_decision
      - validation_authorization_decision
      - DEBT_F003_FIXTURE_impact_decision
```

## 8. Reference-Only Rules

```yaml
reference_only_rules:
  selected_surfaces_are_reference_only: true
  unselected_surfaces_are_reference_only: true
  selected_surfaces_are_not_authorized_for_modification: true
  selected_surfaces_are_not_authorized_for_execution: true
  selected_surfaces_do_not_authorize_runtime_integration: true
  selected_surfaces_do_not_authorize_runtime_wiring: true
  selected_surfaces_do_not_authorize_external_calls: true
  selected_surfaces_do_not_authorize_credential_access: true
  selected_surfaces_do_not_authorize_request_transformation: true
  selected_surfaces_do_not_authorize_transport_payload_creation: true
  selected_surfaces_do_not_authorize_production_ready: true
```

## 9. DEBT-F003-FIXTURE Impact

```yaml
DEBT_F003_FIXTURE_impact:
  status: parallel_debt_track_carried
  selected_surface_impacted: backend/app/api/v1/endpoints/status.py
  resolved_by_this_selection: false
  blocks_production_ready: true
  blocks_unrestricted_F003_closure: true
  must_be_reviewed_before_any_runtime_integration_authorization_for_status_surface: true
  future_resolution_branch_preserved: true
```

## 10. Explicitly Forbidden

```yaml
forbidden_by_this_selection:
  - runtime_integration
  - runtime_wiring
  - runtime_execution
  - modify_code
  - modify_tests
  - create_tests
  - execute_tests
  - modify_fixtures
  - resolve_DEBT_F003_FIXTURE
  - read_dotenv
  - read_env_values
  - access_credentials
  - instantiate_http_client
  - instantiate_sdk_client
  - call_endpoint
  - perform_dns_network_execution
  - create_request_transformation
  - create_transport_payload
  - upload
  - schedule
  - publish
  - declare_production_ready
  - close_F003_unrestricted
```

## 11. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  runtime_exact_surface_subset_selection_created: true
  selected_surfaces_reference_only: true
  runtime_integration_authorized: false
  runtime_wiring_authorized: false
  runtime_execution_authorized: false
  wave_4_operational_start_authorized: false
  code_authorized: false
  tests_authorized: false
  test_execution_authorized: false
  fixture_change_authorized: false
  runner_authorized: false
  static_scan_execution_authorized: false
  import_graph_execution_authorized: false
  new_tooling_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  credential_value_access_authorized: false
  env_value_read_authorized: false
  request_transformation_authorized: false
  transport_payload_authorized: false
  publisher_external_client_authorized: false
  upload_authorized: false
  scheduling_authorized: false
  publishing_authorized: false
  production_ready: false
  F_003_fixture_debt_resolved: false
  F_003_closed: false
```

## 12. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 4 Runtime Exact Surface Subset Selection Review
  path: docs/runtime/wave-4/runtime-readiness/CortAI_Full_Repo_Critical_Checklist_Wave_4_Runtime_Exact_Surface_Subset_Selection_Review.md
  purpose:
    - review selected and unselected runtime surfaces
    - confirm selected surfaces remain reference-only
    - confirm dependency decisions are identified
    - confirm no runtime integration or runtime wiring was authorized
```

## 13. Final Verdict

```yaml
final_verdict:
  runtime_exact_surface_subset_selection_created: true
  selection_mode: documentation_reference_only_subset_selection
  selected_surfaces:
    - backend/app/creative/agents/account_health/service.py
    - backend/app/api/v1/endpoints/status.py
  selected_surfaces_reference_only: true
  unselected_surface_groups_count: 6

  runtime_integration_authorized: false
  runtime_wiring_authorized: false
  runtime_execution_authorized: false
  wave_4_operational_start_authorized: false
  code_authorized: false
  tests_authorized: false
  test_execution_authorized: false
  fixture_change_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  request_transformation_authorized: false
  transport_payload_authorized: false
  publishing_authorized: false
  scheduling_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  F_003_fixture_conflict_status: parallel_debt_track_carried
  F_003_fixture_debt_carried_forward: true
  F_003_fixture_debt_resolved: false
  F_003_closed: false

  next_artifact: CortAI Full Repo Critical Checklist Wave 4 Runtime Exact Surface Subset Selection Review
```
