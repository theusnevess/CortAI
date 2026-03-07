from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.content.creative_pack.models import CreativePack, CreativePackGenerationResult
from app.content.creative_pack.repo import save_if_absent

ALLOWED_POLICY_STAGES = {"GROWTH", "MONETIZATION", "RECOVERY"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip()).strip("-")


def _build_pack_id(
    *,
    account_id: str,
    policy_stage: str,
    theme: str,
    variation_index: int,
    config_signature: str,
) -> str:
    material = f"{account_id}|{policy_stage}|{theme}|{variation_index}|{config_signature}".encode("utf-8")
    return f"cp_{sha256(material).hexdigest()[:16]}"


def _config_signature(policy_config: dict[str, Any], strategy_patch: dict[str, Any] | None) -> str:
    active_patch = strategy_patch if isinstance(strategy_patch, dict) and strategy_patch.get("active") is True else None
    patch_id = "" if active_patch is None else str(active_patch.get("patch_id") or "")
    policy_signature = json_dumps(policy_config)
    return sha256(f"{policy_signature}|{patch_id}".encode("utf-8")).hexdigest()[:12]


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass
class CreativePackGeneratorService:
    output_path: Path = Path("OUT/content/creative_packs/creative_packs.jsonl")

    def generate(
        self,
        *,
        theme: str,
        account_id: str,
        policy_stage: str,
        account_policy: dict[str, Any] | None = None,
        strategy_patch: dict[str, Any] | None = None,
        variation_count: int = 3,
        generated_at: str | None = None,
    ) -> CreativePackGenerationResult:
        if policy_stage not in ALLOWED_POLICY_STAGES:
            raise ValueError("CREATIVE_PACK_POLICY_STAGE_INVALID")
        normalized_theme = theme.strip()
        if not normalized_theme:
            raise ValueError("CREATIVE_PACK_THEME_INVALID")
        if variation_count < 1:
            raise ValueError("CREATIVE_PACK_VARIATION_COUNT_INVALID")

        timestamp = generated_at or _now_iso()
        policy_config = self._resolve_policy_config(account_policy=account_policy, strategy_patch=strategy_patch)
        signature = _config_signature(policy_config, strategy_patch)

        packs: list[CreativePack] = []
        actions: list[str] = []
        for variation_index in range(1, variation_count + 1):
            pack = self._build_pack(
                theme=normalized_theme,
                account_id=account_id.strip(),
                policy_stage=policy_stage,
                variation_index=variation_index,
                policy_config=policy_config,
                strategy_patch=strategy_patch if isinstance(strategy_patch, dict) and strategy_patch.get("active") is True else None,
                generated_at=timestamp,
                config_signature=signature,
            )
            action = save_if_absent(pack.to_dict(), path=self.output_path)
            packs.append(pack)
            actions.append(action)

        status = "NOOP" if actions and all(item == "NOOP" for item in actions) else "WRITTEN"
        return CreativePackGenerationResult(status=status, creative_packs=packs, actions=actions)

    def _resolve_policy_config(
        self,
        *,
        account_policy: dict[str, Any] | None,
        strategy_patch: dict[str, Any] | None,
    ) -> dict[str, Any]:
        config: dict[str, Any] = {}
        if isinstance(account_policy, dict):
            policy_config = account_policy.get("config", {})
            if isinstance(policy_config, dict):
                config.update(policy_config)
        if isinstance(strategy_patch, dict) and strategy_patch.get("active") is True:
            overrides = strategy_patch.get("overrides", {})
            if isinstance(overrides, dict):
                for key, value in overrides.items():
                    if isinstance(value, dict):
                        config.setdefault(key, {})
                        if isinstance(config[key], dict):
                            config[key] = {**config[key], **value}
        return config

    def _build_pack(
        self,
        *,
        theme: str,
        account_id: str,
        policy_stage: str,
        variation_index: int,
        policy_config: dict[str, Any],
        strategy_patch: dict[str, Any] | None,
        generated_at: str,
        config_signature: str,
    ) -> CreativePack:
        a1 = policy_config.get("a1_prefs_override", {}) if isinstance(policy_config.get("a1_prefs_override"), dict) else {}
        a4 = policy_config.get("a4_defaults_override", {}) if isinstance(policy_config.get("a4_defaults_override"), dict) else {}
        a5 = policy_config.get("a5_rewrite_defaults_override", {}) if isinstance(policy_config.get("a5_rewrite_defaults_override"), dict) else {}

        prefer_angles = a1.get("prefer_angles") if isinstance(a1.get("prefer_angles"), list) else []
        niches_boost = a1.get("niches_boost") if isinstance(a1.get("niches_boost"), list) else []
        angle = str(prefer_angles[variation_index % len(prefer_angles)]) if prefer_angles else [
            "case_breakdown",
            "unexpected_turn",
            "why_it_mattered",
        ][(variation_index - 1) % 3]

        hook_style = str(a4.get("hook_style") or "curiosity_gap")
        increase_tension = bool(a4.get("increase_tension") is True)
        force_number = bool(a4.get("force_number") is True)
        cta_style = str(a5.get("cta_style") or "comment_prompt")

        base_phrase = self._build_base_phrase(theme=theme, angle=angle, increase_tension=increase_tension)
        title = self._build_title(theme=theme, variation_index=variation_index, force_number=force_number, base_phrase=base_phrase)
        hooks = self._build_hooks(theme=theme, hook_style=hook_style, increase_tension=increase_tension)
        hashtags = self._build_hashtags(theme=theme, policy_stage=policy_stage, niches_boost=niches_boost)
        cta = self._build_cta(cta_style=cta_style, theme=theme)
        script_skeleton = self._build_script_skeleton(theme=theme, angle=angle, hook=hooks[0], cta=cta)

        return CreativePack(
            creative_pack_id=_build_pack_id(
                account_id=account_id,
                policy_stage=policy_stage,
                theme=theme,
                variation_index=variation_index,
                config_signature=config_signature,
            ),
            account_id=account_id,
            policy_stage=policy_stage,
            theme=theme,
            variation_index=variation_index,
            angle=angle,
            title=title,
            hook_candidates=hooks,
            script_skeleton=script_skeleton,
            hashtags=hashtags,
            cta=cta,
            strategy_patch_id=None if strategy_patch is None else str(strategy_patch.get("patch_id") or ""),
            generated_at=generated_at,
        )

    def _build_base_phrase(self, *, theme: str, angle: str, increase_tension: bool) -> str:
        if increase_tension:
            return f"o detalhe de {theme} que quase todo mundo ignora em {angle}"
        return f"como {theme} muda quando voce olha por {angle}"

    def _build_title(self, *, theme: str, variation_index: int, force_number: bool, base_phrase: str) -> str:
        if force_number:
            return f"{variation_index}. {base_phrase}"
        return f"{theme}: {base_phrase}"

    def _build_hooks(self, *, theme: str, hook_style: str, increase_tension: bool) -> list[str]:
        if hook_style == "story_arc":
            hooks = [
                f"parecia so mais um caso sobre {theme}, ate o ponto de virada",
                f"ninguem esperava que {theme} terminasse assim",
            ]
        elif hook_style == "listicle":
            hooks = [
                f"3 sinais de que {theme} nao e o que parece",
                f"2 pistas que mudam tudo em {theme}",
            ]
        else:
            hooks = [
                f"o que faltava entender sobre {theme}",
                f"por que {theme} continua intrigando tanta gente",
            ]
        if increase_tension:
            hooks.append(f"o momento mais desconfortavel de {theme}")
        return hooks

    def _build_hashtags(self, *, theme: str, policy_stage: str, niches_boost: list[Any]) -> list[str]:
        tags = [f"#{_slug(theme)}", f"#{policy_stage.lower()}"]
        for item in niches_boost[:3]:
            text = str(item).strip()
            if text:
                tags.append(f"#{_slug(text)}")
        return tags

    def _build_cta(self, *, cta_style: str, theme: str) -> str:
        if cta_style == "save_share":
            return f"salva este corte sobre {theme} e manda para quem acompanha esse caso"
        if cta_style == "follow_prompt":
            return f"segue para ver a proxima camada de {theme}"
        return f"comenta 'parte 2' se voce quer o proximo recorte sobre {theme}"

    def _build_script_skeleton(self, *, theme: str, angle: str, hook: str, cta: str) -> str:
        return "\n".join(
            [
                f"HOOK: {hook}",
                f"SETUP: contexto rapido sobre {theme}",
                f"ANGLE: mostrar {angle}",
                "PAYOFF: revelar o detalhe que muda a leitura",
                f"CTA: {cta}",
            ]
        )
