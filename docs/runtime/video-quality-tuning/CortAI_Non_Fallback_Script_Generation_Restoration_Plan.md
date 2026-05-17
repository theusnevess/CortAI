---
artifact_id: cortai_non_fallback_script_generation_restoration_plan
artifact_name: CortAI Non-Fallback Script Generation Restoration Plan
artifact_type: non_fallback_script_generation_restoration_plan
system: CortAI
date: 2026-05-06
lane: Video Quality Tuning
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

plan_mode: documentation_only_restoration_plan
reviewed_authorization_review: CortAI Non-Fallback Script Generation Restoration Authorization Review
restoration_plan_defined: true
preferred_boundary: offline_local_only

execution_authorized: false
script_generation_patch_authorized: false
test_execution_authorized: false
docker_execution_authorized: false
external_calls_authorized: false
credential_access_authorized: false
secret_value_access_authorized: false
production_ready: false
---

# CortAI Non-Fallback Script Generation Restoration Plan

## 1. Purpose

This artifact defines the documentation-only plan for restoring non-fallback script generation.

It compares local options, identifies probable fallback causes, defines the HOOK -> SETUP -> PAYOFF quality contract, and sets future validation criteria. It does not authorize implementation, code patches, tests, Docker execution, external LLM calls, credential access, runtime execution, real publishing, or production readiness.

## 2. Current Context

```yaml
current_context:
  local_TTS_quality_gate: closed_with_monitoring
  piper_audio_status: accepted
  silent_fallback_blocker: resolved_for_controlled_batch

  current_primary_quality_gap:
    lane: restore_non_fallback_script_generation
    issue: script_generation_fallback_still_produces_generic_narrative_outputs
    impact:
      - weak_or_repetitive_hooks
      - predictable_setup_progression
      - payoff_specificity_loss
      - reduced_retention_quality
```

## 3. Observed Script Generation Architecture

```yaml
observed_architecture:
  script_agent_entry:
    file: backend/app/creative/agents/script/service.py
    role:
      - builds_ScriptGenerationContext
      - calls_LocalScriptGeneratorService_generate_structured
      - adapts_HOOK_SETUP_PAYOFF_through_ScreenTextAdapter
      - evaluates_quality_rubric_hook_setup_payoff_diversity_and_confidence

  script_generation_service:
    file: backend/app/content/script_gen/service.py
    role:
      - builds_prompt
      - chooses_provider_order
      - supports_groq_and_ollama_generation_paths
      - emits_deterministic_fallback_when_no_provider_succeeds

  current_contract:
    output_contract: ScriptPlan
    required_blocks:
      - hook
      - setup
      - payoff
    narration_method: ScriptPlan.narration_text
```

## 4. Probable Fallback Causes

```yaml
probable_fallback_causes:
  primary_cause:
    id: provider_order_empty_under_SAFE_PRE_CROSSING
    evidence:
      - SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED_false_blocks_groq
      - SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED_false_blocks_groq_key_use
      - SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED_false_blocks_ollama
      - SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED_false_blocks_ollama_request
      - _provider_order_returns_empty_when_both_external_and_local_runtime_paths_are_blocked
      - generate_structured_then_uses_deterministic_fallback
    interpretation:
      - fallback_is_expected_under_current_governance
      - fallback_is_not_a_runtime_failure
      - fallback_is_quality_degradation_from_missing_authorized_local_nonfallback_provider

  secondary_cause:
    id: deterministic_fallback_marked_as_fallback_even_when_structurally_valid
    evidence:
      - _deterministic_fallback_sets_provider_used_fallback
      - generation_mode_is_fallback_contextual
      - fallback_decision_used_true
    interpretation:
      - structurally_valid_scripts_are_not_counted_as_nonfallback_generation
      - future_local_generator_must_report_provider_success_without_mislabeling_fallback

  tertiary_cause:
    id: local_ollama_path_is_not_authorized_in_current_boundary
    evidence:
      - ollama_generation_requires_runtime_wiring_authorization
      - ollama_generation_requires_request_transformation_authorization
      - ollama_generation_requires_transport_payload_authorization
    interpretation:
      - local_Ollama_may_be_future_option
      - local_Ollama_requires_separate_authorization_before use
```

## 5. Local Restoration Options

```yaml
local_restoration_options:
  option_1:
    name: offline_structured_template_generator
    boundary: offline_local_only
    description:
      - promote_a_dedicated_local_structured_generator_path
      - generate_specific_HOOK_SETUP_PAYOFF_from_topic_niche_strategy_trends_learning_and_experiment_context
      - mark_provider_used_as_local_structured_when_quality_contract_passes
      - keep_fallback_for_exception_or_contract_failure_only
    benefits:
      - no_external_calls
      - no_credentials
      - deterministic_and_testable
      - compatible_with_Docker_network_none
      - fastest_path_to_zero_script_fallback_count
    risks:
      - may_remain_template_like_if_variation_is_weak
      - quality_depends_on_strong_topic_and_payoff_rules
    recommendation: preferred

  option_2:
    name: offline_rule_based_narrative_combinator
    boundary: offline_local_only
    description:
      - use_curated_narrative_families_and_specificity_rules
      - combine_entity_event_anomaly_evidence_and_payoff_structures
      - use_novelty_hints_to_avoid_repeated_payoff_shapes
    benefits:
      - no_runtime_service_dependency
      - better_variation_than_single_fallback_templates
      - can_integrate_with_existing_quality_rubric
    risks:
      - still_not_true_LLM_generation
      - needs_enough_families_to_avoid_repetition
    recommendation: acceptable_if_option_1_and_2_are_combined

  option_3:
    name: local_ollama_provider
    boundary: local_runtime_service
    description:
      - use_local_Ollama_http_endpoint_for_JSON_script_generation
      - keep_external_calls_blocked
      - require_runtime_wiring_and_transport_payload_authorization
    benefits:
      - higher_semantic_variety
      - closer_to_true_generation
    risks:
      - requires_local_runtime_service
      - crosses_current_transport_boundary
      - requires_separate_authorization_artifact
    recommendation: defer_until_offline_structured_path_is_evaluated

  option_4:
    name: external_LLM_provider
    boundary: external_call_and_credentials
    description:
      - Groq_or_other_external_LLM_generates_structured_JSON
    benefits:
      - highest_semantic_flexibility
    risks:
      - external_call_boundary
      - credential_boundary
      - request_transformation_and_transport_payload_boundary
    recommendation: not_selected
    current_authorization: false
```

## 6. Recommended Plan

```yaml
recommended_plan:
  selected_path: offline_structured_template_generator_plus_rule_based_narrative_combinator
  preferred_boundary: offline_local_only
  external_LLM_dependency: none
  local_runtime_service_dependency: none

  goal:
    - introduce_a_real_local_nonfallback_script_provider
    - preserve_fallback_only_for_failure_or_quality_contract_violation
    - keep_all_generation_inside_process_and_Docker_network_none

  provider_identity_candidate:
    provider_used: local_structured
    model_used: deterministic_narrative_rules_v1
    generation_mode: local_structured
    fallback_used: false

  core_change_to_plan_for_future_patch:
    - split_current_deterministic_fallback_from_normal_local_structured_generation
    - make_local_structured_generation_the_default_safe_pre_crossing_provider
    - reserve_fallback_contextual_for_exceptions_or_failed_quality_contract
```

## 7. HOOK -> SETUP -> PAYOFF Quality Contract

```yaml
quality_contract:
  global_requirements:
    - English_only
    - three_blocks_required
    - each_block_non_empty
    - narration_text_preserves_block_order
    - screen_text_adapter_must_not_remove_narrative_specificity

  hook:
    purpose: immediate_specific_anomaly
    requirements:
      - concrete_entity_or_artifact_present
      - anomaly_or_contradiction_visible_in_first_clause
      - no_generic_mediator_opening_unless_topic_requires_it
      - no_empty_mystery_language
      - target_length_words_6_to_11

  setup:
    purpose: escalation_or_evidence
    requirements:
      - intensifies_hook_instead_of_repeating_it
      - adds_observable_evidence_or_constraint
      - maintains_topic_specific_nouns
      - target_length_words_7_to_13

  payoff:
    purpose: concrete_turn_or_resolution
    requirements:
      - resolves_narrative_promise_with_observable_reveal
      - includes_concrete_fact_or_object
      - avoids_abstract_unknown_presence_endings
      - avoids_weak_payoff_terms_where_possible
      - target_length_words_7_to_13
```

## 8. Future Patch Candidate Scope

```yaml
future_patch_candidate_scope:
  primary_files:
    - backend/app/content/script_gen/service.py
    - backend/app/creative/agents/script/service.py

  secondary_files_if_needed:
    - backend/app/creative/agents/script/provider_fallback_trace.py
    - backend/app/creative/agents/script/models.py
    - tests/validation/manual/run_manual_pipeline_batch_10.py

  contracts_read_only_unless_separately_authorized:
    - backend/app/creative/contracts/creative_pack.py

  explicit_note:
    - no_patch_scope_is_authorized_by_this_plan
    - exact_patch_scope_requires_future_execution_authorization
```

## 9. Future Validation Model

```yaml
future_validation_model:
  static_validation:
    - py_compile_changed_python_files
    - diff_review_for_provider_boundary
    - scan_for_external_call_authority_regression
    - scan_for_credential_access_regression

  unit_or_targeted_validation_candidates:
    - local_structured_provider_returns_fallback_used_false
    - local_structured_provider_outputs_HOOK_SETUP_PAYOFF
    - safe_pre_crossing_external_guards_remain_false
    - external_provider_paths_still_block_without_separate_authorization
    - ScreenTextAdapter_preserves_script_blocks

  batch_validation_candidate:
    - controlled_10_video_batch
    - piper_TTS_quality_gate_still_passes
    - script_fallback_count_is_zero
    - generation_mode_is_local_structured_for_all_10_runs
    - provider_used_is_local_structured_for_all_10_runs
    - complete_agent_outputs_json_preserved
```

## 10. Acceptance Criteria

```yaml
acceptance_criteria:
  script_generation:
    fallback_used: false
    provider_used: local_structured
    generation_mode: local_structured
    script_fallback_count: 0

  quality_contract:
    hook_setup_payoff_present: true
    hook_specificity_passed: true
    setup_progression_passed: true
    payoff_specificity_passed: true
    narration_text_valid_for_TTS: true
    screen_text_contract_preserved: true

  batch:
    total_runs: 10
    valid_video_count: 10
    publishable_count: 10
    piper_executed_count: 10
    silent_fallback_count: 0
    audio_non_silent_count: 10

  boundaries:
    external_calls_performed: false
    credential_access_performed: false
    secret_value_access_performed: false
    production_ready: false
```

## 11. Non-Authorization Boundary

```yaml
non_authorization_boundary:
  execution_authorized: false
  script_generation_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  local_ollama_runtime_authorized: false
  external_LLM_authorized: false
  external_calls_authorized: false
  external_call_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  env_value_read_authorized: false
  real_publish_authorized: false
  production_ready: false
```

## 12. Dependencies And Carry-Forward

```yaml
dependencies_and_carry_forward:
  depends_on:
    - local_TTS_quality_gate_closed_with_monitoring

  should_not_block_this_lane:
    - experiment_assignment_gap
    - asset_reuse_gap
    - catalog_json_runtime_mutation_policy_gap

  must_preserve:
    - local_Piper_TTS_success
    - complete_agent_outputs_json
    - SAFE_PRE_CROSSING_external_call_boundary
    - credential_boundary
```

## 13. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Non-Fallback Script Generation Restoration Plan Review
  path: docs/runtime/video-quality-tuning/CortAI_Non_Fallback_Script_Generation_Restoration_Plan_Review.md
  purpose:
    - accept_or_reject_restoration_plan
    - accept_or_reject_offline_local_structured_generator_path
    - confirm_external_LLM_and_local_Ollama_are_not_authorized_by_this_plan
    - decide_if_execution_authorization_can_be_created
```

## 14. Final Verdict

```yaml
final_verdict:
  plan_mode: documentation_only_restoration_plan
  restoration_plan_defined: true
  preferred_boundary: offline_local_only
  recommended_path: offline_structured_template_generator_plus_rule_based_narrative_combinator

  execution_authorized: false
  script_generation_patch_authorized: false
  test_execution_authorized: false
  docker_execution_authorized: false
  external_calls_authorized: false
  credential_access_authorized: false
  secret_value_access_authorized: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true
```
