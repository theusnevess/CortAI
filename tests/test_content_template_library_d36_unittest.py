from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.creative_pack.service import CreativePackGeneratorService
from app.content.templates.repo import list_templates, save_template_if_absent
from app.content.templates.service import ContentTemplateService


class ContentTemplateLibraryD36Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.templates_path = self.out / "content" / "templates" / "templates.jsonl"
        self.creative_packs_path = self.out / "content" / "creative_packs" / "creative_packs.jsonl"
        self.service = ContentTemplateService(output_path=self.templates_path)
        self.creative_service = CreativePackGeneratorService(output_path=self.creative_packs_path)

    def _read_jsonl(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        rows: list[dict] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def test_template_pode_ser_salvo(self) -> None:
        actions = self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")

        self.assertTrue(actions)
        self.assertTrue(all(action == "WRITTEN" for action in actions))
        self.assertTrue(self.templates_path.exists())

    def test_template_pode_ser_carregado(self) -> None:
        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")

        template = self.service.get_template("tpl_hook_question_v1")

        self.assertIsNotNone(template)
        self.assertEqual(template["template_type"], "HOOK_QUESTION")

    def test_selecao_por_tipo_funciona(self) -> None:
        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")

        selected = self.service.select_templates_by_type("HOOK_REVEAL")

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["template_id"], "tpl_hook_reveal_v1")

    def test_variacoes_sao_deterministicas(self) -> None:
        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")

        first = self.service.generate_template_variations("tpl_hook_countdown_v1", count=3)
        second = self.service.generate_template_variations("tpl_hook_countdown_v1", count=3)

        self.assertEqual(first, second)
        self.assertEqual([item["variation_index"] for item in first], [1, 2, 3])

    def test_templates_nao_alteram_creative_pack_existente(self) -> None:
        baseline = self.creative_service.generate(
            theme="true crime",
            account_id="acc_001",
            policy_stage="GROWTH",
            variation_count=1,
            generated_at="2026-03-07T11:00:00Z",
        )
        before = baseline.creative_packs[0].to_dict()

        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")

        rerun = self.creative_service.generate(
            theme="true crime",
            account_id="acc_001",
            policy_stage="GROWTH",
            variation_count=1,
            generated_at="2026-03-07T11:00:00Z",
        )
        after = rerun.creative_packs[0].to_dict()

        self.assertEqual(before, after)
        self.assertEqual(rerun.status, "NOOP")

    def test_persistencia_em_jsonl_correta(self) -> None:
        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")
        rows = self._read_jsonl(self.templates_path)

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["template_id"], "tpl_hook_question_v1")
        self.assertEqual(rows[-1]["template_id"], "tpl_hook_countdown_v1")

    def test_duplicidade_vira_noop_e_conflito_eh_explicito(self) -> None:
        self.service.bootstrap_defaults(created_at="2026-03-07T10:00:00Z")
        template = self.service.get_template("tpl_hook_question_v1")
        assert template is not None

        action = save_template_if_absent(template, path=self.templates_path)
        self.assertEqual(action, "NOOP")

        conflicting = dict(template)
        conflicting["body_pattern"] = "corpo diferente"
        with self.assertRaisesRegex(ValueError, "CONTENT_TEMPLATE_CONFLICT"):
            save_template_if_absent(conflicting, path=self.templates_path)

        self.assertEqual(len(list_templates(path=self.templates_path)), 5)


if __name__ == "__main__":
    unittest.main()

