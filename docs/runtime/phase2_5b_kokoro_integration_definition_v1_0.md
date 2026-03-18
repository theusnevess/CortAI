# Phase 2.5B Kokoro Integration

Versao: 1.0  
Status: Definicao formal da integracao do provider Kokoro  
Dependencia: `Phase 2.5A` concluida

## Objetivo
Introduzir `Kokoro` como provider local principal de TTS sem reabrir a arquitetura da voz.

## Regras

- `VoicePlan`, `Voice Interpreter` e `TTS Router` continuam como base arquitetural
- roteamento de provider continua apenas no `TTS Router`
- `Piper` permanece fallback duro
- esta fase integra apenas `Kokoro`

## Arquitetura alvo

```text
VoicePlan
-> TTS Router
   -> Kokoro (primary)
   -> Piper (fallback)
-> Content Pipeline
```

## Resultado esperado

- voz mais natural que o baseline `Piper`
- arquitetura preservada
- fallback seguro
- comparacao objetiva via rerun do `Voice Agent Excellence Gate`
