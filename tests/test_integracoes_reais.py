"""Confere as requisições das integrações reais com respostas HTTP simuladas (sem rede)."""

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import config
from integracoes import reais


def resposta(dados):
    return SimpleNamespace(raise_for_status=lambda: None, json=lambda: dados)


class TestTrello(unittest.TestCase):
    def test_criar_cartao_resolve_lista_pelo_nome(self):
        get = mock.Mock(return_value=resposta([{"name": "A fazer", "id": "L1"}]))
        post = mock.Mock(return_value=resposta({"id": "C1", "name": "Novo", "shortUrl": "https://trello.com/c/x"}))
        with mock.patch.object(reais.requests, "get", get), mock.patch.object(reais.requests, "post", post):
            r = reais.Trello().criar_cartao("Novo", "A fazer", None, "2026-10-15")
        params = post.call_args.kwargs["params"]
        self.assertEqual((params["idList"], params["name"], params["due"]), ("L1", "Novo", "2026-10-15"))
        self.assertEqual(r["link"], "https://trello.com/c/x")

    def test_lista_inexistente(self):
        with mock.patch.object(reais.requests, "get", return_value=resposta([{"name": "A fazer", "id": "L1"}])):
            with self.assertRaises(ValueError):
                reais.Trello().criar_cartao("Novo", "Backlog", None, None)


class TestSlack(unittest.TestCase):
    def test_erro_da_api_vira_excecao(self):
        with mock.patch.object(reais.requests, "post", return_value=resposta({"ok": False, "error": "not_in_channel"})):
            with self.assertRaisesRegex(RuntimeError, "not_in_channel"):
                reais.Slack().enviar_mensagem("#geral", "oi")

    def test_listar_converte_timestamp(self):
        dados = {"ok": True, "messages": [{"user": "U1", "ts": "1760000000.000100", "text": "oi"}]}
        with mock.patch.object(reais.requests, "get", return_value=resposta(dados)):
            msgs = reais.Slack().listar_mensagens()
        self.assertEqual(msgs[0]["texto"], "oi")
        self.assertTrue(msgs[0]["data"].startswith("2025-10-"))


class TestLinear(unittest.TestCase):
    def test_filtra_issues_concluidas(self):
        nos = [{"identifier": "ENG-1", "title": "a", "priority": 1, "estimate": None, "dueDate": None, "url": "u",
                "state": {"name": "Todo", "type": "unstarted"}},
               {"identifier": "ENG-2", "title": "b", "priority": 2, "estimate": None, "dueDate": None, "url": "u",
                "state": {"name": "Done", "type": "completed"}}]
        dados = {"data": {"viewer": {"assignedIssues": {"nodes": nos}}}}
        with mock.patch.object(reais.requests, "post", return_value=resposta(dados)):
            issues = reais.Linear().listar_issues()
        self.assertEqual([i["id"] for i in issues], ["ENG-1"])

    def test_erro_graphql(self):
        with mock.patch.object(reais.requests, "post", return_value=resposta({"errors": [{"message": "teamId inválido"}]})):
            with self.assertRaisesRegex(RuntimeError, "teamId"):
                reais.Linear().criar_issue("x", None, 2)


class TestNotion(unittest.TestCase):
    def test_criar_pagina_fatia_texto_longo(self):
        post = mock.Mock(return_value=resposta({"id": "P1", "url": "https://notion.so/p1"}))
        with mock.patch.object(reais.requests, "post", post), mock.patch.object(config, "NOTION_PAGINA_PAI_ID", "PAI"):
            reais.Notion().criar_pagina("Plano", "linha curta\n\n" + "x" * 4500)
        corpo = post.call_args.kwargs["json"]
        self.assertEqual(corpo["parent"], {"page_id": "PAI"})
        self.assertEqual(len(corpo["children"]), 4)  # 1 curta + 4500 caracteres em 3 blocos de até 2000
        self.assertTrue(all(len(b["paragraph"]["rich_text"][0]["text"]["content"]) <= 2000 for b in corpo["children"]))

    def test_titulo_da_pagina(self):
        pagina = {"properties": {"Name": {"type": "title", "title": [{"plain_text": "Roadmap"}]}}}
        self.assertEqual(reais.Notion._titulo(pagina), "Roadmap")


class TestGoogleAgenda(unittest.TestCase):
    def test_evento_com_alerta_popup(self):
        agenda = reais.GoogleAgenda.__new__(reais.GoogleAgenda)  # pula o OAuth
        agenda.servico = mock.MagicMock()
        agenda.servico.events().insert().execute.return_value = {"id": "E1", "htmlLink": "https://calendar/e1"}
        inicio = datetime(2026, 10, 12, 10, tzinfo=config.FUSO)
        r = agenda.criar_evento("Foco", inicio, inicio.replace(hour=11), None, 15)
        corpo = agenda.servico.events().insert.call_args.kwargs["body"]
        self.assertEqual(corpo["reminders"], {"useDefault": False, "overrides": [{"method": "popup", "minutes": 15}]})
        self.assertEqual(corpo["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(r["link"], "https://calendar/e1")


if __name__ == "__main__":
    unittest.main()
