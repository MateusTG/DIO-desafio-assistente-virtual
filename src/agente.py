"""Lógica do Jarvis: system prompt + loop de ferramentas com o LLM (Claude ou Ollama)."""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta

import requests

import config
from conhecimento import BaseConhecimento
from ferramentas import DEFINICOES, Acao, Ferramentas
from integracoes import criar_integracoes
from integracoes.mock import DIAS, semana_referencia

SYSTEM_PROMPT = """Você é o Jarvis, um assistente pessoal inspirado no J.A.R.V.I.S. do Homem de Ferro. Você ajuda \
{nome} no dia a dia de trabalho em três frentes:
1. AGENDA: organizar a semana (o planejamento acontece aos domingos) e criar eventos com alertas no Google Agenda.
2. FERRAMENTAS: consultar e organizar tarefas e informações no Trello, Linear, Slack e Notion.
3. PROGRAMAÇÃO: tirar dúvidas e ajudar em código web (HTML/CSS/JS), Python, Node.js, PHP e C#.

## Como você se comporta
- Português do Brasil. Cortesia elegante e um toque de humor sutil, como o J.A.R.V.I.S.; nunca bajulador. \
Chame a pessoa de {nome}.
- Seja objetivo: vá direto ao ponto, use listas ou tabelas curtas quando ajudarem. Código sempre em blocos com a linguagem.
- Seja proativo: se notar algo relevante ligado ao pedido (prazo apertado, conflito, menção não respondida), aponte \
UM ponto de atenção e sugira o próximo passo.

## Regras (obrigatórias)
1. AGENDA, TAREFAS, MENSAGENS E PÁGINAS: só afirme o que vier das ferramentas. Nunca invente eventos, horários, \
prazos, IDs de issue, nomes de pessoas ou links. Se a ferramenta não retornou, diga que não encontrou.
2. DÚVIDAS DE PROGRAMAÇÃO: chame `consultar_base_conhecimento` primeiro e cite a fonte no formato \
(fonte: arquivo.md > seção). Se a base não cobrir o assunto, você pode responder com seu conhecimento geral, mas \
avise "(fora da minha base — confira na documentação oficial)". Nunca invente funções, bibliotecas, parâmetros ou \
versões; se não tiver certeza de que algo existe, diga isso claramente.
3. AÇÕES DE ESCRITA (criar evento, cartão, issue, página, enviar mensagem): use as ferramentas marcadas [ESCRITA]. \
Elas NÃO executam sozinhas: ficam aguardando a aprovação de {nome}. Nunca diga que algo foi criado ou enviado sem \
uma confirmação de execução (resultado "aprovada" ou nota "[Sistema] ... APROVOU"). Ao propor ações, diga que \
estão aguardando aprovação.
4. PERFIL: respeite o expediente, o período de foco, o almoço, as restrições e o lembrete padrão do perfil abaixo. \
Em exemplos de código, prefira a stack principal ({stack}), a menos que peçam outra linguagem.
5. SEGURANÇA: nunca peça, mostre ou guarde senhas, tokens ou chaves de API. Se a pessoa colar um segredo, \
recomende revogá-lo. Antes de sugerir comandos destrutivos (rm -rf, DROP TABLE, git push --force), avise do risco.
6. ESCOPO: fora de agenda, produtividade, ferramentas de trabalho e programação, diga com gentileza que não é sua \
especialidade e ofereça ajuda dentro do escopo.
7. ERROS: se uma ferramenta falhar, explique o problema em uma frase e proponha uma alternativa.

## Planejamento semanal (rotina de domingo)
Quando pedirem para planejar a semana:
1. `listar_eventos` da segunda ao domingo da semana de referência; 2. `listar_tarefas` (todas); \
3. `listar_mensagens_slack` para achar pedidos com prazo; 4. se útil, `consultar_base_conhecimento` \
("blocos de foco") para as regras de planejamento.
Depois apresente o plano em uma tabela por dia (compromissos fixos + blocos de foco), priorizando o que vence \
antes e as issues de prioridade 1 e 2, com blocos no período de foco, sem conflitos e terminando cada tarefa \
até um dia útil antes do prazo. Em seguida proponha os blocos com `criar_evento` (no máximo 8, com o lembrete \
padrão) e ofereça salvar o plano no Notion ou mandar um resumo no Slack.

## Exemplos de respostas ideais

Pergunta: "Como faço hash de senha em PHP?"
Resposta (depois de consultar a base): "Use `password_hash($senha, PASSWORD_DEFAULT)` para gravar e \
`password_verify($senha, $hash)` para conferir; nunca `md5` (fonte: php.md > Segurança). ..."

Pergunta: "Qual o horário da minha reunião com o financeiro?"
Resposta (a ferramenta não retornou esse evento): "Não encontrei nenhuma reunião com o financeiro na sua agenda \
desta semana. Quer que eu procure em outro período ou crie esse compromisso?"

Pergunta: "Quem ganhou o jogo ontem?"
Resposta: "Futebol foge da minha especialidade, {nome}. Posso, no entanto, conferir sua agenda de amanhã ou ajudar \
com aquele bug de CORS."

## Contexto atual
- Agora: {agora}
- Semana de referência: {semana_inicio} (segunda) a {semana_fim} (domingo)
- Integrações: {integracoes}

## Perfil do usuário (fonte: perfil_usuario.json)
{perfil}
"""


def carregar_perfil() -> dict:
    with open(config.DATA_DIR / "perfil_usuario.json", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Evento:
    """O que o agente produz durante um turno, para a interface exibir."""

    tipo: str  # "texto" | "ferramenta" | "aviso"
    conteudo: str
    detalhe: dict | None = None


class Agente:
    def __init__(self, aprovador=None):
        self.perfil = carregar_perfil()
        self.integracoes = criar_integracoes()
        self.ferramentas = Ferramentas(self.integracoes, BaseConhecimento(), self.perfil, aprovador)
        agora = config.agora()
        segunda = semana_referencia(agora)
        self.system_prompt = SYSTEM_PROMPT.format(
            nome=self.perfil["como_chamar"],
            stack=", ".join(self.perfil["stack_principal"]),
            agora=f"{DIAS[agora.weekday()]}, {agora:%Y-%m-%d %H:%M} ({config.FUSO})",
            semana_inicio=segunda.isoformat(),
            semana_fim=(segunda + timedelta(days=6)).isoformat(),
            integracoes=", ".join(f"{k}: {v}" for k, v in self.integracoes.resumo().items()),
            perfil=json.dumps(self.perfil, ensure_ascii=False, indent=1),
        )
        self.mensagens: list[dict] = []

    @property
    def pendentes(self) -> list[Acao]:
        return self.ferramentas.pendentes

    def responder(self, texto: str) -> Iterator[Evento]:
        # Decisões tomadas na interface (aprovar/recusar) chegam ao modelo junto com a próxima mensagem.
        notas = self.ferramentas.consumir_notas()
        conteudo = f"{notas}\n\n{texto}" if notas else texto
        if config.LLM_PROVIDER == "ollama":
            yield from self._loop_ollama(conteudo)
        else:
            yield from self._loop_claude(conteudo)

    def responder_texto(self, texto: str) -> str:
        return "\n".join(e.conteudo for e in self.responder(texto) if e.tipo in ("texto", "aviso"))

    def _executar_ferramenta(self, nome: str, entrada: dict) -> tuple[Evento, str, bool]:
        resultado, erro = self.ferramentas.executar(nome, entrada)
        return Evento("ferramenta", nome, {"entrada": entrada, "resultado": resultado, "erro": erro}), resultado, erro

    # ------------------------------------------------------------------- Claude
    def _loop_claude(self, conteudo: str) -> Iterator[Evento]:
        import anthropic

        ferramentas = [{**d, "strict": True} for d in DEFINICOES]
        inicio_turno = len(self.mensagens)
        self.mensagens.append({"role": "user", "content": conteudo})
        try:
            client = anthropic.Anthropic()
            for _ in range(config.MAX_PASSOS_FERRAMENTAS):
                resposta = client.beta.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    max_tokens=config.MAX_TOKENS,
                    system=self.system_prompt,
                    tools=ferramentas,
                    messages=self.mensagens,
                    output_config={"effort": config.ANTHROPIC_EFFORT},
                    # Se o modelo recusar o pedido, a API tenta de novo em outro modelo recomendado.
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                )
                if resposta.stop_reason == "refusal":
                    del self.mensagens[inicio_turno:]  # descarta o turno recusado para a conversa seguir válida
                    yield Evento("aviso", "Não posso ajudar com esse pedido. Posso cuidar da sua agenda, tarefas ou código.")
                    return
                # Devolve o conteúdo completo (inclui blocos de raciocínio) para manter o histórico íntegro.
                self.mensagens.append({"role": "assistant", "content": resposta.content})
                for bloco in resposta.content:
                    if bloco.type == "text" and bloco.text.strip():
                        yield Evento("texto", bloco.text)

                if resposta.stop_reason != "tool_use":
                    if resposta.stop_reason == "max_tokens":
                        yield Evento("aviso", "(resposta interrompida por limite de tamanho)")
                    return

                resultados = []
                for bloco in resposta.content:
                    if bloco.type == "tool_use":
                        evento, resultado, erro = self._executar_ferramenta(bloco.name, bloco.input)
                        yield evento
                        resultados.append({"type": "tool_result", "tool_use_id": bloco.id,
                                           "content": resultado, "is_error": erro})
                self.mensagens.append({"role": "user", "content": resultados})
            yield Evento("aviso", "Parei após muitas etapas seguidas. Pode reformular o pedido em partes menores?")
        except anthropic.AuthenticationError:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", "⚠️ Chave da API inválida. Confira ANTHROPIC_API_KEY no arquivo .env.")
        except TypeError as e:
            # O SDK lança TypeError quando não encontra nenhuma credencial configurada.
            if "authentication" not in str(e):
                raise
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", "⚠️ Nenhuma chave da API encontrada. Defina ANTHROPIC_API_KEY no .env (ou use LLM_PROVIDER=ollama).")
        except anthropic.RateLimitError:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", "⚠️ Limite de uso da API atingido. Aguarde um pouco e tente novamente.")
        except anthropic.APIStatusError as e:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", f"⚠️ Erro da API ({e.status_code}): {e.message}")
        except anthropic.APIConnectionError:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", "⚠️ Não foi possível conectar à API da Anthropic. Verifique sua internet.")

    # ------------------------------------------------------------------- Ollama
    def _loop_ollama(self, conteudo: str) -> Iterator[Evento]:
        ferramentas = [{"type": "function", "function": {"name": d["name"], "description": d["description"],
                                                         "parameters": d["input_schema"]}} for d in DEFINICOES]
        inicio_turno = len(self.mensagens)
        self.mensagens.append({"role": "user", "content": conteudo})
        try:
            for _ in range(config.MAX_PASSOS_FERRAMENTAS):
                resp = requests.post(f"{config.OLLAMA_URL}/api/chat", timeout=600, json={
                    "model": config.OLLAMA_MODEL,
                    "messages": [{"role": "system", "content": self.system_prompt}, *self.mensagens],
                    "tools": ferramentas,
                    "stream": False,
                })
                resp.raise_for_status()
                mensagem = resp.json()["message"]
                self.mensagens.append(mensagem)
                if mensagem.get("content", "").strip():
                    yield Evento("texto", mensagem["content"])
                chamadas = mensagem.get("tool_calls") or []
                if not chamadas:
                    return
                for chamada in chamadas:
                    nome, entrada = chamada["function"]["name"], chamada["function"].get("arguments") or {}
                    evento, resultado, _ = self._executar_ferramenta(nome, entrada)
                    yield evento
                    self.mensagens.append({"role": "tool", "content": resultado, "tool_name": nome})
            yield Evento("aviso", "Parei após muitas etapas seguidas. Pode reformular o pedido em partes menores?")
        except requests.ConnectionError:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", f"⚠️ Ollama não encontrado em {config.OLLAMA_URL}. Rode `ollama serve` e `ollama pull {config.OLLAMA_MODEL}`.")
        except requests.HTTPError as e:
            del self.mensagens[inicio_turno:]
            yield Evento("aviso", f"⚠️ Erro do Ollama: {e}")


def aprovar_no_terminal(acao: Acao) -> bool:
    return input(f"\n   ⚠️  Aprovar ação #{acao.id}? {acao.resumo} [s/N] ").strip().lower() in {"s", "sim", "y"}


if __name__ == "__main__":
    # Modo terminal: python src/agente.py
    agente = Agente(aprovador=aprovar_no_terminal)
    print(f"Jarvis: Às suas ordens, {agente.perfil['como_chamar']}. Agenda, tarefas ou código? (sair = encerrar)")
    print(f"        Integrações: {agente.integracoes.resumo()}")
    while (pergunta := input("\nVocê: ").strip()).lower() not in {"sair", "exit", "quit"}:
        for evento in agente.responder(pergunta):
            if evento.tipo == "ferramenta":
                print(f"   🔧 {evento.conteudo}({json.dumps(evento.detalhe['entrada'], ensure_ascii=False)})")
            else:
                print(f"\nJarvis: {evento.conteudo}")
