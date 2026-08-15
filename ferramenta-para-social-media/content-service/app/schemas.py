from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


FormatoConteudo = Literal["post_unico", "carrossel", "reels", "story"]
StatusConteudo = Literal["rascunho", "pronto_para_gerar", "arquivado"]
FrameworkConteudo = Literal[
    "AIDA",
    "PAS",
    "BAB",
    "4Ps",
    "FAB",
    "ACCA",
    "QUEST",
    "Storytelling",
    "Jornada do Herói",
    "Educacional",
    "Lista",
    "Comparação",
    "Mito versus verdade",
    "Problema e solução",
    "Estudo de caso",
]
TecnicaConteudo = Literal[
    "copywriting",
    "storytelling",
    "persuasao",
    "pnl",
    "prova_social",
    "autoridade",
    "curiosidade",
    "escassez",
    "urgencia",
    "reciprocidade",
    "antecipacao",
    "aversao_perda",
    "identificacao",
]
NarrativaConteudo = Literal[
    "Conversacional",
    "Direta",
    "Storytelling",
    "Educacional",
    "Emocional",
    "Provocativa",
    "Bastidores",
    "Tutorial passo a passo",
    "Antes e depois",
    "Problema e solução",
]
TamanhoLegenda = Literal["ultracurta", "curta", "media", "longa", "maxima"]


class QuantidadesFormatos(BaseModel):
    post_unico: int = Field(default=0, ge=0, le=10)
    carrossel: int = Field(default=0, ge=0, le=10)
    reels: int = Field(default=0, ge=0, le=10)
    story: int = Field(default=0, ge=0, le=10)

    @property
    def total(self) -> int:
        return self.post_unico + self.carrossel + self.reels + self.story

    @model_validator(mode="after")
    def limitar_total(self):
        if self.total > 20:
            raise ValueError("A quantidade total não pode ultrapassar 20 conteúdos")
        return self


class NarrativasFormatos(BaseModel):
    post_unico: NarrativaConteudo = "Conversacional"
    carrossel: NarrativaConteudo = "Conversacional"
    reels: NarrativaConteudo = "Conversacional"
    story: NarrativaConteudo = "Conversacional"
    legenda: NarrativaConteudo = "Conversacional"


class RegrasTexto(BaseModel):
    voz_ativa: bool = True
    comunicacao_um_para_um: bool = True
    perspectiva_emissor: str = "eu"
    perspectiva_leitor: str = "você"
    hook_maximo_caracteres: int = 125
    usar_paragrafos_curtos: bool = True
    informar_contagem_caracteres: bool = True
    informar_contagem_palavras: bool = True


class ConteudoBase(BaseModel):
    cliente_id: UUID | None = None
    intencao: str = Field(min_length=3, max_length=500)
    tema: str = Field(min_length=3, max_length=300)
    perspectiva: str = Field(min_length=3, max_length=500)
    modelo: FrameworkConteudo
    tom_de_voz: str = Field(min_length=2, max_length=80)
    formato: FormatoConteudo | None = None
    quantidades: QuantidadesFormatos = Field(default_factory=QuantidadesFormatos)
    narrativas: NarrativasFormatos = Field(default_factory=NarrativasFormatos)
    tamanho_legenda: TamanhoLegenda = "media"
    observacoes: str | None = Field(default=None, max_length=2000)
    arsenal_campos: list[str] = Field(default_factory=list, max_length=30)
    instrucoes_ia: str | None = Field(default=None, max_length=5000)
    tecnicas: list[TecnicaConteudo] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def normalizar_formatos(self):
        mapa = {
            "post_unico": "post_unico",
            "carrossel": "carrossel",
            "reels": "reels",
            "story": "story",
        }
        if self.quantidades.total == 0 and self.formato:
            setattr(self.quantidades, mapa[self.formato], 1)
        if self.quantidades.total == 0:
            raise ValueError("Informe a quantidade de ao menos um formato")
        if self.formato is None:
            self.formato = next(
                nome
                for nome in ("post_unico", "carrossel", "reels", "story")
                if getattr(self.quantidades, nome) > 0
            )
        return self


class ConteudoCreate(ConteudoBase):
    status: StatusConteudo = "rascunho"


class ConteudoUpdate(BaseModel):
    cliente_id: UUID | None = None
    intencao: str | None = Field(default=None, min_length=3, max_length=500)
    tema: str | None = Field(default=None, min_length=3, max_length=300)
    perspectiva: str | None = Field(default=None, min_length=3, max_length=500)
    modelo: FrameworkConteudo | None = None
    tom_de_voz: str | None = Field(default=None, min_length=2, max_length=80)
    formato: FormatoConteudo | None = None
    quantidades: QuantidadesFormatos | None = None
    narrativas: NarrativasFormatos | None = None
    tamanho_legenda: TamanhoLegenda | None = None
    observacoes: str | None = Field(default=None, max_length=2000)
    arsenal_campos: list[str] | None = Field(default=None, max_length=30)
    instrucoes_ia: str | None = Field(default=None, max_length=5000)
    status: StatusConteudo | None = None
    tecnicas: list[TecnicaConteudo] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def validar_alteracao(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        if self.quantidades is not None and self.quantidades.total == 0:
            raise ValueError("Informe a quantidade de ao menos um formato")
        return self


class ConteudoResponse(ConteudoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    status: StatusConteudo
    criado_em: datetime
    atualizado_em: datetime
    regras_texto: RegrasTexto = Field(default_factory=RegrasTexto)


class ConteudoGerado(BaseModel):
    formato: FormatoConteudo
    titulo: str
    slides: list[str] = Field(default_factory=list)
    roteiro: list[str] = Field(default_factory=list)
    telas: list[str] = Field(default_factory=list)
    legenda: str
    hashtags: list[str] = Field(default_factory=list)
    contagem_caracteres: int = Field(ge=0)
    contagem_palavras: int = Field(ge=0)


class GeracaoResponse(BaseModel):
    conteudo_id: UUID
    modelo: str
    conteudos: list[ConteudoGerado]


class GeracaoHistoricoResponse(GeracaoResponse):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    criado_em: datetime


class GeracaoUpdate(BaseModel):
    conteudos: list[ConteudoGerado] = Field(min_length=1, max_length=20)


class GeracaoImagemRequest(BaseModel):
    prompt_adicional: str | None = Field(default=None, max_length=1500)
    paleta: list[str] = Field(default_factory=list, max_length=8)
    tipografia: str | None = Field(default=None, max_length=120)
    tamanho: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quantidade: int = Field(default=1, ge=1, le=4)


class ImagemGerada(BaseModel):
    url: str | None = None
    b64_json: str | None = None
    prompt_revisado: str | None = None

    @model_validator(mode="after")
    def exigir_imagem(self):
        if not self.url and not self.b64_json:
            raise ValueError("A resposta não contém URL nem imagem em base64")
        return self


class GeracaoImagemResponse(BaseModel):
    conteudo_id: UUID
    modelo: str
    imagens: list[ImagemGerada]
