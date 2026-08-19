import asyncio
import json
import re
from typing import Any

import httpx

from app.config import settings
from app.models import Conteudo
from app.schemas import GeracaoImagemRequest

MAX_TENTATIVAS_IA = 3
FAIXAS_LEGENDA = {
    "ultracurta": "até 100 caracteres e aproximadamente 15 a 20 palavras",
    "curta": "101 a 300 caracteres e aproximadamente 20 a 50 palavras",
    "media": "301 a 800 caracteres e aproximadamente 50 a 130 palavras",
    "longa": "801 a 1.500 caracteres e aproximadamente 130 a 250 palavras",
    "maxima": "1.501 a 2.200 caracteres e aproximadamente 250 a 350 palavras",
}


class OmniRouteError(Exception):
    pass


def _extrair_json(texto: str) -> dict[str, Any]:
    limpo = texto.strip()
    if limpo.startswith("```"):
        limpo = re.sub(r"^```(?:json)?\s*", "", limpo, flags=re.IGNORECASE)
        limpo = re.sub(r"\s*```$", "", limpo)
    try:
        resultado = json.loads(limpo)
    except json.JSONDecodeError as erro:
        raise OmniRouteError("A IA retornou uma resposta que não é um JSON válido") from erro
    if not isinstance(resultado, dict) or not isinstance(resultado.get("conteudos"), list):
        raise OmniRouteError("A IA retornou um JSON sem a lista de conteúdos")
    return resultado


async def _postar_com_retry(url: str, headers: dict, payload: dict) -> dict:
    ultimo_erro: Exception | None = None
    for tentativa in range(MAX_TENTATIVAS_IA):
        try:
            async with httpx.AsyncClient(timeout=settings.omniroute_timeout_seconds) as cliente:
                resposta = await cliente.post(url, headers=headers, json=payload)
                resposta.raise_for_status()
                return resposta.json()
        except httpx.HTTPStatusError as erro:
            ultimo_erro = erro
            if erro.response.status_code in (400, 401, 403, 404, 422):
                raise
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, httpx.HTTPError) as erro:
            ultimo_erro = erro
        except ValueError as erro:
            raise erro
        if tentativa < MAX_TENTATIVAS_IA - 1:
            await asyncio.sleep(0.8 * (2 ** tentativa))
    raise ultimo_erro or httpx.HTTPError("OmniRouter indisponível")


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.omniroute_api_key:
        headers["Authorization"] = f"Bearer {settings.omniroute_api_key}"
    return headers


def _criar_prompt(conteudo: Conteudo) -> str:
    quantidades = conteudo.quantidades
    narrativas = conteudo.narrativas
    tecnicas = ", ".join(conteudo.tecnicas) or "nenhuma técnica adicional"
    contexto_arsenal = getattr(conteudo, "contexto_arsenal", "") or "nenhuma informação selecionada"
    manual_arsenal = getattr(conteudo, "manual_arsenal", "") or "nenhum manual permanente"
    narrativa_estrategica = getattr(conteudo, "narrativa_estrategica", "") or "nenhuma narrativa estratégica selecionada"
    hashtags_padrao = ", ".join(getattr(conteudo, "hashtags_padrao", []) or []) or "nenhuma hashtag padrão cadastrada"
    return f"""
Crie um lote de conteúdos para redes sociais em português brasileiro.

Briefing:
- Intenção: {conteudo.intencao}
- Tema: {conteudo.tema}
- Perspectiva: {conteudo.perspectiva}
- Framework: {conteudo.modelo}
- Tom de voz: {conteudo.tom_de_voz}
- Técnicas: {tecnicas}
- Observações: {conteudo.observacoes or 'nenhuma'}
- Arsenal de Copy completo do cliente: {contexto_arsenal}
- Manual permanente do cliente: {manual_arsenal}
- Instruções específicas desta criação: {conteudo.instrucoes_ia or 'nenhuma'}
- Narrativa Estratégica do cliente: {narrativa_estrategica}
- Hashtags padrão do cliente: {hashtags_padrao}
- Quantidades: {json.dumps(quantidades, ensure_ascii=False)}
- Narrativas: {json.dumps(narrativas, ensure_ascii=False)}
- Legenda: {FAIXAS_LEGENDA[conteudo.tamanho_legenda]}

Regras obrigatórias:
1. Use voz ativa e comunicação individual: eu falando diretamente com você.
2. A primeira linha deve ser um hook forte com no máximo 125 caracteres.
3. Use parágrafos curtos, apropriados para leitura no celular.
4. Respeite a faixa de caracteres da legenda.
5. Calcule caracteres e palavras somente da legenda e informe valores exatos.
6. Produza exatamente as quantidades solicitadas, sem repetir ideias.
7. Priorize as hashtags padrão do cliente, sem duplicá-las; complemente somente quando necessário.
8. Post único: título, legenda e hashtags.
9. Carrossel: título, slides, legenda e hashtags.
10. Reels: título, roteiro, legenda e hashtags.
11. Story: título, telas, legenda e hashtags.

Responda somente com JSON válido, sem Markdown, neste formato:
{{
  "conteudos": [
    {{
      "formato": "post_unico|carrossel|reels|story",
      "titulo": "texto",
      "slides": [],
      "roteiro": [],
      "telas": [],
      "legenda": "texto",
      "hashtags": ["#exemplo"],
      "contagem_caracteres": 0,
      "contagem_palavras": 0
    }}
  ]
}}
""".strip()


async def gerar_textos(conteudo: Conteudo) -> tuple[str, list[dict[str, Any]]]:
    if not settings.omniroute_enabled:
        raise OmniRouteError("A integração com o OmniRoute não foi configurada")
    payload = {
        "model": settings.omniroute_text_model,
        "messages": [
            {"role": "system", "content": "Você é um estrategista de conteúdo e copywriter. Siga o briefing com precisão e retorne somente JSON válido."},
            {"role": "user", "content": _criar_prompt(conteudo)},
        ],
        "temperature": 0.7,
        "stream": False,
    }
    try:
        dados = await _postar_com_retry(f"{settings.omniroute_base_url.rstrip('/')}/chat/completions", _headers(), payload)
    except httpx.TimeoutException as erro:
        raise OmniRouteError("O OmniRoute demorou mais que o limite para responder") from erro
    except httpx.HTTPStatusError as erro:
        codigo = erro.response.status_code
        mensagem = "O OmniRoute recusou a chave de API configurada" if codigo in (401, 403) else "O OmniRoute está sem capacidade disponível no momento" if codigo == 429 else f"O OmniRoute respondeu com erro HTTP {codigo}"
        raise OmniRouteError(mensagem) from erro
    except (httpx.HTTPError, ValueError) as erro:
        raise OmniRouteError("Não foi possível comunicar com o OmniRoute") from erro
    try:
        texto = dados["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as erro:
        raise OmniRouteError("O OmniRoute retornou uma resposta incompleta") from erro
    resultado = _extrair_json(texto)
    return dados.get("model", settings.omniroute_text_model), resultado["conteudos"]


async def gerar_json_estrategico(instrucoes: str, prompt: str) -> tuple[str, dict[str, Any]]:
    if not settings.omniroute_enabled:
        raise OmniRouteError("A integração com o OmniRoute não foi configurada")
    payload = {"model": settings.omniroute_text_model, "messages": [{"role": "system", "content": instrucoes}, {"role": "user", "content": prompt}], "temperature": 0.65, "stream": False}
    try:
        dados = await _postar_com_retry(f"{settings.omniroute_base_url.rstrip('/')}/chat/completions", _headers(), payload)
        texto = dados["choices"][0]["message"]["content"].strip()
        if texto.startswith("```"):
            texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.IGNORECASE)
            texto = re.sub(r"\s*```$", "", texto)
        resultado = json.loads(texto)
        if not isinstance(resultado, dict):
            raise ValueError
        return dados.get("model", settings.omniroute_text_model), resultado
    except httpx.TimeoutException as erro:
        raise OmniRouteError("A IA demorou mais que o limite para responder") from erro
    except httpx.HTTPStatusError as erro:
        raise OmniRouteError(f"O OmniRoute respondeu com erro HTTP {erro.response.status_code}") from erro
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as erro:
        raise OmniRouteError("A IA retornou uma estratégia fora do formato esperado") from erro


def _prompt_imagem(conteudo: Conteudo, opcoes: GeracaoImagemRequest) -> str:
    paleta = ", ".join(opcoes.paleta) if opcoes.paleta else "harmônica com o tema"
    tipografia = opcoes.tipografia or "tipografia legível e moderna"
    adicional = opcoes.prompt_adicional or "sem instruções adicionais"
    return ("Crie uma peça visual profissional para rede social. " f"Tema: {conteudo.tema}. Intenção: {conteudo.intencao}. " f"Perspectiva: {conteudo.perspectiva}. Tom: {conteudo.tom_de_voz}. " f"Paleta: {paleta}. Direção tipográfica: {tipografia}. " f"Instruções adicionais: {adicional}. " "Composição limpa, alta legibilidade no celular, sem logotipos inventados, sem marcas d'água e sem texto com erros ortográficos.")


async def gerar_imagens(conteudo: Conteudo, opcoes: GeracaoImagemRequest) -> tuple[str, list[dict[str, Any]]]:
    if not settings.omniroute_enabled:
        raise OmniRouteError("A integração com o OmniRoute não foi configurada")
    if not settings.omniroute_image_model:
        raise OmniRouteError("Nenhum modelo de geração de imagens foi configurado")
    payload = {"model": settings.omniroute_image_model, "prompt": _prompt_imagem(conteudo, opcoes), "n": opcoes.quantidade, "size": opcoes.tamanho}
    try:
        dados = await _postar_com_retry(f"{settings.omniroute_base_url.rstrip('/')}/images/generations", _headers(), payload)
    except httpx.TimeoutException as erro:
        raise OmniRouteError("A geração da imagem excedeu o tempo limite") from erro
    except httpx.HTTPStatusError as erro:
        codigo = erro.response.status_code
        mensagem = "O OmniRoute recusou a chave usada para gerar imagens" if codigo in (401, 403) else "Não há capacidade disponível para gerar imagens agora" if codigo == 429 else f"A geração de imagens respondeu com erro HTTP {codigo}"
        raise OmniRouteError(mensagem) from erro
    except (httpx.HTTPError, ValueError) as erro:
        raise OmniRouteError("Não foi possível gerar a imagem pelo OmniRoute") from erro
    imagens = [{"url": item.get("url"), "b64_json": item.get("b64_json"), "prompt_revisado": item.get("revised_prompt")} for item in dados.get("data", [])]
    if not imagens:
        raise OmniRouteError("O OmniRoute não retornou nenhuma imagem")
    return dados.get("model", settings.omniroute_image_model), imagens
