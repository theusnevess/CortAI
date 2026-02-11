from typing import List, Dict
import os
import numpy as np
import librosa
from faster_whisper import WhisperModel

from .schemas import SegmentInput, TranscriptionOutput


class TranscriberAgent:
    def __init__(self, model_size: str = "small"):
        device = os.getenv("WHISPER_DEVICE", "cuda")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
        # Require GPU. If CUDA init fails, let it raise.
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        # Explicit log for runtime verification.
        print(f"[TRANSCRIBER] device={device} compute_type={compute_type} model_size={model_size}")

    def transcribe(self, audio_path: str, segments: List[Dict]) -> List[Dict]:
        """
        Transcreve segmentos de audio usando Whisper.
        Args:
            audio_path: Caminho do arquivo de audio completo.
            segments: Lista de segmentos com segment_id, start_time e end_time.
        Returns:
            Lista com segment_id, start_time, end_time e text.
        """
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        results: List[Dict] = []

        for segment in segments:
            seg = SegmentInput(**segment)
            start_sample = int(seg.start_time * sr)
            end_sample = int(seg.end_time * sr)

            if start_sample >= end_sample or start_sample >= len(y):
                text = ""
            else:
                audio_slice = y[start_sample:end_sample]
                segments_gen, _ = self.model.transcribe(
                    audio_slice,
                    language="en",
                    beam_size=5,
                )
                text = " ".join(s.text.strip() for s in segments_gen)
                print(f"[DEBUG] Transcribed segment {seg.segment_id}: '{text}'")

            results.append(
                TranscriptionOutput(
                    segment_id=seg.segment_id,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=text,
                ).dict()
            )

        return results
