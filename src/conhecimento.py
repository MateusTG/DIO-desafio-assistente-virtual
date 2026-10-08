"""Busca na base de conhecimento de programação (data/conhecimento/*.md).

Cada arquivo é dividido em seções (títulos "## ") e a busca pontua as seções
pela quantidade de palavras da consulta que aparecem nelas. É simples, sem
dependências e suficiente para uma base pequena; o resultado sempre traz a
fonte (arquivo > seção) para o agente citar.
"""

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import config

PASTA = config.DATA_DIR / "conhecimento"

# Palavras muito comuns que não ajudam a encontrar a seção certa.
STOPWORDS = set(
    "a o e de da do das dos em no na nos nas um uma para por com como que se ao aos à às é ou mais "
    "meu minha qual quais quando onde porque por que eu voce você isso esse essa este esta the of to in "
    "and is how what fazer faço usar uso".split()
)

# Sinônimos simples para aproximar a pergunta do vocabulário da base.
SINONIMOS = {
    "node": "nodejs", "js": "javascript", "ts": "typescript", "csharp": "c#", "dotnet": ".net",
    "py": "python", "teste": "testes", "erro": "erros", "senha": "senhas", "agenda": "agendar",
}


@dataclass
class Trecho:
    arquivo: str
    secao: str
    texto: str

    @property
    def fonte(self) -> str:
        return f"{self.arquivo} > {self.secao}"


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def tokens(texto: str) -> list[str]:
    palavras = re.findall(r"[a-z0-9#+._]+", normalizar(texto))
    palavras = [p.strip("._") for p in palavras]
    return [SINONIMOS.get(p, p) for p in palavras if p and p not in STOPWORDS and len(p) > 1]


def carregar_trechos(pasta: Path = PASTA) -> list[Trecho]:
    trechos = []
    for arquivo in sorted(pasta.glob("*.md")):
        titulo_doc, secoes = arquivo.stem, []  # secoes: [(título da seção, linhas)]
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            if linha.startswith("# "):
                titulo_doc = linha[2:].strip()
            elif linha.startswith("## "):
                secoes.append((linha[3:].strip(), []))
            elif secoes:
                secoes[-1][1].append(linha)
        # O título do documento (ex.: "Node.js") entra no texto para contar na busca.
        for secao, linhas in secoes:
            trechos.append(Trecho(arquivo.name, secao, f"[{titulo_doc}]\n" + "\n".join(linhas).strip()))
    return trechos


class BaseConhecimento:
    def __init__(self, pasta: Path = PASTA):
        self.trechos = carregar_trechos(pasta)
        self._tokens = [Counter(tokens(f"{t.arquivo} {t.secao} {t.secao} {t.texto}")) for t in self.trechos]
        # IDF: palavras que aparecem em poucas seções valem mais.
        n = len(self.trechos)
        df = Counter(p for c in self._tokens for p in c)
        self._idf = {p: math.log(1 + n / q) for p, q in df.items()}

    def buscar(self, consulta: str, limite: int = 3) -> list[tuple[float, Trecho]]:
        termos = set(tokens(consulta))
        pontuados = []
        for trecho, contagem in zip(self.trechos, self._tokens):
            pontos = sum(self._idf.get(t, 0) * (1 + math.log(contagem[t])) for t in termos if contagem[t])
            if pontos > 0:
                pontuados.append((pontos, trecho))
        pontuados.sort(key=lambda x: -x[0])
        return pontuados[:limite]

    def buscar_formatado(self, consulta: str, limite: int = 3) -> str:
        resultados = self.buscar(consulta, limite)
        if not resultados:
            return "Nenhum trecho da base de conhecimento corresponde a essa consulta."
        return "\n\n---\n\n".join(f"FONTE: {t.fonte}\n{t.texto}" for _, t in resultados)


if __name__ == "__main__":
    import sys

    base = BaseConhecimento()
    print(f"{len(base.trechos)} seções carregadas.\n")
    for pontos, t in base.buscar(" ".join(sys.argv[1:]) or "erro de cors no node"):
        print(f"{pontos:5.2f}  {t.fonte}")
