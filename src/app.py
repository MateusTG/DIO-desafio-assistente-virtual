"""Interface de chat do Jarvis em Streamlit.

Rodar a partir da raiz do projeto:  streamlit run src/app.py
"""

import json

import streamlit as st

import config
from agente import Agente, Evento
from integracoes.mock import DIAS

st.set_page_config(page_title="Jarvis — Assistente Pessoal", page_icon="🤖", layout="wide")

PEDIDO_PLANEJAMENTO = "Planeje minha semana: revise agenda, tarefas e mensagens e proponha os blocos de foco com alertas."

if "agente" not in st.session_state:
    st.session_state.agente = Agente()  # sem aprovador: ações de escrita vão para a fila da interface
    st.session_state.historico = []  # o que é exibido: {"papel", "texto" | "eventos"}
agente: Agente = st.session_state.agente
perfil = agente.perfil


def exibir_eventos(eventos: list[Evento]) -> None:
    for e in eventos:
        if e.tipo == "texto":
            st.markdown(e.conteudo)
        elif e.tipo == "aviso":
            st.warning(e.conteudo)
        else:
            icone = "✍️" if e.conteudo.startswith(("criar", "enviar")) else "🔧"
            with st.expander(f"{icone} {e.conteudo}", expanded=False):
                st.code(json.dumps(e.detalhe["entrada"], ensure_ascii=False, indent=1), language="json")
                st.text(e.detalhe["resultado"][:3000])


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header(f"🤖 Jarvis · {perfil['como_chamar']}")
    agora = config.agora()
    st.caption(f"{DIAS[agora.weekday()].capitalize()}, {agora:%d/%m/%Y %H:%M}")

    if agora.weekday() == 6:
        st.info("É domingo, dia de planejar a semana.")
    if st.button("📅 Planejar minha semana", type="primary", width="stretch"):
        st.session_state.pedido = PEDIDO_PLANEJAMENTO
        st.rerun()

    st.subheader("✅ Aguardando sua aprovação")
    if not agente.pendentes:
        st.caption("Nenhuma ação pendente.")
    for acao in agente.pendentes:
        with st.container(border=True):
            st.write(f"**#{acao.id}** {acao.resumo}")
            c1, c2 = st.columns(2)
            if c1.button("Aprovar", key=f"ok{acao.id}", width="stretch"):
                agente.ferramentas.decidir(acao.id, True)
                st.rerun()
            if c2.button("Recusar", key=f"no{acao.id}", width="stretch"):
                agente.ferramentas.decidir(acao.id, False)
                st.rerun()
    if len(agente.pendentes) > 1 and st.button("Aprovar todas", width="stretch"):
        for acao in list(agente.pendentes):
            agente.ferramentas.decidir(acao.id, True)
        st.rerun()

    concluidas = [a for a in agente.ferramentas.acoes if a.status != "pendente"]
    if concluidas:
        with st.expander(f"Histórico de ações ({len(concluidas)})"):
            for a in concluidas:
                st.write({"executada": "✅", "recusada": "🚫", "erro": "❌"}[a.status], a.resumo)

    st.divider()
    st.caption("Integrações: " + " · ".join(f"{k} ({v})" for k, v in agente.integracoes.resumo().items()))
    modelo = config.OLLAMA_MODEL if config.LLM_PROVIDER == "ollama" else config.ANTHROPIC_MODEL
    st.caption(f"LLM: {config.LLM_PROVIDER} · {modelo}")
    if st.button("🗑️ Nova conversa", width="stretch"):
        del st.session_state.agente
        st.rerun()

# ------------------------------------------------------------------------- chat
st.title("🤖 Jarvis")
st.caption("Agenda, Trello, Linear, Slack, Notion e programação. Nenhuma ação de escrita acontece sem a sua aprovação.")

SUGESTOES = [
    "O que tenho na agenda amanhã?",
    "Quais tarefas vencem esta semana?",
    "Tenho menções no Slack para responder?",
    "Como resolvo um erro de CORS no Node.js?",
]

pedido = st.chat_input("Às suas ordens...") or st.session_state.pop("pedido", None)

if notas := agente.ferramentas.notas_para_o_agente:
    st.info("Decisões registradas (o Jarvis será avisado na próxima mensagem):\n\n" + "\n\n".join(
        n.replace("[Sistema] ", "") for n in notas))

if not st.session_state.historico and not pedido:
    with st.chat_message("assistant", avatar="🤖"):
        st.write(f"Às suas ordens, {perfil['como_chamar']}. Posso organizar sua semana, consultar suas "
                 "ferramentas ou ajudar com código. Por onde começamos?")
    for coluna, sugestao in zip(st.columns(len(SUGESTOES)), SUGESTOES):
        if coluna.button(sugestao, width="stretch"):
            st.session_state.pedido = sugestao
            st.rerun()

for item in st.session_state.historico:
    with st.chat_message(item["papel"], avatar="🤖" if item["papel"] == "assistant" else None):
        if item["papel"] == "user":
            st.markdown(item["texto"])
        else:
            exibir_eventos(item["eventos"])

if pedido:
    st.session_state.historico.append({"papel": "user", "texto": pedido})
    with st.chat_message("user"):
        st.markdown(pedido)
    with st.chat_message("assistant", avatar="🤖"):
        eventos = []
        with st.status("Trabalhando nisso...", expanded=False) as status:
            for evento in agente.responder(pedido):
                eventos.append(evento)
                if evento.tipo == "ferramenta":
                    status.update(label=f"Usando {evento.conteudo}...")
            usadas = sum(e.tipo == "ferramenta" for e in eventos)
            status.update(label=f"Concluído ({usadas} ferramentas usadas)", state="complete")
        st.session_state.historico.append({"papel": "assistant", "eventos": eventos})
    st.rerun()  # atualiza a barra lateral com novas ações pendentes
