"""Testes sem LLM. Rodar da raiz:  python -m unittest discover tests"""

import os
import sys
import tempfile
from pathlib import Path

# Data fixa num domingo e integrações simuladas: os testes não dependem do dia em que rodam.
os.environ["JARVIS_HOJE"] = "2026-10-11"
os.environ["JARVIS_MODO"] = "demo"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402

# Ações simuladas são registradas numa pasta temporária, não em saida/.
config.SAIDA_DIR = Path(tempfile.mkdtemp(prefix="jarvis-testes-"))
