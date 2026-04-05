# TREND_ANALYSIS_AGENT_MANUAL_CURATION_CANONICAL_FORMAT_v1_0

## Objective

This document defines the canonical `manual_curation` input format for `Trend Analysis Agent v2.0`.

This format exists to provide:
- structured human-curated trend evidence
- explicit provenance
- freshness metadata
- evidence references compatible with Trend validation and fallback governance

This is not a legacy profile file format.
This is the governed manual evidence format that feeds Trend source assembly in Phase B and Phase C.

## Storage Location

Canonical location:
- `backend/data/trends/manual_curation/<niche>.json`

Examples:
- `backend/data/trends/manual_curation/horror.json`
- `backend/data/trends/manual_curation/true_crime.json`

## Required Fields

Minimum required fields:
- `niche`
- `region`
- `source`
- `collected_at`
- `sample_size`
- `dominant_hooks`
- `avg_duration`
- `pacing`
- `visual_style`
- `evidence`
- `source_metadata`

## Optional Fields

Optional but allowed:
- `text_style`
- `updated_at`
- `valid_until`
- `trend_version`
- `collector_version`

Important:
- `text_style` remains weakly consumed downstream and should not be inflated with unnecessary complexity.
- `valid_until` may be present for documentation, but the current source-record assembly path derives freshness primarily from `collected_at` and source freshness policy.

## Canonical JSON Shape

```json
{
  "niche": "horror",
  "region": "US",
  "source": "manual_curation",
  "collected_at": "2026-04-03T00:00:00Z",
  "updated_at": "2026-04-03T00:00:00Z",
  "valid_until": "2026-04-17T00:00:00Z",
  "sample_size": 8,
  "dominant_hooks": ["story_opening", "ominous_question"],
  "avg_duration": "8-12s",
  "pacing": "fast_first_3s",
  "visual_style": "dark_backgrounds",
  "text_style": "large_caption_focus",
  "evidence": [
    {
      "evidence_type": "manual_top_video",
      "source": "manual_curation",
      "reference_id": "horror_seed_001",
      "reference_url": "https://example.com/horror_seed_001",
      "captured_at": "2026-04-03T00:00:00Z",
      "region": "US",
      "metadata": {
        "rank": 1,
        "notes": "Fast cold-open with high-contrast captions."
      }
    }
  ],
  "source_metadata": {
    "curation_method": "human_structured_review",
    "curator_id": "trend_seed_v1",
    "sample_window": "last_14_days",
    "record_version": "manual-curation-v1"
  },
  "trend_version": "2.0",
  "collector_version": "manual-curation-v1"
}
```

## Rules

### Provenance

`source` must be:
- `manual_curation`

Each `evidence` item must include:
- `evidence_type`
- `source`
- `reference_id`

Recommended:
- `reference_url`
- `captured_at`
- `metadata.rank`

### Freshness

Manual curation is governed by the 14-day freshness window currently defined in Trend v2.0.

Operational implication:
- stale manual curation should not be treated as primary approved evidence
- stale manual curation may only survive through explicit fallback paths if separately validated

### Sample Size

`sample_size` should reflect the number of manually reviewed items contributing to the summary.

Rule of thumb:
- `< 3` is weak
- `3-5` may degrade to `HOLD`
- `>= 6` is preferred for stable manual seeds

### Hook Ordering

`dominant_hooks` should be ordered from strongest to weakest manual signal.

The current Trend assembly path preserves ordering significance and combines it with source priority.

### Niche Discipline

Each file must be niche-specific.

Do not mix:
- `horror`
- `true_crime`
- `facts`
- `history`
- `conspiracy`

inside the same record.

## Non-Goals

This format is not intended to:
- replace Creative Center
- replace Learning
- encode downstream strategy directly
- become an ungoverned opinion dump

## Current Status

This format is operational in the current Trend runtime as a source-record input for:
- source assembly
- confidence assembly
- validation
- fallback hierarchy

It is the correct interim evidence path before Creative Center real collection is activated.
