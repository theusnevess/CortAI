from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class HookRewriteResult:
    original: str
    rewritten: str
    transformed: bool
    rule: str | None = None
    provenance_preserved: bool = False


class HookRewriter:
    _PREFIXES: tuple[tuple[str, str], ...] = (
        ("A WITNESS SAW ", "witness_observed"),
        ("POLICE REOPENED ", "police_reopened"),
        ("A REPORT SAID ", "report_said"),
        ("A RECOVERED TAPE MENTIONED ", "recovered_tape"),
        ("FILES SHOW ", "files_show"),
        ("RECORDS INDICATE ", "records_indicate"),
        ("ARCHIVES SHOW ", "archives_show"),
        ("AN OFFICIAL MEMO FLAGGED ", "official_memo"),
    )

    def rewrite(self, hook_text: str) -> HookRewriteResult:
        original = self._normalize(hook_text)
        if not original:
            return HookRewriteResult(original=original, rewritten=original, transformed=False)

        for prefix, rule in self._PREFIXES:
            if not original.startswith(prefix):
                continue
            event = original[len(prefix) :].strip()
            rewritten = self._rewrite_event(raw_event=event, event=event, rule=rule)
            if rewritten and rewritten != original:
                return HookRewriteResult(
                    original=original,
                    rewritten=rewritten,
                    transformed=True,
                    rule=rule,
                    provenance_preserved=True,
                )
            break
        return HookRewriteResult(original=original, rewritten=original, transformed=False)

    def _rewrite_event(self, *, raw_event: str, event: str, rule: str) -> str:
        cleaned = self._cleanup_event(event, rule=rule)
        specific = self._specific_transform(cleaned, rule=rule)
        if specific:
            return specific
        prefix = self._rule_prefix(rule)
        if not prefix:
            return ""
        if rule == "police_reopened":
            return self._normalize(f"{prefix} {raw_event}")
        return self._normalize(f"{prefix} {cleaned}")

    def _cleanup_event(self, event: str, *, rule: str) -> str:
        cleaned = self._normalize(event)
        if rule == "police_reopened" and cleaned.endswith(" REOPENED"):
            cleaned = cleaned[: -len(" REOPENED")].strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,!?:;")
        return cleaned

    def _specific_transform(self, event: str, rule: str) -> str | None:
        provenance = self._provenance_suffix(rule)
        patterns: tuple[tuple[str, str], ...] = (
            (r"^(?P<subject>.+?) SEALED AFTER (?P<time>.+)$", "AFTER {time} THE {subject} WAS SEALED{provenance}"),
            (r"^(?P<subject>.+?) SEALED FROM THE INSIDE$", "THE {subject} WAS SEALED FROM THE INSIDE{provenance}"),
            (r"^(?P<subject>.+?) REOPENED ITSELF$", "THE {subject} REOPENED ITSELF{provenance}"),
            (r"^(?P<subject>.+?) WITH FUTURE DATE$", "THE {subject} CARRIED A FUTURE DATE{provenance}"),
            (r"^(?P<subject>.+?) CHANGED DATE$", "THE {subject} CHANGED DATE{provenance}"),
            (r"^(?P<subject>.+?) MISSING CORRIDOR$", "THE {subject} WAS MISSING A CORRIDOR{provenance}"),
            (r"^(?P<subject>.+?) CONTRADICTION$", "THE {subject} CONTAINED A CONTRADICTION{provenance}"),
            (r"^(?P<subject>.+?) TRANSCRIPT DISCREPANCY$", "THE {subject} SHOWED A DISCREPANCY{provenance}"),
            (r"^(?P<subject>.+?) CAMERA DESYNC$", "THE {subject} CAMERA FELL OUT OF SYNC{provenance}"),
            (r"^(?P<subject>.+?) BLACKOUT IN (?P<place>.+)$", "THE {subject} WENT DARK IN {place}{provenance}"),
            (r"^(?P<subject>.+?) WARNING$", "THE {subject} DISPLAYED A WARNING{provenance}"),
            (r"^(?P<subject>.+?) ERASED A MINUTE$", "THE {subject} ERASED A MINUTE{provenance}"),
        )
        for pattern, template in patterns:
            match = re.match(pattern, event, flags=re.IGNORECASE)
            if not match:
                continue
            data = {key: value.strip() for key, value in match.groupdict().items()}
            data["provenance"] = provenance
            return template.format(**data).upper()
        return None

    def _ensure_subject(self, event: str, suffix: str | None = None) -> str:
        normalized = self._normalize(event)
        if not normalized:
            return normalized
        if normalized.startswith(("THE ", "THIS ", "THAT ", "EVERY ", "AT ", "AFTER ")):
            base = normalized
        else:
            base = f"THE {normalized}"
        if suffix:
            if base.endswith(suffix):
                return base
            return f"{base} {suffix}".strip()
        return base

    def _can_passivize_reopened(self, event: str) -> bool:
        concrete_targets = (
            "TAPE",
            "RECORDER",
            "ROOM",
            "LOCKER",
            "LOG",
            "FILE",
            "EVIDENCE",
        )
        blocked_targets = ("STATEMENT", "TRANSCRIPT", "OVERRIDE", "WITNESS")
        if any(token in event for token in blocked_targets):
            return False
        return any(token in event for token in concrete_targets)

    def _rule_prefix(self, rule: str) -> str:
        prefixes = {
            "witness_observed": "A WITNESS SAW",
            "police_reopened": "POLICE REOPENED",
            "report_said": "A REPORT SAID",
            "recovered_tape": "A RECOVERED TAPE MENTIONED",
            "files_show": "FILES SHOW",
            "records_indicate": "RECORDS INDICATE",
            "archives_show": "ARCHIVES SHOW",
            "official_memo": "AN OFFICIAL MEMO FLAGGED",
        }
        return prefixes.get(rule, "")

    def _provenance_suffix(self, rule: str) -> str:
        suffixes = {
            "witness_observed": ", A WITNESS SAID",
            "police_reopened": ", POLICE RECORDS SHOW",
            "report_said": ", A REPORT SAID",
            "recovered_tape": ", ON TAPE",
            "files_show": ", FILES SHOW",
            "records_indicate": ", RECORDS SHOW",
            "archives_show": ", ARCHIVES SHOW",
            "official_memo": ", AN OFFICIAL MEMO SHOWS",
        }
        return suffixes.get(rule, "")

    def _normalize(self, text: str) -> str:
        cleaned = (
            text.replace("\u2014", " ")
            .replace("\u2013", " ")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2026", "...")
        )
        cleaned = cleaned.encode("ascii", "ignore").decode("ascii")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.upper()


def rewrite_hook(hook_text: str) -> str:
    return HookRewriter().rewrite(hook_text).rewritten
