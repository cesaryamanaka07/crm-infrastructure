from urllib.parse import urlparse

import httpx

from app.config import settings


class IntegrationError(ValueError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _url(base: str, path: str) -> str:
    return f"{settings.normalizar_url(base)}/{path.lstrip('/')}"


async def _request(method: str, url: str, *, headers=None, json=None, params=None):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(method, url, headers=headers, json=json, params=params)
    except httpx.RequestError as exc:
        raise IntegrationError("Serviço externo indisponível no momento.") from exc
    if response.status_code >= 400:
        try:
            corpo = response.json()
            detalhe = corpo.get("message") or corpo.get("error") or corpo.get("response", {}).get("message")
        except (ValueError, AttributeError):
            detalhe = None
        raise IntegrationError(
            str(detalhe or f"Serviço respondeu com HTTP {response.status_code}."),
            status_code=response.status_code,
        )
    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise IntegrationError("O serviço retornou uma resposta inválida.") from exc


def evolution_configurada() -> bool:
    return bool(settings.evolution_api_url and settings.evolution_api_key)


async def evolution(method: str, path: str, *, payload=None, params=None):
    if not evolution_configurada():
        raise IntegrationError("Evolution API ainda não foi configurada no servidor.")
    return await _request(
        method,
        _url(settings.evolution_api_url, path),
        headers={"apikey": settings.evolution_api_key},
        json=payload,
        params=params,
    )


def n8n_configurado() -> bool:
    return bool(settings.n8n_api_url and settings.n8n_api_key)


async def n8n(method: str, path: str, *, payload=None, params=None):
    if not n8n_configurado():
        raise IntegrationError("A API do n8n ainda não foi configurada no servidor.")
    return await _request(
        method,
        _url(settings.n8n_api_url, f"api/v1/{path.lstrip('/')}"),
        headers={"X-N8N-API-KEY": settings.n8n_api_key},
        json=payload,
        params=params,
    )


def validar_typebot_publico(url: str) -> str:
    url = url.strip().rstrip("/")
    base = settings.normalizar_url(settings.typebot_viewer_url)
    if not base:
        raise IntegrationError("O visualizador do Typebot ainda não foi configurado no servidor.")
    recebido, permitido = urlparse(url), urlparse(base)
    if recebido.scheme != "https" or recebido.netloc != permitido.netloc:
        raise IntegrationError("Use um endereço publicado no visualizador Typebot configurado.")
    return url
