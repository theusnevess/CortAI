# Phase 2.5B Kokoro File List

Versao: 1.0  
Status: File list congelada para integracao controlada do provider Kokoro

## Escopo permitido

Diretorios:

- `backend/app/content/pipeline/`
- `backend/scripts/`
- `tests/`
- `docs/runtime/`
- `OUT/audit/phase2_5b_kokoro/`
- `OUT/audit/voice_agent_excellence_gate/`

## Arquivos criados

- `backend/app/content/pipeline/kokoro_adapter.py`
- `tests/test_kokoro_adapter_phase2_5b_unittest.py`
- `tests/test_tts_router_kokoro_phase2_5b_unittest.py`
- `tests/test_kokoro_fallback_phase2_5b_unittest.py`
- `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`
- `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`

## Arquivos alterados permitidos

- `backend/app/content/pipeline/tts_router.py`
- `backend/app/content/pipeline/tts.py`
- `backend/app/content/pipeline/models.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/service.py`
- `backend/scripts/run_voice_agent_excellence_gate.ps1`

## Restricoes

- nao alterar a camada cognitiva
- nao bypassar `TTS Router`
- nao quebrar `tts_trace`
- nao remover `Piper` como fallback
