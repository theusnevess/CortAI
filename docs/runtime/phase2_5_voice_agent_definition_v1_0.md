# Phase 2.5 Voice Agent Definition

Versao: 1.0  
Status: Definicao formal de escopo  
Fase: Phase 2.5A

## Objetivo
Corrigir a arquitetura de controle da voz sem redesenhar o CortAI.

Ao final da fase:

- `VoicePlan` deve ser contrato operativo real
- `Voice Interpreter` deve existir e ser deterministicamente rule-based
- `TTS Router` deve ser o ponto canônico de roteamento
- o pipeline deve obedecer `VoicePlan`
- `Piper` deve permanecer funcional

## Problema atual que esta fase corrige

- `VoicePlan` era parcialmente decorativo
- provider declarado e provider executado podiam divergir sem rastreabilidade adequada
- o Voice Agent nao interpretava `hook/setup/payoff`
- a entrega de voz nao possuia modelagem minima de ritmo, pausa e contraste

## Escopo permitido

- ampliar `VoicePlan`
- criar `Voice Interpreter`
- criar `TTS Router`
- adaptar `Creative Orchestrator -> Voice Agent -> Content Pipeline`
- adicionar observabilidade minima de provider requisitado, provider executado e fallback

## Fora de escopo

- novos providers pesados
- benchmarking amplo de TTS
- clonagem de voz
- emotion engine avancado
- refactor amplo da Fase 1

## Estado-alvo

```text
Creative Orchestrator
-> Voice Agent
-> Voice Interpreter
-> VoicePlan
-> Content Pipeline
-> TTS Router
-> Provider Adapter
-> Audio
```

## Regras

- Fase 2 decide; Fase 1 executa
- `Creative Orchestrator` continua coordenador unico
- `Voice Agent` continua cognitivo e nao sintetiza audio diretamente
- fallback deve ser explicito e auditavel
- a v1 deve ser pequena, simples e auditavel

## Criterios de aceite

- existe `Voice Interpreter`
- existe `TTS Router`
- `VoicePlan.provider` deixa de ser decorativo
- pipeline respeita `VoicePlan`
- `Piper` continua operacional
- testes, regressao e smoke passam
