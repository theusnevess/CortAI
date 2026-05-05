# CortAI Content Pipeline

## 1. Purpose

The CortAI Content Pipeline is the local artifact-production pipeline that turns creative inputs into generated content artifacts.

It coordinates local steps such as:

- script text adaptation;
- TTS audio generation through the TTS Router;
- asset resolution;
- video rendering;
- metadata and trace writing;
- local publish manifest creation when permitted by governance flow.

The Content Pipeline is not the Publisher external execution layer. It does not authorize real upload, real scheduling, real platform publishing, real platform URL emission, `platform_content_id` emission or production receipt creation.

Current system state remains:

```json
{
  "system_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false
}
```

This document describes the pipeline as implemented. It does not authorize runtime integration, external calls, platform APIs, upload, scheduler behavior, real publishing or production residual closure.

## 2. Pipeline Overview

The core production flow is implemented by `ContentPipelineOrchestrator` in `backend/app/content/pipeline/orchestrator.py` and exposed through `ContentPipelineService` in `backend/app/content/pipeline/service.py`.

The high-level flow is:

```text
ExecutionEnvelope
-> create_or_get RenderJob
-> screen text adaptation
-> resolve VoicePlan
-> resolve AssetPlan
-> write visual/edit trace
-> TTS_RUNNING
-> TTS_DONE
-> RENDER_RUNNING
-> RENDER_DONE
-> optional local PublishManifest creation
-> READY or governed HOLD/REJECT/FAILED
```

The pipeline produces local artifacts and local trace surfaces. It does not create platform-side evidence.

The key distinction is:

```text
Generated artifact != published content
PublishManifest != external platform publish
Pipeline READY != production posted
```

Within the Creative Orchestrator flow, the pipeline is first run with `defer_publish_manifest=true`. This means audio and video artifacts can be generated before QC decides whether manifest creation is allowed. If QC approves, the orchestrator may call `finalize_publish`, which creates a local manifest. If QC holds or rejects, the pipeline marks the job as non-publishable and does not attach a manifest.

## 3. Main Files / Modules

| Module | Responsibility |
| --- | --- |
| `backend/app/content/pipeline/models.py` | Defines `ExecutionEnvelope`, `RenderJob`, `RenderJobStatus`, `PublishManifest`, `TtsExecutionTrace` and `PipelineResult`. |
| `backend/app/content/pipeline/service.py` | Public service wrapper around the content pipeline orchestrator. |
| `backend/app/content/pipeline/orchestrator.py` | Coordinates TTS, asset resolution, rendering, local manifest creation and governance outcomes. |
| `backend/app/content/pipeline/tts_router.py` | Executes TTS provider selection and fallback according to `VoicePlan`. |
| `backend/app/content/pipeline/tts.py` | Contains TTS adapters and fallback local/silent audio behavior. |
| `backend/app/content/pipeline/kokoro_adapter.py` | Kokoro TTS adapter used by the TTS Router when available. |
| `backend/app/content/pipeline/render.py` | Renders local video artifacts, subtitles, metadata and corrected backgrounds. |
| `backend/app/content/pipeline/publish.py` | Creates local `PublishManifest` through `StubPublishAdapter`. |
| `backend/app/content/screen_text/service.py` | Converts script text into screen text and narration blocks. |
| `backend/app/runtime/asset_router.py` | Resolves asset plans into runtime visual traces. |
| `backend/app/data/schemas/publish_record.py` | Defines publish record schema constraints. |
| `backend/app/data/publish_records/` | Append/read/query helpers for publish records. |

The module names contain historical terms such as `publish` and `publishable`. In this repository state, those terms must be interpreted carefully: local manifest readiness is not external publication.

## 4. Input Contracts

### ExecutionEnvelope

`ExecutionEnvelope` defines the job-level execution identity:

- `job_id`
- `account_id`
- `creative_pack_id`
- `publish_slot`
- optional `experiment_variant`

The render job ID is derived deterministically from:

```text
creative_pack_id::account_id::publish_slot
```

### Creative Inputs

The pipeline accepts:

- `script_text`
- optional `AssetPlan`
- optional `EditPlan`
- optional `VoicePlan`
- optional legacy `voice_profile`
- language, template, aspect ratio, caption and hashtags metadata

The primary multi-agent source for these inputs is the creative `CreativePack`, defined in `backend/app/creative/contracts/creative_pack.py`.

A full creative pack can include:

- `strategy_profile`
- `trend_profile`
- `script_plan`
- `voice_plan`
- `asset_plan`
- `learning_insights`
- `experiment_plan`
- `experiment_assignment`
- optional `edit_plan`
- account health and constraints

The Content Pipeline consumes these outputs. It does not own the decisions that produced them.

### Relationship With Agents

| Agent / Layer | Relationship To Pipeline |
| --- | --- |
| Script Agent | Provides narration text through `ScriptPlan`. |
| Voice Agent | Provides `VoicePlan` for requested provider, voice ID, style and segment timing. |
| Asset Selection | Provides `AssetPlan` for background/visual asset resolution. |
| Editor / Edit Plan | Provides optional timing, captions, motion, transitions and visual style constraints. |
| Video QC | Evaluates final rendered artifacts and decides APPROVE/HOLD/REJECT semantics. |
| Publisher Governance | Governs publication authority separately from artifact generation. |

See [[CortAI_Architecture_Bible]] and [[CortAI_Governance_Model]].

## 5. Artifact Generation

The pipeline creates local artifacts through three main execution stages.

### TTS Artifact Stage

The orchestrator adapts script text into screen text and narration blocks, then calls `TtsRouter.generate_audio` with:

- narration text;
- `VoicePlan`;
- language;
- render job ID;
- attempt count.

On success, the job moves to `TTS_DONE` and stores:

- `audio_path`;
- `TtsExecutionTrace`;
- TTS events such as `CONTENT/tts_started` and `CONTENT/tts_completed`.

`TtsExecutionTrace` includes:

- `provider_requested`;
- `provider_executed`;
- `voice_id_requested`;
- `voice_id_executed`;
- `style_requested`;
- `fallback_used`;
- `fallback_reason`;
- `latency_s`;
- `audio_duration_s`;
- `segment_durations`.

This is TTS execution evidence within the local content pipeline. It is not publish evidence.

### Render Artifact Stage

The render stage calls `RenderAdapter.render_video` with:

- audio path;
- script text;
- asset plan;
- optional edit plan;
- screen blocks;
- segment durations;
- render job ID;
- template and aspect ratio metadata.

The default `StubRenderAdapter` writes local outputs under `OUT/content`, including:

- rendered video file;
- metadata JSON;
- adapted script text;
- subtitle file;
- corrected background frames;
- render metadata such as timing, theme, asset plan and edit plan.

On success, the job moves to `RENDER_DONE` and stores `video_path`.

Generated video file presence is not publication. It is only a local artifact.

### Trace Artifact Stage

The pipeline also writes local traces:

- visual trace at `OUT/audit/asset_agent_runtime/visual_trace.json`;
- edit trace at `OUT/audit/editor_agent_runtime/edit_trace.json`;
- event records through `OUT/events/events.jsonl` when event emission is configured.

Trace files explain pipeline state. They do not prove external platform success.

## 6. TTS / Render / Publish Boundary

The Content Pipeline contains three distinct concepts that must not be collapsed.

### TTS

TTS can generate audio artifacts locally or through configured provider paths inside the TTS subsystem. Voice Agent does not perform this execution. TTS output can produce `audio_path`, duration and segment durations.

TTS success does not mean video success.

### Render

Render consumes audio, script, assets and edit plan to create a local video artifact.

Render success does not mean QC approval.

### Local Publish Manifest

`StubPublishAdapter.create_manifest` creates a deterministic local `PublishManifest` if the video path exists.

It does not:

- upload a video;
- schedule a platform post;
- call a platform API;
- emit a public URL;
- emit a platform content ID;
- emit a platform receipt;
- persist a publish record by itself.

The word `publish` in `PublishAdapter` currently means local manifest creation, not external publication.

A local `PipelineResult` with `publishable=true` means the pipeline has reached local manifest-readiness semantics. It must not be interpreted as production publish success.

## 7. Manifest And Publish Record

### PublishManifest

`PublishManifest` is defined in `backend/app/content/pipeline/models.py`.

It contains:

- `publish_id`
- `account_id`
- `video_path`
- `caption`
- `hashtags`
- `scheduled_time`

`StubPublishAdapter` builds it deterministically as:

```text
publish_id = "pub_" + envelope.job_id
```

The manifest is a local handoff object. It is not a platform receipt.

A manifest must not contain:

- real platform URL;
- `platform_content_id`;
- production receipt;
- upload confirmation;
- scheduler confirmation.

### Publish Record

Publish record support exists under `backend/app/data/publish_records/` and `backend/app/data/schemas/publish_record.py`.

The schema requires fields such as:

- `publish_id`
- `account_id`
- `job_id`
- `video_id`
- `platform`
- `publish_mode`
- `status`
- `published_at`
- `created_at`

Allowed platforms include:

- `tiktok`
- `youtube_shorts`
- `instagram_reels`

Allowed statuses include:

- `posted`
- `failed`
- `blocked`

The publish record layer is a data contract. It must not be interpreted as proof of real platform posting unless backed by governed external execution evidence, which is not authorized in the current state.

Current Publisher governance and sandbox chain keep production residuals open. Sandbox evidence is not production evidence.

## 8. QC Relationship

Video QC is downstream of local artifact generation.

The Creative Orchestrator runs the content pipeline with `defer_publish_manifest=true`, then calls Video QC with:

- render job ID;
- video path;
- audio path;
- metadata path;
- script text;
- `tts_trace`;
- `visual_trace`;
- `edit_trace`.

Video QC evaluates the final local artifact and returns APPROVE/HOLD/REJECT semantics.

Observed governance flow:

- `APPROVE` can allow local manifest finalization through `finalize_publish`.
- `HOLD` marks the job as non-publishable with HOLD state.
- `REJECT` marks the job as non-publishable with REJECT state.

QC evaluates artifacts. QC does not upload, publish or become Publisher.

Pipeline manifest-readiness after QC approval is still not external platform success.

## 9. Publisher Governance Boundary

Publisher governance is separate from the Content Pipeline.

The Phase 3 Publisher chain established:

- Publisher governance before implementation;
- trace-only Publisher implementation;
- dry-run evidence gates;
- sandbox adapter;
- validation envelope;
- execution simulation;
- controlled binding;
- external-call boundary;
- pre-execution guard;
- offline preparation layer;
- runtime integration readiness gates.

The current state is still:

```json
{
  "external_call_authorized": false,
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "production_ready": false
}
```

The Content Pipeline may produce local artifacts and local manifests. It does not cross the Publisher external-call boundary.

Publisher authority is governed, but Publisher is not an external execution client in the current state.

## 10. What Is Not Authorized

The Content Pipeline documentation does not authorize:

- real upload;
- real scheduler;
- real publish;
- external platform API call;
- HTTP/SDK/endpoint/DNS authorization;
- platform credential access;
- request transformation into transport payload;
- production `published_url`;
- production `platform_content_id`;
- production receipt;
- treating `PublishManifest` as posted content;
- treating `publishable=true` as production publish success;
- treating local video artifact existence as publish success;
- closing production residuals;
- runtime integration beyond the already implemented local pipeline behavior.

Forbidden equivalences:

```text
artifact generated != publish success
render done != QC approval
QC approve != external publish
manifest created != platform receipt
publishable true != production posted
publish record schema != real platform evidence
sandbox evidence != production evidence
```

Fail-closed rule:

```text
If production publish evidence is absent, the system must report absent evidence. It must not infer external success.
```

## 11. Obsidian Links

Primary links:

- [[CortAI_Architecture_Bible]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_System_State_Definition]]

Related links:

- [[CortAI_Script_Agent]]
- [[CortAI_Voice_Agent]]
- [[CortAI_Creative_Orchestrator]]
- [[CortAI_Publisher_Agent]]
- [[CortAI_Video_QC_Agent]]

Final invariant:

> The Content Pipeline generates local artifacts and local manifest-readiness evidence. It does not prove external publication, does not emit platform identity and does not close production residuals.
