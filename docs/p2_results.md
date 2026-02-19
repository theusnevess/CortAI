# P2 Results

## P2-B1 sintetico (Windows/Docker Desktop)

Objetivo:
- Executar uma validacao sintetica do fluxo de observabilidade e SLO quando nao ha runner externo disponivel.

Nao objetivo:
- Este fluxo nao substitui P2-B1 estrutural (runner separado do SUT).

Execucao:

```bash
python scripts/run_p2b1_synthetic.py --metric-date 2026-02-09 --base-url http://localhost:8000 --timing-minutes 60
```

Artefatos esperados (`.tmp_p2/`):
- `p2_a_summary_direct.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `p2_a_summary_edge.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `report_after_synth.json`
- `status_after_synth.json`

Validações obrigatorias:
- Agregacao diaria executada duas vezes sem duplicar `metrics_slo_alert`.
- Monotonicidade de latencia no CSV sintetico (`C1 < C2 < C5`) por endpoint.
- `report_after_synth.json` com:
  - `timing.events > 0`
  - `slo_daily.has_requests == true`
  - `bad_duration == 0`
  - `publish_receipts.path_leaks_30d == 0`

Observacao:
- Resultado sintetico e util para validar pipeline e contratos.
- Decisao estrutural de capacidade segue dependente de medicao com runner externo.

