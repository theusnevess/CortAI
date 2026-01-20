import os
from minio import Minio # Importa o cliente MinIO
from minio.error import S3Error


class MinioService:
    """
    Serviço responsável por toda a comunicação com o MinIO (Object Storage).

    Função arquitetural:
    - Armazenar arquivos grandes (vídeos, clipes, thumbnails)
    - Evitar guardar arquivos binários no banco de dados
    - Garantir persistência mesmo que containers sejam reiniciados

    Este serviço é utilizado principalmente pelos workers (Celery), mas também pode ser usado pela API se necessário.
    """

    def __init__(self):
        """
        Construtor da classe.

        Executa automaticamente quando o serviço é instanciado.
        Aqui fazemos:
        1. Conexão com o MinIO
        2. Leitura das variáveis de ambiente
        3. Garantia de que o bucket existe
        """

        # Configuração do endpoint do MinIO
        minio_endpoint_env = os.getenv("MINIO_ENDPOINT")

        if minio_endpoint_env:
            # Permite que o usuário passe o prefixo com esquema
            # Ex: http://minio:9000 ou minio:9000
            if minio_endpoint_env.startswith("http://") or minio_endpoint_env.startswith("https://"):
                # Remove o esquema para a API do Minio Python
                parsed = minio_endpoint_env.split("://", 1)[1]
            else:
                parsed = minio_endpoint_env
            minio_endpoint = parsed
            secure_flag = minio_endpoint_env.startswith("https://") # Define se a conexão é segura
        else:
            # Configuração padrão usando host e porta
            minio_host = os.getenv("MINIO_HOST", "minio")
            minio_port = os.getenv("MINIO_PORT", "9000")
            minio_endpoint = f"{minio_host}:{minio_port}"
            secure_flag = os.getenv("MINIO_SECURE", "false").lower() in ["1", "true", "yes"]

        # Credenciais do MinIO vindas do .env
        access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")

        # Instancia o cliente MinIO com as respectivas credenciais 
        self.client = Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure_flag
        )

        # Nome do bucket onde os vídeos serão armazenados
        # Bucket é equivalente a uma "pasta raiz" no Object Storage
        self.bucket_name = os.getenv("MINIO_BUCKET_VIDEOS", "videos-raw")

        # Garante que o bucket exista ao subir o sistema, evitando erros futuros
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """
        Método interno (privado por convenção).

        Responsável por:
        - Verificar se o bucket já existe
        - Criar o bucket automaticamente caso não exista

        Isso torna o sistema:
        - Idempotente
        - Seguro para reinícios
        - Independente de setup manual
        """
        try:
            # Verifica se o bucket já existe no MinIO
            if not self.client.bucket_exists(self.bucket_name):
                # Cria o bucket se não existir
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' criado com sucesso.")
        except S3Error as e:
            # Captura erros de conexão, autenticação ou rede
            print(f"Erro ao conectar no MinIO: {e}")

    def upload_file(self, file_path: str, object_name: str) -> str:
        """
        Realiza o upload de um arquivo local para o MinIO.

        Parâmetros:
        - file_path: caminho do arquivo DENTRO do container
          Ex: /tmp/video_abc.mp4

        - object_name: nome final do arquivo no MinIO
          Ex: raw/abc123.mp4

        Retorno:
        - Caminho lógico do arquivo salvo no MinIO
          Ex: videos-raw/raw/abc123.mp4

        Esse retorno é o que será salvo no BANCO DE DADOS.
        """
        try:
            # Envia o arquivo para o bucket configurado
            # fput_object faz:
            # - leitura do arquivo local
            # - upload em chunks
            # - persistência no Object Storage
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
            )

            # Retorna o caminho lógico do objeto para salvar no banco
            return f"{self.bucket_name}/{object_name}"

        except S3Error as e:
            # Caso algo dê errado no upload:
            # - bucket não existe
            # - MinIO offline
            # - erro de permissão
            print(f"Erro no upload para MinIO: {e}")

            # Relança o erro para que o Worker saiba que a tarefa falhou
            raise e

    def download_file(self, object_name: str, file_path: str):
        """
        Baixa um arquivo do MinIO para o disco local.

        Parâmetros:
        - object_name: nome do objeto no bucket (ex: raw/video.mp4)
        - file_path: caminho local onde salvar (ex: /tmp/video.mp4)
        """
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            return file_path
        except S3Error as e:
            print(f"Erro no download do MinIO: {e}")
            raise e
