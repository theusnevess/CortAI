# PR - Governance Formalization (P1 Closed + P2 Start)

## Title
`docs(observability): encerra P1 e formaliza inicio de P2 (throughput/infra path)`

## O que
- Registra resultado oficial da Matriz P1 (Linux nativo) em `docs/observability.md`.
- Formaliza entrada do ciclo P2 em `docs/roadmap_v2.md` com Definition of Done.

## Decisao
- `safe_envelope_v2.0 != C2` com SLO atual.
- Winner P1: `API_WORKERS=2`, `DB_POOL_SIZE=10`.
- Endpoint limitante principal: `/api/v1/metrics/overview`.
- Proximo passo canonico: P2 (throughput/infra path), sem mexer em logica de endpoint.

## Escopo
- Docs-only.
- Sem mudanca funcional de API/DB/core.

## Risco
- Nenhum risco de runtime (documentacao apenas).

## Evidencia
- Artefato da matriz: `.tmp_matrix_p1/matrix_p1_summary.csv`.
- Secao adicionada em `docs/observability.md` com resultados e decisao.
- Secao adicionada em `docs/roadmap_v2.md` com checklist e criterios de encerramento de P2.
