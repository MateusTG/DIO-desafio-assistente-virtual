"""Integrações reais com as APIs de Google Agenda, Trello, Slack, Linear e Notion.

Cada classe só é usada quando JARVIS_MODO=real e as credenciais dela estão no .env
(veja docs/06-integracoes.md). As interfaces são as mesmas das versões simuladas.
"""

from datetime import datetime

import requests

import config

TIMEOUT = 20


# --------------------------------------------------------------------------- Google Agenda
class GoogleAgenda:
    """Usa OAuth de aplicativo instalado: na primeira execução abre o navegador para autorizar."""

    nome, modo = "Google Agenda", "real"
    ESCOPOS = ["https://www.googleapis.com/auth/calendar.events"]

    def __init__(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        cred = None
        if config.GOOGLE_TOKEN.exists():
            cred = Credentials.from_authorized_user_file(str(config.GOOGLE_TOKEN), self.ESCOPOS)
        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                cred.refresh(Request())
            else:
                fluxo = InstalledAppFlow.from_client_secrets_file(str(config.GOOGLE_CREDENCIAIS), self.ESCOPOS)
                cred = fluxo.run_local_server(port=0)
            config.GOOGLE_TOKEN.write_text(cred.to_json(), encoding="utf-8")
        self.servico = build("calendar", "v3", credentials=cred)

    def listar_eventos(self, inicio: datetime, fim: datetime) -> list[dict]:
        resp = self.servico.events().list(
            calendarId=config.GOOGLE_CALENDAR_ID, timeMin=inicio.isoformat(), timeMax=fim.isoformat(),
            singleEvents=True, orderBy="startTime",
        ).execute()
        eventos = []
        for e in resp.get("items", []):
            inicio_e = e["start"].get("dateTime", e["start"].get("date"))
            fim_e = e["end"].get("dateTime", e["end"].get("date"))
            eventos.append({"id": e["id"], "titulo": e.get("summary", "(sem título)"), "inicio": inicio_e, "fim": fim_e})
        return eventos

    def criar_evento(self, titulo: str, inicio: datetime, fim: datetime, descricao: str | None,
                     lembrete_minutos: int) -> dict:
        corpo = {
            "summary": titulo,
            "description": descricao or "Criado pelo Jarvis",
            "start": {"dateTime": inicio.isoformat(), "timeZone": str(config.FUSO)},
            "end": {"dateTime": fim.isoformat(), "timeZone": str(config.FUSO)},
            # O alerta do Google Agenda: notificação popup N minutos antes.
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": lembrete_minutos}]},
        }
        criado = self.servico.events().insert(calendarId=config.GOOGLE_CALENDAR_ID, body=corpo).execute()
        return {"id": criado["id"], "titulo": titulo, "inicio": inicio.isoformat(), "link": criado.get("htmlLink")}


# --------------------------------------------------------------------------------- Trello
class Trello:
    nome, modo = "Trello", "real"
    URL = "https://api.trello.com/1"

    def _get(self, caminho: str, **params) -> list | dict:
        params |= {"key": config.TRELLO_KEY, "token": config.TRELLO_TOKEN}
        resp = requests.get(f"{self.URL}{caminho}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def _listas(self) -> dict[str, str]:
        return {l["name"]: l["id"] for l in self._get(f"/boards/{config.TRELLO_BOARD_ID}/lists")}

    def listar_cartoes(self) -> list[dict]:
        nomes = {v: k for k, v in self._listas().items()}
        cartoes = self._get(f"/boards/{config.TRELLO_BOARD_ID}/cards/open")
        return [{"id": c["id"], "titulo": c["name"], "lista": nomes.get(c["idList"], "?"), "prazo": c.get("due"),
                 "etiquetas": [e["name"] for e in c.get("labels", [])]} for c in cartoes]

    def criar_cartao(self, titulo: str, lista: str, descricao: str | None, prazo: str | None) -> dict:
        listas = self._listas()
        if lista not in listas:
            raise ValueError(f"Lista '{lista}' não existe. Listas disponíveis: {list(listas)}")
        params = {"idList": listas[lista], "name": titulo, "desc": descricao or "",
                  "key": config.TRELLO_KEY, "token": config.TRELLO_TOKEN}
        if prazo:
            params["due"] = prazo
        resp = requests.post(f"{self.URL}/cards", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        c = resp.json()
        return {"id": c["id"], "titulo": c["name"], "lista": lista, "link": c.get("shortUrl")}


# ---------------------------------------------------------------------------------- Slack
class Slack:
    """Bot token (xoxb-...) com os escopos channels:history e chat:write; o bot precisa estar no canal."""

    nome, modo = "Slack", "real"
    URL = "https://slack.com/api"

    def _chamar(self, metodo: str, http: str = "get", **dados) -> dict:
        cabecalhos = {"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}"}
        if http == "get":
            resp = requests.get(f"{self.URL}/{metodo}", headers=cabecalhos, params=dados, timeout=TIMEOUT)
        else:
            resp = requests.post(f"{self.URL}/{metodo}", headers=cabecalhos, json=dados, timeout=TIMEOUT)
        resp.raise_for_status()
        corpo = resp.json()
        if not corpo.get("ok"):  # a API do Slack responde 200 mesmo em erro
            raise RuntimeError(f"Slack: {corpo.get('error')}")
        return corpo

    def listar_mensagens(self) -> list[dict]:
        corpo = self._chamar("conversations.history", channel=config.SLACK_CANAL_ID, limit=20)
        return [{"canal": config.SLACK_CANAL_ID, "autor": m.get("user", m.get("bot_id", "?")),
                 "data": datetime.fromtimestamp(float(m["ts"]), config.FUSO).isoformat(timespec="minutes"),
                 "texto": m.get("text", "")} for m in corpo.get("messages", [])]

    def enviar_mensagem(self, canal: str, texto: str) -> dict:
        corpo = self._chamar("chat.postMessage", http="post", channel=canal, text=texto)
        return {"canal": corpo["channel"], "texto": texto, "status": "enviada"}


# --------------------------------------------------------------------------------- Linear
class Linear:
    nome, modo = "Linear", "real"
    URL = "https://api.linear.app/graphql"

    def _graphql(self, consulta: str, variaveis: dict | None = None) -> dict:
        resp = requests.post(self.URL, json={"query": consulta, "variables": variaveis or {}},
                             headers={"Authorization": config.LINEAR_API_KEY}, timeout=TIMEOUT)
        resp.raise_for_status()
        corpo = resp.json()
        if corpo.get("errors"):
            raise RuntimeError(f"Linear: {corpo['errors'][0].get('message')}")
        return corpo["data"]

    def listar_issues(self) -> list[dict]:
        dados = self._graphql("""
            query { viewer { assignedIssues(first: 50) { nodes {
                identifier title priority estimate dueDate url state { name type }
            } } } }""")
        return [{"id": i["identifier"], "titulo": i["title"], "estado": i["state"]["name"], "prioridade": i["priority"],
                 "estimativa": i["estimate"], "prazo": i["dueDate"], "link": i["url"]}
                for i in dados["viewer"]["assignedIssues"]["nodes"]
                if i["state"]["type"] not in {"completed", "canceled"}]

    def criar_issue(self, titulo: str, descricao: str | None, prioridade: int) -> dict:
        dados = self._graphql(
            """mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) { success issue { identifier title url } } }""",
            {"input": {"teamId": config.LINEAR_TEAM_ID, "title": titulo, "description": descricao or "",
                       "priority": prioridade}},
        )
        issue = dados["issueCreate"]["issue"]
        return {"id": issue["identifier"], "titulo": issue["title"], "link": issue["url"]}


# --------------------------------------------------------------------------------- Notion
class Notion:
    """Token de integração interna; compartilhe as páginas desejadas com a integração no Notion."""

    nome, modo = "Notion", "real"
    URL = "https://api.notion.com/v1"
    VERSAO = "2022-06-28"

    def _cabecalhos(self) -> dict:
        return {"Authorization": f"Bearer {config.NOTION_TOKEN}", "Notion-Version": self.VERSAO}

    @staticmethod
    def _titulo(pagina: dict) -> str:
        for prop in pagina.get("properties", {}).values():
            if prop.get("type") == "title":
                return "".join(t.get("plain_text", "") for t in prop["title"]) or "(sem título)"
        return "(sem título)"

    def buscar(self, consulta: str) -> list[dict]:
        resp = requests.post(f"{self.URL}/search", headers=self._cabecalhos(), timeout=TIMEOUT,
                             json={"query": consulta, "filter": {"property": "object", "value": "page"}, "page_size": 10})
        resp.raise_for_status()
        return [{"id": p["id"], "titulo": self._titulo(p), "link": p.get("url")} for p in resp.json()["results"]]

    def criar_pagina(self, titulo: str, conteudo: str) -> dict:
        # A API limita cada bloco de texto a 2000 caracteres: um parágrafo por linha, fatiado se preciso.
        blocos = [{"object": "block", "type": "paragraph",
                   "paragraph": {"rich_text": [{"type": "text", "text": {"content": linha[i:i + 2000]}}]}}
                  for linha in conteudo.splitlines() if linha.strip() for i in range(0, len(linha), 2000)]
        corpo = {"parent": {"page_id": config.NOTION_PAGINA_PAI_ID},
                 "properties": {"title": {"title": [{"type": "text", "text": {"content": titulo}}]}},
                 "children": blocos[:100]}
        resp = requests.post(f"{self.URL}/pages", headers=self._cabecalhos(), json=corpo, timeout=TIMEOUT)
        resp.raise_for_status()
        p = resp.json()
        return {"id": p["id"], "titulo": titulo, "link": p.get("url")}
