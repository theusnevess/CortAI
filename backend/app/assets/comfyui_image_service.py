from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import httpx


class ComfyUIImageError(RuntimeError):
    """Raised when local ComfyUI generation or regeneration fails."""


SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED = False
SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED = False
SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED = False


def _ensure_comfyui_runtime_authorized() -> None:
    if not SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED:
        raise ComfyUIImageError("CORTAI_RUNTIME_WIRING_BLOCKED_SAFE_PRE_CROSSING")
    if not SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED:
        raise ComfyUIImageError("CORTAI_REQUEST_TRANSFORMATION_BLOCKED_SAFE_PRE_CROSSING")
    if not SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED:
        raise ComfyUIImageError("CORTAI_TRANSPORT_PAYLOAD_BLOCKED_SAFE_PRE_CROSSING")


@dataclass(frozen=True)
class ComfyUIImageResult:
    image_path: str
    metadata_path: str
    source_type: str
    model: str
    operation: str


@dataclass
class ComfyUIImageService:
    base_dir: Path = Path("OUT/content/comfyui_assets")
    base_url: str = os.getenv("CORTAI_COMFYUI_BASE_URL", "http://127.0.0.1:8188")
    checkpoint_name: str = os.getenv("CORTAI_COMFYUI_CHECKPOINT_NAME", "sd_xl_base_1.0.safetensors")
    negative_prompt: str = os.getenv(
        "CORTAI_COMFYUI_NEGATIVE_PROMPT",
        "blurry, low quality, watermark, text, logo, deformed, extra limbs",
    )
    sampler_name: str = os.getenv("CORTAI_COMFYUI_SAMPLER", "euler")
    scheduler: str = os.getenv("CORTAI_COMFYUI_SCHEDULER", "normal")
    steps: int = int(os.getenv("CORTAI_COMFYUI_STEPS", "20"))
    cfg: float = float(os.getenv("CORTAI_COMFYUI_CFG", "7.0"))
    width: int = int(os.getenv("CORTAI_COMFYUI_WIDTH", "832"))
    height: int = int(os.getenv("CORTAI_COMFYUI_HEIGHT", "1472"))
    timeout_s: float = 180.0
    poll_interval_s: float = 1.0

    def available(self) -> bool:
        if not (
            SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED
            and SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED
        ):
            return False
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url.rstrip('/')}/system_stats")
                response.raise_for_status()
            return True
        except Exception:
            return False

    def generate_image(
        self,
        *,
        prompt: str,
        render_job_id: str,
        segment_name: str,
        seed: str = "",
    ) -> ComfyUIImageResult:
        _ensure_comfyui_runtime_authorized()
        prompt_id = self._queue_prompt(
            workflow=self._txt2img_workflow(
                prompt=prompt,
                seed=self._seed_int(seed=seed),
                filename_prefix=f"{render_job_id}_{segment_name}_generate",
            )
        )
        image_info = self._wait_for_image(prompt_id=prompt_id)
        image_bytes = self._download_image(image_info=image_info)
        return self._persist_response(
            image_bytes=image_bytes,
            render_job_id=render_job_id,
            segment_name=segment_name,
            operation="generate",
            model=self.checkpoint_name,
            prompt=prompt,
        )

    def edit_image(
        self,
        *,
        prompt: str,
        input_image_path: str,
        render_job_id: str,
        segment_name: str,
    ) -> ComfyUIImageResult:
        _ensure_comfyui_runtime_authorized()
        image_path = Path(input_image_path)
        if not image_path.exists():
            raise ComfyUIImageError("COMFYUI_EDIT_INPUT_MISSING")
        regeneration_prompt = f"{prompt}, preserve scene continuity, strengthen case evidence, same composition bias"
        prompt_id = self._queue_prompt(
            workflow=self._txt2img_workflow(
                prompt=regeneration_prompt,
                seed=self._seed_int(seed=f"{render_job_id}:{segment_name}:edit"),
                filename_prefix=f"{render_job_id}_{segment_name}_edit",
            )
        )
        image_info = self._wait_for_image(prompt_id=prompt_id)
        image_bytes = self._download_image(image_info=image_info)
        return self._persist_response(
            image_bytes=image_bytes,
            render_job_id=render_job_id,
            segment_name=segment_name,
            operation="edit",
            model=self.checkpoint_name,
            prompt=regeneration_prompt,
            input_image_path=str(image_path),
        )

    def _txt2img_workflow(self, *, prompt: str, seed: int, filename_prefix: str) -> dict[str, Any]:
        _ensure_comfyui_runtime_authorized()
        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": self.checkpoint_name},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": self.width, "height": self.height, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": self.negative_prompt, "clip": ["4", 1]},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": self.steps,
                    "cfg": self.cfg,
                    "sampler_name": self.sampler_name,
                    "scheduler": self.scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]},
            },
        }

    def _queue_prompt(self, *, workflow: dict[str, Any]) -> str:
        _ensure_comfyui_runtime_authorized()
        payload = {
            "prompt": workflow,
            "client_id": str(uuid.uuid4()),
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(f"{self.base_url.rstrip('/')}/prompt", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ComfyUIImageError(f"COMFYUI_QUEUE_FAILED:{exc}") from exc
        prompt_id = str(data.get("prompt_id") or "").strip()
        if not prompt_id:
            raise ComfyUIImageError("COMFYUI_PROMPT_ID_MISSING")
        return prompt_id

    def _wait_for_image(self, *, prompt_id: str) -> dict[str, Any]:
        _ensure_comfyui_runtime_authorized()
        deadline = time.time() + self.timeout_s
        last_payload: dict[str, Any] = {}
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=15.0) as client:
                    response = client.get(f"{self.base_url.rstrip('/')}/history/{prompt_id}")
                    response.raise_for_status()
                    payload = response.json()
            except Exception as exc:  # noqa: BLE001
                raise ComfyUIImageError(f"COMFYUI_HISTORY_FAILED:{exc}") from exc
            last_payload = payload
            item = payload.get(prompt_id) or {}
            outputs = item.get("outputs") or {}
            for output in outputs.values():
                images = output.get("images") or []
                if images:
                    return images[0]
            time.sleep(self.poll_interval_s)
        raise ComfyUIImageError(f"COMFYUI_TIMEOUT:{json.dumps(last_payload)[:300]}")

    def _download_image(self, *, image_info: dict[str, Any]) -> bytes:
        _ensure_comfyui_runtime_authorized()
        filename = str(image_info.get("filename") or "").strip()
        if not filename:
            raise ComfyUIImageError("COMFYUI_IMAGE_FILENAME_MISSING")
        params = {
            "filename": filename,
            "subfolder": str(image_info.get("subfolder") or ""),
            "type": str(image_info.get("type") or "output"),
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.get(f"{self.base_url.rstrip('/')}/view", params=params)
                response.raise_for_status()
                return response.content
        except Exception as exc:  # noqa: BLE001
            raise ComfyUIImageError(f"COMFYUI_VIEW_FAILED:{exc}") from exc

    def _persist_response(
        self,
        *,
        image_bytes: bytes,
        render_job_id: str,
        segment_name: str,
        operation: str,
        model: str,
        prompt: str,
        input_image_path: str = "",
    ) -> ComfyUIImageResult:
        segment_dir = self.base_dir / render_job_id / segment_name
        segment_dir.mkdir(parents=True, exist_ok=True)
        image_path = segment_dir / f"{operation}.png"
        metadata_path = segment_dir / f"{operation}.json"
        image_path.write_bytes(image_bytes)
        metadata_path.write_text(
            json.dumps(
                {
                    "operation": operation,
                    "model": model,
                    "prompt": prompt,
                    "input_image_path": input_image_path,
                    "base_url": self.base_url,
                    "checkpoint_name": self.checkpoint_name,
                    "width": self.width,
                    "height": self.height,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return ComfyUIImageResult(
            image_path=str(image_path),
            metadata_path=str(metadata_path),
            source_type="comfyui",
            model=model,
            operation=operation,
        )

    def _seed_int(self, *, seed: str) -> int:
        normalized = str(seed or "").strip()
        if not normalized:
            return 0
        return int(sha256(normalized.encode("utf-8")).hexdigest()[:8], 16)
