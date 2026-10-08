"""Ferramentas que o Jarvis pode usar e a fila de aprovação das ações de escrita.

Ferramentas de LEITURA executam na hora. Ferramentas de ESCRITA (criar evento,
cartão, issue, página ou enviar mensagem) nunca executam direto: viram uma Acao
pendente que só roda quando a pessoa aprova (botão na interface ou "s" no terminal).
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import config
from conhecimento import BaseConhecimento
from integracoes import Integracoes


def _opcional(tipo: str, descricao: str) -> dict:
    return {"anyOf": [{"type": tipo}, {"type": "null"}], "description": descricao}


def _ferramenta(nome: str, descricao: str, propriedades: dict) -> dict:
    return {
        "name": nome,
        "description": descricao,
        "input_schema": {"type": "object", "properties": propriedades,
                         "required": list(propriedades), "additionalProperties": False},
    }


DEFINICOES = [
    _ferramenta(
        "consultar_base_conhecimento",
        "Busca na base de conhecimento de programação (web/HTML/CSS/JS, Python, Node.js, PHP, C#, boas práticas, "
        "produtividade e planejamento semanal). Use ANTES de responder dúvidas técnicas. Retorna trechos com a FONTE.",
        {"consulta": {"type": "string", "description": "Palavras-chave da dúvida, ex.: 'erro de CORS no node'"}},
    ),
    _ferramenta(
        "listar_eventos",
        "Lista os eventos do Google Agenda entre duas datas (inclusive).",
        {"data_inicio": {"type": "string", "description": "AAAA-MM-DD"},
         "data_fim": {"type": "string", "description": "AAAA-MM-DD (inclusive)"}},
    ),
    _ferramenta(
        "criar_evento",
        "[ESCRITA - requer aprovação] Cria um evento no Google Agenda com alerta (lembrete popup). "
        "Recusa automaticamente se houver conflito de horário.",
        {"titulo": {"type": "string", "description": "Título acionável, ex.: 'Foco: corrigir CORS (ENG-142)'"},
         "inicio": {"type": "string", "description": "AAAA-MM-DDTHH:MM no fuso do usuário"},
         "fim": {"type": "string", "description": "AAAA-MM-DDTHH:MM no fuso do usuário"},
         "descricao": _opcional("string", "Detalhes do evento"),
         "lembrete_minutos": _opcional("integer", "Minutos antes para o alerta; null usa o padrão do perfil")},
    ),
    _ferramenta(
        "listar_tarefas",
        "Lista tarefas abertas do Trello (cartões) e/ou do Linear (issues), com prazo e prioridade.",
        {"fonte": {"type": "string", "enum": ["trello", "linear", "todas"]}},
    ),
    _ferramenta(
        "criar_cartao_trello",
        "[ESCRITA - requer aprovação] Cria um cartão no quadro do Trello.",
        {"titulo": {"type": "string"},
         "lista": {"type": "string", "description": "Nome exato da lista, ex.: 'A fazer'"},
         "descricao": _opcional("string", "Descrição do cartão"),
         "prazo": _opcional("string", "Prazo AAAA-MM-DD")},
    ),
    _ferramenta(
        "criar_issue_linear",
        "[ESCRITA - requer aprovação] Cria uma issue no Linear.",
        {"titulo": {"type": "string"},
         "descricao": _opcional("string", "Contexto e critério de aceite"),
         "prioridade": {"type": "integer", "enum": [0, 1, 2, 3, 4],
                        "description": "0 sem prioridade, 1 urgente, 2 alta, 3 média, 4 baixa"}},
    ),
    _ferramenta(
        "listar_mensagens_slack",
        "Lista as mensagens recentes do Slack em que o usuário foi mencionado ou do canal configurado.",
        {},
    ),
    _ferramenta(
        "enviar_mensagem_slack",
        "[ESCRITA - requer aprovação] Envia uma mensagem no Slack.",
        {"canal": {"type": "string", "description": "Canal (ex.: '#time-eng') ou ID"},
         "texto": {"type": "string"}},
    ),
    _ferramenta(
        "buscar_notion",
        "Busca páginas no Notion pelo título/conteúdo.",
        {"consulta": {"type": "string"}},
    ),
    _ferramenta(
        "criar_pagina_notion",
        "[ESCRITA - requer aprovação] Cria uma página no Notion (ex.: o plano da semana).",
        {"titulo": {"type": "string"}, "conteudo": {"type": "string", "description": "Texto; uma linha por parágrafo"}},
    ),
]

ESCRITA = {"criar_evento", "criar_cartao_trello", "criar_issue_linear", "enviar_mensagem_slack", "criar_pagina_notion"}


@dataclass
class Acao:
    id: int
    ferramenta: str
    entrada: dict
    resumo: str
    status: str = "pendente"  # pendente | executada | recusada | erro
    resultado: str = ""


def _data_hora(texto: str) -> datetime:
    dt = datetime.fromisoformat(texto)
    return dt if dt.tzinfo else dt.replace(tzinfo=config.FUSO)


def _json(dados) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=1)


@dataclass
class Ferramentas:
    integracoes: Integracoes
    conhecimento: BaseConhecimento
    perfil: dict
    # Se definido (terminal/avaliação), decide na hora; se None (Streamlit), a ação fica na fila.
    aprovador: Callable[[Acao], bool] | None = None
    acoes: list[Acao] = field(default_factory=list)
    notas_para_o_agente: list[str] = field(default_factory=list)
    chamadas: list[str] = field(default_factory=list)  # histórico de nomes (usado na avaliação)

    @property
    def pendentes(self) -> list[Acao]:
        return [a for a in self.acoes if a.status == "pendente"]

    # ------------------------------------------------------------------ entrada
    def executar(self, nome: str, entrada: dict) -> tuple[str, bool]:
        """Retorna (texto do resultado, é_erro)."""
        self.chamadas.append(nome)
        try:
            if nome in ESCRITA:
                return self._propor(nome, entrada)
            metodo = getattr(self, f"_{nome}", None)
            if metodo is None:
                return f"Ferramenta desconhecida: {nome}", True
            return metodo(**entrada), False
        except (ValueError, TypeError, KeyError) as e:
            return f"Erro nos parâmetros: {e}", True
        except Exception as e:  # falha da API externa: o agente deve avisar a pessoa
            return f"Falha ao acessar a integração: {e}", True

    # ------------------------------------------------------------------ leitura
    def _consultar_base_conhecimento(self, consulta: str) -> str:
        return self.conhecimento.buscar_formatado(consulta)

    def _listar_eventos(self, data_inicio: str, data_fim: str) -> str:
        inicio = datetime.combine(date.fromisoformat(data_inicio), time.min, config.FUSO)
        fim = datetime.combine(date.fromisoformat(data_fim) + timedelta(days=1), time.min, config.FUSO)
        eventos = self.integracoes.agenda.listar_eventos(inicio, fim)
        return _json(eventos) if eventos else "Nenhum evento nesse período."

    def _listar_tarefas(self, fonte: str) -> str:
        resultado = {}
        if fonte in ("trello", "todas"):
            resultado["trello"] = self.integracoes.trello.listar_cartoes()
        if fonte in ("linear", "todas"):
            resultado["linear"] = self.integracoes.linear.listar_issues()
        return _json(resultado)

    def _listar_mensagens_slack(self) -> str:
        return _json(self.integracoes.slack.listar_mensagens())

    def _buscar_notion(self, consulta: str) -> str:
        paginas = self.integracoes.notion.buscar(consulta)
        return _json(paginas) if paginas else "Nenhuma página encontrada no Notion."

    # ------------------------------------------------------------------ escrita
    def _propor(self, nome: str, entrada: dict) -> tuple[str, bool]:
        entrada = self._validar(nome, dict(entrada))
        acao = Acao(len(self.acoes) + 1, nome, entrada, self._resumo(nome, entrada))
        self.acoes.append(acao)
        if self.aprovador is None:
            return (f"Ação #{acao.id} registrada e AGUARDANDO APROVAÇÃO do usuário na interface "
                    f"({acao.resumo}). Ela ainda NÃO foi executada."), False
        if self.aprovador(acao):
            self._efetivar(acao)
            return f"Ação #{acao.id} aprovada pelo usuário. Resultado: {acao.resultado}", acao.status == "erro"
        acao.status = "recusada"
        return f"Ação #{acao.id} RECUSADA pelo usuário. Não foi executada.", False

    def _validar(self, nome: str, e: dict) -> dict:
        if nome == "criar_evento":
            inicio, fim = _data_hora(e["inicio"]), _data_hora(e["fim"])
            if fim <= inicio:
                raise ValueError("o fim do evento precisa ser depois do início")
            if inicio < config.agora():
                raise ValueError(f"{e['inicio']} já passou; agende a partir de agora")
            # Eventos de dia inteiro (só data, sem "T") não bloqueiam horário.
            conflitos = [ev for ev in self.integracoes.agenda.listar_eventos(inicio - timedelta(hours=12), fim)
                         if "T" in ev["inicio"] and _data_hora(ev["inicio"]) < fim and _data_hora(ev["fim"]) > inicio]
            # Considera também ações já propostas e ainda pendentes nesta conversa.
            conflitos += [{"titulo": a.entrada["titulo"], "inicio": a.entrada["inicio"], "fim": a.entrada["fim"]}
                          for a in self.pendentes if a.ferramenta == "criar_evento"
                          and _data_hora(a.entrada["inicio"]) < fim and _data_hora(a.entrada["fim"]) > inicio]
            if conflitos:
                raise ValueError(f"conflito de horário com: {_json(conflitos)}. Escolha outro horário.")
            if e.get("lembrete_minutos") is None:
                e["lembrete_minutos"] = self.perfil.get("lembrete_padrao_minutos", 15)
        if nome == "criar_issue_linear" and e["prioridade"] not in range(5):
            raise ValueError("prioridade deve ser de 0 a 4")
        return e

    @staticmethod
    def _resumo(nome: str, e: dict) -> str:
        if nome == "criar_evento":
            return f"📅 {e['titulo']} — {e['inicio'].replace('T', ' ')} até {e['fim'][-5:]} (alerta {e['lembrete_minutos']} min antes)"
        if nome == "criar_cartao_trello":
            return f"🗂️ Trello: '{e['titulo']}' na lista {e['lista']}" + (f", prazo {e['prazo']}" if e.get("prazo") else "")
        if nome == "criar_issue_linear":
            return f"📌 Linear: '{e['titulo']}' (prioridade {e['prioridade']})"
        if nome == "enviar_mensagem_slack":
            return f"💬 Slack {e['canal']}: {e['texto'][:80]}"
        return f"📝 Notion: página '{e['titulo']}'"

    def _efetivar(self, acao: Acao) -> None:
        e, i = acao.entrada, self.integracoes
        try:
            if acao.ferramenta == "criar_evento":
                r = i.agenda.criar_evento(e["titulo"], _data_hora(e["inicio"]), _data_hora(e["fim"]),
                                          e.get("descricao"), e["lembrete_minutos"])
            elif acao.ferramenta == "criar_cartao_trello":
                r = i.trello.criar_cartao(e["titulo"], e["lista"], e.get("descricao"), e.get("prazo"))
            elif acao.ferramenta == "criar_issue_linear":
                r = i.linear.criar_issue(e["titulo"], e.get("descricao"), e["prioridade"])
            elif acao.ferramenta == "enviar_mensagem_slack":
                r = i.slack.enviar_mensagem(e["canal"], e["texto"])
            else:
                r = i.notion.criar_pagina(e["titulo"], e["conteudo"])
            acao.status, acao.resultado = "executada", _json(r)
        except Exception as erro:
            acao.status, acao.resultado = "erro", f"falhou: {erro}"

    # ----------------------------------------------------- aprovação pela interface
    def decidir(self, acao_id: int, aprovar: bool) -> Acao:
        acao = next(a for a in self.acoes if a.id == acao_id and a.status == "pendente")
        if aprovar:
            self._efetivar(acao)
            nota = f"[Sistema] O usuário APROVOU a ação #{acao.id} ({acao.resumo}). Status: {acao.status}. {acao.resultado}"
        else:
            acao.status = "recusada"
            nota = f"[Sistema] O usuário RECUSOU a ação #{acao.id} ({acao.resumo}). Ela não foi executada."
        self.notas_para_o_agente.append(nota)
        return acao

    def consumir_notas(self) -> str:
        notas, self.notas_para_o_agente = "\n".join(self.notas_para_o_agente), []
        return notas
