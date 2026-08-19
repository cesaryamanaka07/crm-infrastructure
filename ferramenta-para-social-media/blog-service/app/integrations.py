import base64
import html
import json
import time
from datetime import datetime, timedelta, timezone
import httpx
from jose import jwt
from app.crypto import criptografar, descriptografar
from app.config import settings
from sqlalchemy import text


def normalizar_wordpress_url(url):
    url = (url or "").strip().rstrip("/")
    for trecho in ("/wp-admin", "/wp-json"):
        if trecho in url:
            url = url.split(trecho)[0]
    if not url.startswith("https://"):
        raise ValueError("O WordPress deve usar HTTPS")
    return url


def _wp_headers(integracao):
    senha = descriptografar(integracao.wordpress_senha_app)
    if not integracao.wordpress_usuario or not senha:
        raise ValueError("Credencial WordPress incompleta")
    token = base64.b64encode(f"{integracao.wordpress_usuario}:{senha}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def testar_wordpress(integracao):
    url = normalizar_wordpress_url(integracao.wordpress_url)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{url}/wp-json/wp/v2/users/me?context=edit", headers=_wp_headers(integracao))
        response.raise_for_status()
        data = response.json()
    return {"ok": True, "usuario": data.get("name") or data.get("slug")}


async def publicar_wordpress(integracao, artigo, status, agendado_para=None):
    if artigo.wordpress_post_id:
        return artigo.wordpress_post_id, artigo.wordpress_url
    url = normalizar_wordpress_url(integracao.wordpress_url)
    async with httpx.AsyncClient(timeout=60) as client:
        conteudo = artigo.conteudo_html
        media_ids = []
        for indice, imagem in enumerate(artigo.imagens or []):
            try:
                if imagem.get("url"):
                    arquivo = await client.get(imagem["url"]); arquivo.raise_for_status(); bytes_imagem = arquivo.content
                    mime = arquivo.headers.get("content-type", "image/png").split(";")[0]
                elif imagem.get("data_url"):
                    cabecalho, codificado = imagem["data_url"].split(",", 1)
                    mime = cabecalho.split(":", 1)[1].split(";", 1)[0]; bytes_imagem = base64.b64decode(codificado)
                else: continue
                extensao = "jpg" if "jpeg" in mime else mime.split("/")[-1]
                upload_headers = {**_wp_headers(integracao), "Content-Disposition": f'attachment; filename="artigo-{artigo.id}-{indice + 1}.{extensao}"', "Content-Type": mime}
                upload = await client.post(f"{url}/wp-json/wp/v2/media", headers=upload_headers, content=bytes_imagem)
                upload.raise_for_status(); media = upload.json(); media_ids.append(media["id"])
                await client.post(f"{url}/wp-json/wp/v2/media/{media['id']}", headers=_wp_headers(integracao), json={"alt_text": imagem.get("alt", artigo.palavra_chave)})
                src = html.escape(media.get("source_url", ""), quote=True)
                alt = html.escape(imagem.get("alt", artigo.palavra_chave), quote=True)
                conteudo += f'<figure><img src="{src}" alt="{alt}"></figure>'
            except Exception:
                # Uma imagem defeituosa não impede o envio do texto do artigo.
                continue
        payload = {"title": artigo.titulo, "content": conteudo, "excerpt": artigo.resumo,
                   "slug": artigo.slug, "status": status}
        if media_ids: payload["featured_media"] = media_ids[0]
        if status == "future" and agendado_para:
            payload["date_gmt"] = agendado_para.astimezone(timezone.utc).replace(tzinfo=None).isoformat()
        response = await client.post(f"{url}/wp-json/wp/v2/posts", headers=_wp_headers(integracao), json=payload)
        response.raise_for_status()
        data = response.json()
    return data["id"], data.get("link")


async def _google_token(integracao, db):
    agora = datetime.now(timezone.utc)
    central = db.execute(text("SELECT access_token,refresh_token,expira_em FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":integracao.usuario_id,"c":integracao.cliente_id}).mappings().first()
    if central:
        exp=central["expira_em"]; exp=exp.replace(tzinfo=timezone.utc) if exp and exp.tzinfo is None else exp
        if central["access_token"] and exp and exp>agora+timedelta(minutes=2): return descriptografar(bytes(central["access_token"]))
        async with httpx.AsyncClient(timeout=30) as client:
            response=await client.post("https://oauth2.googleapis.com/token",data={"client_id":settings.google_oauth_client_id,"client_secret":settings.google_oauth_client_secret,"refresh_token":descriptografar(bytes(central["refresh_token"])),"grant_type":"refresh_token"})
        if response.status_code>=400: raise ValueError("Reconecte a conta Google no cadastro do cliente")
        dados=response.json(); acesso=criptografar(dados["access_token"]); nova_exp=agora+timedelta(seconds=dados.get("expires_in",3600))
        db.execute(text("UPDATE social.google_conexoes SET access_token=:a,expira_em=:e WHERE usuario_id=:u AND cliente_id=:c"),{"a":acesso,"e":nova_exp,"u":integracao.usuario_id,"c":integracao.cliente_id});db.commit();return dados["access_token"]
    expira = integracao.google_token_expira_em
    if expira and expira.tzinfo is None: expira = expira.replace(tzinfo=timezone.utc)
    if integracao.google_refresh_token:
        if integracao.google_access_token and expira and expira > agora + timedelta(minutes=2):
            return descriptografar(integracao.google_access_token)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={"client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret, "refresh_token": descriptografar(integracao.google_refresh_token),
                "grant_type": "refresh_token"})
        if response.status_code >= 400: raise ValueError("A autorização Google expirou ou foi revogada. Reconecte a conta")
        dados = response.json(); integracao.google_access_token = criptografar(dados["access_token"])
        integracao.google_token_expira_em = agora + timedelta(seconds=dados.get("expires_in", 3600)); db.commit()
        return dados["access_token"]
    raw = descriptografar(integracao.google_conta_servico)
    if not raw:
        raise ValueError("Conta de serviço Google não configurada")
    info = json.loads(raw)
    now = int(time.time())
    assertion = jwt.encode({"iss": info["client_email"], "scope": "https://www.googleapis.com/auth/spreadsheets",
                            "aud": info.get("token_uri", "https://oauth2.googleapis.com/token"), "iat": now, "exp": now + 3600},
                           info["private_key"], algorithm="RS256")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(info.get("token_uri", "https://oauth2.googleapis.com/token"), data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
        response.raise_for_status()
        return response.json()["access_token"]


async def adicionar_ideia_planilha(integracao, ideia, db):
    if not integracao.google_planilha_id:
        raise ValueError("Planilha Google não configurada")
    token = await _google_token(integracao, db)
    aba = "Ideias de Blog"
    headers = {"Authorization": f"Bearer {token}"}
    base = f"https://sheets.googleapis.com/v4/spreadsheets/{integracao.google_planilha_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        metadata = await client.get(base, headers=headers, params={"fields": "sheets.properties.title"})
        metadata.raise_for_status()
        titulos = [item.get("properties", {}).get("title") for item in metadata.json().get("sheets", [])]
        if aba not in titulos:
            criada = await client.post(f"{base}:batchUpdate", headers=headers, json={"requests": [{"addSheet": {"properties": {"title": aba}}}]})
            criada.raise_for_status()
            cabecalho_url = f"{base}/values/{aba}!A1:J1"
            cabecalho = [["ID", "Título", "Palavra-chave", "Intenção", "Status", "Agendado para", "Publicado em", "Tema", "Foco", "Criado em"]]
            resposta_cabecalho = await client.put(cabecalho_url, headers=headers, params={"valueInputOption": "RAW"}, json={"values": cabecalho})
            resposta_cabecalho.raise_for_status()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{integracao.google_planilha_id}/values/{aba}!A:J:append"
    valores = [[str(ideia.id), ideia.titulo, ideia.palavra_chave, ideia.intencao_busca, ideia.status,
                ideia.agendado_para.isoformat() if ideia.agendado_para else "", "", ideia.tema, ideia.foco or "", datetime.now(timezone.utc).isoformat()]]
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"}, json={"values": valores})
        response.raise_for_status()
        return response.json().get("updates", {}).get("updatedRange")

async def listar_planilhas_google(integracao, db):
    token = await _google_token(integracao, db)
    params = {"q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
              "fields": "files(id,name,modifiedTime,webViewLink)", "orderBy": "modifiedTime desc",
              "pageSize": 100, "spaces": "drive", "includeItemsFromAllDrives": "true", "supportsAllDrives": "true"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://www.googleapis.com/drive/v3/files", headers={"Authorization": f"Bearer {token}"}, params=params)
    if response.status_code == 403:
        raise ValueError("Reconecte a conta Google para autorizar a seleção de arquivos do Drive")
    response.raise_for_status()
    return response.json().get("files", [])
