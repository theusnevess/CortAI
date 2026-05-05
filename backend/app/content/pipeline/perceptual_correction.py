from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageStat


@dataclass(frozen=True)
class PerceptualProfile:
    mean_luminance: float
    contrast: float
    shadow_floor: float
    histogram_spread: float


def analyze_frame(image: Image.Image) -> PerceptualProfile:
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    histogram = grayscale.histogram()
    total = max(1, int(sum(histogram)))
    cumulative = 0
    p05 = 0
    p95 = 255
    low_target = total * 0.05
    high_target = total * 0.95
    for index, count in enumerate(histogram):
        cumulative += count
        if cumulative >= low_target and p05 == 0:
            p05 = index
        if cumulative >= high_target:
            p95 = index
            break
    return PerceptualProfile(
        mean_luminance=float(stat.mean[0]),
        contrast=float(stat.stddev[0]),
        shadow_floor=float(p05),
        histogram_spread=float(max(0, p95 - p05)),
    )


def correct_frame(image: Image.Image) -> Image.Image:
    corrected = image.convert("RGB")
    original_profile = analyze_frame(corrected)
    profile = original_profile

    if profile.mean_luminance < 72:
        brightness_factor = _brightness_factor(profile.mean_luminance)
        corrected = ImageEnhance.Brightness(corrected).enhance(brightness_factor)
        profile = analyze_frame(corrected)

    if profile.mean_luminance < 84:
        gamma = _gamma_for_luminance(profile.mean_luminance)
        corrected = _gamma_correct(corrected, gamma=gamma)
        profile = analyze_frame(corrected)

    if profile.contrast < 52:
        contrast_factor = min(1.18, 1.0 + ((52 - profile.contrast) / 52.0) * 0.18)
        corrected = ImageEnhance.Contrast(corrected).enhance(contrast_factor)
        profile = analyze_frame(corrected)

    if profile.shadow_floor < 26:
        corrected = _lift_shadows(
            corrected,
            lift=min(34.0, 12.0 + ((26 - profile.shadow_floor) * 0.85) + max(0.0, 34.0 - profile.mean_luminance) * 0.55),
        )
        profile = analyze_frame(corrected)

    if original_profile.mean_luminance < 30 and profile.mean_luminance < 46:
        corrected = _normalize_dark_frame(corrected, target_mean=48.0)

    return corrected


def balance_sequence(images: list[Image.Image]) -> list[Image.Image]:
    if not images:
        return []
    corrected = [correct_frame(image) for image in images]
    profiles = [analyze_frame(image) for image in corrected]
    target = min(92.0, max(76.0, sum(profile.mean_luminance for profile in profiles) / len(profiles)))
    balanced: list[Image.Image] = []
    for image, profile in zip(corrected, profiles, strict=True):
        delta = max(-8.0, min(10.0, target - profile.mean_luminance))
        if abs(delta) < 1.0:
            balanced.append(image)
            continue
        factor = max(0.95, min(1.12, 1.0 + (delta / 255.0) * 0.9))
        balanced.append(ImageEnhance.Brightness(image).enhance(factor))
    return balanced


def _gamma_correct(image: Image.Image, *, gamma: float) -> Image.Image:
    safe_gamma = max(0.01, gamma)
    lut = [max(0, min(255, int(((index / 255.0) ** safe_gamma) * 255.0))) for index in range(256)]
    return image.point(lut * 3)


def _lift_shadows(image: Image.Image, *, lift: float) -> Image.Image:
    shadow_limit = 96.0
    lut = []
    for index in range(256):
        if index >= shadow_limit:
            lut.append(index)
            continue
        ratio = 1.0 - (index / shadow_limit)
        boosted = int(index + (lift * ratio * 0.8))
        lut.append(max(0, min(255, boosted)))
    return image.point(lut * 3)


def _brightness_factor(mean_luminance: float) -> float:
    if mean_luminance < 28:
        return 1.95
    if mean_luminance < 40:
        return 1.70
    if mean_luminance < 56:
        return 1.42
    return min(1.26, 1.0 + ((72 - mean_luminance) / 72.0) * 0.22)


def _gamma_for_luminance(mean_luminance: float) -> float:
    if mean_luminance < 28:
        return 0.58
    if mean_luminance < 40:
        return 0.68
    if mean_luminance < 56:
        return 0.78
    return max(0.86, min(0.94, 1.0 - ((84 - mean_luminance) / 260.0)))


def _normalize_dark_frame(image: Image.Image, *, target_mean: float) -> Image.Image:
    profile = analyze_frame(image)
    if profile.mean_luminance >= target_mean:
        return image
    factor = min(1.55, max(1.08, target_mean / max(1.0, profile.mean_luminance)))
    normalized = ImageEnhance.Brightness(image).enhance(factor)
    normalized = _gamma_correct(normalized, gamma=0.86)
    return normalized
