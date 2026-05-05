---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_4_f_003_ssrf_blocker_design
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design
artifact_type: wave_5_track_4_f_003_ssrf_blocker_design
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

design_mode: documentation_only_ssrf_blocker_design
security_track: F_003_SSRF_BLOCKER
reviewed_authorization: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Authorization Review
problem_statement: future_external_fetch_or_video_ingestion_surface_requires_SSRF_protection_before_external_call_authorization
selected_design: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary

track_4_ssrf_blocker_design_created: true
track_4_ssrf_blocker_design_reviewed: false
track_4_ssrf_blocker_design_accepted: false
track_4_execution_authorized: false
code_change_authorized: false
test_change_authorized: false
test_execution_authorized: false
endpoint_execution_authorized: false
URL_fetch_authorized: false
external_call_authorized: false
application_external_call_authorized: false
runtime_integration_authorized: false
runtime_execution_authorized: false
credential_access_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design

## 1. Purpose

This artifact creates the documentation-only design for Track 4: F-003 SSRF BLOCKER.

It defines the SSRF protection model for user-supplied URLs and future external fetch/video ingestion surfaces.

It does not implement the design and does not authorize code changes, tests, endpoint execution, URL fetches, DNS probes, external calls, runtime execution, credential access, or production readiness.

## 2. Authorization Lineage

```yaml
authorization_lineage:
  authorization_review:
    name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Authorization Review
    path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_4_F_003_SSRF_BLOCKER_Authorization_Review.md
    review_verdict: PASS_WITH_MONITORING
    track_4_ssrf_blocker_design_authorized_for_future_step: true
    can_proceed_to_track_4_design_artifact: true

  this_artifact:
    creates_design: true
    reviews_design: false
    authorizes_implementation: false
    authorizes_tests: false
    authorizes_endpoint_execution: false
    authorizes_URL_fetch: false
    authorizes_external_calls: false
```

## 3. Current Governed State

```yaml
current_state:
  system_state: SAFE_PRE_CROSSING
  hold_status: HOLD_CRITICAL_PRESERVED

  Wave_5_opened: true
  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_2_F_004_CONFIG_HARDENING: remediated_with_monitoring_pending_final_wave_5_retest
  Track_3_F_005_DEPENDENCY_SECURITY: remediated_with_monitoring_pending_final_wave_5_retest
  active_security_track: F_003_SSRF_BLOCKER
  current_step: track_4_ssrf_blocker_design

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  application_external_call_authorized: false
  credential_access_authorized: false
```

## 4. Observed Surface Notes

```yaml
observed_surface_notes:
  videos_endpoint:
    file: backend/app/api/v1/endpoints/videos.py
    observed_behavior:
      - VideoCreateRequest_accepts_url_as_string
      - create_video_persists_source_url
      - create_video_enqueues_process_video_task_with_request_url
    ssrf_relevance:
      - user_supplied_url_crosses_from_api_to_background_collector_queue
      - validation_boundary_should_exist_before_enqueue

  collector_service:
    file: backend/app/agents/collector/service.py
    observed_behavior:
      - CollectorAgent_process_accepts_url_string
      - current_input_check_accepts_http_or_https_via_regex
      - yt_dlp_extract_info_can_perform_network_fetch_when_external_guards_are_open
      - SAFE_PRE_CROSSING_external_request_transformation_transport_and_storage_guards_are_present
    ssrf_relevance:
      - regex_scheme_check_is_not_sufficient_SSRF_policy
      - validation_boundary_should_exist_again_before_download

  execution_performed_by_design_artifact: false
  endpoint_called_by_design_artifact: false
  URL_fetched_by_design_artifact: false
```

## 5. Problem Definition

```yaml
problem_definition:
  finding_id: F_003
  problem_statement: future_external_fetch_or_video_ingestion_surface_requires_SSRF_protection_before_external_call_authorization

  issue_class:
    - user_controlled_URL_can_reach_background_fetch_surface
    - http_https_regex_does_not_block_private_or_reserved_network_targets
    - external_call_guard_blocks_current_runtime_but_does_not_replace_future_SSRF_policy
    - queued_URL_must_be_validated_before_persistence_and_before_download
    - redirect_and_DNS_rebinding_behavior_must_be_governed_before_fetch

  not_merely:
    - URL_string_format_validation
    - yt_dlp_error_handling
    - generic_api_input_sanitization
    - enabling_external_calls

  required_security_direction:
    - centralize_SSRF_policy
    - validate_before_enqueue
    - validate_again_before_download
    - reject_unsafe_schemes_and_hosts
    - reject_private_loopback_link_local_multicast_reserved_IP_targets
    - enforce_redirect_revalidation
    - preserve_no_external_call_authority
```

## 6. Selected Design

```yaml
selected_design:
  name: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary

  core_principles:
    - one_shared_SSRF_policy_module_for_all_user_supplied_URLs
    - API_boundary_validation_before_queue_enqueue
    - collector_boundary_validation_before_any_downloader_invocation
    - deny_by_default_for_unknown_or_ambiguous_targets
    - no_network_probe_required_for_basic_policy_tests
    - future_external_call_authorization_must_reconfirm_policy

  target_boundaries:
    pre_enqueue_boundary:
      surface: backend/app/api/v1/endpoints/videos.py
      goal: reject_unsafe_URL_before_DB_persistence_and_Celery_enqueue

    pre_download_boundary:
      surface: backend/app/agents/collector/service.py
      goal: reject_unsafe_URL_before_yt_dlp_extract_info_or_download

  rejected_designs:
    regex_only_scheme_validation:
      rejected: true
      reason: does_not_block_localhost_private_IP_metadata_or_redirect_risk

    collector_only_validation:
      rejected: true
      reason: unsafe_URL_should_not_be_persisted_or_queued_as_valid_work

    live_network_validation_first:
      rejected: true
      reason: Wave_5_design_and_initial_validation_should_not_require_real_external_calls

  design_result: selected
```

## 7. Policy Model

```yaml
policy_model:
  allowed_schemes:
    - https
    - http

  disallowed_schemes:
    - file
    - ftp
    - gopher
    - dict
    - ldap
    - data
    - javascript
    - ws
    - wss

  default_decision: deny

  host_validation:
    reject_empty_host: true
    reject_username_password_in_url: true
    reject_localhost_names: true
    reject_dotless_internal_names: true
    normalize_IDNA_hostname_before_policy: true
    reject_host_parse_ambiguity: true

  IP_range_policy:
    reject_loopback: true
    reject_private: true
    reject_link_local: true
    reject_multicast: true
    reject_reserved: true
    reject_unspecified: true
    reject_documentation_ranges: true
    reject_ipv4_mapped_ipv6_private_targets: true

  redirect_policy:
    follow_redirects_only_if_downloader_requires_it: false
    every_redirect_target_must_be_revalidated: true
    max_redirects_must_be_bounded: true

  DNS_policy:
    initial_design_prefers_static_parsing_and_IP_literal_rejection: true
    future_DNS_resolution_policy_requires_separate_execution_authorization: true
    DNS_rebinding_risk_must_be_addressed_before_real_external_call_authorization: true
```

## 8. Future Implementation Shape

```yaml
future_implementation_shape:
  proposed_policy_module:
    candidate_file: backend/app/security/ssrf.py
    responsibilities:
      - parse_and_normalize_URL
      - reject_unsafe_scheme
      - reject_unsafe_hostname
      - reject_unsafe_IP_literal
      - produce_safe_error_without_disclosing_sensitive_context

  videos_endpoint_integration:
    file: backend/app/api/v1/endpoints/videos.py
    future_behavior:
      - validate_request_url_before_get_default_user
      - validate_request_url_before_DB_persistence
      - validate_request_url_before_process_video_task_delay
      - return_400_for_policy_rejection

  collector_integration:
    file: backend/app/agents/collector/service.py
    future_behavior:
      - validate_url_before_SAFE_PRE_CROSSING_external_guard_checks_or_downloader_invocation
      - return_invalid_input_or_external_boundary_blocked_contract_for_policy_rejection
      - preserve_existing_SAFE_PRE_CROSSING_external_call_guards

  not_in_future_patch_without_separate_authorization:
    - enabling_external_call_flags
    - adding_live_fetch_validation
    - adding_allowlist_runtime_config_with_secret_values
    - modifying_storage_transfer_authority
```

## 9. Future Validation Model

```yaml
future_validation_model:
  no_real_external_calls_required: true

  policy_unit_tests:
    should_reject:
      - http://127.0.0.1
      - http://localhost
      - http://0.0.0.0
      - http://169.254.169.254
      - http://10.0.0.1
      - http://172.16.0.1
      - http://192.168.0.1
      - http://[::1]
      - file:///etc/passwd
      - gopher://example.com
      - http://user:pass@example.com

    should_allow_as_policy_candidate_without_fetch:
      - https://example.com/video.mp4
      - https://www.youtube.com/watch?v=example

  endpoint_tests:
    - unsafe_URL_returns_400_before_DB_persistence_or_task_enqueue
    - safe_candidate_URL_can_reach_existing_non_fetch_path_if_external_call_remains_blocked_or_mocked

  collector_tests:
    - unsafe_URL_returns_invalid_input_without_yt_dlp_invocation
    - existing_SAFE_PRE_CROSSING_external_call_block_remains_preserved_for_safe_candidate_URL

  forbidden_validation_methods:
    - live_external_fetch
    - real_DNS_probe_without_authorization
    - endpoint_runtime_execution_against_live_server
```

## 10. Closure Criteria

```yaml
closure_criteria:
  F_003_can_close_with_monitoring_only_if:
    - centralized_SSRF_policy_is_implemented
    - videos_endpoint_validates_before_persistence_and_enqueue
    - collector_validates_before_downloader_invocation
    - private_loopback_link_local_multicast_reserved_targets_are_rejected
    - unsafe_schemes_are_rejected
    - tests_prove_no_downloader_call_for_blocked_targets
    - SAFE_PRE_CROSSING_external_call_guards_remain_false
    - no_real_external_calls_are_required_for_validation

  F_003_must_remain_open_if:
    - validation_is_only_regex_based
    - unsafe_URL_can_be_queued_as_valid_work
    - collector_can_invoke_yt_dlp_for_private_or_local_target
    - patch_enables_external_call_authority
    - tests_require_live_network_without_separate_authorization
```

## 11. Monitoring Conditions

```yaml
monitoring_conditions:
  after_track_closure:
    - future_external_call_authorization_must_reconfirm_SSRF_policy
    - any_new_URL_accepting_route_must_use_central_policy
    - any_downloader_or_collector_change_must_revalidate_policy
    - redirect_and_DNS_rebinding_controls_must_be revisited_before_real_external_fetch

  reopen_conditions:
    - user_supplied_URL_bypasses_policy
    - new_fetch_surface_is_added_without_policy
    - private_or_metadata_target_is_accepted
    - external_call_authority_is_opened_without_SSRF_review
```

## 12. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  track_4_ssrf_blocker_design_created: true
  track_4_ssrf_blocker_design_reviewed: false
  track_4_ssrf_blocker_design_accepted: false
  track_4_execution_authorized: false

  code_change_authorized: false
  test_change_authorized: false
  test_execution_authorized: false
  endpoint_execution_authorized: false
  URL_fetch_authorized: false
  DNS_probe_authorized: false
  external_call_authorized: false
  application_external_call_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  credential_access_authorized: false
  production_ready: false
```

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_4_F_003_SSRF_BLOCKER_Design_Review.md
  purpose:
    - review_SSRF_blocker_design
    - accept_or_reject_selected_policy_model
    - confirm_no_code_or_external_call_execution_occurred
    - decide_whether_execution_authorization_can_be_created
```

## 14. Final Verdict

```yaml
final_verdict:
  track_4_ssrf_blocker_design_created: true
  selected_design: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  track_4_execution_authorized: false

  code_change_authorized: false
  test_execution_authorized: false
  endpoint_execution_authorized: false
  URL_fetch_authorized: false
  external_call_authorized: false
  application_external_call_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  credential_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design Review
```
