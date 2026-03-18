# Phase 2.5 Voice Agent File List

Versao: 1.0  
Status: File list congelada para implementacao controlada  
Fase: Phase 2.5A

## Objetivo
Congelar o raio de alteracao da correcao arquitetural do subsistema de voz.

## Diretórios permitidos

- `backend/app/creative/agents/voice/`
- `backend/app/creative/contracts/`
- `backend/app/creative/orchestrator/`
- `backend/app/content/pipeline/`
- `tests/`
- `docs/runtime/`
- `OUT/audit/phase2_5_voice_agent/`

## Arquivos criados nesta fase

- `backend/app/creative/agents/voice/interpreter.py`
- `backend/app/content/pipeline/tts_router.py`
- `tests/test_voice_interpreter_phase2_5_unittest.py`
- `tests/test_voice_agent_service_phase2_5_unittest.py`
- `tests/test_tts_router_phase2_5_unittest.py`
- `tests/test_voice_plan_integration_phase2_5_unittest.py`
- `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`
- `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`

## Arquivos alterados permitidos

- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/tts.py`

Alteracoes condicionais permitidas:

- `backend/app/content/pipeline/models.py`
- `backend/app/creative/orchestrator/events.py`

## Integrações obrigatórias

- `Voice Agent -> Voice Interpreter`
- `Content Pipeline -> TTS Router`
- `TTS Router -> tts.py`

## Integrações proibidas

- `Voice Agent -> provider TTS direto`
- `Creative Orchestrator -> provider TTS direto`
- `Voice Interpreter -> Content Pipeline direto`
- heuristica cognitiva escondida em `tts.py`

## Testes obrigatórios

- interpretacao de `hook/setup/payoff`
- `VoicePlan` operativo
- fallback explicito
- respeito a `VoicePlan.provider`
- compatibilidade com `Piper`

## Critério de conclusão

- `VoicePlan` operativo
- `TTS Router` canônico
- pipeline obedece o plano
- `Piper` preservado
- regressao controlada
