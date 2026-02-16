# Politica de Versionamento (CortAI)

Este documento define a politica minima de versionamento semantico da plataforma.

## Regra geral

- Formato: `MAJOR.MINOR.PATCH`
- Exemplo atual: `1.6.0`

## MAJOR (X.0.0)

Incrementar MAJOR quando houver quebra de contrato publico:

- Mudanca de shape de resposta da API sem compatibilidade.
- Remocao de campos existentes.
- Mudanca de semantica de uma versao de CES ja publicada.

## MINOR (0.X.0)

Incrementar MINOR quando houver expansao backward-compatible:

- Nova versao de CES (`CES_vN`) sem alterar versoes anteriores.
- Novo endpoint.
- Novos campos opcionais em respostas existentes.
- Novo alerta de observabilidade sem quebra de contrato.

## PATCH (0.0.X)

Incrementar PATCH para correcao sem mudanca de contrato:

- Bugfix de implementacao.
- Ajuste interno de calculo que nao altera contrato publico.
- Correcao de documentacao.

## Contrato de imutabilidade do CES

- `CES_v1` e imutavel.
- `CES_v2` e imutavel.
- Qualquer mudanca de formula/componente/peso gera nova versao (`CES_vN`).

