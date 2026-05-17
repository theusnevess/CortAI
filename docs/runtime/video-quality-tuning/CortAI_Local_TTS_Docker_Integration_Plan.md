---
artifact_id: cortai_local_tts_docker_integration_plan
artifact_name: CortAI Local TTS Docker Integration Plan
artifact_type: local_tts_docker_integration_plan
system: CortAI
date: 2026-05-06
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: local_tts_quality_tuning_plan
preferred_path: piper_first
docker_runtime_scope: offline_local_only

plan_created: true
execution_authorized: false
docker_image_change_authorized: false
docker_runtime_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
production_ready: false
---

# CortAI Local TTS Docker Integration Plan

## 1. Purpose

This artifact defines the local Docker TTS quality plan for replacing silent audio fallback in batch video generation.

It selects Piper as the first local TTS integration path and defines the future implementation and validation model. It does not install Piper, rebuild Docker images, run containers, read credentials, call external services, activate publishing, or declare production readiness.

## 2. Current Evidence

```yaml
current_evidence:
  latest_controlled_batch: docker_pipeline_batch_10_best_local_run
  total_runs: 10
  successful_runs: 10
  valid_video_count: 10
  publishable_count: 10

  render_status: structurally_valid
  video_resolution: 1080x1920
  audio_stream_present: true

  tts_requested: kokoro
  tts_executed: silent
  silent_fallback_used: true

  quality_blocker:
    - docker_image_has_no_kokoro_runtime
    - docker_image_has_no_piper_binary
    - silent_audio_preserves_mux_but_degrades_video_quality
```

## 3. Selected Path

```yaml
selected_path:
  preferred_path: piper_first
  rationale:
    - lower_dependency_risk_than_kokoro
    - easier_to_package_in_docker
    - compatible_with_offline_network_none_batches
    - sufficient_to_remove_silent_audio_as_primary_quality_bottleneck
    - existing_repo_voice_assets_can_be_used_or_versioned

  candidate_voice_assets:
    - tools/piper/voices/en_US-lessac-high.onnx
    - tools/piper/voices/en_US-lessac-high.onnx.json
```

## 4. Allowed Future Technical Scope

```yaml
allowed_future_scope:
  - integrate_piper_binary_into_docker_image_or_controlled_local_tool_path
  - pin_or_document_piper_binary_version
  - use_local_versioned_or_mounted_voice_model
  - configure_pipeline_to_request_piper_for_docker_batch
  - keep_batch_network_none
  - keep_silent_fallback_as_last_resort_only
  - add_non_silent_audio_validation_to_batch_quality_gate
  - preserve_complete_agent_outputs_json_for_each_video

candidate_environment_contract:
  CORTAI_TTS_MODE: piper
  CORTAI_PIPER_MODEL: tools/piper/voices/en_US-lessac-high.onnx
  CORTAI_ALLOW_SILENT_TTS_FALLBACK: last_resort_only
```

## 5. Not Authorized

```yaml
not_authorized:
  external_voice_api: true
  api_key_read: true
  credential_access: true
  secret_value_access: true
  env_value_disclosure: true
  real_publish_activation: true
  docker_runtime_execution_by_this_plan: true
  docker_image_change_by_this_plan: true
  production_ready_declaration: true
```

## 6. Future Validation Model

```yaml
future_validation_model:
  docker_precheck:
    - piper_binary_available_inside_image
    - piper_voice_model_available_inside_container
    - batch_runs_with_network_none

  batch_validation:
    - generate_10_videos
    - complete_agent_outputs_json_created
    - all_video_files_probe_valid
    - audio_stream_present
    - audio_is_non_silent
    - tts_provider_executed_is_piper
    - silent_fallback_used_is_false

  non_silent_audio_checks:
    - ffmpeg_or_ffprobe_audio_volume_statistics
    - reject_all_zero_or_near_zero_pcm_audio
    - record_audio_validation_result_in_consolidated_json
```

## 7. Acceptance Criteria

```yaml
acceptance_criteria:
  tts_backend: piper
  tts_provider_executed: piper
  silent_fallback_used: false
  audio_stream_present: true
  audio_is_non_silent: true
  batch_total_runs: 10
  batch_valid_video_count: 10
  complete_agent_outputs_present: true
  external_calls_performed: false
  credential_access_performed: false
  production_ready: false
```

## 8. Risk Notes

```yaml
risk_notes:
  dependency_packaging:
    risk: piper_binary_or_runtime_dependency_missing_in_image
    mitigation: deterministic_image_precheck_before_batch

  model_asset_control:
    risk: voice_model_not_versioned_or_not_mounted
    mitigation: explicit_model_path_and_checksum_or_version_record

  timing_shift:
    risk: real_voice_duration_changes_render_pacing
    mitigation: compare_script_duration_audio_duration_and_final_video_duration

  false_positive_audio:
    risk: audio_stream_exists_but_is_silent
    mitigation: non_silent_audio_probe_required
```

## 9. Guardrail Preservation

```yaml
guardrails_preserved:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved
  docker_runtime_scope: offline_local_only

  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false
```

## 10. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Local TTS Docker Integration Plan Review
  path: docs/runtime/video-quality-tuning/CortAI_Local_TTS_Docker_Integration_Plan_Review.md
  purpose:
    - accept_or_reject_piper_first_path
    - confirm_offline_local_only_scope
    - confirm_non_silent_audio_acceptance_criteria
    - decide_if_docker_integration_execution_authorization_can_be_created
```

## 11. Final Verdict

```yaml
final_verdict:
  plan_mode: local_tts_quality_tuning_plan
  preferred_path: piper_first
  plan_created: true

  docker_image_change_authorized: false
  docker_runtime_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  production_ready: false

  next_artifact: CortAI Local TTS Docker Integration Plan Review
```
