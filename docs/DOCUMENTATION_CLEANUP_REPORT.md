# Documentation Cleanup Report

## Summary

- Files before cleanup: 220
- Files after cleanup: 113
- Legacy files removed after consolidation: 116
- Empty directories removed: 19
- Runtime/code changes: none

## New Structure

- `docs/active/` - consolidated current-state entrypoints.
- `docs/reference/` - consolidated legacy reference archives.
- `docs/runtime/` - compatibility paths for executable audit gates and current runtime artifacts.

## Consolidated Files Created

- `docs/README.md`
- `docs/active/CORTAI_ARCHITECTURE_AND_STATE.md`
- `docs/active/PHASE_2_6_RELEASE_RECORD.md`
- `docs/active/PHASE_3_PUBLISHER_AND_SANDBOX_RECORD.md`
- `docs/reference/LEGACY_COGNITIVE_MODEL.md`
- `docs/reference/LEGACY_ARCHITECTURE_LAYERS.md`
- `docs/reference/LEGACY_OPERATIONS_AND_PRODUCT_SPECS.md`
- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

## Active Runtime Documents Retained

These were kept in place because current gate runners and audit records use exact paths under `docs/runtime`.

- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md`
- `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
- `docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN.md`
- `docs/runtime/sandbox/controlled-binding/EXTERNAL_SANDBOX_CONTROLLED_BINDING_REVIEW.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_GATE.md`
- `docs/runtime/sandbox/evidence/EXTERNAL_SANDBOX_EVIDENCE_COLLECTION_PLAN.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_PLAN.md`
- `docs/runtime/sandbox/simulation/EXTERNAL_SANDBOX_EXECUTION_SIMULATION_REVIEW.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_EXTERNAL_CALL_AUTHORIZATION_CHECKPOINT.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN.md`
- `docs/runtime/sandbox/external-call-boundary/EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW.md`
- `docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE.md`
- `docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_PLAN.md`
- `docs/runtime/sandbox/pre-execution-guard/EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_REVIEW.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_PLAN.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_GATE.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/envelope/EXTERNAL_SANDBOX_REQUEST_ENVELOPE_PLAN.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/authorization/EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_PLAN.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_PLAN.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE.md`
- `docs/runtime/sandbox/validation-call/implementation-authorization/EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_PLAN.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_ACCEPTANCE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_GATE.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_PLAN.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_GATE.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_GATE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/offline-preparation/EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_PLAN.md`
- `docs/runtime/sandbox/validation-call/pre-implementation/EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE.md`
- `docs/runtime/sandbox/validation-call/pre-implementation/EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE_REVIEW.md`
- `docs/runtime/sandbox/validation-call/pre-implementation/EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/full-system-audit/FULL_SYSTEM_AUDIT_REPORT.md`
- `docs/runtime/full-system-audit/FULL_SYSTEM_EXTREME_AUDIT_CHECKLIST.md`
- `docs/runtime/full-system-audit/FULL_SYSTEM_EXTREME_AUDIT_GATE.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_FINAL_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`
- `docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/reports/PHASE_2_6_WAVES_1_AND_2_REPORT.md`
- `docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md`
- `docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md`
- `docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE_PLAN.md`
- `docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_GATE_PLAN.md`
- `docs/runtime/publisher/platform-integration/PUBLISHER_PLATFORM_INTEGRATION_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE_PLAN.md`
- `docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_GATE.md`
- `docs/runtime/sandbox/adapter/SANDBOX_ADAPTER_IMPLEMENTATION_PLAN.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_GATE.md`
- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`

## Baseline Documents Retained

These historical baselines remain in place because active architecture or v2.6 documents still cite them as context.

- `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_BASELINE_OPERATION_RULES_v1_0.md`
- `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/asset/ASSET_AGENT_DECISION_STANDARD.md`
- `docs/runtime/baselines/asset/ASSET_AGENT_SYSTEM_BIBLE.md`
- `docs/runtime/baselines/attribution/CONTENT_PERFORMANCE_ATTRIBUTION_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/experiment/EXPERIMENT_CAPABILITY_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/learning/LEARNING_AGENT_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/qc/QC_AGENT_SYSTEM_BIBLE.md`
- `docs/runtime/baselines/strategy/STRATEGY_AGENT_SYSTEM_BIBLE_PHASE1.md`
- `docs/runtime/baselines/trend-analysis/TREND_ANALYSIS_AGENT_SYSTEM_BIBLE_PHASE1.md`

## Removed Legacy Files

- `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_FULL_VALIDATION_GATE.md`
- `docs/runtime/LEARNING_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/phase1_completion_report_v1_0.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_VALIDATION_GATE.md`
- `docs/runtime/distributed_scheduler_v1_0.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/EXPERIMENT_CAPABILITY_v2_0_GOVERNANCE_DECISION.md`
- `docs/runtime/phase2_block1_file_list_v1_0.md`
- `docs/runtime/phase2_block2_definition_v1_0.md`
- `docs/runtime/phase2_block2_file_list_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`
- `docs/runtime/distributed_execution_v1_0.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_STANDALONE_GOVERNANCE_DECISION_v2_0.md`
- `docs/runtime/ASSET_AGENT_DECISION_GATE_v1_0.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_HEAVY_AUDIT_CHECKLIST_v2_0.md`
- `docs/runbook_operacional_v1.8.2.md`
- `docs/versioning.md`
- `docs/runtime/ACCOUNT_HEALTH_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/d23_pilot_learning_plan_v1_0.md`
- `docs/runtime/d23_pilot_operational_checklist_v1_0.md`
- `docs/runtime/d23_pilot_operator_index_v1_0.md`
- `docs/runtime/d23_pilot_day_go_no_go_checklist_v1_0.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_GOVERNANCE_DECISION.md`
- `docs/runtime/CONTENT_PERFORMANCE_ATTRIBUTION_v2_0_VALIDATION_GATE.md`
- `docs/runtime/d23_first_12_hours_monitoring_map_v1_0.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_SYSTEM_PLAN.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_v1_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/script_agent_excellence_gate_v1_0.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_PRODUCTION_SOAK_PLAN.md`
- `docs/runtime/QC_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/real_batch_rollout_v1_0.md`
- `docs/runtime/SATURATION_NOVELTY_ENGINE_FULL_VALIDATION_GATE_v1_0.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_MANUAL_CURATION_CANONICAL_FORMAT_v1_0.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_POST_GATE_MONITORING_PLAN_v1_0.md`
- `docs/runtime/voice_agent_excellence_gate_v1_0.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_GATE_EVENT_ARTIFACT_FREEZE_v1_0.md`
- `docs/runtime/SCRIPT_AGENT_PAYOFF_INTELLIGENCE_UPGRADE_PLAN.md`
- `docs/runtime/STRATEGY_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/TREND_ANALYSIS_AGENT_EVOLUTION_v2_0_IMPLEMENTATION_PLAN.md`
- `docs/runtime/pre_phase3_system_final_gate_v1_0.md`
- `docs/runtime/phase2_completion_report_v1_0.md`
- `docs/runtime/phase2_definition_report_v1_0.md`
- `docs/runtime/phase2_implementation_map_v1_0.md`
- `docs/runtime/phase2_block4_file_list_v1_0.md`
- `docs/runtime/phase2_block3_definition_v1_0.md`
- `docs/runtime/phase2_block3_file_list_v1_0.md`
- `docs/runtime/phase2_block4_definition_v1_0.md`
- `docs/runtime/PIPELINE_V2_FULL_SYSTEM_VALIDATION_GATE_v1_0.md`
- `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`
- `docs/runtime/pre_d23_integration_merge_checklist_v1_0.md`
- `docs/runtime/PIPELINE_V2_FULL_SYSTEM_CERTIFICATION_CHECKLIST.md`
- `docs/runtime/PIPELINE_FULL_SYSTEM_MASTER_CERTIFICATION_CHECKLIST_v1_0.md`
- `docs/runtime/PIPELINE_MULTIAGENT_HEAVY_AUDIT_CHECKLIST_v1_0.md`
- `docs/runtime/PIPELINE_TOTAL_HEAVY_AUDIT_CHECKLIST_v1_0.md`
- `docs/cognitive/EXECUTOR.md`
- `docs/cognitive/INDEX.md`
- `docs/cognitive/OBSERVATION.MD`
- `docs/cognitive/EVENT_LOG.md`
- `docs/cognitive/AGENT_REGISTRY.md`
- `docs/cognitive/COGNITIVE_LOOP.md`
- `docs/cognitive/DECISION.md`
- `docs/concurrency/concurrency_failure_matrix_v1_0.md`
- `docs/concurrency/d12_concurrency_hardening_v1_0.md`
- `docs/concurrency/op_key_catalog_v1_0.md`
- `docs/cognitive/STATE_SNAPSHOT.md`
- `docs/cognitive/OUTCOME.md`
- `docs/cognitive/PIPELINE_PHASE.md`
- `docs/cognitive/STATE.md`
- `docs/cognitive/ACTION.md`
- `docs/arquitecture layers/CHECKLIST.md`
- `docs/arquitecture layers/CORE_LOCK.md`
- `docs/arquitecture layers/EXECUTOR_LAYER.md`
- `docs/arquitecture layers/ARCHITECTURE_FREEZE.md`
- `docs/analysis/analysis_research_layer_v1_0.md`
- `docs/analysis/data_consistency_checker_v1_0.md`
- `docs/analytics/content_performance_attribution_v1_0.md`
- `docs/arquitecture layers/TEST_STRATEGY.md`
- `docs/arquitecture layers/VALIDATION_CHECKLIST.md`
- `docs/audit/release_audit_gate_d27_d33_v1_0.md`
- `docs/arquitecture layers/TEST_CASES.md`
- `docs/arquitecture layers/EXTENSION_MAP.md`
- `docs/arquitecture layers/OBSERVER_LAYER.md`
- `docs/arquitecture layers/PLANNER_LAYER.md`
- `docs/ui/operator_actions_v1_0.md`
- `docs/ui/operator_console_v1_0.md`
- `docs/ui/strategy_observatory_v1_0.md`
- `docs/simulation/offline_simulation_engine_v1_0.md`
- `docs/product/content_attribution_v1_0.md`
- `docs/product/strategy_learning_v1_0.md`
- `docs/product/strategy_patch_application_v1_0.md`
- `docs/pr_p1_closed_p2_start.md`
- `docs/roadmap_v2.md`
- `docs/runbook_operacional_v1.8.1.md`
- `docs/pr_checklist_observability.md`
- `docs/d3_go_nogo_checklist.md`
- `docs/observability.md`
- `docs/p2_results.md`
- `docs/pipeline/window_post_pipeline_v1_0.md`
- `docs/integration/external_platform_integration_v1_0.md`
- `docs/intelligence/platform_intelligence_v1_0.md`
- `docs/metrics/metrics_collector_v1_0.md`
- `docs/experiments/experiment_framework_v1_0.md`
- `docs/content/content_template_library_v1_0.md`
- `docs/content/creative_pack_generator_v1_0.md`
- `docs/data/publish_record_v1.md`
- `docs/observability/seek_cursor_encoding_v1_0.md`
- `docs/ops/slo_alerting_v1_0.md`
- `docs/perf/load_testing_v1_0.md`
- `docs/observability/hot_storage_v1_0.md`
- `docs/observability/event_append_v1_0.md`
- `docs/observability/event_index_v1_0.md`
- `docs/observability/event_query_forensics_v1_0.md`

## Removed Empty Directories

- `docs/ui`
- `docs/simulation`
- `docs/product`
- `docs/pipeline`
- `docs/perf`
- `docs/ops`
- `docs/observability`
- `docs/metrics`
- `docs/intelligence`
- `docs/integration`
- `docs/experiments`
- `docs/data`
- `docs/content`
- `docs/concurrency`
- `docs/cognitive`
- `docs/audit`
- `docs/arquitecture layers`
- `docs/analytics`
- `docs/analysis`

## Runtime Reorganization Addendum

- Runtime root markdown files after reorganization: 1
- Runtime documents moved into categorized subfolders: 104
- Runtime index created: docs/runtime/README.md`r
- Gate/test references updated to the new runtime paths.
