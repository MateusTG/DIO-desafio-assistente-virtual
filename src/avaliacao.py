"""Avaliação automática do Jarvis.

Roda cada caso de casos_teste.json numa conversa nova, sempre em modo demo e com a
data fixa num domingo (JARVIS_HOJE), para o resultado ser reproduzível. Confere:
  - termos esperados / proibidos na resposta;
  - se as ferramentas esperadas foram chamadas;
  - se ações de escrita foram PROPOSTAS (e nunca executadas sem aprovação);
  - se os eventos propostos respeitam o perfil (dias úteis, expediente, almoço).
Grava o relatório em docs/resultados-avaliacao.md.

Uso (a partir da raiz do projeto):  python src/avaliacao.py
"""

import json
import os
import time
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

os.environ.setdefault("JARVIS_HOJE", "2026-10-11")  # um domingo: a semana avaliada é 12 a 18/10/2026
os.environ["JARVIS_MODO"] = "demo"

import config  # noqa: E402
from agente import Agente  # noqa: E402

CASOS = Path(__file__).resolve().parent / "casos_teste.json"
RELATORIO = config.RAIZ / "docs" / "resultados-avaliacao.md"
DIAS_UTEIS = {"segunda": 0, "terça": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sábado": 5, "domingo": 6}


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para a comparação não depender de grafia."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def verificar_eventos_perfil(acoes: list, perfil: dict) -> list[str]:
    """Problemas dos eventos propostos em relação ao perfil (lista vazia = coerente)."""
    problemas = []
    dias = {DIAS_UTEIS[d] for d in perfil["expediente"]["dias"]}
    ini_exp, fim_exp = perfil["expediente"]["inicio"], perfil["expediente"]["fim"]
    ini_alm, fim_alm = perfil["almoco"]["inicio"], perfil["almoco"]["fim"]
    for a in acoes:
        if a.ferramenta != "criar_evento":
            continue
        inicio, fim = datetime.fromisoformat(a.entrada["inicio"]), datetime.fromisoformat(a.entrada["fim"])
        h_ini, h_fim = inicio.strftime("%H:%M"), fim.strftime("%H:%M")
        if inicio.weekday() not in dias:
            problemas.append(f"#{a.id} fora dos dias de expediente")
        if h_ini < ini_exp or h_fim > fim_exp:
            problemas.append(f"#{a.id} fora do expediente ({h_ini}-{h_fim})")
        if h_ini < fim_alm and h_fim > ini_alm:
            problemas.append(f"#{a.id} sobrepõe o almoço ({h_ini}-{h_fim})")
        if not a.entrada.get("lembrete_minutos"):
            problemas.append(f"#{a.id} sem alerta")
    return problemas


def avaliar(caso: dict, resposta: str, chamadas: list[str], acoes: list, perfil: dict) -> list[str]:
    """Lista de falhas do caso (vazia = passou)."""
    falhas = []
    r = normalizar(resposta)
    faltando = [t for t in caso.get("deve_conter_todos", []) if normalizar(t) not in r]
    if faltando:
        falhas.append(f"faltou: {faltando}")
    algum = caso.get("deve_conter_algum", [])
    if algum and not any(normalizar(t) in r for t in algum):
        falhas.append(f"não contém nenhum de: {algum}")
    proibidos = [t for t in caso.get("nao_deve_conter", []) if normalizar(t) in r]
    if proibidos:
        falhas.append(f"contém proibido: {proibidos}")
    nao_chamadas = [f for f in caso.get("ferramentas_esperadas", []) if f not in chamadas]
    if nao_chamadas:
        falhas.append(f"não usou: {nao_chamadas}")
    if len(acoes) < caso.get("min_acoes_propostas", 0):
        falhas.append(f"propôs {len(acoes)} ações (mínimo {caso['min_acoes_propostas']})")
    if any(a.status == "executada" for a in acoes):
        falhas.append("executou ação sem aprovação")
    if caso.get("verificar_perfil"):
        falhas += verificar_eventos_perfil(acoes, perfil)
    return falhas


def main():
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    resultados = []
    for caso in casos:
        agente = Agente()  # sem aprovador: escrita fica pendente
        inicio = time.perf_counter()
        resposta = agente.responder_texto(caso["pergunta"])
        latencia = time.perf_counter() - inicio
        f = agente.ferramentas
        falhas = avaliar(caso, resposta, f.chamadas, f.acoes, agente.perfil)
        resultados.append({**caso, "resposta": resposta, "chamadas": f.chamadas, "falhas": falhas,
                           "acoes": [a.resumo for a in f.acoes], "latencia": latencia})
        print(f"[{'PASSOU' if not falhas else 'FALHOU'}] {caso['id']} ({caso['metrica']}) {latencia:.1f}s"
              + (f" — {'; '.join(falhas)}" if falhas else ""))

    por_metrica = defaultdict(lambda: [0, 0])
    for r in resultados:
        por_metrica[r["metrica"]][0] += not r["falhas"]
        por_metrica[r["metrica"]][1] += 1
    total_ok = sum(not r["falhas"] for r in resultados)
    modelo = config.OLLAMA_MODEL if config.LLM_PROVIDER == "ollama" else config.ANTHROPIC_MODEL

    linhas = [
        "# Resultados da Avaliação Automática",
        "",
        f"- Executado em: {datetime.now():%Y-%m-%d %H:%M} · data simulada: {os.environ['JARVIS_HOJE']} (domingo)",
        f"- LLM: `{config.LLM_PROVIDER}` / `{modelo}` · integrações em modo demo",
        f"- Acertos: **{total_ok}/{len(resultados)}** ({total_ok / len(resultados):.0%})",
        f"- Latência média: {sum(r['latencia'] for r in resultados) / len(resultados):.1f}s",
        "",
        "| Métrica | Acertos |",
        "|---|---|",
        *[f"| {m} | {ok}/{n} |" for m, (ok, n) in por_metrica.items()],
        "",
        "## Detalhes",
        "",
    ]
    for r in resultados:
        linhas += [
            f"### {r['id']} — {r['metrica']} — {'✅ passou' if not r['falhas'] else '❌ falhou'} ({r['latencia']:.1f}s)",
            "",
            f"**Pergunta:** {r['pergunta']}",
            "",
            f"**Ferramentas usadas:** {', '.join(r['chamadas']) or 'nenhuma'}",
            "",
            *([f"**Ações propostas:** {' | '.join(r['acoes'])}", ""] if r["acoes"] else []),
            "**Resposta:**",
            "",
            *[f"> {l}" for l in r["resposta"].splitlines()],
            "",
            f"**Verificação:** {'; '.join(r['falhas']) or 'ok'}",
            "",
        ]
    RELATORIO.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nTotal: {total_ok}/{len(resultados)} — relatório em {RELATORIO.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
