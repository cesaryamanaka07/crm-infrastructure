import base64
import json
import re
import httpx
from app.config import settings


class ErroIA(Exception):
    pass


def _json(texto):
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.I)
    try:
        return json.loads(texto)
    except (ValueError, TypeError) as erro:
        raise ErroIA("A IA retornou dados fora do formato esperado") from erro


async def gerar_json(prompt, system):
    if not settings.omniroute_base_url:
        raise ErroIA("OmniRoute não configurado")
    headers = {"Content-Type": "application/json"}
    if settings.omniroute_api_key:
        headers["Authorization"] = f"Bearer {settings.omniroute_api_key}"
    payload = {"model": settings.omniroute_text_model, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": prompt}
    ], "temperature": .55, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=settings.omniroute_timeout_seconds) as client:
            response = await client.post(f"{settings.omniroute_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get("model", settings.omniroute_text_model), _json(data["choices"][0]["message"]["content"])
    except ErroIA:
        raise
    except httpx.HTTPStatusError as erro:
        raise ErroIA(f"OmniRoute respondeu HTTP {erro.response.status_code}") from erro
    except Exception as erro:
        raise ErroIA("Não foi possível gerar o conteúdo com a IA") from erro


async def gerar_ideias(arsenal, manual, quantidade, instrucao=""):
    prompt = f"""Gere {quantidade} ideias únicas de artigos de blog em português brasileiro.
Use prioritariamente dores, mitos, objeções, sonhos, produtos e proposta de valor deste Arsenal de Copy:
{json.dumps(arsenal, ensure_ascii=False)}
Manual permanente: {manual or 'não informado'}
Orientação adicional: {instrucao or 'nenhuma'}
Cada ideia precisa ter oportunidade real de busca e não pode canibalizar outra.
Retorne somente JSON: {{"ideias":[{{"titulo":"", "tema":"", "palavra_chave":"", "palavras_secundarias":[], "intencao_busca":"informacional|comercial|transacional|navegacional", "foco":""}}]}}"""
    modelo, data = await gerar_json(prompt, "Você é estrategista de SEO sênior, orientado a conteúdo útil e intenção de busca.")
    ideias = data.get("ideias")
    if not isinstance(ideias, list):
        raise ErroIA("A IA não retornou uma lista de ideias")
    return modelo, ideias[:quantidade]


async def gerar_artigo(ideia, arsenal, manual):
    limites = {"800_1200": "800 a 1.200", "1500_2500": "1.500 a 2.500", "2500_4000": "2.500 a 4.000", "4000_6000": "4.000 a 6.000"}
    prompt = f"""Crie um artigo original e aprofundado em português brasileiro.
Título-base: {ideia.titulo}
Tema: {ideia.tema}
Palavra-chave principal: {ideia.palavra_chave}
Palavras-chave secundárias: {json.dumps(ideia.palavras_secundarias, ensure_ascii=False)}
Intenção de busca: {ideia.intencao_busca}
Foco: {ideia.foco or 'não informado'}
Extensão: {limites.get(ideia.tamanho, '1.500 a 2.500')} palavras.
Arsenal de Copy: {json.dumps(arsenal, ensure_ascii=False)}
Manual do cliente: {manual or 'não informado'}

Regras: satisfaça a intenção logo no início; use H2/H3 descritivos; exemplos práticos; entidades e termos semanticamente relacionados; linguagem natural; links internos devem ser apenas sugestões marcadas; não invente estatísticas; inclua FAQ útil; conclusão e CTA coerente. Evite keyword stuffing. O HTML deve começar no conteúdo, sem html/body/h1, scripts ou estilos.
Retorne somente JSON com: titulo, meta_titulo (até 60 caracteres), meta_descricao (até 155), slug, resumo, conteudo_html, estrutura (lista), faq (lista de objetos pergunta/resposta), palavras_secundarias, checklist_seo (objeto), pontuacao_seo (0-100), total_palavras e prompts_imagens (lista com posicao, alt, prompt)."""
    return await gerar_json(prompt, "Você é redator SEO sênior. Priorize utilidade, experiência, clareza, precisão e intenção de busca; retorne JSON válido.")


async def gerar_imagem(prompt):
    if not settings.omniroute_image_model:
        return None
    headers = {"Content-Type": "application/json"}
    if settings.omniroute_api_key:
        headers["Authorization"] = f"Bearer {settings.omniroute_api_key}"
    async with httpx.AsyncClient(timeout=settings.omniroute_timeout_seconds) as client:
        response = await client.post(f"{settings.omniroute_base_url.rstrip('/')}/images/generations", headers=headers, json={
            "model": settings.omniroute_image_model, "prompt": prompt, "n": 1, "size": "1536x1024"
        })
        response.raise_for_status()
        item = response.json().get("data", [{}])[0]
    # O banco guarda apenas a referência. Base64 grande não é persistido por segurança/tamanho.
    if item.get("url"):
        return {"url": item["url"]}
    if item.get("b64_json"):
        return {"data_url": "data:image/png;base64," + item["b64_json"]}
    return None

