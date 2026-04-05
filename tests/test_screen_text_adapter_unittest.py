from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.screen_text.service import ScreenTextAdapterService


class ScreenTextAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ScreenTextAdapterService()

    def test_adapt_builds_complete_canonical_blocks(self) -> None:
        blocks = self.service.adapt(
            "In the dead of night, the old Maplewood Motels lights flickered on by themselves. "
            "Who was sneaking in to flip those switches? "
            "Then one light showed a face staring back at me from a dusty mirror."
        )

        self.assertEqual(blocks.hook_text, "THE OLD MOTEL LIGHTS TURNED ON BY THEMSELVES")
        self.assertEqual(blocks.setup_text, "WHO WAS FLIPPING THE SWITCHES?")
        self.assertEqual(blocks.payoff_text, "A FACE STARED BACK FROM THE MIRROR")

    def test_narration_text_matches_canonical_blocks(self) -> None:
        blocks = self.service.adapt(
            "In the dead of night, the old Maplewood Motels lights flickered on by themselves. "
            "Who was sneaking in to flip those switches? "
            "Then one light showed a face staring back at me from a dusty mirror."
        )

        self.assertEqual(
            blocks.narration_text(),
            "THE OLD MOTEL LIGHTS TURNED ON BY THEMSELVES.\n\nWHO WAS FLIPPING THE SWITCHES?\n\nA FACE STARED BACK FROM THE MIRROR.",
        )

    def test_two_sentence_script_does_not_duplicate_payoff(self) -> None:
        blocks = self.service.adapt(
            "In the old Lincoln Building, everyone ignored the faint ticking noise until one night it led them to a room with no exit... "
            "and a tiny gear wheel buried in the wall."
        )

        self.assertNotEqual(blocks.setup_text, blocks.payoff_text)
        self.assertIn("LINCOLN BUILDING", blocks.hook_text)
        self.assertIn("ROOM WITH NO EXIT", blocks.setup_text)
        self.assertIn("GEAR WHEEL", blocks.payoff_text)

    def test_timed_cues_expose_canonical_roles_and_ranges(self) -> None:
        blocks = self.service.adapt(
            "The old motel lights turned on by themselves. "
            "Who was flipping the switches? "
            "A face stared back from the mirror."
        )

        cues = blocks.timed_cues([(0.0, 2.4), (2.4, 5.0), (5.0, 8.0)])

        self.assertEqual([cue.style_role for cue in cues], ["hook", "setup", "payoff"])
        self.assertEqual(cues[0].text, blocks.hook_text)
        self.assertEqual(cues[1].text, blocks.setup_text)
        self.assertEqual(cues[2].text, blocks.payoff_text)
        self.assertEqual((cues[2].start, cues[2].end), (5.0, 8.0))

    def test_adapt_aggressively_compresses_screen_copy_for_short_form(self) -> None:
        blocks = self.service.adapt(
            "In the old motel, someone wrote: \"don't look back,\" on the mirror. "
            "Who left that warning: the night guard, or someone else? "
            "Then the lights failed, and the door wouldn't open."
        )

        self.assertEqual(blocks.hook_text, "SOMEONE WROTE ON THE MIRROR")
        self.assertEqual(blocks.setup_text, "WHO LEFT THE WARNING?")
        self.assertEqual(blocks.payoff_text, "THE DOOR WOULDN'T OPEN")

    def test_adapt_preserves_strong_tail_details_for_horror_copy(self) -> None:
        blocks = self.service.adapt(
            "Inside the shuttered hospital wing, a red phone started ringing again. "
            "No one could explain why it still had power. "
            "Then a voice whispered the patient number of an empty room."
        )

        self.assertEqual(blocks.hook_text, "THE RED PHONE STARTED RINGING AGAIN")
        self.assertEqual(blocks.setup_text, "NO ONE COULD EXPLAIN WHY IT HAD POWER")
        self.assertEqual(blocks.payoff_text, "A VOICE WHISPERED AN EMPTY ROOM NUMBER")

    def test_adapt_preserves_station_and_departure_closure(self) -> None:
        blocks = self.service.adapt(
            "At the abandoned train platform, one timetable kept changing after midnight. "
            "No employee admitted touching it. "
            "Then the final departure appeared for a station that never existed."
        )

        self.assertEqual(blocks.hook_text, "ONE TIMETABLE KEPT CHANGING AFTER MIDNIGHT")
        self.assertEqual(blocks.setup_text, "NO EMPLOYEE ADMITTED TOUCHING IT")
        self.assertEqual(blocks.payoff_text, "FINAL DEPARTURE TO A STATION THAT NEVER EXISTED")

    def test_adapt_structured_blocks_preserves_semantics_with_light_compression(self) -> None:
        blocks = self.service.adapt_structured_blocks(
            hook="Police reopened the locked evidence room.",
            setup="They were just dusting for old clues.",
            payoff="The recorder picked up whispers from sealed evidence.",
        )

        self.assertEqual(blocks.hook_text, "POLICE REOPENED THE LOCKED EVIDENCE ROOM")
        self.assertEqual(blocks.setup_text, "THEY WERE JUST DUSTING FOR OLD CLUES")
        self.assertEqual(blocks.payoff_text, "THE RECORDER PICKED UP WHISPERS FROM SEALED EVIDENCE")


if __name__ == "__main__":
    unittest.main()
