"""Configurações lidas de variáveis de ambiente (ou de um arquivo .env)."""

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DATA_DIR = RAIZ / "data"
SAIDA_DIR = RAIZ / "saida"

# "anthropic" (Claude, via API) ou "ollama" (modelo local e gratuito)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

# Claude: a chave é lida pelo SDK de ANTHROPIC_API_KEY
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
ANTHROPIC_EFFORT = os.getenv("ANTHROPIC_EFFORT", "medium")

# Ollama: use um modelo com suporte a ferramentas (ex.: qwen2.5, llama3.1)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))
MAX_PASSOS_FERRAMENTAS = int(os.getenv("MAX_PASSOS_FERRAMENTAS", "10"))

# "demo" usa os dados simulados de data/mock para todas as integrações.
# "real" usa a API de cada ferramenta que tiver credenciais configuradas (as demais continuam simuladas).
JARVIS_MODO = os.getenv("JARVIS_MODO", "demo").lower()
FUSO = ZoneInfo(os.getenv("JARVIS_FUSO", "America/Sao_Paulo"))

# Credenciais das integrações reais
GOOGLE_CREDENCIAIS = Path(os.getenv("GOOGLE_CREDENCIAIS", RAIZ / "credentials.json"))
GOOGLE_TOKEN = Path(os.getenv("GOOGLE_TOKEN", RAIZ / "token.json"))
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
TRELLO_KEY = os.getenv("TRELLO_KEY", "")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN", "")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CANAL_ID = os.getenv("SLACK_CANAL_ID", "")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGINA_PAI_ID = os.getenv("NOTION_PAGINA_PAI_ID", "")


def agora() -> datetime:
    """Data/hora atual no fuso do usuário. JARVIS_HOJE=AAAA-MM-DD fixa a data (útil para demo e testes)."""
    fixo = os.getenv("JARVIS_HOJE")
    if fixo:
        return datetime.fromisoformat(fixo).replace(hour=19, minute=0, tzinfo=FUSO)
    return datetime.now(FUSO)
