from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx
from PIL import Image, ImageStat


class BackgroundGenerationError(RuntimeError):
    """Raised when remote background generation fails."""


@dataclass(frozen=True)
class AssetProfile:
    path: Path
    mean_luma: float
    contrast: float


@dataclass
class BackgroundGeneratorService:
    base_dir: Path = Path("OUT/content/backgrounds")
    local_assets_dir: Path = Path("assets/backgrounds")
    provider: str = os.getenv("CORTAI_BG_PROVIDER", "local_assets").lower()
    timeout_s: float = 120.0

    def generate(self, *, script_text: str, theme: str, render_job_id: str) -> str | None:
        local_asset = self.pick_local_asset(theme=theme, render_job_id=render_job_id, variant="hook")
        if local_asset is not None:
            return str(local_asset)

        prompt = self._build_prompt(script_text=script_text, theme=theme)
        target = self.base_dir / f"{render_job_id}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)

        if self.provider == "pollinations":
            return self._generate_pollinations(prompt=prompt, target=target)
        return None

    def pick_local_asset(self, *, theme: str, render_job_id: str, variant: str = "hook") -> Path | None:
        theme_dir = self.local_assets_dir / theme
        if not theme_dir.exists():
            theme_dir = self.local_assets_dir / "default"
            if not theme_dir.exists():
                return None

        candidates = sorted(
            path
            for path in theme_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        if not candidates:
            return None

        profiles = [self.describe_asset(path) for path in candidates]
        assigned = self._assign_variant_assets(profiles=profiles, render_job_id=render_job_id)
        return assigned.get(variant, profiles[0].path)

    def describe_asset(self, path: Path) -> AssetProfile:
        with Image.open(path) as image:
            grayscale = image.convert("L")
            grayscale.thumbnail((256, 256))
            stat = ImageStat.Stat(grayscale)
        return AssetProfile(
            path=path,
            mean_luma=float(stat.mean[0]),
            contrast=float(stat.stddev[0]),
        )

    def _assign_variant_assets(self, *, profiles: list[AssetProfile], render_job_id: str) -> dict[str, Path]:
        roles = ("hook", "setup", "payoff")
        assignments: dict[str, Path] = {}
        used: set[Path] = set()

        for role in roles:
            eligible = [profile for profile in profiles if profile.path not in used]
            viable_unused = self._viable_profiles(eligible, variant=role)
            viable_any = self._viable_profiles(profiles, variant=role)
            ranked = sorted(
                viable_unused or viable_any or eligible or profiles,
                key=lambda profile: self._variant_score(profile=profile, variant=role, render_job_id=render_job_id),
                reverse=True,
            )
            chosen = ranked[0]
            assignments[role] = chosen.path
            used.add(chosen.path)
        return assignments

    def _viable_profiles(self, profiles: list[AssetProfile], *, variant: str) -> list[AssetProfile]:
        if variant == "hook":
            return [profile for profile in profiles if profile.mean_luma >= 40]
        if variant == "payoff":
            return [profile for profile in profiles if profile.mean_luma >= 38]
        return [profile for profile in profiles if profile.mean_luma >= 24]

    def _variant_score(self, *, profile: AssetProfile, variant: str, render_job_id: str) -> float:
        mean = profile.mean_luma
        contrast = profile.contrast
        jitter = ((sum(ord(ch) for ch in f"{render_job_id}:{profile.path.name}:{variant}") % 17) - 8) * 0.01

        if variant == "hook":
            penalty = 0.0
            if mean < 45:
                penalty += 80
            return (contrast * 1.8) + (mean * 0.9) - penalty + jitter

        if variant == "setup":
            return (contrast * 1.0) - (abs(mean - 90) * 0.65) + jitter

        penalty = 0.0
        if mean < 38:
            penalty += 120
        elif mean < 52:
            penalty += 25
        return (contrast * 1.6) - (abs(mean - 74) * 0.55) - penalty + jitter

    def _generate_pollinations(self, *, prompt: str, target: Path) -> str | None:
        api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
        if not api_key:
            return None

        url = (
            "https://enter.pollinations.ai/api/generate/image/"
            f"{quote(prompt)}?model=flux&width=1024&height=1792"
        )
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            with httpx.Client(timeout=self.timeout_s, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                content_type = str(response.headers.get("content-type") or "").lower()
                if "image" not in content_type:
                    raise BackgroundGenerationError(f"POLLINATIONS_INVALID_CONTENT_TYPE:{content_type}")
                target.write_bytes(response.content)
                return str(target)
        except Exception as exc:  # noqa: BLE001
            raise BackgroundGenerationError(f"POLLINATIONS_GENERATION_FAILED: {exc}") from exc

    def _build_prompt(self, *, script_text: str, theme: str) -> str:
        text = " ".join(script_text.split())
        core = re.sub(r"[^a-zA-Z0-9 ,'\\-]", "", text)[:220]
        base = (
            "cinematic vertical background, realistic, dark atmosphere, moody lighting, "
            "high contrast, no text, no captions, no letters, no people facing camera"
        )
        if theme == "horror":
            return f"{base}, abandoned hotel corridor at night, unsettling realism, {core}"
        if theme == "conspiracy":
            return f"{base}, secret archive room, analog equipment, hidden files, {core}"
        return f"{base}, mysterious documentary scene, realistic environment, {core}"
