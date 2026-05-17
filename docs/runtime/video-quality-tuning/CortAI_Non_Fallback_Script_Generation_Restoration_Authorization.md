---
artifact_id: cortai_non_fallback_script_generation_restoration_authorization
artifact_name: CortAI Non-Fallback Script Generation Restoration Authorization
artifact_type: non_fallback_script_generation_restoration_authorization
system: CortAI
date: 2026-05-06
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

authorization_mode: documentation_only_script_generation_restoration_planning
authorization_verdict: AUTHORIZE_FUTURE_NON_FALLBACK_SCRIPT_GENERATION_RESTORATION_PLANNING_PENDING_REVIEW

planning_authorized: true
execution_authorized: false
script_generation_patch_authorized: false
test_execution_authorized: false
docker_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
runtime_execution_authorized: false
production_ready: false
---

# CortAI Non-Fallback Script Generation Restoration Authorization

## 1. Purpose

This artifact authorizes a future documentation-only planning step for restoring non-fallback script generation quality.

It opens a separate quality lane after the local Piper TTS quality gate closed with monitoring. It does not authorize code changes, script generation implementation changes, tests, Docker execution, external LLM calls, credential access, runtime execution, real publishing, or production readiness.

## 2. Current Quality Context

```yaml
current_quality_context:
  local_TTS_quality_gate: closed_with_monitoring
  piper_local_audio_accepted: true
  silent_fallback_blocker_resolved_for_batch: true

  remaining_primary_quality_blocker:
    id: restore_non_fallback_script_generation
    issue: script_generation_fallback_still_drives_generic_hooks_setups_and_payoffs
    priority: highest_remaining_video_quality_lane

  related_but_separate_lanes:
    - restore_experiment_assignment_and_result_recording
    - reduce_asset_reuse_and_signature_collisions
    - decide_catalog_json_runtime_mutation_policy
```

## 3. Authorization Decision

```yaml
authorization_decision:
  authorization_verdict: AUTHORIZE_FUTURE_NON_FALLBACK_SCRIPT_GENERATION_RESTORATION_PLANNING_PENDING_REVIEW
  planning_authorized: true

  execution_authorized: false
  script_generation_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  production_ready: false
```

## 4. Planning Scope

```yaml
planning_scope:
  allowed_future_planning:
    - inspect_current_script_agent_fallback_causes_without_execution
    - identify_offline_local_generation_options
    - define_contract_for_HOOK_SETUP_PAYOFF_quality
    - define_validation_model_for_non_fallback_script_output
    - define_whether_existing_local_Ollama_path_is_viable_without_external_calls
    - define_separate_authorization_needed_if_external_LLM_is_considered

  preferred_boundary:
    - offline_local_only

  external_LLM_rule:
    if_considered: requires_separate_explicit_authorization_artifact
    current_authorization: false
```

## 5. Candidate Future Surfaces For Planning

```yaml
candidate_future_surfaces_for_planning:
  script_agent:
    - backend/app/creative/agents/script/service.py
    - backend/app/creative/agents/script/models.py
    - backend/app/creative/agents/script/provider_fallback_trace.py

  script_generation_service:
    - backend/app/content/script_gen/service.py

  batch_quality_validation:
    - tests/validation/manual/run_manual_pipeline_batch_10.py

  contracts:
    - backend/app/creative/contracts/creative_pack.py

  note:
    - these_are_planning_surfaces_only
    - no_future_patch_scope_is_authorized_by_this_artifact
```

## 6. Future Acceptance Model To Define

```yaml
future_acceptance_model_to_define:
  required_properties:
    - script_generation_mode_not_fallback
    - provider_success_or_local_generation_success_visible
    - hook_setup_payoff_structure_present
    - hook_is_specific_not_generic
    - setup_builds_tension_or_context
    - payoff_has_clear_turn_or_resolution
    - narration_text_feeds_TTS_correctly
    - screen_text_does_not_degrade_script
    - fallback_used_false_for_script_generation

  batch_acceptance_candidate:
    - ten_video_batch_generated
    - script_fallback_count_zero_or_explicitly_bounded
    - piper_audio_quality_gate_stays_passed
    - complete_agent_outputs_json_preserved
```

## 7. Non-Authorization Boundary

```yaml
not_authorized:
  code_patch: true
  script_generation_patch: true
  test_execution: true
  docker_execution: true
  runtime_execution: true
  external_LLM_call: true
  external_calls: true
  credential_access: true
  secret_value_access: true
  env_value_read: true
  real_publish: true
  production_ready_declaration: true
```

## 8. Guardrail Preservation

```yaml
guardrails_preserved:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  runtime_execution_authorized: false
  runtime_integration_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false
```

## 9. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Non-Fallback Script Generation Restoration Authorization Review
  path: docs/runtime/video-quality-tuning/CortAI_Non_Fallback_Script_Generation_Restoration_Authorization_Review.md
  purpose:
    - accept_or_reject_documentation_only_planning_authorization
    - confirm_offline_local_only_preference
    - confirm_external_LLM_requires_separate_authorization
    - decide_if_restoration_plan_can_be_created
```

## 10. Final Verdict

```yaml
final_verdict:
  authorization_verdict: AUTHORIZE_FUTURE_NON_FALLBACK_SCRIPT_GENERATION_RESTORATION_PLANNING_PENDING_REVIEW
  planning_authorized: true
  execution_authorized: false
  script_generation_patch_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  runtime_execution_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
