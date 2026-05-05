# CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Map

```yaml
artifact_id: cortai_full_repo_critical_checklist_lane_3_external_boundary_guard_policy_map
artifact_name: CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Map
artifact_type: documentation_only_guard_policy_map
system: CortAI
date: 2026-05-01
lane: Lane 3 - Strict External Boundary for F-003
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

guard_policy_map_created: true
documentation_only: true
repository_mutation_authorized: true
repository_mutation_scope: this_artifact_only

code_authorized: false
tests_authorized: false
runner_authorized: false
static_scan_execution_authorized: false
automated_scan_authorized: false
import_graph_execution_authorized: false
new_tooling_authorized: false
external_call_authorized: false
credential_access_authorized: false
credential_value_access_authorized: false
env_value_read_authorized: false
request_transformation_authorized: false
transport_payload_authorized: false
http_client_instantiation_authorized: false
sdk_client_instantiation_authorized: false
endpoint_call_authorized: false
dns_network_authorized: false
api_call_authorized: false
runtime_integration_authorized: false
runtime_wiring_authorized: false
publisher_external_client_authorized: false
upload_authorized: false
scheduling_authorized: false
publishing_authorized: false
production_ready: false
```

## 1. Purpose

This artifact creates a documentation-only guard policy map for Lane 3 F-003 external boundary capability surfaces.

The map classifies observed provider, credential, request, transport, webhook, asset ingestion, downloader and storage transfer surfaces by required guard policy. It separates reference-only allowance from forbidden execution while CortAI remains in `SAFE_PRE_CROSSING`.

This artifact does not authorize code, tests, external calls, credential access, credential value reads, request transformation, transport payload creation, runtime integration, runtime wiring, publishing, production readiness or F-003 closure.

## 2. Source Artifacts Reviewed

```yaml
source_artifacts_reviewed:
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Evidence Inventory
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Evidence Inventory Review
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Guarding Decision
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Documentation Reconciliation Execution Review
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Mapping Planning Authorization
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Mapping Planning Review
  - CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Map Authorization
```

## 3. Current State

```yaml
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED
wave_3_status: active_hold_review
wave_3_exit_allowed: false
wave_4_status: blocked_not_started

F_003: guard_policy_map_authorized_pending_creation
F_003_blocker_reduced: true
F_003_closed: false

external_call_authorized: false
credential_access_authorized: false
credential_value_access_authorized: false
request_transformation_authorized: false
transport_payload_authorized: false
runtime_integration_authorized: false
runtime_wiring_authorized: false
production_ready: false
```

## 4. Policy Outcome Definitions

```yaml
policy_outcome_definitions:
  BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING:
    meaning: capability must not execute while system remains SAFE_PRE_CROSSING

  ALLOW_REFERENCE_ONLY:
    meaning: names, paths, provider identifiers, endpoint strings or env var names may exist only as references, not executable authority

  ALLOW_LOCAL_NON_TRANSPORT_PREPARATION_ONLY:
    meaning: local inert preparation may exist only if it does not create request/transport payloads and does not execute clients

  REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION:
    meaning: any HTTP/API/DNS/provider call requires a future explicit authorization chain

  REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION:
    meaning: reading or using credential values requires a future explicit credential boundary authorization

  REQUIRE_SEPARATE_RUNTIME_WIRING_AUTHORIZATION:
    meaning: connecting capability into runtime execution requires a future explicit runtime wiring authorization

  REQUIRE_FUTURE_GUARD_IMPLEMENTATION:
    meaning: future code-level guard may be required, but is not authorized by this map
```

## 5. Guard Policy Map Table

| surface | representative_files | capability_type | current_authority_status | required_guard_policy | allowed_in_SAFE_PRE_CROSSING | forbidden_in_SAFE_PRE_CROSSING | evidence_required_before_use | future_correction_needed | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Script_Groq_provider_capability | `backend/app/content/script_gen/service.py` | provider_http_call<br>credential_reference<br>authorization_header_construction<br>request_body_construction | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | env var names and provider names as references only | reading credential values; creating Authorization header for execution; client.post; transport payload creation | separate external call authorization; separate credential access authorization; guard review; no SAFE_PRE_CROSSING execution proof | likely | Capability evidence is not external call authority. |
| Script_Ollama_local_provider_capability | `backend/app/content/script_gen/service.py` | local_http_provider_call<br>endpoint_reference<br>request_body_construction | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_RUNTIME_WIRING_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | local endpoint reference only | client.post; local transport execution; runtime wiring | separate runtime wiring authorization; local provider guard review; no SAFE_PRE_CROSSING transport proof | likely | Local provider URL remains a transport surface if executed. |
| Trend_TikTok_collector_capability | `backend/app/creative/agents/trend_analysis/collectors.py` | external_http_get<br>public_endpoint_reference | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | endpoint/source name as reference only | client.get; DNS/network execution; API call | separate external call authorization; collector guard review; proof no external call occurs in SAFE_PRE_CROSSING | likely | Public endpoint strings are references only without call authorization. |
| Unsplash_asset_ingestor_capability | `backend/app/assets/unsplash_ingestor.py` | external_http_get<br>credential_reference<br>request_params_or_header_construction<br>asset_download_capability | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | provider name, env var name and endpoint reference only | key read/use; Authorization/API key header or params; client.get; asset download | separate external call authorization; separate credential access authorization; asset ingestor guard review | likely | Missing-key guards are monitored evidence only. |
| Pixabay_asset_ingestor_capability | `backend/app/assets/pixabay_ingestor.py` | external_http_get<br>credential_reference<br>request_params_or_header_construction<br>asset_download_capability | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | provider name, env var name and endpoint reference only | key read/use; Authorization/API key header or params; client.get; asset download | separate external call authorization; separate credential access authorization; asset ingestor guard review | likely | Credential env var names are not credential value access. |
| Pexels_asset_ingestor_capability | `backend/app/assets/pexels_ingestor.py` | external_http_get<br>credential_reference<br>request_params_or_header_construction<br>asset_download_capability | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | provider name, env var name and endpoint reference only | key read/use; Authorization/API key header or params; client.get; asset download | separate external call authorization; separate credential access authorization; asset ingestor guard review | likely | Provider capability requires future guarding before use. |
| Shared_asset_ingestion_http_helper | `backend/app/assets/ingestion_common.py` | generic_http_fetch_helper<br>arbitrary_url_fetch<br>optional_header_merge | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | helper existence as reference only | download_bytes execution; resolve_og_image execution; arbitrary URL fetch | separate external call authorization; helper guard review; URL allowlist or equivalent future guard evidence | likely | Shared helper capability must not become implicit transport authority. |
| ComfyUI_local_provider_capability | `backend/app/assets/comfyui_image_service.py` | local_http_provider_call<br>workflow_payload_construction<br>polling_and_download_capability | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_RUNTIME_WIRING_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | local provider reference only | prompt queue; polling; image download; local HTTP execution | separate runtime wiring authorization; local provider guard review; no SAFE_PRE_CROSSING local transport proof | likely | Workflow construction capability is not runtime wiring authorization. |
| Collector_downloader_storage_transfer_capability | `backend/app/agents/collector/service.py` | downloader<br>remote_url_access<br>storage_transfer<br>cookie_file_reference | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | downloader capability documented as non-authorized | yt-dlp execution; requests execution; cookie access; storage upload | separate external call authorization; separate credential access authorization if cookies or secrets are involved; downloader/storage guard review | likely | Storage transfer and downloader capability remain forbidden in SAFE_PRE_CROSSING. |
| Status_webhook_capability | `backend/app/api/v1/endpoints/status.py` | webhook_post<br>secret_reference<br>HMAC_signature_construction<br>public_status_payload | capability_confirmed_authority_absent | BLOCK_ALWAYS_IN_SAFE_PRE_CROSSING<br>REQUIRE_SEPARATE_EXTERNAL_CALL_AUTHORIZATION<br>REQUIRE_SEPARATE_CREDENTIAL_ACCESS_AUTHORIZATION<br>REQUIRE_FUTURE_GUARD_IMPLEMENTATION | public payload schema reference only | webhook post; secret value use; HMAC execution for external send | separate external call authorization; separate credential access authorization; webhook guard review; transition guard validation | likely | Webhook transition guards do not authorize webhook execution. |

## 6. Surface-Specific Notes

```yaml
surface_specific_notes:
  - positive guards such as missing-key checks are monitored evidence only
  - local provider URLs are still transport surfaces if executed
  - public endpoints are still external boundary surfaces if called
  - webhook transition guards do not authorize webhook execution
  - provider fallback does not authorize primary provider execution
  - credential env var names are not credential value access
```

The map treats reference, naming, schema and documentation as non-executing evidence only. Any future execution, credential access, request transformation, transport payload creation or runtime wiring requires a separate authorization chain.

## 7. Non-Authorization Matrix

```yaml
non_authorization_matrix:
  guard_policy_map_created: true
  documentation_only: true
  code_authorized: false
  tests_authorized: false
  runner_authorized: false
  static_scan_execution_authorized: false
  automated_scan_authorized: false
  import_graph_execution_authorized: false
  new_tooling_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  credential_value_access_authorized: false
  env_value_read_authorized: false
  request_transformation_authorized: false
  transport_payload_authorized: false
  http_client_instantiation_authorized: false
  sdk_client_instantiation_authorized: false
  endpoint_call_authorized: false
  dns_network_authorized: false
  api_call_authorized: false
  runtime_integration_authorized: false
  runtime_wiring_authorized: false
  publisher_external_client_authorized: false
  upload_authorized: false
  scheduling_authorized: false
  publishing_authorized: false
  production_ready: false
```

## 8. F-003 Impact Decision

```yaml
F_003_impact_decision:
  previous_status: guard_policy_map_authorized_pending_creation
  new_status: guard_policy_map_created_pending_review
  blocker_reduced: true
  blocker_closed: false
  reason:
    - external capability surfaces now have documented required guard policies
    - map separates reference-only allowance from forbidden execution
    - map identifies future correction need
    - no code guard or runtime enforcement has been implemented
```

F-003 remains open pending map review and any future guard implementation or correction chain separately authorized.

## 9. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Map Review
  purpose:
    - accept or reject the documentation-only guard policy map
    - validate that all required surfaces and policy outcomes are present
    - preserve no code, no tests, no runtime, no external calls and no credential access
    - decide whether F_003 can be reduced further or requires guard implementation planning
  must_not:
    - authorize_code
    - authorize_tests
    - authorize_external_calls
    - authorize_credential_access
    - authorize_request_transformation
    - authorize_transport_payload
    - authorize_runtime_integration
    - authorize_runtime_wiring
    - declare_production_ready
    - close_F003
```

## 10. Final Verdict

```yaml
final_verdict:
  guard_policy_map_created: true
  documentation_only: true
  F_003_status: guard_policy_map_created_pending_review
  F_003_blocker_reduced: true
  F_003_closed: false
  HOLD_CRITICAL_preserved: true
  SAFE_PRE_CROSSING_preserved: true
  wave_4_status: blocked_not_started

  code_authorized: false
  tests_authorized: false
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
  http_client_instantiation_authorized: false
  sdk_client_instantiation_authorized: false
  endpoint_call_authorized: false
  dns_network_authorized: false
  api_call_authorized: false
  runtime_integration_authorized: false
  runtime_wiring_authorized: false
  publisher_external_client_authorized: false
  upload_authorized: false
  scheduling_authorized: false
  publishing_authorized: false
  production_ready: false

  next_artifact: CortAI Full Repo Critical Checklist Lane 3 External Boundary Guard Policy Map Review
```
