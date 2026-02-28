import os  # Para operacoes de sistema de arquivos e variaveis de ambiente
import re
import socket
import ssl
import uuid  # Para manipulacao de UUIDs
from datetime import datetime  # Manipulacao de datas

import requests
import yt_dlp  # Biblioteca para download de videos
from slugify import slugify  # Para criar nomes de arquivos seguros

from app.agents.collector.errors import CollectorError
from app.services.storage import MinioService  # Servico de armazenamento MinIO




def _classify_collector_exc(exc: Exception) -> CollectorError:
    """Classifica falhas conhecidas do coletor em um contrato estavel."""
    msg = str(exc)

    if isinstance(exc, ValueError):
        return CollectorError(
            "invalid_input",
            "Entrada invalida para coleta.",
            retryable=False,
            cause=msg[:500],
        )

    if isinstance(exc, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in msg:
        return CollectorError(
            "ssl_cert_verify_failed",
            "Falha de verificacao TLS/CA ao acessar a origem.",
            retryable=True,
            cause=msg[:500],
        )

    if isinstance(exc, socket.gaierror) or "getaddrinfo failed" in msg:
        return CollectorError(
            "dns_failed",
            "Falha de DNS ao resolver o host da origem.",
            retryable=True,
            cause=msg[:500],
        )

    if isinstance(exc, (requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout)) or "timed out" in msg.lower():
        return CollectorError(
            "timeout",
            "Timeout ao acessar a origem.",
            retryable=True,
            cause=msg[:500],
        )

    match = re.search(r"\bHTTP Error (\d{3})\b", msg)
    if match:
        status = int(match.group(1))
        if 400 <= status < 500:
            error_type = "upstream_blocked" if status in (403, 429) else "http_4xx"
            return CollectorError(
                error_type,
                f"Origem respondeu HTTP {status}.",
                http_status=status,
                retryable=status in (403, 429),
                cause=msg[:500],
            )
        if 500 <= status < 600:
            return CollectorError(
                "http_5xx",
                f"Origem respondeu HTTP {status}.",
                http_status=status,
                retryable=True,
                cause=msg[:500],
            )

    return CollectorError(
        "unknown",
        "Falha desconhecida no coletor.",
        retryable=True,
        cause=msg[:500],
    )


class CollectorAgent:
    def __init__(self):
        self.storage = None
        # Caminho de download configurável (usa /tmp por padrão em containers)
        self.download_path = os.getenv("COLLECTOR_DOWNLOAD_PATH", "/tmp/downloads")
        os.makedirs(self.download_path, exist_ok=True) # Garante que o diretório de download exista

    def process(self, url: str) -> dict:
        if not isinstance(url, str) or not url.strip() or not re.match(r"^https?://", url.strip()):
            err = _classify_collector_exc(ValueError(f"Invalid source_ref: {url!r}"))
            return {
                "title": None,
                "duration": None,
                "minio_path": None,
                "source_type": None,
                "metadata": {"original_url": url},
                "error": err.to_dict(),
            }

        url = url.strip()
        if self.storage is None:
            self.storage = MinioService()
        print(f"⬇️ Iniciando download: {url}")
        
        # Tenta localizar o cookies.txt na pasta 'backend' relativa a este módulo
        cookie_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cookies.txt'))
        if os.path.exists(cookie_file):
            print(f"🍪 Arquivo de cookies encontrado em: {cookie_file}")
        else:
            print(f"⚠️ AVISO: Arquivo de cookies não encontrado em: {cookie_file}")

        video_id = str(uuid.uuid4())
        output_template = f"{self.download_path}/{video_id}.%(ext)s"
        
        # Configurações do yt-dlp
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', # Tenta baixar o melhor vídeo + áudio disponível e, se não, o melhor formato disponível
            'outtmpl': output_template, # Força o output temporário com o id gerado
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'merge_output_format': 'mp4', # Tenta mesclar em mp4 quando possível
            'retries': 5, # Retry em caso de erros de rede
            'fragment_retries': 5,
        }

        # O yt-dlp usa certifi por padrao quando disponivel. Neste runtime, o
        # bundle valido e o store de CAs do sistema; por isso forcamos o modo
        # no-certifi para alinhar o downloader ao mesmo trust store do requests.
        ydl_opts['compat_opts'] = ['no-certifi']

        # Se temos cookies, passa para o yt-dlp para suportar vídeos privados/restritos
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file
        
        # Flag para indicar que devemos usar o downloader Playwright como último recurso
        use_playwright = False


        try:
            # Primeiro tenta obter metadados sem baixar para validar formatos disponíveis
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_preview = ydl.extract_info(url, download=False)
                    formats = info_preview.get('formats') or [] 

                # Alguns URLs diretos (ex: .mp4 hospedado) não populam 'formats' mas possuem 'url'/'ext'.
                if not formats:
                    # fallback: se o preview tiver um url ou ext, consideramos como download direto
                    # Também verificamos se a URL original termina com uma extensão de mídia
                    direct_file = False

                    if info_preview.get('url') or info_preview.get('ext'):
                        direct_file = True
                    else:
                        # usa a URL de entrada para tentar detectar um arquivo direto
                        lower_url = url.split('?')[0].lower()
                        if lower_url.endswith(('.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.mp3', '.m4a', '.opus', '.wav', '.aac')):
                            direct_file = True

                    # Se for um arquivo direto, inferimos se é vídeo ou áudio pela extensão
                    if direct_file:
                        ext_preview = (info_preview.get('ext') or url.split('?')[0].split('.')[-1] or '').lower()
                        if ext_preview in ('mp4', 'mkv', 'webm', 'mov', 'avi', 'flv'):
                            has_video = True
                            has_audio = True
                        elif ext_preview in ('mp3', 'm4a', 'opus', 'wav', 'aac'):
                            has_video = False
                            has_audio = True
                        else:
                            # Se ext desconhecida, assumimos que é um arquivo de vídeo
                            has_video = True
                            has_audio = True
                    else:
                        has_video = False
                        has_audio = False
                else:
                    video_exts = ('mp4','mkv','webm','mov','avi','flv')
                    audio_exts = ('mp3','m4a','opus','wav','aac')

                    # Verifica se há formatos de vídeo ou áudio disponíveis
                    has_video = any(
                        (f.get('vcodec') not in (None, 'none'))
                        or (f.get('video_ext') and f.get('video_ext') not in (None, 'none', ''))
                        or ((f.get('ext') or '').lower() in video_exts)
                        for f in formats
                    )

                    has_audio = any(
                        (f.get('acodec') not in (None, 'none'))
                        or (f.get('audio_ext') and f.get('audio_ext') not in (None, 'none', ''))
                        or ((f.get('ext') or '').lower() in audio_exts)
                        for f in formats
                    )

                    if not has_video and not has_audio:
                        # não há formatos para download (ex: apenas imagens)
                        raise RuntimeError("Nenhum formato de vídeo/áudio disponível para download (apenas imagens ou bloqueado)")
            except yt_dlp.utils.DownloadError as de:
                # Em alguns casos o preview falha; tentamos um preview apenas de áudio como fallback
                print(f"⚠️ Preview falhou: {de}. Tentando preview apenas de áudio...")
                try:
                    ydl_opts_audio = ydl_opts.copy()
                    ydl_opts_audio['format'] = 'bestaudio/best'
                    ydl_opts_audio.pop('merge_output_format', None)
                    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                        info_preview = ydl.extract_info(url, download=False)
                        formats = info_preview.get('formats') or []
                        has_video = any(f.get('vcodec') not in (None, 'none') for f in formats)
                        has_audio = any(f.get('acodec') not in (None, 'none') for f in formats)

                        if not has_video and not has_audio:
                            raise RuntimeError("Nenhum formato de vídeo/áudio disponível para download após fallback de áudio")
                except Exception:
                    # Se o preview só de áudio também falhar, tentamos um fallback extra com extractor args e UA
                    print("⚠️ Preview de áudio falhou também — tentando extractor_args + User-Agent fallback...")
                    try:
                        ydl_opts_fallback = ydl_opts.copy()
                        # Força um extractor client alternativo que às vezes contorna nsig issues
                        ydl_opts_fallback['extractor_args'] = {'youtube': {'player_client': 'android'}}
                        ydl_opts_fallback['http_headers'] = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
                        }
                        with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                            info_preview = ydl.extract_info(url, download=False)
                            formats = info_preview.get('formats') or []
                            has_video = any(f.get('vcodec') not in (None, 'none') for f in formats)
                            has_audio = any(f.get('acodec') not in (None, 'none') for f in formats)

                            if not has_video and not has_audio:
                                raise RuntimeError("Nenhum formato de vídeo/áudio disponível para download após fallback de extractor_args")
                    except Exception as exc:
                        # Repropaga a falha original se todos os fallbacks falharem
                        print("⚠️ extractor_args fallback falhou — tentando fallback com Playwright (headless browser)...")
                        try:
                            # Log do tipo de exceção para diagnóstico
                            print(f"DEBUG: extractor_args raised: {type(exc).__name__}: {exc}")

                            ydl_opts_playwright = ydl_opts.copy()
                            ydl_opts_playwright['downloader'] = 'playwright'
                            ydl_opts_playwright['downloader_args'] = {'playwright': {'timeout': 120}}

                            print("DEBUG: Executando preview com Playwright... (isso pode demorar)")
                            with yt_dlp.YoutubeDL(ydl_opts_playwright) as ydl:
                                info_preview = ydl.extract_info(url, download=False)
                                formats = info_preview.get('formats') or []
                                has_video = any(f.get('vcodec') not in (None, 'none') for f in formats)
                                has_audio = any(f.get('acodec') not in (None, 'none') for f in formats)

                                print(f"DEBUG: Playwright preview formats found: {len(formats)}; has_video={has_video}; has_audio={has_audio}")

                                if not has_video and not has_audio:
                                    raise RuntimeError("Nenhum formato disponível mesmo com Playwright")

                                use_playwright = True
                                print("✅ Playwright fallback obteve formatos disponíveis.")
                        except Exception as play_exc:
                            # Logamos os detalhes completos da falha do Playwright e repropagamos a exceção original para manter o context
                            print(f"ERROR: Falha no fallback Playwright: {type(play_exc).__name__}: {play_exc}")
                            # Inclui ambas as causas na mensagem para facilitar triagem
                            raise RuntimeError(f"Falha em extractor_args: {exc}; Falha em Playwright: {play_exc}") from play_exc
            # Decide se fará download de vídeo ou áudio (fallback)
            download_type = 'video'
            if not has_video and has_audio:
                print("ℹ️ Sem vídeo disponível, tentando fallback para áudio-only.")
                download_type = 'audio'
                ydl_opts_audio = ydl_opts.copy()
                ydl_opts_audio['format'] = 'bestaudio/best'
                ydl_opts_audio.pop('merge_output_format', None)
                if use_playwright:
                    ydl_opts_audio['downloader'] = 'playwright'
                    ydl_opts_audio['downloader_args'] = {'playwright': {'timeout': 120}}
                final_opts = ydl_opts_audio
            else:
                final_opts = ydl_opts_playwright if use_playwright else ydl_opts
            # Tenta download padrão e, se falhar por "Requested format is not available", tenta formatos explícitos
            try:
                with yt_dlp.YoutubeDL(final_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info_dict)
            except yt_dlp.utils.DownloadError as dl_err:
                print(f"⚠️ Download padrão falhou: {dl_err}. Tentando formatos explícitos detectados no preview...")

                # Gera lista de format_ids candidatos a partir do preview 'formats' (prioriza video>audio e exclui m3u8_native)
                candidates = []
                for f in (formats or []):
                    fid = f.get('format_id') or f.get('format') or str(f.get('format_id') or '')
                    proto = (f.get('protocol') or '').lower()
                    # Ignora storyboards/images e m3u8_native (iOS m3u8 that may require PO tokens)
                    if fid and fid.startswith('sb'):
                        continue
                    if proto and proto.startswith('m3u8'):
                        continue
                    # Prioriza formatos com vídeo
                    has_vid = (f.get('vcodec') not in (None, 'none'))
                    has_aud = (f.get('acodec') not in (None, 'none'))
                    candidates.append((has_vid, has_aud, int(f.get('resolution') or 0 if f.get('resolution') and isinstance(f.get('resolution'), int) else 0), fid))

                # Ordena: video first, then audio, then higher resolution
                candidates = sorted(candidates, key=lambda x: (not x[0], not x[1], -x[2]))

                success = False
                last_exc = dl_err
                for _,_,_,fmt_id in candidates:
                    try:
                        print(f"DEBUG: Tentando download com formato explícito: {fmt_id}")
                        opts_try = final_opts.copy()
                        opts_try['format'] = fmt_id
                        with yt_dlp.YoutubeDL(opts_try) as ydl:
                            info_dict = ydl.extract_info(url, download=True)
                            file_path = ydl.prepare_filename(info_dict)
                        success = True
                        print(f"✅ Download com formato {fmt_id} teve sucesso.")
                        break
                    except yt_dlp.utils.DownloadError as e2:
                        print(f"⚠️ Falha com formato {fmt_id}: {e2}")
                        last_exc = e2

                if not success:
                    # Se nada funcionou, repropaga a última exceção para ser tratada mais acima
                    raise last_exc

            video_title = info_dict.get('title', 'Video Desconhecido')
            duration = info_dict.get('duration', 0)

            # Garante extensão correta no arquivo baixado
            _, ext = os.path.splitext(file_path)
            if not ext:
                ext = f".{info_dict.get('ext','mp4')}"

            safe_filename = f"{slugify(video_title)}_{video_id}{ext}"

            print(f"☁️ Subindo para o Storage: {safe_filename}")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo baixado não encontrado: {file_path}")

            minio_path = self.storage.upload_file(file_path, safe_filename)

            try:
                os.remove(file_path)
            except Exception:
                print(f"⚠️ Não foi possível remover o arquivo local: {file_path}")

            metadata = {
                "original_url": url,
                "uploader": info_dict.get('uploader'),
                "views": info_dict.get('view_count'),
                "download_type": download_type
            }

            return {
                "title": video_title,
                "duration": duration,
                "minio_path": minio_path,
                "source_type": download_type,
                "metadata": metadata,
                "error": None,
            }

        except Exception as exc:
            err = _classify_collector_exc(exc)
            print(f"Erro no Agente Coletor ({err.error_type}): {err.message} | cause={err.cause}")
            return {
                "title": None,
                "duration": None,
                "minio_path": None,
                "source_type": None,
                "metadata": {"original_url": url},
                "error": err.to_dict(),
            }
