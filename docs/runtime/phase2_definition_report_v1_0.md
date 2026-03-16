CortAI - Relatorio de Definicao da Fase 2

Creative Intelligence Layer

Versao: 1.1
Status: Aprovado para Implementacao
Documento: `docs/runtime/phase2_definition_report_v1_0.md`

---

## 1. Objetivo do Documento

Este relatorio define a arquitetura, os componentes, os contratos, os criterios de conclusao e as regras de integracao da Fase 2 do CortAI.

A Fase 2 introduz a camada cognitiva do sistema, responsavel por decisoes criativas, estrategicas e adaptativas na geracao de conteudo.

O documento consolida as revisoes tecnicas realizadas e estabelece um escopo congelado para implementacao, garantindo alinhamento com a arquitetura, o runtime e o pipeline operacional da Fase 1.

---

## 2. Contexto: Transicao entre Fases

### 2.1 Fase 1 - Infraestrutura Operacional

A Fase 1 foi dedicada a construcao da infraestrutura operacional do CortAI, incluindo:

- runtime distribuido
- scheduler
- planner
- safety layer
- content pipeline
- geracao de video automatizada
- publish manifest
- publish records
- metrics collector
- camada de analise
- sistema de auditoria e consistencia

O objetivo da Fase 1 foi provar que o sistema e capaz de gerar videos de forma automatizada, consistente e auditavel.

Essa fase foi concluida com sucesso, incluindo execucao de batch de validacao com geracao de multiplos videos e verificacao completa do pipeline.

### 2.2 Fase 2 - Camada Cognitiva

A Fase 2 introduz a Creative Intelligence Layer, responsavel por:

- aplicar contexto estrategico
- entender tendencias
- adaptar conteudo por conta
- avaliar qualidade antes da publicacao
- aprender com metricas
- melhorar decisoes criativas ao longo do tempo

Em termos conceituais:

| Fase | Papel |
| --- | --- |
| Fase 1 | Provar que o sistema funciona |
| Fase 2 | Provar que o sistema pensa e aprende |

---

## 3. Principios Arquiteturais da Fase 2

A Fase 2 segue os seguintes principios:

### Separacao de responsabilidades

A camada cognitiva nao substitui o runtime nem o pipeline da Fase 1.

Ela prepara decisoes criativas e estrategicas, enquanto a infraestrutura existente executa a producao.

### Orquestracao centralizada

Os agentes nao se chamam diretamente.
A coordenacao e feita por um servico especifico:

`Creative Orchestrator Service`

### Contexto persistente

Todos os agentes utilizam contexto armazenado e auditavel, incluindo:

- tendencias
- estrategias de conta
- resultados de experimentos
- historico de decisoes

### Aprendizado incremental

O sistema evolui a partir de metricas reais.

A Fase 2 introduz mecanismos de aprendizado baseado em dados, mas nao depende de modelos treinados internamente.

### Compatibilidade com a Fase 1

Nenhum componente da Fase 2 pode violar contratos da Fase 1.

Em especial:

- nao alterar contratos de runtime
- nao alterar contratos de safety
- nao alterar contratos canonicos de `publish_record`
- nao alterar contratos canonicos de `metrics`
- nao permitir que agentes contornem o `Creative Orchestrator`

---

## 4. Creative Orchestrator Service

### 4.1 Papel

O Creative Orchestrator Service e o componente responsavel por coordenar a execucao dos agentes da camada cognitiva.

Ele atua como ponte entre:

- camada cognitiva
- pipeline operacional da Fase 1

### 4.2 Responsabilidades

O servico e responsavel por:

- carregar contexto estrategico
- consultar perfis de tendencia
- executar agentes criativos
- consolidar decisoes
- montar o `creative_pack`
- entregar o `creative_pack` ao pipeline de renderizacao

### 4.3 Integracao com o pipeline existente

Apos a geracao do `creative_pack`, o fluxo segue normalmente:

```text
Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video Renderer
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
```

### 4.4 Entrada canonica do Orchestrator

O `Creative Orchestrator Service` deve receber uma entrada canonica contendo, no minimo:

- `account_id`
- `niche`
- `topic`
- `publish_slot`
- `creative_pack_id` quando ja existir
- `experiment_assignment` quando aplicavel
- `account_context_ref`
- `trend_context_ref`

### 4.5 Saida canonica do Orchestrator

A saida do `Creative Orchestrator Service` deve ser um `creative_pack` imutavel para a execucao corrente, contendo:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `strategy_profile`
- `trend_profile`
- `script_plan`
- `voice_plan`
- `asset_plan`
- `experiment_assignment`
- `generated_at`
- `orchestrator_version`

O `creative_pack` e o contrato de integracao entre a Fase 2 e o pipeline da Fase 1.

### 4.6 Regras de falha do Orchestrator

Se um agente falhar, o `Creative Orchestrator` deve:

- aplicar fallback, quando definido
- registrar decisao e motivo
- falhar de forma explicita se o fallback nao existir

O `Creative Orchestrator` nao pode:

- produzir `creative_pack` parcial silenciosamente
- esconder falhas de agente
- pular agentes obrigatorios sem registrar motivo

---

## 5. Contrato do Creative Pack

### 5.1 Objetivo

O `creative_pack` e a unidade canonica de decisao criativa da Fase 2.

### 5.2 Estrutura minima

```json
{
  "creative_pack_id": "cp_xxx",
  "account_id": "acc_xxx",
  "niche": "dark_history",
  "topic": "abandoned station mystery",
  "strategy_profile": {
    "pacing": "fast",
    "hook_intensity": "high",
    "target_duration_s": 10
  },
  "trend_profile": {
    "dominant_hooks": ["question hook"],
    "visual_style": "dark cinematic backgrounds"
  },
  "script_plan": {
    "hook": "THE LAST TRAIN NEVER STOPPED HERE",
    "setup": "SO WHY DID THE SPEAKERS ANNOUNCE IT?",
    "payoff": "THE STATION CLOSED THIRTY YEARS AGO"
  },
  "voice_plan": {
    "provider": "premium_tts",
    "voice_id": "voice_x",
    "style": "calm_dark"
  },
  "asset_plan": {
    "hook_asset": "assets/backgrounds/horror/hook_01.jpg",
    "setup_asset": "assets/backgrounds/horror/setup_01.jpg",
    "payoff_asset": "assets/backgrounds/horror/payoff_01.jpg",
    "motion_profile": "subtle_push_in"
  },
  "experiment_assignment": {
    "experiment_id": "exp_hook_style_v1",
    "variant_id": "variant_b"
  },
  "generated_at": "2026-03-16T00:00:00Z",
  "orchestrator_version": "v1"
}
```

### 5.3 Regras

- o `creative_pack` deve ser deterministicamente reconstruivel a partir das entradas e refs persistidas
- o `creative_pack` nao pode ser reescrito pelo renderer
- o pipeline da Fase 1 consome o `creative_pack`, nao o reinterpreta estrategicamente

---

## 6. Agentes da Fase 2

A Fase 2 introduz um conjunto de agentes responsaveis por decisoes criativas e estrategicas.

### 6.1 Trend Analysis Agent

#### Objetivo

Identificar padroes relevantes de conteudo dentro de um nicho.

#### Implementacao inicial

O agente utilizara curadoria manual (MVP).

Fontes utilizadas:

- TikTok Creative Center
- observacao direta de conteudo bem-sucedido
- analise manual de tendencias

#### Saida

Arquivos estruturados por nicho:

`backend/data/trends/{niche}.json`

#### Fallback

Se nao houver contexto de tendencia para um nicho:

- usar perfil generico do nicho-pai
- registrar `trend_profile_fallback_used=true`
- nunca retornar vazio silenciosamente

### 6.2 Strategy Agent

#### Objetivo

Definir a estrategia de conteudo para cada conta.

#### Entradas

- perfil da conta
- historico de metricas
- objetivos da conta
- tendencias do nicho
- recomendacoes de aprendizado

#### Saida

`account_strategy_profile`

Exemplos de parametros:

- pacing recomendado
- estilo narrativo
- intensidade do hook
- duracao ideal
- variacao de conteudo

#### Fallback

Se a conta nao tiver historico suficiente:

- usar `default_strategy_profile` por nicho
- marcar a estrategia como `cold_start=true`

### 6.3 Script Agent

#### Objetivo

Gerar roteiros adaptados ao contexto.

#### Estrutura narrativa padrao

O agente gera roteiros seguindo a estrutura:

- Hook
- Setup
- Payoff

#### Entradas

- topico
- nicho
- estrategia da conta
- perfil de tendencias
- variacao experimental quando aplicavel

#### Papel

Substituir a geracao generica de roteiros por geracao orientada por retencao e contexto.

#### Regras

- cada bloco deve ser semanticamente fechado
- hook deve ser curto e de alto impacto
- setup deve sustentar a curiosidade
- payoff deve fechar a promessa narrativa

#### Fallback

Se a geracao contextual falhar:

- usar prompt simplificado orientado por nicho
- registrar `script_generation_fallback_used=true`
- falhar explicitamente se nem o fallback produzir `hook/setup/payoff`

### 6.4 Voice Agent

#### Objetivo

Selecionar voz e estilo de narracao.

#### Requisito da Fase 2

Suporte a TTS premium.

#### Estrategia

- Primary: TTS premium, ex.: ElevenLabs
- Fallback: Piper local

#### Parametros controlados

- voz
- velocidade
- intensidade emocional
- tom narrativo

#### Regras

- a escolha de voz deve ser persistida no `voice_plan`
- o fallback para Piper deve ser explicito e auditavel
- o agente nao pode trocar provider silenciosamente

### 6.5 Asset Selection Agent

#### Objetivo

Selecionar assets visuais adequados ao conteudo.

#### Entradas

- script
- nicho
- tendencias
- estrategia da conta

#### Saida

Selecao de:

- background do hook
- background do setup
- background do payoff
- estilo visual
- parametros de motion

#### Regras

- hook usa asset forte e legivel
- setup usa asset contextual
- payoff usa asset mais dramatico ou ameacador
- assets devem respeitar luminancia minima operacional

#### Fallback

Se nao houver assets especializados:

- usar biblioteca local por nicho
- reusar asset elegivel mais forte antes de usar asset inadequado

### 6.6 Video QC Agent

#### Objetivo

Avaliar a qualidade do video antes da publicacao.

#### Verificacoes

- integridade do arquivo
- presenca de audio
- resolucao correta
- duracao valida
- legibilidade das legendas
- coerencia narrativa
- presenca de hook forte
- ausencia de falhas visuais

#### Resultado

- `APPROVE`
- `REJECT`

Se rejeitado, o video nao segue para publicacao.

#### Regras objetivas minimas

O `Video QC Agent` deve rejeitar se houver qualquer um dos seguintes:

- arquivo de video ausente ou corrompido
- resolucao diferente de `1080x1920`
- audio ausente
- legenda fora da safe area
- overflow de legenda
- texto semantica ou visualmente quebrado
- duracao abaixo do minimo operacional definido
- payoff visual ilegivel

#### Integracao com Safety

- `Video QC Agent` rejeita por qualidade de producao
- `Safety Layer` bloqueia por risco e politica

Se `Video QC Agent` retornar `REJECT`:

- nao segue para `Safety Layer`
- nao gera publicacao
- nao gera `publish_record`
- deve emitir evento proprio de rejeicao

### 6.7 Account Health Agent

#### Objetivo

Monitorar sinais de risco relacionados a saude da conta.

#### Exemplos de sinais analisados

- queda brusca de visualizacoes
- repeticao excessiva de formato
- frequencia de postagem elevada
- videos consecutivos com desempenho anormal

#### Saida

- `SAFE`
- `CAUTION`
- `HOLD`

Esse agente atua como camada de protecao de distribuicao.

#### Regras

- `SAFE`: execucao normal
- `CAUTION`: execucao permitida com sinalizacao
- `HOLD`: impedir novos videos para a conta ate revisao ou ate janela liberada

### 6.8 Learning and Optimization Agent

#### Objetivo

Extrair aprendizado a partir das metricas geradas.

#### Entradas

- `publish_records`
- metricas de video
- resultados de experimentos
- relatorios de analise

#### Saida

Recomendacoes como:

- estilos de hook mais eficazes
- duracao ideal
- assets mais performaticos
- ajustes de estrategia

#### Regras

- a camada de aprendizado e read-only sobre historico bruto
- recomenda mudancas; nao reescreve eventos historicos

### 6.9 Experiment Capability

A experimentacao sera inicialmente uma capability integrada, nao um agente independente.

#### Implementacao inicial

Integrada aos agentes:

- Strategy Agent
- Script Agent

#### Funcao

Permitir geracao de variacoes como:

- multiplos hooks
- variacoes de estilo visual
- variacoes de narracao

#### Base tecnica

Utiliza o Experiment Framework (D31) ja existente.

#### Escopo congelado da capability

Na Fase 2, a experimentacao pode variar apenas:

- hook
- estrutura narrativa curta
- voz
- visual style leve

Nao pode variar nesta fase:

- contratos do runtime
- regras de safety
- formato canonico de `publish_record`
- formato canonico de `metrics`

---

## 7. Fluxo Cognitivo

Fluxo da camada cognitiva:

```text
Account Health Agent
-> Trend Analysis Agent
-> Strategy Agent
-> Experiment Capability
-> Script Agent
-> Asset Selection Agent
-> Voice Agent
-> Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
-> Metrics Collector
-> Learning Agent
```

### 7.1 Ordem obrigatoria e opcional

Obrigatorios:

- Creative Orchestrator
- Script Agent
- Voice Agent
- Video QC Agent

Condicionais:

- Trend Analysis Agent
- Strategy Agent
- Account Health Agent
- Learning Agent
- Experiment Capability
- Asset Selection Agent

Se um agente condicional nao puder rodar, o fallback deve ser aplicado e auditado.

### 7.2 Regra de falha parcial

Se um agente obrigatorio falhar sem fallback:

- o fluxo deve falhar
- o motivo deve ser materializado
- nenhum publish deve seguir adiante

Se um agente condicional falhar com fallback valido:

- o fluxo pode seguir
- a decisao deve ser persistida

---

## 8. Armazenamento de Contexto

A Fase 2 introduz armazenamento estruturado de contexto.

### 8.1 Estrutura recomendada

`backend/data/context/`

Subpastas:

- `trends/`
- `strategy/`
- `learning/`
- `qc_history/`

### 8.2 Estrategia de persistencia

- PostgreSQL como fonte principal
- arquivos JSON/JSONL como backup auditavel

### 8.3 Fonte canonica por dominio

| Dominio | Fonte canonica | Backup auditavel |
| --- | --- | --- |
| trend profiles | PostgreSQL | JSON |
| strategy profiles | PostgreSQL | JSON |
| learning recommendations | PostgreSQL | JSONL |
| qc decisions | PostgreSQL | JSONL |
| experiment assignments | PostgreSQL | JSONL |
| orchestrator outputs | PostgreSQL | JSON |

### 8.4 Regra de escrita

- agentes escrevem apenas no dominio que controlam
- o `Creative Orchestrator` consolida refs, nao duplica historico bruto
- arquivos JSON/JSONL servem como evidencias e backup, nao como fonte primaria em producao

---

## 9. Eventos e Observabilidade da Fase 2

Devem existir eventos proprios da camada cognitiva, separados dos eventos da Fase 1.

Eventos minimos:

- `CREATIVE/orchestrator_started`
- `CREATIVE/orchestrator_completed`
- `CREATIVE/orchestrator_failed`
- `CREATIVE/script_generated`
- `CREATIVE/voice_selected`
- `CREATIVE/assets_selected`
- `CREATIVE/video_qc_approved`
- `CREATIVE/video_qc_rejected`
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/learning_recommendations_generated`

Regra:

- cada agente emite apenas eventos do seu dominio
- a camada cognitiva nao emite eventos `CONTENT/*` nem `SAFETY/*`

---

## 10. Roadmap de Implementacao

A implementacao sera dividida em quatro blocos.

### Bloco 1 - Qualidade minima inteligente

- Creative Orchestrator Service minimo
- Video QC Agent
- Script Agent
- Voice Agent

### Bloco 2 - Estrategia por conta

- Strategy Agent
- Account Health Agent

### Bloco 3 - Contexto e visual

- Asset Selection Agent
- Trend Analysis Agent manual-curated

### Bloco 4 - Aprendizado e experimentacao

- Learning Agent
- formalizacao da Experiment Capability

---

## 11. Criterios de Conclusao da Fase 2

A Fase 2 sera considerada concluida quando o sistema for capaz de:

1. gerar conteudo baseado em estrategia de conta
2. utilizar contexto de tendencias na geracao de roteiros
3. operar com TTS premium integrado
4. bloquear videos ruins via Video QC Agent
5. proteger contas via Account Health Agent
6. gerar recomendacoes baseadas em metricas reais
7. produzir conteudo variado e nao repetitivo
8. executar o fluxo cognitivo completo via Creative Orchestrator

---

## 12. Criterios Tecnicos de Aceite

A Fase 2 so pode ser considerada concluida se, alem dos criterios funcionais, tambem atender aos criterios tecnicos abaixo.

### 12.1 Testes minimos

Devem existir testes unitarios e de integracao para:

- Creative Orchestrator
- Script Agent
- Voice Agent
- Video QC Agent
- Strategy Agent
- Account Health Agent
- Asset Selection Agent
- Learning Agent
- experiment assignment

### 12.2 Smoke obrigatorio

Deve existir pelo menos um smoke completo cobrindo:

`Creative Orchestrator -> Content Pipeline -> Video QC -> Safety -> Runtime -> Metrics -> Learning`

### 12.3 Evidencias obrigatorias

Para declarar Fase 2 concluida, devem ser materializadas evidencias em diretorio dedicado contendo:

- relatorio de testes
- smoke report
- eventos da camada cognitiva
- amostras de `creative_pack`
- decisoes do `Video QC Agent`
- recomendacoes do `Learning Agent`

### 12.4 Regressao proibida

A implementacao da Fase 2 nao pode quebrar:

- baseline validada da Fase 1
- gate final pre-D23
- batch local validado

---

## 13. Limitacoes da Fase 2

Nao fazem parte desta fase:

- geracao completa de video por IA
- avatares
- animacoes complexas
- edicao cinematografica avancada
- automacao de analise massiva de redes sociais
- otimizacao financeira agressiva

Esses temas pertencem a fases futuras.

---

## 14. Conclusao

A Fase 2 estabelece a camada de inteligencia do CortAI.

Com sua implementacao, o sistema evolui de um pipeline automatizado de geracao de conteudo para um sistema cognitivo capaz de tomar decisoes criativas, adaptar estrategias e aprender com metricas reais.

Esta especificacao define um escopo realista, modular e compativel com a infraestrutura ja construida na Fase 1.

Com a presente revisao, o documento passa a incluir os elementos necessarios para implementacao segura:

- contratos explicitos
- regras de fallback
- persistencia canonica por dominio
- integracao clara com safety e runtime
- criterios objetivos de qualidade
- criterios tecnicos de aceite

---

## Status Final

Fase 2 - Especificacao Tecnica Congelada para Implementacao
