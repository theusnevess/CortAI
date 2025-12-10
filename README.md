# 🎬 CortAI

![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_14-black)
![Infrastructure](https://img.shields.io/badge/Infra-Docker_Compose-green)
![AI](https://img.shields.io/badge/AI-Local_LLM-orange)

> **Engenharia de Automação de Conteúdo.**
> [cite_start]O CortAI 2.0 é uma plataforma SaaS autônoma que utiliza um ecossistema de 11 Agentes Inteligentes para capturar, analisar, editar e publicar conteúdo viral automaticamente[cite: 6, 7].

---

## 🚀 Visão Geral

O CortAI resolve o problema da edição manual de vídeos longos (podcasts, lives, aulas). [cite_start]Diferente de scripts simples, ele utiliza uma arquitetura **assíncrona e distribuída** para processar múltiplos vídeos em paralelo, garantindo escalabilidade e robustez[cite: 13, 18].

[cite_start]O sistema não apenas corta vídeos; ele "assiste" ao conteúdo, entende o contexto semântico, identifica momentos de alto potencial viral ("ganchos"), edita em formato vertical (9:16), adiciona legendas dinâmicas e publica nas redes sociais[cite: 18, 20].

## 🧠 Arquitetura dos Agentes

[cite_start]O sistema é orquestrado por um pipeline de 11 agentes especializados[cite: 50]:

1.  [cite_start]**Coletor:** Download e normalização de vídeo (YouTube/Twitch/Upload)[cite: 51, 52].
2.  [cite_start]**Segmentador:** Detecção de cenas e remoção de silêncio[cite: 116, 117].
3.  [cite_start]**Transcritor:** Speech-to-Text de alta precisão (Whisper)[cite: 83, 84].
4.  [cite_start]**Analista Semântico:** Classificação de tópicos, sentimentos e detecção de "momentos virais" usando LLMs[cite: 144, 145].
5.  [cite_start]**Gerador de Cortes:** Edição via FFmpeg baseada nos timestamps da análise[cite: 190, 191].
6.  [cite_start]**Legendador:** Geração de legendas "estilo Hormozi" sincronizadas[cite: 236, 237].
7.  [cite_start]**Gerador de Miniaturas:** Criação de thumbnails atraentes com IA[cite: 272, 273].
8.  [cite_start]**Roteirista:** Geração de títulos e descrições otimizados para SEO[cite: 313, 314].
9.  [cite_start]**Viral Score:** Ranking preditivo do potencial de sucesso do clipe[cite: 441, 485].
10. [cite_start]**Publicador:** Agendamento e upload automático (TikTok, Reels, Shorts)[cite: 351, 352].
11. [cite_start]**TrendScout:** Monitoramento contínuo de tendências para retroalimentar a IA[cite: 405, 406].

## 🛠️ Stack Tecnológico

[cite_start]A infraestrutura foi desenhada para ser modular, agnóstica de nuvem e escalável horizontalmente [cite: 503-519].

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Backend API** | Python (FastAPI) | Gateway, Gestão de Auth e Orquestração |
| **Frontend** | Next.js 14 + Tailwind | Dashboard do Usuário e Analytics |
| **Task Queue** | Celery + Redis | Processamento assíncrono distribuído |
| **Database** | PostgreSQL 16 | Armazenamento relacional robusto |
| **Storage** | MinIO (S3 Compatible) | Armazenamento de vídeos brutos e processados |
| **AI Engine** | Ollama / Torch | Execução de LLMs locais (Llama 3, Mistral) e Whisper |
| **Vídeo** | FFmpeg | Processamento bruto de imagem e som |
| **Infra** | Docker & Docker Compose | Containerização e ambiente de desenvolvimento |

## 📂 Estrutura do Projeto

```text
cortai-v2/
├── backend/            # API FastAPI e Celery Workers
│   ├── app/agents/     # Lógica dos 11 Agentes de IA
│   └── worker/         # Processamento de tarefas pesadas
├── frontend/           # Aplicação Next.js (Dashboard)
├── infra/              # Configurações de Deploy e CI/CD
└── storage/            # Volume local para o MinIO (ignorado pelo Git)