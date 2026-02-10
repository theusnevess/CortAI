import subprocess
import uuid
from pathlib import Path

from app.services.storage import MinioService


class AudioExtractorAdapter:
    def process(self, state: dict, payload: dict | None = None) -> dict:
        """
        Extraí o áudio de um vídeo usando FFmpeg. O caminho do vídeo deve ser fornecido em payload.raw_video_minio_path. O áudio extraído é salvo localmente e seu caminho é adicionado ao estado. O formato do
        áudio pode ser especificado em payload.audio_format (padrão: "wav").
        Args:
            state (dict): O estado atual do agente.
            payload (dict | None): O payload contendo os parâmetros necessários.
        Returns:
            dict: O estado atualizado com o caminho do áudio extraído.
        Raises:
            ValueError: Se o campo raw_video_minio_path estiver ausente ou inválido.
            OSError: Se o FFmpeg falhar ao processar o vídeo.
        """

        # Se o payload não for fornecido, tente obter do estado
        payload = payload or state.get("_action", {}).get("payload", {})
        raw_video_minio_path = payload.get("raw_video_minio_path")
        if not isinstance(raw_video_minio_path, str) or not raw_video_minio_path:
            raise ValueError("MissingField: payload.raw_video_minio_path")

        audio_format = payload.get("audio_format", "wav")
        if audio_format not in ("wav", "mp3"):
            raise ValueError("InvalidField: payload.audio_format")

        # Determina o nome do objeto no Minio a partir do caminho fornecido. 
        # O caminho pode ser no formato "bucket/object" ou apenas "object". 
        # Se for no formato "bucket/object", o bucket é extraído e o prefixo é removido para obter o nome do objeto. 
        # Se for apenas "object", o nome do objeto é usado diretamente.
        object_name = raw_video_minio_path
        if "/" in raw_video_minio_path:
            bucket = raw_video_minio_path.split("/", 1)[0]
            prefix = f"{bucket}/"
            if raw_video_minio_path.startswith(prefix):
                object_name = raw_video_minio_path[len(prefix):]

        ext = Path(raw_video_minio_path).suffix or ".mp4"
        video_local_path = Path("/tmp") / f"cortai_{uuid.uuid4()}{ext}"
        audio_local_path = Path("/tmp") / f"cortai_{uuid.uuid4()}.{audio_format}"

        MinioService().download_file(object_name, str(video_local_path))

        # Extraí o áudio usando FFmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_local_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_local_path),
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()
            raise OSError(f"FFmpegFailed: {msg}")

        state["audio_local_path"] = str(audio_local_path)
        state.setdefault("artifacts", {})
        state["artifacts"]["audio_ready"] = True
        state["artifacts"]["audio_local_path"] = state["audio_local_path"]
        return state
