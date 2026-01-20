from typing import List, Dict # Importa List e Dict do módulo typing
import numpy as np # Importa numpy para operações numéricas
import librosa # Importa librosa para processamento de áudio


class SegmenterAgent:
    # Inicializa o segmentador com parâmetros padrão
    def __init__(
        self,
        frame_length: int = 2048,
        hop_length: int = 512,
        energy_threshold: float = 0.01, # Threshold para detectar energia no áudio
        min_duration: float = 0.5,  # Minimo de duracao para considerar um segmento válido
    ):
        self.frame_length = frame_length # Tamanho do frame para calcular energia
        self.hop_length = hop_length # Tamanho do hop para calcular energia
        self.energy_threshold = energy_threshold # Threshold para detectar energia no áudio
        self.min_duration = min_duration # Minimo de duracao para considerar um segmento válido

    def process(self, audio_path: str) -> List[Dict]:
        print(f"✂️ Segmenter iniciado para: {audio_path}")
        
        # Carrega o áudio
        # Força o uso do audioread do librosa se necessário, mas o librosa geralmente lida com isso.
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        
        print(f"🎵 Áudio carregado. Amostras: {len(y)}, SR: {sr}")

        # Calcula a energia RMS por frame
        rms = librosa.feature.rms(
            y=y,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]

        # Normaliza a energia
        max_rms = np.max(rms) if len(rms) > 0 else 0
        print(f"📊 Max RMS: {max_rms:.4f}")
        
        rms_norm = rms / max_rms if max_rms > 0 else rms

        # Detecta os frames ativos
        active_frames = rms_norm >= self.energy_threshold
        print(f"🔔 Frames ativos: {np.sum(active_frames)} / {len(active_frames)}")

        segments = []
        segment_id = 0
        start_frame = None

        # Itera sobre os frames ativos
        for i, is_active in enumerate(active_frames):
            # Se o frame for ativo e não houver um frame de início, define o frame de início
            if is_active and start_frame is None:
                start_frame = i

            # Se o frame for inativo e houver um frame de início, define o frame de fim e cria um segmento
            elif not is_active and start_frame is not None:
                end_frame = i
                segment = self._build_segment(
                    segment_id,
                    start_frame,
                    end_frame,
                    rms_norm,
                    sr
                )
                if segment:
                    segments.append(segment)
                    segment_id += 1
                start_frame = None

        # Se houver um frame de início, define o frame de fim e cria um segmento
        if start_frame is not None:
            segment = self._build_segment(
                segment_id,
                start_frame,
                len(rms_norm),
                rms_norm,
                sr
            )
            if segment:
                segments.append(segment)
        
        print(f"✅ Segmentação concluída. Segmentos encontrados: {len(segments)}")
        return segments

    # Função para construir um segmento
    def _build_segment(
        self,
        segment_id: int,
        start_frame: int,
        end_frame: int,
        rms_norm: np.ndarray,
        sr: int
    ) -> Dict | None:
        start_time = start_frame * self.hop_length / sr
        end_time = end_frame * self.hop_length / sr
        duration = end_time - start_time

        if duration < self.min_duration:
            return None

        energy_score = float(np.mean(rms_norm[start_frame:end_frame])) # Calcula a energia média do segmento

        return {
            "segment_id": segment_id,
            "start_time": start_time,
            "end_time": end_time,
            "energy_score": energy_score
        }
