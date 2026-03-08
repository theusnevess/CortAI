from __future__ import annotations

from app.content.templates.models import ContentTemplate

DEFAULT_STRUCTURE = ["hook", "setup", "tension", "reveal", "cta"]


def default_templates(*, created_at: str) -> list[ContentTemplate]:
    return [
        ContentTemplate(
            template_id="tpl_hook_question_v1",
            template_type="HOOK_QUESTION",
            structure=list(DEFAULT_STRUCTURE),
            hook_pattern="voce percebeu o detalhe mais estranho sobre {theme}?",
            body_pattern="setup: {theme}. tension: o ponto ignorado. reveal: o detalhe muda tudo.",
            cta_pattern="comenta se voce quer a proxima parte sobre {theme}",
            tags=["question", "curiosity", "stable"],
            created_at=created_at,
        ),
        ContentTemplate(
            template_id="tpl_hook_curious_statement_v1",
            template_type="HOOK_CURIOUS_STATEMENT",
            structure=list(DEFAULT_STRUCTURE),
            hook_pattern="o que quase todo mundo entende errado sobre {theme}",
            body_pattern="setup: contexto rapido. tension: a leitura comum. reveal: a virada real.",
            cta_pattern="salva este video se voce quer rever esse caso depois",
            tags=["statement", "curiosity", "stable"],
            created_at=created_at,
        ),
        ContentTemplate(
            template_id="tpl_hook_reveal_v1",
            template_type="HOOK_REVEAL",
            structure=list(DEFAULT_STRUCTURE),
            hook_pattern="a revelacao sobre {theme} aparece no segundo detalhe",
            body_pattern="setup: fato inicial. tension: o detalhe cresce. reveal: a virada fecha a historia.",
            cta_pattern="segue para ver o proximo recorte sobre {theme}",
            tags=["reveal", "payoff", "stable"],
            created_at=created_at,
        ),
        ContentTemplate(
            template_id="tpl_hook_contrast_v1",
            template_type="HOOK_CONTRAST",
            structure=list(DEFAULT_STRUCTURE),
            hook_pattern="todo mundo fala isso sobre {theme}, mas o contraste real e outro",
            body_pattern="setup: versao comum. tension: a contradicao. reveal: o contraste decisivo.",
            cta_pattern="manda para quem acompanha {theme}",
            tags=["contrast", "debunk", "stable"],
            created_at=created_at,
        ),
        ContentTemplate(
            template_id="tpl_hook_countdown_v1",
            template_type="HOOK_COUNTDOWN",
            structure=list(DEFAULT_STRUCTURE),
            hook_pattern="3 pontos que explicam por que {theme} ainda prende tanta atencao",
            body_pattern="setup: ponto 1. tension: ponto 2. reveal: ponto 3 fecha a leitura.",
            cta_pattern="comenta qual ponto sobre {theme} te pegou mais",
            tags=["countdown", "listicle", "stable"],
            created_at=created_at,
        ),
    ]

