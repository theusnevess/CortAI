import sys # Importa o módulo sys para obter argumentos de linha de comando
from src.agents.segmenter.service import SegmenterAgent 
from src.agents.transcriber.service import TranscriberAgent


def main(audio_path: str):
    segmenter = SegmenterAgent()
    transcriber = TranscriberAgent()

    segments = segmenter.process(audio_path)
    transcriptions = transcriber.transcribe(audio_path, segments)

    # Imprime as transcrições
    for t in transcriptions:
        print("=" * 40)
        print(f"Segmento {t['segment_id']}")
        print(f"{t['start_time']:.2f}s → {t['end_time']:.2f}s")
        print(t["text"])


if __name__ == "__main__":
    # Verifica se o arquivo de áudio foi fornecido como argumento
    if len(sys.argv) != 2:
        print("Uso: python -m src.agents.transcriber.main <audio.wav>")
        sys.exit(1)

    main(sys.argv[1]) # Chama a função main com o arquivo de áudio fornecido
