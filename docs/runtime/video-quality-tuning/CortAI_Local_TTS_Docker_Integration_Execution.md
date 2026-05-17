---
artifact_id: cortai_local_tts_docker_integration_execution
artifact_name: CortAI Local TTS Docker Integration Execution
artifact_type: local_tts_docker_integration_execution
system: CortAI
date: 2026-05-06
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

execution_mode: controlled_local_tts_docker_integration_execution
reviewed_authorization_review: CortAI Local TTS Docker Integration Execution Authorization Review
execution_verdict: COMPLETED_WITH_QUALITY_VALIDATION_PASS_PENDING_REVIEW

changed_files_within_frozen_scope: true
docker_image_changed: true
docker_image_tag: cortai10-api:piper-local
docker_network_mode: none
piper_binary_available: true
piper_voice_model_available: true
tts_provider_requested: piper
tts_provider_executed: piper
silent_fallback_used: false
audio_stream_present: true
audio_is_non_silent: true
valid_video_count: 10
publishable_count: 10
external_calls_performed: false
credential_access_performed: false
secret_value_access_performed: false
production_ready: false
---

# CortAI Local TTS Docker Integration Execution

## 1. Purpose

This artifact records the controlled execution of the local Piper TTS Docker integration.

It documents the Docker image update, offline Piper precheck, controlled 10-video batch execution, and non-silent audio validation. It does not authorize production readiness, runtime integration, runtime production execution, external service calls, credential access, or real publishing.

## 2. Execution Scope

```yaml
execution_scope:
  selected_path: piper_first
  docker_image_tag: cortai10-api:piper-local
  docker_network_mode: none
  batch_id: docker_pipeline_batch_10_piper_local_run

  source_patch_changed_files_within_frozen_scope: true
  changed_files:
    - backend/Dockerfile
    - backend/app/content/pipeline/tts.py
    - backend/app/content/pipeline/tts_router.py
    - tests/validation/manual/run_manual_pipeline_batch_10.py

  existing_voice_assets_used:
    - tools/piper/voices/en_US-lessac-high.onnx
    - tools/piper/voices/en_US-lessac-high.onnx.json

  explicitly_not_changed:
    - docker-compose.yml
    - backend/Dockerfile.gpu
    - backend/requirements.txt
```

## 3. Implementation Summary

```yaml
implementation_summary:
  backend_Dockerfile:
    - added_piper_tts_1_4_1_to_controlled_image
    - added_pathvalidate_3_3_1_required_by_piper_cli

  backend_app_content_pipeline_tts_py:
    - added_CORTAI_PIPER_BIN_override_support
    - preserved_existing_piper_model_path_contract
    - preserved_silent_provider_as_explicit_last_resort_capability

  backend_app_content_pipeline_tts_router_py:
    - CORTAI_TTS_MODE_can_force_requested_provider_for_controlled_batches
    - CORTAI_TTS_MODE_piper_sets_provider_requested_to_piper
    - provider_executed_remains_traceable

  tests_validation_manual_run_manual_pipeline_batch_10_py:
    - added_runtime_Piper_precheck_metadata
    - added_per_run_TTS_provider_status_summary
    - added_non_silent_WAV_probe
    - added_batch_counts_for_piper_requested_piper_executed_silent_fallback_and_non_silent_audio
```

## 4. Docker Build Result

```yaml
docker_build:
  command: docker build -f backend/Dockerfile -t cortai10-api:piper-local backend
  result: passed
  image_tag: cortai10-api:piper-local
  piper_tts_version: 1.4.1
  pathvalidate_version: 3.3.1

  notable_event:
    initial_piper_precheck_failed: true
    failure: ModuleNotFoundError_pathvalidate
    corrective_action: add_pathvalidate_3_3_1_to_backend_Dockerfile
    rebuild_result: passed

  note:
    - Docker_image_build_downloaded_package_dependencies_for_image_construction
    - controlled_batch_runtime_remained_network_none
    - application_external_calls_performed: false
```

## 5. Offline Piper Precheck

```yaml
piper_precheck:
  docker_network_mode: none
  piper_binary_available: true
  piper_binary_path: /usr/local/bin/piper
  piper_voice_model_available: true
  piper_voice_model_path: /workspace/tools/piper/voices/en_US-lessac-high.onnx
  local_synthesis_precheck: passed
  precheck_audio_duration_s: 1.904036
```

## 6. Controlled Batch Execution

```yaml
controlled_batch_execution:
  command_type: docker_run_network_none
  image: cortai10-api:piper-local
  network_mode: none
  batch_id: docker_pipeline_batch_10_piper_local_run
  env_contract:
    CORTAI_TTS_MODE: piper
    CORTAI_PIPER_MODEL: tools/piper/voices/en_US-lessac-high.onnx
    CORTAI_ALLOW_SILENT_TTS_FALLBACK: "0"
    CORTAI_DOCKER_NETWORK_MODE: none

  output_json:
    path: OUT/docker_pipeline_batch_10_piper_local_run/all_agents_all_videos_outputs.json
    complete_agent_outputs_present: true

  output_video_dir:
    path: OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video
```

## 7. Batch Result

```yaml
batch_result:
  total_runs: 10
  runs_completed: 10
  successful_runs: 10
  failed_runs: 0
  valid_video_count: 10
  publishable_count: 10

  piper_binary_available: true
  piper_voice_model_available: true
  docker_network_mode: none

  piper_requested_count: 10
  piper_executed_count: 10
  silent_fallback_count: 0
  audio_non_silent_count: 10
```

## 8. Per-Run TTS Validation

```yaml
per_run_tts_validation:
  run_1:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_2:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_3:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_4:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_5:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_6:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_7:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_8:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_9:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
  run_10:
    tts_provider_requested: piper
    tts_provider_executed: piper
    silent_fallback_used: false
    audio_is_non_silent: true
    valid_video: true
    publishable: true
```

## 9. Audio Quality Evidence

```yaml
audio_quality_evidence:
  audio_stream_present: true
  audio_is_non_silent: true
  non_silent_probe_method: WAV_PCM_RMS_and_max_abs_sample
  audio_non_silent_count: 10

  observed_audio_rms_range:
    min: 4878.615
    max: 5859.461

  observed_audio_max_sample:
    all_runs_max_abs_sample: 32767

  interpretation:
    - audio_stream_is_not_merely_muxed_silence
    - silent_TTS_fallback_quality_blocker_removed_for_this_batch
```

## 10. Generated Videos

```yaml
generated_videos:
  count: 10
  files:
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_138d85a08c41132e.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_1d02e97aa103c515.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_20d72c0f9ec30de3.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_2a86841832147c30.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_6fddf949f08e2209.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_7b656f724eaf97e0.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_7bf223c3416e1694.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_daf6618f83a214a7.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_f2a168fa85f8c697.mp4
    - OUT/docker_pipeline_batch_10_piper_local_run/runtime/content/video/rj_fb1c19bb288e5fae.mp4
```

## 11. Residual Notes

```yaml
residual_notes:
  script_generation_fallback_not_resolved_by_this_execution: true
  trend_analysis_fallback_not_resolved_by_this_execution: true
  experiment_fallback_not_resolved_by_this_execution: true
  voice_quality_improved_from_silent_to_local_Piper_audio: true

  runtime_generated_side_effects:
    - backend/app/assets/catalog.json_has_runtime_usage_counter_mutation

  interpretation:
    - Piper_TTS_quality_gate_passed
    - creative_semantic_quality_still_requires_separate_script_and_experiment_lanes
```

## 12. Non-Authorization Confirmation

```yaml
non_authorization_confirmation:
  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_calls_authorized: false
  external_call_authorized: false
  application_external_calls_performed: false
  batch_external_calls_performed: false
  credential_access_authorized: false
  credential_access_performed: false
  secret_value_access_authorized: false
  secret_value_access_performed: false
  real_publish_authorized: false
  production_ready: false
```

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Local TTS Docker Integration Execution Review
  path: docs/runtime/video-quality-tuning/CortAI_Local_TTS_Docker_Integration_Execution_Review.md
  purpose:
    - accept_or_reject_Piper_Docker_execution
    - accept_or_reject_non_silent_audio_validation
    - decide_if_local_TTS_quality_gate_can_close_with_monitoring
    - preserve_no_runtime_no_external_calls_no_credentials_no_production
```

## 14. Final Verdict

```yaml
final_verdict:
  execution_verdict: COMPLETED_WITH_QUALITY_VALIDATION_PASS_PENDING_REVIEW
  changed_files_within_frozen_scope: true
  docker_image_changed: true
  docker_image_tag: cortai10-api:piper-local
  docker_network_mode: none
  piper_binary_available: true
  piper_voice_model_available: true
  tts_provider_requested: piper
  tts_provider_executed: piper
  silent_fallback_used: false
  audio_stream_present: true
  audio_is_non_silent: true
  valid_video_count: 10
  publishable_count: 10

  external_calls_performed: false
  credential_access_performed: false
  secret_value_access_performed: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
