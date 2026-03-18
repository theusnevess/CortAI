# Voice Agent Excellence Gate

Versao: 1.0  
Status: Aprovado para execucao  
Script: `backend/scripts/run_voice_agent_excellence_gate.ps1`

## Objetivo
Medir a qualidade real do subsistema de voz apos a correcao estrutural da `Phase 2.5A`.

O gate valida:

- obediencia arquitetural a `VoicePlan`
- rastreabilidade de provider requisitado e executado
- contraste narrativo entre `hook/setup/payoff`
- distribuicao de pausas
- monotonia perceptiva por proxies deterministicas
- latencia e fallback operacional
- comportamento em bateria textual e em lote minimo de videos

## Pre-requisitos

- `Phase 2.5A` concluida e estruturalmente validada
- `Voice Interpreter` presente
- `TTS Router` presente
- `Piper` funcional

## Evidencia gerada

- `OUT/audit/voice_agent_excellence_gate/AUDIT_REPORT.md`
- `OUT/audit/voice_agent_excellence_gate/voice_battery_25.json`
- `OUT/audit/voice_agent_excellence_gate/video_batch_5.json`
- `OUT/audit/voice_agent_excellence_gate/fallback_trace.json`
- `OUT/audit/voice_agent_excellence_gate/delivery_profile_summary.json`
- `OUT/audit/voice_agent_excellence_gate/latency_summary.json`
- `OUT/audit/voice_agent_excellence_gate/segment_pause_analysis.json`
- `OUT/audit/voice_agent_excellence_gate/monotony_proxy_analysis.json`

## Bateria minima

- 25 casos textuais:
  - 5 horror
  - 5 true crime
  - 5 investigative
  - 5 curiosity
  - 5 dark storytelling
- 5 videos completos
- 1 bateria forcada de fallback

## Criterio de GO / NO-GO

O gate retorna `GO` apenas se:

- `VoicePlan` continuar obedecido
- provider traceability estiver materializada
- fallback permanecer explicito
- `Piper` continuar funcional
- a bateria textual permanecer estavel
- o lote de video continuar operacional
- proxies de contraste/pausa/monotonia passarem thresholds minimos

## Interpretacao

`GO` significa que o subsistema de voz esta:

- arquiteturalmente coerente
- perceptivelmente melhor que o baseline simbolico anterior
- operacionalmente auditavel

`NO-GO` significa que a voz ainda nao e componente forte do produto.
