---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_4_f_003_ssrf_blocker_design_review
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design Review
artifact_type: wave_5_track_4_f_003_ssrf_blocker_design_review
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

review_mode: documentation_only_ssrf_blocker_design_review
reviewed_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design
review_verdict: PASS_WITH_MONITORING

track_4_ssrf_blocker_design_reviewed: true
track_4_ssrf_blocker_design_accepted: true
selected_design_accepted: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
can_proceed_to_track_4_execution_authorization: true

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
---

# CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design Review

## 1. Purpose

This artifact reviews the Track 4 F-003 SSRF BLOCKER Design.

It accepts or rejects the documentation-only SSRF blocker design and decides whether a future execution authorization artifact can be created.

It does not authorize implementation, code changes, tests, endpoint execution, URL fetches, DNS probes, external calls, runtime execution, credential access, production readiness, or operational start.

## 2. Reviewed Artifact

```yaml
reviewed_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Design
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_4_F_003_SSRF_BLOCKER_Design.md
  artifact_type: wave_5_track_4_f_003_ssrf_blocker_design
  design_mode: documentation_only_ssrf_blocker_design
  selected_design: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  track_4_ssrf_blocker_design_created: true
  track_4_execution_authorized: false
  external_call_authorized: false
```

## 3. Current Governed State

```yaml
current_state:
  system_state: SAFE_PRE_CROSSING
  hold_status: HOLD_CRITICAL_PRESERVED

  Wave_5_opened: true
  current_step: track_4_ssrf_blocker_design_review
  active_security_track: F_003_SSRF_BLOCKER

  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_2_F_004_CONFIG_HARDENING: remediated_with_monitoring_pending_final_wave_5_retest
  Track_3_F_005_DEPENDENCY_SECURITY: remediated_with_monitoring_pending_final_wave_5_retest

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  external_call_authorized: false
  application_external_call_authorized: false
  credential_access_authorized: false
```

## 4. Design Review Decision

```yaml
design_review_decision:
  review_verdict: PASS_WITH_MONITORING
  track_4_ssrf_blocker_design_reviewed: true
  track_4_ssrf_blocker_design_accepted: true
  selected_design_accepted: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  can_proceed_to_track_4_execution_authorization: true

  reason:
    - selected_design_places_policy_before_queue_enqueue_and_before_downloader_invocation
    - design_rejects_regex_only_URL_validation
    - design_preserves_no_external_call_authority
    - design_supports_validation_without_real_external_fetches
    - design_keeps_runtime_and_production_progression_blocked
```

## 5. Observed Surface Review

```yaml
observed_surface_review:
  videos_endpoint_surface_accepted:
    file: backend/app/api/v1/endpoints/videos.py
    accepted_risk:
      - VideoCreateRequest_accepts_url_as_string
      - create_video_persists_source_url
      - create_video_enqueues_process_video_task_with_request_url
      - pre_enqueue_validation_boundary_required

  collector_surface_accepted:
    file: backend/app/agents/collector/service.py
    accepted_risk:
      - CollectorAgent_process_accepts_url_string
      - current_regex_http_https_check_is_not_complete_SSRF_policy
      - yt_dlp_can_fetch_when_future_external_guards_are_open
      - pre_download_validation_boundary_required

  endpoint_called_by_review: false
  URL_fetched_by_review: false
  result: PASS
```

## 6. Selected Design Review

```yaml
selected_design_review:
  selected_design: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  accepted: true

  accepted_core_principles:
    - one_shared_SSRF_policy_module_for_all_user_supplied_URLs
    - API_boundary_validation_before_queue_enqueue
    - collector_boundary_validation_before_any_downloader_invocation
    - deny_by_default_for_unknown_or_ambiguous_targets
    - no_network_probe_required_for_basic_policy_tests
    - future_external_call_authorization_must_reconfirm_policy

  accepted_target_boundaries:
    pre_enqueue_boundary: backend/app/api/v1/endpoints/videos.py
    pre_download_boundary: backend/app/agents/collector/service.py

  rejected_designs_accepted:
    regex_only_scheme_validation: true
    collector_only_validation: true
    live_network_validation_first: true

  result: PASS
```

## 7. Policy Model Review

```yaml
policy_model_review:
  policy_model_accepted: true

  accepted_scheme_policy:
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

  accepted_host_policy:
    reject_empty_host: true
    reject_username_password_in_url: true
    reject_localhost_names: true
    reject_dotless_internal_names: true
    normalize_IDNA_hostname_before_policy: true
    reject_host_parse_ambiguity: true

  accepted_IP_policy:
    reject_loopback: true
    reject_private: true
    reject_link_local: true
    reject_multicast: true
    reject_reserved: true
    reject_unspecified: true
    reject_documentation_ranges: true
    reject_ipv4_mapped_ipv6_private_targets: true

  result: PASS_WITH_MONITORING
```

## 8. Future Implementation Shape Review

```yaml
future_implementation_shape_review:
  proposed_policy_module_accepted:
    candidate_file: backend/app/security/ssrf.py
    responsibilities:
      - parse_and_normalize_URL
      - reject_unsafe_scheme
      - reject_unsafe_hostname
      - reject_unsafe_IP_literal
      - produce_safe_error_without_disclosing_sensitive_context

  videos_endpoint_integration_accepted:
    file: backend/app/api/v1/endpoints/videos.py
    future_behavior:
      - validate_request_url_before_get_default_user
      - validate_request_url_before_DB_persistence
      - validate_request_url_before_process_video_task_delay
      - return_400_for_policy_rejection

  collector_integration_accepted:
    file: backend/app/agents/collector/service.py
    future_behavior:
      - validate_url_before_downloader_invocation
      - return_invalid_input_or_external_boundary_blocked_contract_for_policy_rejection
      - preserve_existing_SAFE_PRE_CROSSING_external_call_guards

  result: PASS
```

## 9. Validation Model Review

```yaml
validation_model_review:
  validation_model_accepted: true
  no_real_external_calls_required: true

  policy_unit_tests_accepted:
    reject_private_loopback_link_local_and_reserved_targets: true
    reject_unsafe_schemes: true
    reject_userinfo_in_URL: true
    allow_public_candidate_URL_without_fetch: true

  endpoint_tests_accepted:
    - unsafe_URL_returns_400_before_DB_persistence_or_task_enqueue
    - no_task_enqueue_for_rejected_URL

  collector_tests_accepted:
    - unsafe_URL_returns_invalid_input_without_yt_dlp_invocation
    - SAFE_PRE_CROSSING_external_call_block_remains_preserved_for_safe_candidate_URL

  validation_execution_authorized_now: false
  result: PASS_WITH_MONITORING
```

## 10. Guardrail Preservation

```yaml
guardrail_preservation:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  code_change_authorized: false
  test_execution_authorized: false
  endpoint_execution_authorized: false
  URL_fetch_authorized: false
  DNS_probe_authorized: false
  external_call_authorized: false
  application_external_call_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  credential_access_authorized: false
  production_ready: false

  result: PASS
```

## 11. Execution Boundary Review

```yaml
execution_boundary_review:
  documentation_review_only: true
  new_code_change_by_this_review: false
  new_test_change_by_this_review: false
  tests_executed_by_this_review: false
  endpoint_executed_by_this_review: false
  runtime_executed_by_this_review: false
  URL_fetch_performed_by_this_review: false
  DNS_probe_performed_by_this_review: false
  external_calls_by_this_review: false
  credentials_accessed_by_this_review: false
  production_ready_declared_by_this_review: false

  result: PASS
```

## 12. Wave 5 Position After Review

```yaml
wave_5_position_after_review:
  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_2_F_004_CONFIG_HARDENING: remediated_with_monitoring_pending_final_wave_5_retest
  Track_3_F_005_DEPENDENCY_SECURITY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_4_F_003_SSRF_BLOCKER: design_accepted_pending_execution_authorization

  security_gate_closed: false
  all_tracks_closed: false

  current_next_step: Track_4_F_003_SSRF_BLOCKER_Execution_Authorization
```

## 13. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  track_4_ssrf_blocker_design_reviewed: true
  track_4_ssrf_blocker_design_accepted: true
  selected_design_accepted: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  can_proceed_to_track_4_execution_authorization: true

  code_change_authorized: false
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

## 14. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Execution Authorization
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_4_F_003_SSRF_BLOCKER_Execution_Authorization.md
  purpose:
    - authorize_or_reject_controlled_SSRF_blocker_patch
    - freeze_exact_files_and_validation_scope
    - preserve_no_external_call_execution
    - preserve_runtime_and_production_blocks
```

## 15. Final Verdict

```yaml
final_verdict:
  review_verdict: PASS_WITH_MONITORING
  track_4_ssrf_blocker_design_reviewed: true
  track_4_ssrf_blocker_design_accepted: true
  selected_design_accepted: centralized_ssrf_policy_pre_enqueue_and_pre_download_boundary
  can_proceed_to_track_4_execution_authorization: true

  code_change_authorized: false
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

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 4 F-003 SSRF BLOCKER Execution Authorization
```
