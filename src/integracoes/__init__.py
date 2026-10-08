"""Escolhe, para cada ferramenta, a integração real (se configurada) ou a simulada."""

from dataclasses import dataclass

import config
from integracoes import mock


@dataclass
class Integracoes:
    agenda: object
    trello: object
    linear: object
    slack: object
    notion: object
    dados_simulados: mock.DadosSimulados

    def resumo(self) -> dict[str, str]:
        return {i.nome: i.modo for i in (self.agenda, self.trello, self.linear, self.slack, self.notion)}


def criar_integracoes() -> Integracoes:
    dados = mock.DadosSimulados()
    real = config.JARVIS_MODO == "real"

    agenda = mock.AgendaSimulada(dados)
    trello = mock.TrelloSimulado(dados)
    linear = mock.LinearSimulado(dados)
    slack = mock.SlackSimulado(dados)
    notion = mock.NotionSimulado(dados)

    if real:
        from integracoes import reais

        if config.GOOGLE_CREDENCIAIS.exists() or config.GOOGLE_TOKEN.exists():
            agenda = reais.GoogleAgenda()
        if config.TRELLO_KEY and config.TRELLO_TOKEN and config.TRELLO_BOARD_ID:
            trello = reais.Trello()
        if config.LINEAR_API_KEY:
            linear = reais.Linear()
        if config.SLACK_BOT_TOKEN:
            slack = reais.Slack()
        if config.NOTION_TOKEN:
            notion = reais.Notion()

    return Integracoes(agenda, trello, linear, slack, notion, dados)
