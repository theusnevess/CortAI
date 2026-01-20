from typing import List, Dict # Importa as classes List e Dict do módulo typing
import numpy as np # Importa a biblioteca numpy para operações numéricas
import librosa # Importa a biblioteca librosa para processamento de áudio
from faster_whisper import WhisperModel # Importa a classe WhisperModel do módulo faster_whisper

from .schemas import SegmentInput, TranscriptionOutput # Importa as classes SegmentInput e TranscriptionOutput do módulo schemas


class TranscriberAgent:
    def __init__(self, model_size: str = "small"):
        try:
            # Tenta usar CUDA se disponível
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16") # Inicializa o modelo Whisper na GPU
            print(f"🚀 Whisper inicializado na GPU ({model_size})")
        except Exception as e:
            print(f"⚠️ GPU não disponível ou erro ({e}). Fallback para CPU.")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # Função para transcrever os segmentos
    def transcribe(
        self,
        audio_path: str,
        segments: List[Dict]
    ) -> List[Dict]:

        # Carrega o áudio uma vez
        y, sr = librosa.load(audio_path, sr=None, mono=True)

        # Lista para armazenar as transcrições
        results: List[Dict] = []

        # Itera sobre os segmentos
        for segment in segments:
            seg = SegmentInput(**segment)

            start_sample = int(seg.start_time * sr)
            end_sample = int(seg.end_time * sr)

            # Verifica se o segmento é válido
            if start_sample >= end_sample or start_sample >= len(y):
                text = ""
            else:
                audio_slice = y[start_sample:end_sample]  # Pega o segmento do áudio

                # Transcreve o segmento
                segments_gen, _ = self.model.transcribe(
                    audio_slice,
                    language="en",
                    beam_size=5
                )

                text = " ".join(s.text.strip() for s in segments_gen)
                print(f"🎤 [DEBUG] Transcrito segmento {seg.segment_id}: '{text}'")

            # Adiciona a transcrição ao resultado
            results.append(
                TranscriptionOutput(
                    segment_id=seg.segment_id,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=text
                ).dict()
            )

        return results
