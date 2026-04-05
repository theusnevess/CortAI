from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService, ScriptGenerationError
from app.creative.contracts.creative_pack import StrategyProfile


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP_{self.status_code}")

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.requests: list[dict] = []

    def __enter__(self):  # noqa: ANN204
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def post(self, url: str, json: dict, **kwargs) -> _FakeResponse:  # noqa: A002, ANN003
        self.requests.append({"url": url, "json": json, "kwargs": kwargs})
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class ScriptGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def _request(self) -> ScriptGenerationRequest:
        return ScriptGenerationRequest(
            context=ScriptGenerationContext(
                account_id="acc_1",
                niche="horror",
                topic="sealed mirror tunnel",
            )
        )

    def test_normalize_script_removes_unbalanced_quotes(self) -> None:
        service = LocalScriptGeneratorService()
        raw = 'Then I found a key under a floorboard with a note: "Welcome Home.'
        normalized = service._normalize_script(raw)
        self.assertNotIn('"', normalized)
        self.assertTrue(normalized.endswith("."))

    def test_parses_structured_json_response(self) -> None:
        service = LocalScriptGeneratorService()
        payload = service._parse_structured_response(
            '{"narrative_mode":"official_warning","hook":"Signal logged after shutdown.","setup":"The warning named the guard.","payoff":"The keycard still scanned at midnight."}',
            request=self._request(),
        )
        self.assertEqual(payload.narrative_mode, "official_warning")
        self.assertEqual(payload.hook, "Signal logged after shutdown.")

    def test_generate_structured_uses_groq_when_api_key_present(self) -> None:
        os.environ["GROQ_API_KEY"] = "test-key"
        fake_payload = {
            "choices": [
                {
                    "message": {
                        "content": '{"narrative_mode":"witness_report","hook":"A witness saw the sealed corridor breathe.","setup":"The second report named the wrong floor.","payoff":"The last photo showed a door behind the wall."}'
                    }
                }
            ]
        }
        service = LocalScriptGeneratorService(http_client_factory=lambda **_: _FakeClient([_FakeResponse(fake_payload)]))

        result = service.generate_structured(self._request())

        self.assertEqual(result.provider_used, "groq")
        self.assertEqual(result.script_plan.generation_mode, "groq_structured")
        self.assertFalse(result.fallback.used)

    def test_generate_structured_falls_back_to_ollama_when_groq_fails(self) -> None:
        os.environ["GROQ_API_KEY"] = "test-key"
        fake_client = _FakeClient(
            [
                RuntimeError("groq unavailable"),
                RuntimeError("groq unavailable"),
                _FakeResponse(
                    {
                        "response": '{"narrative_mode":"procedural_anomaly","hook":"Police reopened the locked archive room.","setup":"The recorder started after the power cut.","payoff":"A dead detectives badge number answered first."}'
                    }
                ),
            ]
        )
        responses = [
            RuntimeError("groq unavailable"),
            RuntimeError("groq unavailable"),
            _FakeResponse(
                {
                    "response": '{"narrative_mode":"procedural_anomaly","hook":"Police reopened the locked archive room.","setup":"The recorder started after the power cut.","payoff":"A dead detectives badge number answered first."}'
                }
            ),
        ]
        del responses
        service = LocalScriptGeneratorService(http_client_factory=lambda **_: fake_client)

        result = service.generate_structured(self._request())

        self.assertEqual(result.provider_used, "ollama")
        self.assertEqual(result.script_plan.generation_mode, "ollama_structured")
        self.assertFalse(result.fallback.used)
        ollama_request = next(item for item in fake_client.requests if item["url"].endswith("/api/generate"))
        self.assertIn("seed", ollama_request["json"]["options"])
        self.assertIsInstance(ollama_request["json"]["options"]["seed"], int)

    def test_generate_structured_uses_contextual_fallback_when_all_providers_fail(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            service = LocalScriptGeneratorService(http_client_factory=lambda **_: _FakeClient([RuntimeError("ollama down")]))
            result = service.generate_structured(
                ScriptGenerationRequest(
                    context=ScriptGenerationContext(
                        account_id="acc_1",
                        niche="true_crime",
                        topic="evidence room recorder",
                    )
                )
            )

        self.assertEqual(result.provider_used, "fallback")
        self.assertTrue(result.fallback.used)
        self.assertEqual(result.script_plan.generation_mode, "fallback_contextual")
        self.assertIn("EVIDENCE ROOM", result.script_plan.hook.upper())
        self.assertTrue(
            any(term in result.script_plan.payoff.upper() for term in ("TAPE", "ROOM", "TIMESTAMP", "VOICE", "FLOORPLAN"))
        )

    def test_prompt_includes_real_cognitive_context(self) -> None:
        request = self._request()
        service = LocalScriptGeneratorService()
        prompt = service._build_prompt(request)
        self.assertIn("Assigned narrative mode", prompt)
        self.assertIn("Niche: horror", prompt)
        self.assertIn("Topic: sealed mirror tunnel", prompt)
        self.assertIn("The payoff must reveal one concrete observable fact", prompt)

    def test_finalize_payload_repairs_weak_payoff_into_concrete_reveal(self) -> None:
        service = LocalScriptGeneratorService()
        request = ScriptGenerationRequest(
            context=ScriptGenerationContext(
                account_id="acc_2",
                niche="horror",
                topic="sealed corridor mirror warning",
            )
        )

        payload = service._parse_structured_response(
            '{"narrative_mode":"official_warning","hook":"A red phone rang inside the shuttered wing.","setup":"The hallway lights died before anyone answered.","payoff":"The caller whispered the number of an empty room."}',
            request=request,
        )

        finalized = service._finalize_payload(payload, context=request.context)

        self.assertNotIn("EMPTY ROOM", finalized.payoff.upper())
        self.assertIn("ROOM 312", finalized.payoff.upper())
        service._validate_payload(finalized)

    def test_finalize_payload_repairs_presence_payoff_into_specific_reveal(self) -> None:
        service = LocalScriptGeneratorService()
        request = ScriptGenerationRequest(
            context=ScriptGenerationContext(
                account_id="acc_3",
                niche="horror",
                topic="sealed corridor mirror warning",
            )
        )

        payload = service._parse_structured_response(
            '{"narrative_mode":"witness_report","hook":"A witness saw the sealed corridor breathe.","setup":"Their story turned stranger every time the lights failed.","payoff":"The final detail put someone breathing behind the door."}',
            request=request,
        )

        finalized = service._finalize_payload(payload, context=request.context)

        self.assertNotIn("SOMEONE BREATHING", finalized.payoff.upper())
        self.assertTrue(
            any(term in finalized.payoff.upper() for term in ("ROOM 312", "DOOR 16"))
        )
        self.assertTrue(
            any(term in finalized.payoff.upper() for term in ("FLOORPLAN", "SEALED FLOOR"))
        )
        service._validate_payload(finalized)

    def test_contextual_fallback_horror_uses_specific_payoff_floor(self) -> None:
        service = LocalScriptGeneratorService()
        payload = service._fallback_payload(
            context=ScriptGenerationContext(
                account_id="acc_4",
                niche="horror",
                topic="sealed corridor mirror warning",
            ),
            mode="witness_report",
        )

        self.assertIn("DOOR 16", payload.payoff.upper())
        self.assertIn("FLOORPLAN", payload.payoff.upper())

    def test_contextual_fallback_avoids_blocked_named_location_removed_structure(self) -> None:
        service = LocalScriptGeneratorService()
        payload = service._fallback_payload(
            context=ScriptGenerationContext(
                account_id="acc_5",
                niche="horror",
                topic="sealed corridor mirror warning",
                strategy_profile=StrategyProfile(
                    novelty_hints={
                        "blocked_payoff_structures": ["named_location_removed"],
                    }
                ),
            ),
            mode="witness_report",
        )

        self.assertNotIn("REMOVED FROM THE FLOORPLAN", payload.payoff.upper())
        self.assertNotIn("MISSING FROM THE MAP", payload.payoff.upper())
        self.assertTrue(any(term in payload.payoff.upper() for term in ("WARNING", "PANEL", "MAP", "STAIRWELL")))

    def test_validate_payload_rejects_generic_abstract_payoff_without_anchor(self) -> None:
        service = LocalScriptGeneratorService()

        with self.assertRaisesRegex(ScriptGenerationError, "SCRIPT_PAYOFF"):
            service._validate_payload(
                service._normalize_payload(
                    service._payload_from_object(
                        {
                            "narrative_mode": "witness_report",
                            "hook": "The camera cut out in the lower tunnel.",
                            "setup": "The warning repeated after the lights returned.",
                            "payoff": "A presence waited in the dark.",
                        }
                    )
                )
            )


if __name__ == "__main__":
    unittest.main()
