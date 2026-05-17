---
artifact_id: cortai_local_tts_docker_integration_execution_authorization
artifact_name: CortAI Local TTS Docker Integration Execution Authorization
artifact_type: local_tts_docker_integration_execution_authorization
system: CortAI
date: 2026-05-06
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

authorization_mode: future_controlled_local_tts_docker_integration_execution_pending_review
reviewed_plan_review: CortAI Local TTS Docker Integration Plan Review
authorization_verdict: AUTHORIZE_FUTURE_LOCAL_TTS_DOCKER_INTEGRATION_EXECUTION_PENDING_REVIEW

future_docker_image_or_tool_path_change_authorized: true
future_offline_docker_validation_authorized: true
future_batch_validation_authorized: true

execution_performed_now: false
docker_image_changed_now: false
docker_container_run_now: false
batch_executed_now: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
production_ready: false
---

# CortAI Local TTS Docker Integration Execution Authorization

## 1. Purpose

This artifact authorizes a future controlled execution path for local Piper TTS integration in Docker, pending review.

It freezes the allowed technical scope and future validation boundaries. It does not perform the integration, modify Docker assets, run Docker, generate a new batch, call external services, access credentials, activate publishing, or declare production readiness.

## 2. Authorization Basis

```yaml
authorization_basis:
  reviewed_plan: CortAI Local TTS Docker Integration Plan
  reviewed_plan_review: CortAI Local TTS Docker Integration Plan Review
  plan_review_verdict: PASS_WITH_MONITORING
  piper_first_path_accepted: true
  offline_local_only_scope_accepted: true
  non_silent_audio_acceptance_criteria_accepted: true
```

## 3. Authorization Decision

```yaml
authorization_decision:
  authorization_verdict: AUTHORIZE_FUTURE_LOCAL_TTS_DOCKER_INTEGRATION_EXECUTION_PENDING_REVIEW
  future_docker_image_or_tool_path_change_authorized: true
  future_offline_docker_validation_authorized: true
  future_batch_validation_authorized: true

  execution_performed_now: false
  docker_image_changed_now: false
  docker_container_run_now: false
  batch_executed_now: false
```

## 4. Frozen Future Scope

```yaml
allowed_future_scope:
  - add_or_mount_piper_binary
  - pin_or_record_piper_binary_version
  - use_local_piper_voice_model
  - configure_tts_provider_to_piper
  - keep_network_none
  - validate_audio_is_non_silent
  - generate_controlled_10_video_batch
  - write_consolidated_all_agents_json
  - preserve_silent_fallback_only_as_last_resort

candidate_voice_assets:
  model: tools/piper/voices/en_US-lessac-high.onnx
  model_config: tools/piper/voices/en_US-lessac-high.onnx.json

candidate_runtime_contract:
  CORTAI_TTS_MODE: piper
  CORTAI_PIPER_MODEL: tools/piper/voices/en_US-lessac-high.onnx
  CORTAI_ALLOW_SILENT_TTS_FALLBACK: last_resort_only
```

## 5. Candidate File Scope

```yaml
candidate_future_files:
  docker_or_tooling:
    - Dockerfile
    - docker-compose.yml
    - tools/piper/**
    - scripts/**

  application_tts_boundary:
    - backend/app/content/pipeline/tts.py
    - backend/app/content/pipeline/tts_router.py

  batch_validation_boundary:
    - tests/validation/manual/run_manual_pipeline_batch_10.py

scope_rules:
  - exact_files_must_be_reconfirmed_by_execution_review_before_patch
  - avoid_product_behavior_changes_unrelated_to_local_TTS
  - preserve_existing_complete_agent_outputs_json_contract
  - preserve_offline_local_only_batch_execution
```

## 6. Required Future Validation

```yaml
required_future_validation:
  docker_precheck:
    - piper_binary_available_inside_execution_context
    - piper_voice_model_available_inside_execution_context
    - docker_network_mode_is_none

  integration_validation:
    - tts_provider_requested_is_piper
    - tts_provider_executed_is_piper
    - silent_fallback_used_is_false
    - generated_audio_file_exists
    - audio_stream_present
    - audio_is_non_silent

  batch_validation:
    - controlled_10_video_batch_completed
    - valid_video_count_is_10
    - publishable_count_is_10
    - consolidated_all_agents_json_created
    - each_run_contains_complete_agent_outputs
```

## 7. Non-Authorization Boundary

```yaml
not_allowed:
  external_voice_api: true
  credential_or_env_value_access: true
  secret_value_access: true
  compose_runtime_start: true
  real_publishing: true
  production_ready_declaration: true
  external_calls: true
  database_usage: true
  runtime_integration: true
  runtime_production_execution: true
```

## 8. Execution Boundary

```yaml
execution_boundary:
  execution_authorized_by_this_artifact_for_future_step_pending_review: true
  execution_allowed_now: false
  docker_image_changed_now: false
  docker_container_run_now: false
  batch_executed_now: false
  tests_executed_now: false
  external_calls_performed_now: false
  credentials_accessed_now: false
```

## 9. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Local TTS Docker Integration Execution Authorization Review
  path: docs/runtime/video-quality-tuning/CortAI_Local_TTS_Docker_Integration_Execution_Authorization_Review.md
  purpose:
    - accept_or_reject_future_execution_authorization
    - freeze_exact_files_for_patch_or_tool_mount
    - confirm_offline_network_none_validation_scope
    - decide_if_controlled_Piper_execution_can_proceed
```

## 10. Final Verdict

```yaml
final_verdict:
  authorization_verdict: AUTHORIZE_FUTURE_LOCAL_TTS_DOCKER_INTEGRATION_EXECUTION_PENDING_REVIEW
  future_docker_image_or_tool_path_change_authorized: true
  future_offline_docker_validation_authorized: true
  future_batch_validation_authorized: true

  execution_performed_now: false
  docker_image_changed_now: false
  docker_container_run_now: false
  batch_executed_now: false

  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
