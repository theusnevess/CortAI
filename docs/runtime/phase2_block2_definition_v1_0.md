CortAI - Definicao do Bloco 2 da Fase 2

Strategy and Account Health Layer

Versao: 1.0
Status: Aprovado para Implementacao
Documento: `docs/runtime/phase2_block2_definition_v1_0.md`

---

## 1. Objetivo

Este documento define o escopo, os contratos minimos, o fluxo e os criterios de conclusao do Bloco 2 da Fase 2 do CortAI.

O Bloco 2 introduz a primeira camada de decisao estrategica por conta, sem expandir para contexto externo amplo, aprendizado adaptativo completo ou experimentacao formal.

O objetivo deste bloco e responder, de forma controlada e auditavel:

- qual objetivo esta conta esta perseguindo agora
- qual abordagem de conteudo faz sentido para esta conta
- se a conta deve operar em modo `SAFE`, `CAUTION` ou `HOLD`
- se a producao atual deve ser mais agressiva ou mais conservadora

---

## 2. Escopo do Bloco 2

O Bloco 2 cobre apenas:

- `Strategy Agent`
- `Account Health Agent`

Nada alem disso.

### 2.1 Escopo proibido

Nao implementar neste bloco:

- `Trend Analysis Agent`
- `Learning Agent`
- `Experiment Capability` formal
- `Asset Selection Agent`
- qualquer mudanca estrutural na Fase 1
- qualquer alteracao em runtime, scheduler, safety, `publish_record`, metrics, analysis, simulation ou consistency fora da integracao minima permitida

---

## 3. Papel do Bloco 2 na Fase 2

O Bloco 1 provou a camada cognitiva minima:

`Creative Orchestrator -> Script Agent -> Voice Agent -> Content Pipeline -> Video QC`

O Bloco 2 adiciona a primeira decisao contextual por conta:

`Account Health Agent -> Strategy Agent -> Creative Orchestrator -> Bloco 1 -> Fase 1`

Em termos práticos:

- `Account Health Agent` protege a conta
- `Strategy Agent` orienta o modo de conteudo
- `Creative Orchestrator` passa a consumir essas decisoes

---

## 4. Regras Arquiteturais

### 4.1 Nao regredir a Fase 1

O Bloco 2 nao pode:

- alterar contratos da Fase 1
- alterar comportamento do runtime
- alterar comportamento do safety
- alterar `publish_record`
- alterar `metrics collector`
- alterar `analysis layer`

### 4.2 Nao regredir o Bloco 1

O Bloco 2 nao pode quebrar:

- `Creative Orchestrator` minimo
- `Script Agent`
- `Voice Agent`
- `Video QC Agent`
- smoke aprovado do Bloco 1

### 4.3 Orquestracao centralizada

`Strategy Agent` e `Account Health Agent` nao chamam runtime, safety ou pipeline diretamente.

Toda coordenacao passa pelo `Creative Orchestrator Service`.

### 4.4 Decisao, nao execucao

O Bloco 2 decide e recomenda.

O Bloco 2 nao:

- publica
- grava `publish_record`
- dispara `metrics`
- altera artefatos apos render

---

## 5. Componentes do Bloco 2

### 5.1 Account Health Agent

#### Objetivo

Avaliar a saude operacional da conta antes da geracao criativa.

#### Entrada minima

- `account_id`
- historico recente
- sinais operacionais
- frequencia de publicacao
- repeticao de formato
- queda brusca de views, quando houver

#### Saida minima

- `health_status`
- `reasons`
- `recommended_constraints`

#### Valores validos de `health_status`

- `SAFE`
- `CAUTION`
- `HOLD`

#### Papel no fluxo

- `SAFE`: fluxo segue normalmente
- `CAUTION`: fluxo segue com restricoes recomendadas
- `HOLD`: fluxo deve parar antes da geracao criativa

### 5.2 Strategy Agent

#### Objetivo

Gerar um `strategy_profile` minimo por conta, com base no estado atual da conta e sinais basicos de performance.

#### Entrada minima

- `account_id`
- `account_profile`
- metricas recentes
- objetivo da conta
- sinais basicos de performance
- `health_status`

#### Saida minima

- `strategy_profile`

#### Campos minimos de `strategy_profile`

- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`

#### Papel no fluxo

Orientar o `Creative Orchestrator` sem substituir `Script Agent`, `Voice Agent` ou `Video QC Agent`.

---

## 6. Fluxo do Bloco 2

Fluxo minimo permitido:

```text
Account Health Agent
-> Strategy Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC Agent
-> Safety Layer
```

### 6.1 Regra de parada

Se `Account Health Agent` retornar `HOLD`:

- o fluxo deve parar
- o `Creative Orchestrator` nao deve montar `creative_pack`
- o pipeline nao deve rodar
- nenhum `publish_record` deve ser gerado

### 6.2 Regra de continuidade

Se `Account Health Agent` retornar `SAFE` ou `CAUTION`:

- o fluxo pode seguir
- `Strategy Agent` deve receber o `health_status`
- o `Creative Orchestrator` deve consumir `strategy_profile`

---

## 7. Contratos Minimos do Bloco 2

### 7.1 Account Health Agent

Entrada minima:

- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

Saida minima:

```json
{
  "status": "CAUTION",
  "reasons": ["RECENT_VIEWS_DROP"],
  "recommended_constraints": {
    "reduce_hook_aggressiveness": true,
    "max_daily_posts": 1
  }
}
```

### 7.2 Strategy Agent

Entrada minima:

- `account_id`
- `account_goal`
- `recent_metrics_summary`
- `health_status`
- `recommended_constraints`

Saida minima:

```json
{
  "goal": "stabilize_growth",
  "content_mode": "conservative_dark",
  "hook_aggressiveness": "medium",
  "target_duration_range": "8-12s",
  "variation_policy": "low"
}
```

### 7.3 Integracao com o Creative Orchestrator

O `Creative Orchestrator` passa a consumir:

- `health_status`
- `recommended_constraints`
- `strategy_profile`

Mas continua sendo o unico componente autorizado a:

- montar o `creative_pack`
- chamar `Script Agent`
- chamar `Voice Agent`
- iniciar o fluxo criativo do slice cognitivo

---

## 8. Fallbacks Obrigatorios

### 8.1 Account Health Agent

Se nao houver historico suficiente:

- retornar `SAFE`
- marcar motivo: `ACCOUNT_HEALTH_COLD_START`
- usar `recommended_constraints` vazias ou minimas

O agente nao pode falhar silenciosamente.

### 8.2 Strategy Agent

Se nao houver dados suficientes para estrategia contextual:

- usar `default_strategy_profile`
- marcar motivo: `STRATEGY_COLD_START`

O agente nao pode retornar perfil vazio.

### 8.3 Creative Orchestrator

Se o `Account Health Agent` ou o `Strategy Agent` falhar sem fallback:

- o fluxo deve falhar explicitamente
- o motivo deve ser materializado

---

## 9. Persistencia Minima do Bloco 2

Neste bloco, a persistencia deve ser minima e auditavel.

Persistir:

- `account_health_decision`
- `strategy_profile`

Formato aceitavel neste slice:

- JSON/JSONL auditavel em diretorio da camada cognitiva

Regra:

- nao criar storage paralelo arbitrario
- nao reescrever historico bruto
- nao tornar o storage mais complexo do que o necessario para o bloco

---

## 10. Eventos Minimos do Bloco 2

Eventos minimos a introduzir:

- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/strategy_profile_generated`

Regra:

- o dominio continua sendo `CREATIVE/*`
- nao introduzir eventos `SAFETY/*`, `CONTENT/*` ou `RUNTIME/*` a partir do Bloco 2

---

## 11. Testes Obrigatorios

O Bloco 2 deve entrar com testes minimos para:

- `Account Health Agent`
- `Strategy Agent`
- integracao do `Creative Orchestrator` consumindo ambos
- smoke pequeno do fluxo:
  - `Account Health Agent`
  - `Strategy Agent`
  - `Creative Orchestrator`
  - `Script Agent`
  - `Voice Agent`
  - `Content Pipeline`
  - `Video QC Agent`

Tambem devem ser rerodados:

- testes do Bloco 1
- regresses relevantes da Fase 1

---

## 12. Criterio de Conclusao do Bloco 2

O Bloco 2 so pode ser considerado concluido se:

1. `Strategy Agent` gerar `strategy_profile` valido
2. `Account Health Agent` gerar `health_status` valido
3. `Creative Orchestrator` consumir ambos sem quebrar o fluxo do Bloco 1
4. `HOLD` impedir execucao criativa
5. `SAFE` e `CAUTION` permitirem continuidade controlada
6. testes do Bloco 2 passarem
7. smoke do Bloco 2 passar
8. nenhuma regressao da Fase 1 ou do Bloco 1 for detectada

---

## 13. Fora de Escopo

Nao fazem parte do Bloco 2:

- contexto de tendencia amplo
- aprendizado adaptativo real
- assignment experimental formal
- selecao visual estrategica avancada
- otimizacao multiagente

Esses temas pertencem aos blocos seguintes.

---

## 14. Conclusao

O Bloco 2 existe para provar a primeira decisao contextual por conta na camada cognitiva.

Ele nao amplia o sistema para contexto externo amplo nem para aprendizado pleno.

Ele apenas introduz, de forma controlada:

- protecao por saude de conta
- estrategia minima por conta
- alimentacao contextual do `Creative Orchestrator`

Com isso, a Fase 2 avanca de:

`execucao cognitiva minima`

para:

`decisao cognitiva contextual por conta`
