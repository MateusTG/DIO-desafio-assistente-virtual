"""Planejamento semanal sem interface: ideal para rodar automaticamente todo domingo.

Gera o plano da semana em saida/plano_semana_AAAA-MM-DD.md. Por padrão, os eventos
propostos ficam só listados no arquivo (nada é criado). Com --aprovar-tudo, os
eventos e alertas são criados de fato (no Google Agenda, se JARVIS_MODO=real).

Uso:  python src/planejamento_semanal.py [--aprovar-tudo]
Cron (domingo, 19h):
  0 19 * * 0  cd /caminho/do/projeto && .venv/bin/python src/planejamento_semanal.py
"""

import argparse

import config
from agente import Agente


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--aprovar-tudo", action="store_true", help="cria os eventos propostos sem perguntar")
    args = parser.parse_args()

    agente = Agente(aprovador=(lambda acao: True) if args.aprovar_tudo else None)
    pedido = ("Planeje minha semana: revise agenda, tarefas e mensagens e proponha os blocos de foco com alertas. "
              "Esta é uma execução automática: não ofereça Notion nem Slack, apenas apresente o plano.")
    textos = []
    for evento in agente.responder(pedido):
        if evento.tipo == "ferramenta":
            print(f"🔧 {evento.conteudo}")
        elif evento.tipo == "aviso" and not textos:
            raise SystemExit(evento.conteudo)  # falha do LLM: não grava um plano vazio
        else:
            textos.append(evento.conteudo)

    hoje = config.agora().date().isoformat()
    linhas = [f"# Plano da semana — gerado em {hoje}", "", *textos, "", "## Ações propostas", ""]
    status = {"pendente": "⏳ pendente (não criada)", "executada": "✅ criada", "recusada": "🚫 recusada", "erro": "❌ erro"}
    linhas += [f"- {status[a.status]}: {a.resumo}" for a in agente.ferramentas.acoes] or ["- Nenhuma."]

    config.SAIDA_DIR.mkdir(exist_ok=True)
    arquivo = config.SAIDA_DIR / f"plano_semana_{hoje}.md"
    arquivo.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(textos))
    print(f"\nPlano salvo em {arquivo.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
