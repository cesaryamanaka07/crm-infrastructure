import base64
import asyncio
import io
import json
import zipfile
from types import SimpleNamespace
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import OmniRouteError, gerar_imagens
from app.auth import obter_usuario_id
from app.database import get_db
from app.models import Conteudo, GeracaoImagemSalva, GeracaoTexto, ImagemSalva, Marca
from app.schemas import GeracaoImagemRequest


router = APIRouter(prefix="/midias", tags=["imagens"])
FORMATOS = {"post_unico", "carrossel", "story"}
TAMANHOS_FINAIS = {
    "1080x1080": ((1080, 1080), "1024x1024"),
    "1080x1350": ((1080, 1350), "1024x1536"),
    "1080x1920": ((1080, 1920), "1024x1536"),
}
MIMES_REFERENCIA = {"image/png", "image/jpeg", "image/webp"}


class AprovacaoImagem(BaseModel):
    cliente_id: UUID
    data_url: str
    formato: str
    tamanho: str
    modelo: str = Field(max_length=120)
    descricao: str = Field(min_length=3, max_length=3000)
    nome: str = Field(default="imagem-aprovada.png", max_length=255)
    geracao_texto_id: UUID | None = None
    conteudo_indice: int | None = None


async def _baixar_imagem(item: dict) -> bytes:
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"], validate=True)
    if item.get("url"):
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as cliente:
            resposta = await cliente.get(item["url"])
            resposta.raise_for_status()
            if not resposta.headers.get("content-type", "").startswith("image/"):
                raise ValueError("A URL retornada não contém uma imagem")
            return resposta.content
    raise ValueError("Imagem sem conteúdo")


def _carregar_fonte(tamanho: int):
    candidatos = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
    for caminho in candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def _quebrar_texto(draw: ImageDraw.ImageDraw, texto: str, fonte, largura: int) -> list[str]:
    linhas = []
    for paragrafo in texto.splitlines() or [texto]:
        palavras = paragrafo.split()
        atual = ""
        for palavra in palavras:
            candidato = f"{atual} {palavra}".strip()
            if atual and draw.textbbox((0, 0), candidato, font=fonte)[2] > largura:
                linhas.append(atual)
                atual = palavra
            else:
                atual = candidato
        if atual:
            linhas.append(atual)
    return linhas or [""]


def _aplicar_texto_slide(imagem: Image.Image, texto: str, arraste_lateral: bool):
    draw = ImageDraw.Draw(imagem, "RGBA")
    margem = max(48, imagem.width // 14)
    largura = imagem.width - (margem * 2)
    largura_texto = int(largura * 0.86)
    tamanho_fonte = max(34, imagem.width // 13)
    fonte = _carregar_fonte(tamanho_fonte)
    linhas = _quebrar_texto(draw, texto.strip(), fonte, largura_texto)
    # Mantém o texto grande, mas reduz a fonte quando o título é muito extenso.
    while len(linhas) > 5 and tamanho_fonte > 34:
        tamanho_fonte = max(34, tamanho_fonte - 4)
        fonte = _carregar_fonte(tamanho_fonte)
        linhas = _quebrar_texto(draw, texto.strip(), fonte, largura_texto)
    altura_linha = max(42, int(draw.textbbox((0, 0), "Ag", font=fonte)[3] * 1.18))
    altura_caixa = altura_linha * len(linhas) + max(42, imagem.height // 35)
    topo = max(margem, imagem.height - altura_caixa - margem)
    draw.rounded_rectangle(
        (margem - 22, topo - 18, imagem.width - margem + 22, topo + altura_caixa),
        radius=18,
        fill=(0, 0, 0, 178),
    )
    for indice, linha in enumerate(linhas):
        draw.text((margem, topo + indice * altura_linha), linha, font=fonte, fill=(255, 255, 255, 255))
    if arraste_lateral:
        aviso = "Arraste para o lado 👉"
        fonte_aviso = _carregar_fonte(max(24, imagem.width // 34))
        caixa = draw.textbbox((0, 0), aviso, font=fonte_aviso)
        largura_aviso = caixa[2] - caixa[0]
        x = imagem.width - largura_aviso - margem
        y = max(18, imagem.height - margem // 2 - (caixa[3] - caixa[1]))
        draw.rounded_rectangle((x - 14, y - 8, imagem.width - margem + 14, y + caixa[3] - caixa[1] + 8), radius=12, fill=(0, 0, 0, 190))
        draw.text((x, y), aviso, font=fonte_aviso, fill=(255, 255, 255, 255))


def _aplicar_identidade(
    imagem_bytes: bytes,
    logo_bytes: bytes | None,
    referencia_bytes: bytes | None,
    dimensoes: tuple[int, int],
    texto_slide: str = "",
    arraste_lateral: bool = False,
) -> str:
    if referencia_bytes:
        with Image.open(io.BytesIO(referencia_bytes)) as referencia_original:
            imagem = ImageOps.fit(
                ImageOps.exif_transpose(referencia_original).convert("RGBA"),
                dimensoes,
                method=Image.Resampling.LANCZOS,
            )
    else:
        with Image.open(io.BytesIO(imagem_bytes)) as original:
            imagem = ImageOps.fit(
                ImageOps.exif_transpose(original).convert("RGBA"),
                dimensoes,
                method=Image.Resampling.LANCZOS,
            )

    if texto_slide.strip():
        _aplicar_texto_slide(imagem, texto_slide, arraste_lateral)

    if logo_bytes:
        with Image.open(io.BytesIO(logo_bytes)) as logo_original:
            logo = ImageOps.exif_transpose(logo_original).convert("RGBA")
        limite = (max(100, int(imagem.width * 0.16)), max(70, int(imagem.height * 0.10)))
        logo.thumbnail(limite, Image.Resampling.LANCZOS)
        margem = max(20, imagem.width // 30)
        imagem.alpha_composite(logo, (margem, margem))

    saida = io.BytesIO()
    imagem.convert("RGB").save(saida, format="PNG", optimize=True)
    return base64.b64encode(saida.getvalue()).decode("ascii")


@router.post("/gerar-imagem")
async def gerar_imagem_de_marca(
    cliente_id: UUID = Form(...),
    formato: str = Form(...),
    descricao: str = Form(..., min_length=3, max_length=1500),
    tom_visual: str = Form(default="", max_length=120),
    tamanho: str = Form(default="1080x1080"),
    quantidade: int = Form(default=1, ge=1, le=20),
    textos_carrossel: str | None = Form(default=None),
    descricoes_carrossel: str | None = Form(default=None),
    referencia: UploadFile | None = File(default=None),
    referencias_carrossel: list[UploadFile] = File(default=[]),
    indices_referencias: str | None = Form(default=None),
    arraste_por_slide: str | None = Form(default=None),
    texto_slide: str | None = Form(default=None, max_length=500),
    arraste_lateral: bool = Form(default=False),
    geracao_texto_id: UUID | None = Form(default=None),
    conteudo_indice: int | None = Form(default=None),
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    if formato not in FORMATOS:
        raise HTTPException(status_code=422, detail="Formato de conteúdo inválido")
    if tamanho not in TAMANHOS_FINAIS:
        raise HTTPException(status_code=422, detail="Proporção inválida")
    if formato != "carrossel" and quantidade != 1:
        raise HTTPException(
            status_code=422,
            detail="A quantidade só pode ser alterada para Carrossel",
        )
    if formato != "carrossel" and not (texto_slide or "").strip():
        raise HTTPException(
            status_code=422,
            detail="Informe o texto grande que deverá aparecer na arte",
        )
    if geracao_texto_id is not None:
        geracao_origem = db.scalar(
            select(GeracaoTexto)
            .join(Conteudo, Conteudo.id == GeracaoTexto.conteudo_id)
            .where(
                GeracaoTexto.id == geracao_texto_id,
                Conteudo.usuario_id == usuario_id,
                Conteudo.cliente_id == cliente_id,
            )
        )
        if geracao_origem is None:
            raise HTTPException(status_code=404, detail="Conteúdo de origem não encontrado")
        if conteudo_indice is None or not 0 <= conteudo_indice < len(geracao_origem.conteudos):
            raise HTTPException(status_code=422, detail="Post de origem inválido")
    textos: list[str] = []
    descricoes_slides: list[str] = []
    if formato == "carrossel":
        try:
            textos = json.loads(textos_carrossel or "[]")
        except json.JSONDecodeError as erro:
            raise HTTPException(status_code=422, detail="Textos do carrossel inválidos") from erro
        if (
            not isinstance(textos, list)
            or len(textos) != quantidade
            or any(not isinstance(texto, str) or not texto.strip() for texto in textos)
        ):
            raise HTTPException(
                status_code=422,
                detail=f"Informe o texto das {quantidade} imagens do carrossel",
            )
        try:
            descricoes_slides = json.loads(descricoes_carrossel or "[]")
        except json.JSONDecodeError as erro:
            raise HTTPException(status_code=422, detail="Descrições das imagens inválidas") from erro
        if (
            not isinstance(descricoes_slides, list)
            or len(descricoes_slides) != quantidade
            or any(not isinstance(item, str) or not item.strip() for item in descricoes_slides)
        ):
            raise HTTPException(
                status_code=422,
                detail=f"Descreva como será cada uma das {quantidade} imagens",
            )
    marca = db.scalar(select(Marca).where(Marca.usuario_id == usuario_id, Marca.cliente_id == cliente_id))
    if marca is None:
        raise HTTPException(status_code=422, detail="Configure a marca deste cliente antes de gerar imagens")
    diretrizes = marca.diretrizes_visuais or {}
    tom_aplicado = tom_visual.strip() or diretrizes.get("tom_visual", "Profissional e equilibrado")

    referencia_bytes = None
    if referencia is not None:
        if referencia.content_type not in MIMES_REFERENCIA:
            raise HTTPException(status_code=422, detail="A referência deve ser PNG, JPEG ou WebP")
        referencia_bytes = await referencia.read(10 * 1024 * 1024 + 1)
        if len(referencia_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="A referência deve ter no máximo 10 MB")

    arraste_slides: list[bool] = []
    if formato == "carrossel":
        try:
            arraste_slides = json.loads(arraste_por_slide or "[]")
        except json.JSONDecodeError as erro:
            raise HTTPException(status_code=422, detail="Configuração de arraste inválida") from erro
        if not isinstance(arraste_slides, list) or len(arraste_slides) != quantidade or any(not isinstance(item, bool) for item in arraste_slides):
            raise HTTPException(status_code=422, detail="Configuração de arraste do carrossel inválida")

    referencias_por_slide: dict[int, bytes] = {}
    if formato == "carrossel":
        try:
            indices = json.loads(indices_referencias or "[]")
        except json.JSONDecodeError as erro:
            raise HTTPException(status_code=422, detail="Índices das referências inválidos") from erro
        if not isinstance(indices, list) or len(indices) != len(referencias_carrossel):
            raise HTTPException(status_code=422, detail="Referências do carrossel inválidas")
        for indice, arquivo in zip(indices, referencias_carrossel):
            if not isinstance(indice, int) or not 0 <= indice < quantidade:
                raise HTTPException(status_code=422, detail="Índice de referência inválido")
            if arquivo.content_type not in MIMES_REFERENCIA:
                raise HTTPException(status_code=422, detail="As referências devem ser PNG, JPEG ou WebP")
            dados = await arquivo.read(10 * 1024 * 1024 + 1)
            if len(dados) > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Cada referência deve ter no máximo 10 MB")
            referencias_por_slide[indice] = dados

    briefing = SimpleNamespace(
        tema=descricao,
        intencao=f"Criar imagem para {formato}",
        perspectiva="Aplicar fielmente a identidade visual da marca",
        tom_de_voz=tom_aplicado,
    )
    dimensoes_finais, tamanho_modelo = TAMANHOS_FINAIS[tamanho]
    try:
        semaforo = asyncio.Semaphore(4)

        async def gerar_slide(indice: int):
            texto_slide = textos[indice - 1].strip() if textos else descricao
            descricao_slide = (
                descricoes_slides[indice - 1].strip() if descricoes_slides else descricao
            )
            opcoes = GeracaoImagemRequest(
                prompt_adicional=(
                    f"Formato: {formato}. Paleta obrigatória: {', '.join(marca.paleta)}. "
                    f"Tipografia da marca: {marca.tipografia}. Tom visual: {tom_aplicado}. "
                    f"Diretrizes visuais permanentes: {json.dumps(diretrizes, ensure_ascii=False)}. "
                    f"Direção geral: {descricao}. Composição desta imagem: {descricao_slide}. "
                    f"Crie a peça {indice} de um total de {quantidade}, "
                    f"usando este texto exatamente: {texto_slide}. "
                    "Mantenha unidade visual com as demais peças e varie a composição. "
                "O texto será aplicado pela plataforma; não invente nem altere palavras."
                ),
                paleta=marca.paleta,
                tipografia=marca.tipografia,
                tamanho=tamanho_modelo,
                quantidade=1,
            )
            async with semaforo:
                modelo_slide, geradas = await gerar_imagens(briefing, opcoes)
            return modelo_slide, geradas[0]

        resultados = await asyncio.gather(
            *(gerar_slide(indice) for indice in range(1, quantidade + 1))
        )
        modelo = resultados[0][0]
        itens = [item for _, item in resultados]

        imagens = []
        arquivos_png = []
        logo_principal = marca.logos[0].arquivo if marca.logos else marca.logo
        for indice, item in enumerate(itens):
            imagem_bytes = await _baixar_imagem(item)
            png_base64 = _aplicar_identidade(
                imagem_bytes,
                logo_principal,
                referencias_por_slide.get(indice) if formato == "carrossel" else referencia_bytes,
                dimensoes_finais,
                textos[indice] if textos else (texto_slide or ""),
                arraste_slides[indice] if formato == "carrossel" else arraste_lateral,
            )
            arquivos_png.append(base64.b64decode(png_base64))
            imagens.append(f"data:image/png;base64,{png_base64}")
    except (OmniRouteError, httpx.HTTPError, ValueError, OSError) as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro

    pacote = io.BytesIO()
    with zipfile.ZipFile(pacote, "w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
        for indice, dados_png in enumerate(arquivos_png, start=1):
            arquivo_zip.writestr(f"{formato}-{indice}.png", dados_png)

    return {
        "modelo": modelo,
        "formato": formato,
        "tamanho": tamanho,
        "imagens": imagens,
        "pacote_zip": f"data:application/zip;base64,{base64.b64encode(pacote.getvalue()).decode('ascii')}",
    }


@router.post("/aprovar-imagem", status_code=status.HTTP_201_CREATED)
def aprovar_imagem(
    dados: AprovacaoImagem,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    if dados.formato not in FORMATOS or dados.tamanho not in TAMANHOS_FINAIS:
        raise HTTPException(status_code=422, detail="Formato ou tamanho inválido")
    marca = db.scalar(select(Marca).where(
        Marca.usuario_id == usuario_id, Marca.cliente_id == dados.cliente_id
    ))
    if marca is None:
        raise HTTPException(status_code=404, detail="Cliente ou marca não encontrado")
    if dados.geracao_texto_id is not None:
        origem = db.scalar(
            select(GeracaoTexto).join(Conteudo, Conteudo.id == GeracaoTexto.conteudo_id).where(
                GeracaoTexto.id == dados.geracao_texto_id,
                Conteudo.usuario_id == usuario_id,
                Conteudo.cliente_id == dados.cliente_id,
            )
        )
        if origem is None or dados.conteudo_indice is None or not 0 <= dados.conteudo_indice < len(origem.conteudos):
            raise HTTPException(status_code=422, detail="Conteúdo de origem inválido")
    prefixo = "data:image/png;base64,"
    if not dados.data_url.startswith(prefixo):
        raise HTTPException(status_code=422, detail="A imagem aprovada deve estar em PNG")
    try:
        arquivo = base64.b64decode(dados.data_url[len(prefixo):], validate=True)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail="Imagem aprovada inválida") from erro
    if not arquivo or len(arquivo) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="A imagem aprovada deve ter no máximo 15 MB")
    geracao = GeracaoImagemSalva(
        usuario_id=usuario_id, cliente_id=dados.cliente_id,
        geracao_texto_id=dados.geracao_texto_id, conteudo_indice=dados.conteudo_indice,
        formato=dados.formato, tamanho=dados.tamanho, modelo=dados.modelo,
        descricao=dados.descricao,
    )
    db.add(geracao); db.flush()
    imagem = ImagemSalva(geracao_imagem_id=geracao.id, arquivo=arquivo, nome=dados.nome)
    db.add(imagem); db.commit(); db.refresh(imagem)
    return {"id": str(imagem.id), "status": "aprovada"}


@router.delete("/imagens/{imagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_imagem_salva(
    imagem_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    imagem = db.scalar(
        select(ImagemSalva)
        .join(GeracaoImagemSalva, GeracaoImagemSalva.id == ImagemSalva.geracao_imagem_id)
        .where(ImagemSalva.id == imagem_id, GeracaoImagemSalva.usuario_id == usuario_id)
    )
    if imagem is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    geracao_id = imagem.geracao_imagem_id
    db.delete(imagem); db.flush()
    restante = db.scalar(select(ImagemSalva.id).where(ImagemSalva.geracao_imagem_id == geracao_id))
    if restante is None:
        geracao = db.get(GeracaoImagemSalva, geracao_id)
        if geracao: db.delete(geracao)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
