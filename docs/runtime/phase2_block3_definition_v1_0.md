CortAI - Fase 2

Bloco 3 - Trend Context and Visual Context

Documento: `docs/runtime/phase2_block3_definition_v1_0.md`
Versao: 1.0
Status: Aprovado para Implementacao (escopo congelado)

---

## 1. Objetivo do Bloco 3

O Bloco 3 introduz contexto externo de tendencia e contexto visual na camada cognitiva do CortAI.

Ate o Bloco 2, o sistema ja possui:

- decisao de saude da conta
- decisao estrategica
- geracao de script
- escolha de voz
- pipeline de geracao
- verificacao de qualidade

O Bloco 3 adiciona duas capacidades fundamentais:

1. `Trend Analysis Agent`
2. `Asset Selection Agent`

Esses agentes permitem que o conteudo passe a considerar:

- padroes de conteudo bem-sucedidos no nicho
- estilo visual coerente com a estrategia
- variacao visual consistente

---

## 2. Escopo Estrito do Bloco 3

O Bloco 3 implementa apenas:

- `Trend Analysis Agent` (manual-curated MVP)
- `Asset Selection Agent`

Nada alem disso.

---

## 3. Escopo Proibido

Nao fazem parte do Bloco 3:

- `Learning / Optimization Agent`
- `Experiment Agent` formal
- RAG completo
- scraping automatizado de plataformas
- automacao de analise massiva de conteudo
- alteracao estrutural da Fase 1
- alteracao estrutural dos Blocos 1 ou 2

O Bloco 3 nao introduz aprendizado adaptativo.

Ele apenas adiciona contexto externo estruturado.

---

## 4. Arquitetura do Bloco 3

Apos o Bloco 3, o fluxo cognitivo passa a ser:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline (Fase 1)
-> Video QC Agent
```

---

## 5. Trend Analysis Agent

### Objetivo

Fornecer ao sistema um perfil estruturado de tendencias por nicho.

Esse perfil e utilizado para influenciar:

- estilo de hook
- estrutura narrativa
- pacing
- estilo visual

### Implementacao MVP

O `Trend Analysis Agent` nao coleta dados automaticamente.

Ele apenas le perfis de tendencia curados manualmente.

### Fonte de dados

Arquivos em:

- `backend/data/trends/`

Exemplo:

- `backend/data/trends/horror.json`
- `backend/data/trends/history.json`
- `backend/data/trends/true_crime.json`

### Estrutura minima do Trend Profile

Exemplo:

```json
{
  "niche": "horror",
  "dominant_hooks": [
    "question",
    "shock_statement",
    "story_opening"
  ],
  "avg_duration": "35-60",
  "pacing": "fast_first_3s",
  "visual_style": "dark_backgrounds",
  "text_style": "large_caption_focus"
}
```

### Saida do agente

- `trend_profile`

Esse objeto sera incluido no contexto consumido pelo `Strategy Agent` e `Asset Selection Agent`.

### Fallback obrigatorio

Se o arquivo de tendencia nao existir:

- `trend_profile = DEFAULT`

Nunca interromper o fluxo por ausencia de tendencia.

---

## 6. Asset Selection Agent

### Objetivo

Selecionar assets visuais coerentes com a estrategia e o nicho.

### Responsabilidades

Escolher:

- background do hook
- background do setup
- background do payoff
- estilo visual dominante

### Entradas

O agente recebe:

- `strategy_profile`
- `trend_profile`
- `niche`
- `topic`

### Saida

- `asset_selection`

Exemplo:

- `hook_background`
- `setup_background`
- `payoff_background`
- `visual_style`
- `motion_profile`

### Integracao

O resultado do `Asset Selection Agent` e incluido no:

- `creative_pack`

---

## 7. Integracao com Creative Orchestrator

O `Creative Orchestrator` passa a chamar:

```text
Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
```

E incluir no `creative_pack`:

- `trend_profile`
- `strategy_profile`
- `asset_selection`

---

## 8. Persistencia

O Bloco 3 utiliza apenas persistencia simples.

Arquivos:

- `backend/data/trends/*.json`

Nenhuma base vetorial e introduzida nesta etapa.

---

## 9. Eventos Cognitivos

Eventos minimos introduzidos:

- `TREND_PROFILE_LOADED`
- `TREND_PROFILE_FALLBACK`
- `ASSET_SELECTION_GENERATED`
- `ASSET_SELECTION_FALLBACK`

Esses eventos devem ser emitidos pelo `Creative Orchestrator`.

---

## 10. Testes Obrigatorios

Devem ser criados testes para:

- `Trend Analysis Agent`
- `Asset Selection Agent`
- smoke do Bloco 3

Arquivos esperados:

- `tests/test_trend_analysis_agent_phase2_unittest.py`
- `tests/test_asset_selection_agent_phase2_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`

---

## 11. Smoke do Bloco 3

Fluxo minimo esperado:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC
```

Resultado esperado:

- `trend_profile_loaded = true`
- `asset_selection_generated = true`
- `pipeline_status = READY`
- `video_qc_status = APPROVE`

---

## 12. Criterio de Conclusao do Bloco 3

O Bloco 3 sera considerado concluido quando:

- `Trend Analysis Agent` funcionar
- `Asset Selection Agent` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir `trend_profile` e `asset_selection`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1 ou 2

---

## 13. Resultado Esperado do Bloco 3

Apos a conclusao do Bloco 3, o CortAI passa a gerar conteudo considerando:

- saude da conta
- estrategia da conta
- tendencias do nicho
- coerencia visual do conteudo

Esse e o primeiro ponto em que o sistema passa a operar com contexto criativo externo estruturado.

---

## 14. Estado da Fase 2 apos Bloco 3

### Bloco 1

- `Creative Orchestrator`
- `Script Agent`
- `Voice Agent`
- `Video QC`

### Bloco 2

- `Strategy Agent`
- `Account Health Agent`

### Bloco 3

- `Trend Analysis Agent`
- `Asset Selection Agent`
