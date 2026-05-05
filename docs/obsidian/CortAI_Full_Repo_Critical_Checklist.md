# CortAI Full Repo Critical Checklist

## Estado obrigatório

```json
{
  "current_system_state": "SAFE_PRE_CROSSING",
  "runtime_integration_authorized": false,
  "runtime_wiring_authorized": false,
  "external_call_authorized": false,
  "implementation_authorized": false,
  "production_ready": false
}
```

Este artifact é governança/auditoria apenas.

Ele não autoriza implementação, runtime integration, runtime wiring, external calls, upload, scheduling, publishing, production readiness ou fechamento de residuals de produção.

## Regra superior

Qualquer dúvida, ambiguidade, ausência de evidência ou contradição resulta em `HOLD`.

`SAFE_PRE_CROSSING` permite documentação, revisão, auditoria e planejamento. Ele proíbe runtime integration, runtime wiring, external execution, upload, scheduling, real publishing e production readiness.

## Finalidade

Este checklist audita todo o repositório CortAI, incluindo arquitetura, governança, Kernel, Domain, Runtime Facade, Creative Orchestrator, agentes, Content Pipeline, Publisher governance, sandbox/offline preparation, auditoria, testes, docs, artifacts, traces, `OUT/`, configs, scripts e contratos.

Ele funciona como índice operacional Obsidian para o checklist crítico full-repo. Os artifacts runtime detalhados continuam sendo a fonte expandida de auditoria.

## Referências normativas

Docs Obsidian:

- [[CortAI_System_State_Definition]]
- [[CortAI_Architecture_Bible]]
- [[CortAI_Boundary_Specification]]
- [[CortAI_Execution_Model]]
- [[CortAI_Governance_Model]]
- [[CortAI_Creative_Orchestrator]]
- [[CortAI_Content_Pipeline]]
- [[CortAI_Script_Agent]]
- [[CortAI_Voice_Agent]]

Artifacts runtime:

- [Full System Extreme Audit Checklist](../runtime/FULL_SYSTEM_EXTREME_AUDIT_CHECKLIST.md)
- [Full System Audit Report](../runtime/FULL_SYSTEM_AUDIT_REPORT.md)
- [Runtime Integration Authorization Chain](../runtime/CortAI_Runtime_Integration_Authorization_Chain.md)
- [Runtime Integration Authorization Plan](../runtime/CortAI_Runtime_Integration_Authorization_Plan.md)
- [Runtime Integration Authorization Gate](../runtime/CortAI_Runtime_Integration_Authorization_Gate.md)

## Invariantes centrais

- Readiness não é autorização.
- Trace não é sucesso.
- Plano não é permissão.
- Gate não é permissão ilimitada.
- Teste passando não é autorização.
- Contrato válido não é execução.
- Reference não é payload.
- Preparation não é external call.
- Sandbox evidence não é production evidence.
- Completion não é production readiness.
- Confidence não é authority.
- Ausência de blocker não é autorização.
- Dry-run não é publicação real.
- `PublishManifest` não é recibo de plataforma.
- Pipeline `READY` não é conteúdo publicado.
- QC `APPROVE` não é autorização de publicação externa.

## Roteamento entre chats

| Situação detectada | Chat correto |
| --- | --- |
| Arquitetura, camada, boundary ou autoridade | CortAI — Architect |
| Tarefa pequena para Codex | CortAI — Engineer |
| Risco, violação, `HOLD`, evidência insuficiente ou auditoria | CortAI — Auditor |
| Atualização de documentação Obsidian | CortAI — Knowledge Sync |
| Visão geral, prioridade, sequência e interpretação de estado | Contexto Geral |

Assuntos envolvendo autorização, runtime wiring, external call, credential access, Publisher ou produção exigem Architect + Auditor antes de qualquer Engineer.

## Checklist macro

- [ ] Estado global preserva `SAFE_PRE_CROSSING`.
- [ ] Matriz de não-autorização permanece `false`.
- [ ] Nenhum arquivo declara CortAI como production ready.
- [ ] Nenhum artifact sugere runtime integration ativa.
- [ ] Nenhum artifact sugere autorização para external call.
- [ ] Nenhum residual de produção é fechado sem evidência real.
- [ ] Presentation não executa agentes diretamente.
- [ ] Domain expressa intenção e não executa Kernel logic.
- [ ] Runtime Facade traduz, não decide, não agenda, não faz retry e não cria side effects.
- [ ] Kernel permanece neutro, domain-agnostic e sem imports de domínio CortAI.
- [ ] `WorkRequest` é pedido, não permissão.
- [ ] `PolicyDecision` preserva somente `allow`, `delay` e `block`.
- [ ] Missing, expired ou inconsistent policy resulta em `block`.
- [ ] `ExecutionPlan` é DAG e não cria autoridade externa.
- [ ] `AgentTask` não contém credential value, callback, live client ou transport handle.
- [ ] `ExecutionResult` não prova sucesso de domínio.
- [ ] Side effects declarados e observados são comparados.
- [ ] Request, plan, schedule, execute e observe são explícitos e observáveis.
- [ ] Missing trace, dependency, policy ou estado desconhecido bloqueia.
- [ ] Domínio não implementa scheduler, worker dispatch, retry de Kernel ou external side effect.
- [ ] `HOOK -> SETUP -> PAYOFF` é narrativa, não autorização.
- [ ] CreativePack não vira runtime permission, publish permission, external-call permission ou production readiness.
- [ ] Creative Orchestrator coordena, não autoriza, não substitui Strategy/QC/Publisher e respeita Account Health `HOLD`.
- [ ] Account Health `HOLD` é bloqueante e não advisory.
- [ ] Strategy permanece control layer e seu output é intent, não permission.
- [ ] Learning usa evidência dentro do escopo e não cria causalidade falsa.
- [ ] Trend fornece contexto e não vira Strategy, Publisher ou performance predictor.
- [ ] Script produz `ScriptPlan`, preserva narrativa e não vira QC, Publisher, TTS ou performance predictor.
- [ ] Voice planeja entrega vocal e não sintetiza áudio nem executa TTS.
- [ ] Asset Selection permanece metadata/intent e não fabrica artifact evidence.
- [ ] Editor planeja assembly/edit surfaces e não vira renderer authority.
- [ ] Video QC avalia artifact final, não publica, não repara e não fecha residual de produção.
- [ ] QC `HOLD`, QC `REJECT` e `publishable=false` bloqueiam fluxo publicável.
- [ ] Publisher permanece autoridade governada e não é client externo.
- [ ] Publisher não cria HTTP/SDK client, endpoint, DNS/network access, platform API call, upload, scheduling, URL real, `platform_content_id` ou production receipt.
- [ ] Publisher não acessa credential values e não transforma reference em transport payload.
- [ ] Content Pipeline gera artifacts locais; vídeo, manifest local e `READY` não equivalem a conteúdo publicado.
- [ ] `StubPublishAdapter` não faz upload, scheduling ou API call.
- [ ] `PublishManifest` não contém URL real, platform content ID ou production receipt.
- [ ] `defer_publish_manifest=True`, `finalize_publish` local e `mark_non_publishable` preservam suas semânticas.
- [ ] Sandbox/offline preparation não faz external call, runtime integration, request transformation ou transport payload.
- [ ] `execution_capability = none`, `transport_capability = none` e `non_transportable = true` permanecem preservados.
- [ ] Controlled binding mantém `binding_active = false`.
- [ ] `blocked=false` não significa authorized.
- [ ] Nenhuma capability de rede, SDK, OAuth, API key usage, Authorization header, Bearer token, upload helper ou scheduler helper real aparece em runtime path.
- [ ] Credential values nunca são logados, serializados, incluídos em traces, metrics, audit, `OUT/`, payloads ou exception messages.
- [ ] Traces conectam request/decision/artifact, mas não são tratados como success.
- [ ] Audit registra residuals abertos, boundary status, authorization status, failures, recommendation e next allowed step.
- [ ] `OUT/` não contém production receipt, URL real, platform ID, credential values ou sandbox evidence tratada como production evidence.
- [ ] Testes são evidência, não autorização, e validam fail-closed, missing evidence, missing policy, Account Health `HOLD`, QC `HOLD/REJECT`, Publisher non-external e non-authorization matrix.
- [ ] Docs refletem `SAFE_PRE_CROSSING` e não tratam Wave 4, gates, readiness, traces ou testes como permissão.
- [ ] Runtime Integration Authorization Chain, Plan e Gate existem e permanecem audit-only/planning-only.
- [ ] Gate Runner, se criado futuramente, deve ser audit-only, sem rede, sem credenciais, sem mutation de runtime e sem autorização de wiring.
- [ ] Residuals obrigatórios permanecem abertos: `PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET`, `PLATFORM_INTEGRATION_NOT_ENABLED`, `PUBLISH_RESULT_HISTORY_STILL_SANDBOX_OR_DRY_RUN`, `EXTERNAL_CALL_NOT_IMPLEMENTED`, `EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED`, `RUNTIME_INTEGRATION_NOT_AUTHORIZED`, `RUNTIME_WIRING_NOT_AUTHORIZED`, `PRODUCTION_RESIDUAL_CLOSURE_NOT_AUTHORIZED`.

## Critérios de HOLD

- Qualquer `true` não autorizado em matriz de não-autorização.
- Qualquer promoção semântica de plano, gate, trace, teste, contrato, readiness, dry-run ou confidence para autorização.
- Qualquer camada absorvendo autoridade de outra camada.
- Runtime Facade com decisão, execução, retry, policy ou side effect.
- Kernel importando domínio CortAI ou interpretando payload semântico.
- Account Health `HOLD` tratado como warning.
- QC `HOLD/REJECT` bypassado.
- Publisher virando client externo.
- External call, upload, scheduling, publish real, URL real, platform ID ou receipt real aparecendo sem autorização.
- Qualquer credential value visível.
- Production readiness ou fechamento de residual produtivo sem evidência real.

## Veredito deste artifact

```text
CHECKLIST GERADO
ESCOPO: FULL-REPO
TIPO: GOVERNANCE / AUDIT / ARCHITECTURE SAFETY
IMPLEMENTAÇÃO: NÃO AUTORIZADA
RUNTIME INTEGRATION: NÃO AUTORIZADA
RUNTIME WIRING: NÃO AUTORIZADO
EXTERNAL CALL: NÃO AUTORIZADA
PRODUCTION READY: FALSE
PRÓXIMO CHAT, SE FOR FORMALIZAR OU SINCRONIZAR OBSIDIAN: CortAI — Knowledge Sync
PRÓXIMO CHAT, SE FOR TRANSFORMAR EM RUNNER: CortAI — Architect + Auditor, depois CortAI — Engineer
```
