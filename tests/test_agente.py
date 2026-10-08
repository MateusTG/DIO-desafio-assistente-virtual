"""Testa o loop do agente com respostas roteirizadas (sem chamar nenhum LLM de verdade)."""

import unittest
from types import SimpleNamespace
from unittest import mock

import anthropic

import agente as modulo_agente
import config
from agente import Agente
from avaliacao import avaliar, verificar_eventos_perfil


def texto(t):
    return SimpleNamespace(type="text", text=t)


def chamada(nome, entrada, id_="tu1"):
    return SimpleNamespace(type="tool_use", id=id_, name=nome, input=entrada)


class ClaudeFalso:
    """Imita client.beta.messages.create devolvendo respostas pré-definidas."""

    def __init__(self, respostas):
        self.respostas, self.pedidos = list(respostas), []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.pedidos.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.respostas.pop(0)


class TestLoopClaude(unittest.TestCase):
    def rodar(self, respostas, pergunta="O que tenho na quarta?"):
        falso = ClaudeFalso(respostas)
        with mock.patch.object(config, "LLM_PROVIDER", "anthropic"), \
                mock.patch.object(anthropic, "Anthropic", return_value=falso):
            ag = Agente()
            eventos = list(ag.responder(pergunta))
        return ag, eventos, falso

    def test_executa_ferramenta_e_devolve_resultado(self):
        ag, eventos, falso = self.rodar([
            SimpleNamespace(stop_reason="tool_use", content=[
                texto("Vou verificar."),
                chamada("listar_eventos", {"data_inicio": "2026-10-14", "data_fim": "2026-10-14"})]),
            SimpleNamespace(stop_reason="end_turn", content=[texto("Às 15:00 você tem a demo do painel.")]),
        ])
        self.assertEqual([e.tipo for e in eventos], ["texto", "ferramenta", "texto"])
        segundo = falso.pedidos[1]
        resultado = segundo["messages"][-1]["content"][0]
        self.assertEqual(resultado["tool_use_id"], "tu1")
        self.assertIn("demo do painel", resultado["content"])
        self.assertFalse(resultado["is_error"])
        # Parâmetros da requisição
        self.assertEqual(segundo["model"], config.ANTHROPIC_MODEL)
        self.assertEqual(segundo["fallbacks"], "default")
        self.assertTrue(all(t["strict"] for t in segundo["tools"]))
        self.assertEqual(len(ag.mensagens), 4)  # user, assistant(tool_use), user(tool_result), assistant

    def test_recusa_descarta_o_turno(self):
        ag, eventos, _ = self.rodar([SimpleNamespace(stop_reason="refusal", content=[])])
        self.assertEqual(eventos[0].tipo, "aviso")
        self.assertEqual(ag.mensagens, [])

    def test_notas_de_aprovacao_vao_na_proxima_mensagem(self):
        falso = ClaudeFalso([
            SimpleNamespace(stop_reason="tool_use", content=[chamada("enviar_mensagem_slack",
                                                                      {"canal": "#time-eng", "texto": "oi"})]),
            SimpleNamespace(stop_reason="end_turn", content=[texto("Aguardando sua aprovação.")]),
            SimpleNamespace(stop_reason="end_turn", content=[texto("Mensagem enviada.")]),
        ])
        with mock.patch.object(config, "LLM_PROVIDER", "anthropic"), \
                mock.patch.object(anthropic, "Anthropic", return_value=falso):
            ag = Agente()
            list(ag.responder("Avisa o time"))
            self.assertEqual(len(ag.pendentes), 1)
            ag.ferramentas.decidir(1, aprovar=True)
            list(ag.responder("Obrigado"))
        ultima = falso.pedidos[-1]["messages"][-1]["content"]
        self.assertIn("APROVOU a ação #1", ultima)
        self.assertTrue(ultima.endswith("Obrigado"))

    def test_sem_credencial_mostra_aviso(self):
        with mock.patch.object(config, "LLM_PROVIDER", "anthropic"), \
                mock.patch.object(anthropic, "Anthropic", side_effect=TypeError("Could not resolve authentication method")):
            ag = Agente()
            eventos = list(ag.responder("oi"))
        self.assertIn("Nenhuma chave", eventos[0].conteudo)
        self.assertEqual(ag.mensagens, [])


class TestLoopOllama(unittest.TestCase):
    def test_chamada_de_ferramenta(self):
        respostas = iter([
            {"message": {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "listar_tarefas", "arguments": {"fonte": "linear"}}}]}},
            {"message": {"role": "assistant", "content": "A ENG-142 é a mais urgente."}},
        ])
        corpos = []

        def post(url, json, timeout):
            corpos.append(json)
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: next(respostas))

        with mock.patch.object(config, "LLM_PROVIDER", "ollama"), mock.patch.object(modulo_agente.requests, "post", post):
            ag = Agente()
            resposta = ag.responder_texto("Qual a issue mais urgente?")
        self.assertEqual(resposta, "A ENG-142 é a mais urgente.")
        self.assertEqual(corpos[1]["messages"][-1]["role"], "tool")
        self.assertIn("ENG-142", corpos[1]["messages"][-1]["content"])


class TestAvaliacao(unittest.TestCase):
    def setUp(self):
        self.ag = Agente()

    def propor(self, inicio, fim):
        self.ag.ferramentas.executar("criar_evento", {"titulo": "Foco", "inicio": inicio, "fim": fim,
                                                      "descricao": None, "lembrete_minutos": None})

    def test_evento_coerente_com_perfil(self):
        self.propor("2026-10-12T10:00", "2026-10-12T11:30")
        self.assertEqual(verificar_eventos_perfil(self.ag.ferramentas.acoes, self.ag.perfil), [])

    def test_evento_incoerente(self):
        self.propor("2026-10-17T10:00", "2026-10-17T11:00")  # sábado
        self.propor("2026-10-13T11:30", "2026-10-13T12:30")  # almoço
        problemas = verificar_eventos_perfil(self.ag.ferramentas.acoes, self.ag.perfil)
        self.assertTrue(any("dias de expediente" in p for p in problemas))
        self.assertTrue(any("almoço" in p for p in problemas))

    def test_avaliar_ignora_acentos_e_checa_ferramentas(self):
        caso = {"deve_conter_algum": ["não encontrei"], "ferramentas_esperadas": ["listar_eventos"]}
        self.assertEqual(avaliar(caso, "NAO ENCONTREI nada", ["listar_eventos"], [], {}), [])
        self.assertTrue(avaliar(caso, "não encontrei", [], [], {}))


if __name__ == "__main__":
    unittest.main()
