"""Integrações simuladas a partir de data/mock/*.json.

As datas nos arquivos são relativas (dia_semana 0 = segunda) e são convertidas
para a "semana de referência": a semana atual, ou a próxima se hoje for domingo
(que é quando o planejamento semanal acontece). Assim a demo nunca fica velha.

Ações de escrita alteram só a memória e são registradas em saida/acoes_simuladas.jsonl.
"""

import json
from datetime import date, datetime, time, timedelta

import config

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def semana_referencia(hoje: datetime) -> date:
    """Segunda-feira da semana de referência."""
    amanha = (hoje + timedelta(days=1)).date()
    return amanha - timedelta(days=amanha.weekday())


def _ler(nome: str) -> dict:
    with open(config.DATA_DIR / "mock" / nome, encoding="utf-8") as f:
        return json.load(f)


def _registrar(acao: str, dados: dict) -> None:
    config.SAIDA_DIR.mkdir(exist_ok=True)
    with open(config.SAIDA_DIR / "acoes_simuladas.jsonl", "a", encoding="utf-8") as f:
        registro = {"quando": config.agora().isoformat(timespec="seconds"), "acao": acao, **dados}
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


class DadosSimulados:
    """Carrega os JSON uma vez e converte dias relativos em datas reais."""

    def __init__(self, hoje: datetime | None = None):
        self.hoje = hoje or config.agora()
        self.segunda = semana_referencia(self.hoje)
        self.eventos = [self._evento(e) for e in _ler("agenda.json")["eventos"]]
        trello = _ler("trello.json")
        self.trello_listas = trello["listas"]
        self.cartoes = [self._com_prazo(c) for c in trello["cartoes"]]
        self.issues = [self._com_prazo(i) for i in _ler("linear.json")["issues"]]
        self.mensagens = [self._mensagem(m) for m in _ler("slack.json")["mensagens"]]
        self.paginas = _ler("notion.json")["paginas"]

    def data(self, dia_semana: int) -> date:
        return self.segunda + timedelta(days=dia_semana)

    def _evento(self, e: dict) -> dict:
        dia = self.data(e["dia_semana"])
        inicio = datetime.combine(dia, time.fromisoformat(e["inicio"]), config.FUSO)
        fim = datetime.combine(dia, time.fromisoformat(e["fim"]), config.FUSO)
        return {"id": e["id"], "titulo": e["titulo"], "inicio": inicio.isoformat(), "fim": fim.isoformat(),
                "dia_semana": DIAS[dia.weekday()], "lembrete_minutos": None}

    def _com_prazo(self, item: dict) -> dict:
        d = item.pop("prazo_dia_semana", None)
        item["prazo"] = f"{self.data(d).isoformat()} ({DIAS[d]})" if d is not None else None
        return item

    def _mensagem(self, m: dict) -> dict:
        dia = self.data(m.pop("dia_semana"))
        m["data"] = f"{dia.isoformat()} {m.pop('hora')} ({DIAS[dia.weekday()]})"
        return m


class AgendaSimulada:
    nome, modo = "Google Agenda", "simulado"

    def __init__(self, dados: DadosSimulados):
        self.dados = dados

    def listar_eventos(self, inicio: datetime, fim: datetime) -> list[dict]:
        eventos = [e for e in self.dados.eventos
                   if inicio <= datetime.fromisoformat(e["inicio"]) < fim]
        return sorted(eventos, key=lambda e: e["inicio"])

    def criar_evento(self, titulo: str, inicio: datetime, fim: datetime, descricao: str | None,
                     lembrete_minutos: int) -> dict:
        evento = {"id": f"ev-novo-{len(self.dados.eventos) + 1}", "titulo": titulo, "inicio": inicio.isoformat(),
                  "fim": fim.isoformat(), "dia_semana": DIAS[inicio.weekday()], "descricao": descricao,
                  "lembrete_minutos": lembrete_minutos}
        self.dados.eventos.append(evento)
        _registrar("criar_evento", evento)
        return evento


class TrelloSimulado:
    nome, modo = "Trello", "simulado"

    def __init__(self, dados: DadosSimulados):
        self.dados = dados

    def listar_cartoes(self) -> list[dict]:
        return [c for c in self.dados.cartoes if c["lista"] != "Feito"]

    def criar_cartao(self, titulo: str, lista: str, descricao: str | None, prazo: str | None) -> dict:
        if lista not in self.dados.trello_listas:
            raise ValueError(f"Lista '{lista}' não existe. Listas disponíveis: {self.dados.trello_listas}")
        cartao = {"id": f"tr-novo-{len(self.dados.cartoes) + 1}", "titulo": titulo, "lista": lista,
                  "descricao": descricao, "prazo": prazo, "etiquetas": []}
        self.dados.cartoes.append(cartao)
        _registrar("criar_cartao_trello", cartao)
        return cartao


class LinearSimulado:
    nome, modo = "Linear", "simulado"

    def __init__(self, dados: DadosSimulados):
        self.dados = dados

    def listar_issues(self) -> list[dict]:
        return [i for i in self.dados.issues if i["estado"] not in {"Done", "Canceled"}]

    def criar_issue(self, titulo: str, descricao: str | None, prioridade: int) -> dict:
        numero = 160 + len(self.dados.issues)
        issue = {"id": f"ENG-{numero}", "titulo": titulo, "descricao": descricao, "estado": "Backlog",
                 "prioridade": prioridade, "estimativa_horas": None, "prazo": None}
        self.dados.issues.append(issue)
        _registrar("criar_issue_linear", issue)
        return issue


class SlackSimulado:
    nome, modo = "Slack", "simulado"

    def __init__(self, dados: DadosSimulados):
        self.dados = dados

    def listar_mensagens(self) -> list[dict]:
        return self.dados.mensagens

    def enviar_mensagem(self, canal: str, texto: str) -> dict:
        mensagem = {"canal": canal, "texto": texto, "status": "enviada (simulação)"}
        _registrar("enviar_mensagem_slack", mensagem)
        return mensagem


class NotionSimulado:
    nome, modo = "Notion", "simulado"

    def __init__(self, dados: DadosSimulados):
        self.dados = dados

    def buscar(self, consulta: str) -> list[dict]:
        termos = consulta.lower().split()
        if not termos:
            return self.dados.paginas
        return [p for p in self.dados.paginas
                if any(t in f"{p['titulo']} {p['conteudo']}".lower() for t in termos)]

    def criar_pagina(self, titulo: str, conteudo: str) -> dict:
        pagina = {"id": f"no-novo-{len(self.dados.paginas) + 1}", "titulo": titulo, "conteudo": conteudo}
        self.dados.paginas.append(pagina)
        _registrar("criar_pagina_notion", pagina)
        return pagina
