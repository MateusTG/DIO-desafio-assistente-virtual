import json
import unittest

from agente import Agente, carregar_perfil
from conhecimento import BaseConhecimento
from ferramentas import DEFINICOES, ESCRITA, Ferramentas
from integracoes import criar_integracoes


def novas_ferramentas(aprovador=None) -> Ferramentas:
    return Ferramentas(criar_integracoes(), BaseConhecimento(), carregar_perfil(), aprovador)


class TestBaseConhecimento(unittest.TestCase):
    def setUp(self):
        self.base = BaseConhecimento()

    def fonte(self, consulta: str) -> str:
        return self.base.buscar(consulta)[0][1].fonte

    def test_encontra_secao_certa(self):
        self.assertEqual(self.fonte("erro de cors no node"), "web.md > CORS")
        self.assertEqual(self.fonte("como fazer hash de senha em php"), "php.md > Segurança")
        self.assertEqual(self.fonte("async await c# deadlock"), "csharp.md > async/await")
        self.assertEqual(self.fonte("criar ambiente virtual python"), "python.md > Ambiente virtual e dependências")
        self.assertEqual(self.fonte("regras blocos de foco"), "produtividade.md > Regras para montar blocos de foco")

    def test_resultado_traz_fonte(self):
        self.assertIn("FONTE: php.md > Segurança", self.base.buscar_formatado("password_hash"))

    def test_sem_resultado(self):
        self.assertIn("Nenhum trecho", self.base.buscar_formatado("zzzz qqqq"))


class TestDefinicoes(unittest.TestCase):
    def test_schemas_strict_validos(self):
        for d in DEFINICOES:
            esquema = d["input_schema"]
            self.assertFalse(esquema["additionalProperties"], d["name"])
            self.assertEqual(set(esquema["required"]), set(esquema["properties"]), d["name"])

    def test_escrita_marcada_na_descricao(self):
        for d in DEFINICOES:
            self.assertEqual(d["name"] in ESCRITA, d["description"].startswith("[ESCRITA"), d["name"])


class TestLeitura(unittest.TestCase):
    def setUp(self):
        self.f = novas_ferramentas()

    def test_semana_de_referencia_no_domingo_e_a_proxima(self):
        resultado, erro = self.f.executar("listar_eventos", {"data_inicio": "2026-10-14", "data_fim": "2026-10-14"})
        self.assertFalse(erro)
        titulos = [e["titulo"] for e in json.loads(resultado)]
        self.assertIn("Reunião com cliente — demo do painel", titulos)
        self.assertIn("Aula do bootcamp DIO", titulos)

    def test_periodo_vazio(self):
        resultado, _ = self.f.executar("listar_eventos", {"data_inicio": "2026-10-17", "data_fim": "2026-10-18"})
        self.assertEqual(resultado, "Nenhum evento nesse período.")

    def test_tarefas_com_prazo_convertido(self):
        tarefas = json.loads(self.f.executar("listar_tarefas", {"fonte": "todas"})[0])
        eng142 = next(i for i in tarefas["linear"] if i["id"] == "ENG-142")
        self.assertEqual(eng142["prazo"], "2026-10-13 (terça)")
        self.assertEqual(len(tarefas["trello"]), 5)

    def test_parametro_invalido_vira_erro_para_o_modelo(self):
        resultado, erro = self.f.executar("listar_eventos", {"data_inicio": "amanhã", "data_fim": "2026-10-18"})
        self.assertTrue(erro)
        self.assertIn("Erro nos parâmetros", resultado)

    def test_ferramenta_desconhecida(self):
        self.assertTrue(self.f.executar("apagar_tudo", {})[1])


class TestEscritaComAprovacao(unittest.TestCase):
    EVENTO = {"titulo": "Foco: ENG-142", "inicio": "2026-10-12T10:00", "fim": "2026-10-12T11:30",
              "descricao": None, "lembrete_minutos": None}

    def test_escrita_fica_pendente_e_nao_executa(self):
        f = novas_ferramentas()
        resultado, erro = f.executar("criar_evento", self.EVENTO)
        self.assertFalse(erro)
        self.assertIn("AGUARDANDO APROVAÇÃO", resultado)
        self.assertEqual(len(f.pendentes), 1)
        self.assertEqual(f.pendentes[0].entrada["lembrete_minutos"], 15)  # padrão do perfil
        eventos = f.executar("listar_eventos", {"data_inicio": "2026-10-12", "data_fim": "2026-10-12"})[0]
        self.assertNotIn("Foco: ENG-142", eventos)

    def test_aprovar_executa_e_avisa_o_agente(self):
        f = novas_ferramentas()
        f.executar("criar_evento", self.EVENTO)
        acao = f.decidir(1, aprovar=True)
        self.assertEqual(acao.status, "executada")
        eventos = f.executar("listar_eventos", {"data_inicio": "2026-10-12", "data_fim": "2026-10-12"})[0]
        self.assertIn("Foco: ENG-142", eventos)
        self.assertIn("APROVOU a ação #1", f.consumir_notas())
        self.assertEqual(f.consumir_notas(), "")

    def test_recusar_nao_executa(self):
        f = novas_ferramentas()
        f.executar("enviar_mensagem_slack", {"canal": "#time-eng", "texto": "oi"})
        self.assertEqual(f.decidir(1, aprovar=False).status, "recusada")
        self.assertIn("RECUSOU", f.consumir_notas())

    def test_aprovador_imediato(self):
        f = novas_ferramentas(aprovador=lambda acao: False)
        resultado, _ = f.executar("criar_issue_linear", {"titulo": "x", "descricao": None, "prioridade": 3})
        self.assertIn("RECUSADA", resultado)
        f = novas_ferramentas(aprovador=lambda acao: True)
        resultado, _ = f.executar("criar_issue_linear", {"titulo": "x", "descricao": None, "prioridade": 3})
        self.assertIn("aprovada", resultado)

    def test_conflito_de_horario_e_recusado(self):
        f = novas_ferramentas()
        conflito = {**self.EVENTO, "inicio": "2026-10-12T09:00", "fim": "2026-10-12T10:00"}  # daily 09:30
        resultado, erro = f.executar("criar_evento", conflito)
        self.assertTrue(erro)
        self.assertIn("Daily do time", resultado)
        self.assertEqual(f.pendentes, [])

    def test_conflito_com_outra_proposta_pendente(self):
        f = novas_ferramentas()
        f.executar("criar_evento", self.EVENTO)
        _, erro = f.executar("criar_evento", {**self.EVENTO, "titulo": "Outro"})
        self.assertTrue(erro)

    def test_evento_no_passado_e_recusado(self):
        f = novas_ferramentas()
        resultado, erro = f.executar("criar_evento", {**self.EVENTO, "inicio": "2026-10-01T10:00",
                                                      "fim": "2026-10-01T11:00"})
        self.assertTrue(erro)
        self.assertIn("já passou", resultado)

    def test_lista_trello_inexistente(self):
        f = novas_ferramentas(aprovador=lambda acao: True)
        resultado, erro = f.executar("criar_cartao_trello", {"titulo": "x", "lista": "Backlog",
                                                             "descricao": None, "prazo": None})
        self.assertTrue(erro)
        self.assertIn("não existe", resultado)


class TestPrompt(unittest.TestCase):
    def test_contexto_no_system_prompt(self):
        prompt = Agente().system_prompt
        self.assertIn("domingo, 2026-10-11", prompt)
        self.assertIn("2026-10-12 (segunda) a 2026-10-18 (domingo)", prompt)
        self.assertIn("Google Agenda: simulado", prompt)
        self.assertIn('"lembrete_padrao_minutos": 15', prompt)


if __name__ == "__main__":
    unittest.main()
