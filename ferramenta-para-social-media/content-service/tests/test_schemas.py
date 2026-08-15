import pytest
from pydantic import ValidationError

from app.schemas import ConteudoCreate, ConteudoUpdate, QuantidadesFormatos


def test_aceita_briefing_valido():
    briefing = ConteudoCreate(
        intencao="Ensinar organização",
        tema="Calendário editorial",
        perspectiva="Passos práticos para autônomos",
        modelo="AIDA",
        tom_de_voz="Educativo",
        formato="carrossel",
        tecnicas=["copywriting", "prova_social", "curiosidade"],
    )

    assert briefing.status == "rascunho"
    assert briefing.formato == "carrossel"
    assert briefing.tecnicas == ["copywriting", "prova_social", "curiosidade"]


def test_rejeita_formato_desconhecido():
    with pytest.raises(ValidationError):
        ConteudoCreate(
            intencao="Ensinar organização",
            tema="Calendário editorial",
            perspectiva="Passos práticos para autônomos",
            modelo="AIDA",
            tom_de_voz="Educativo",
            formato="podcast",
        )


def test_atualizacao_exige_um_campo():
    with pytest.raises(ValidationError):
        ConteudoUpdate()


def test_rejeita_framework_desconhecido():
    with pytest.raises(ValidationError):
        ConteudoCreate(
            intencao="Ensinar organização",
            tema="Calendário editorial",
            perspectiva="Passos práticos para autônomos",
            modelo="Framework inexistente",
            tom_de_voz="Educativo",
            formato="carrossel",
        )


def test_rejeita_tecnica_desconhecida():
    with pytest.raises(ValidationError):
        ConteudoCreate(
            intencao="Ensinar organização",
            tema="Calendário editorial",
            perspectiva="Passos práticos para autônomos",
            modelo="AIDA",
            tom_de_voz="Educativo",
            formato="carrossel",
            tecnicas=["tecnica_inexistente"],
        )


def test_limita_quantidade_de_tecnicas():
    with pytest.raises(ValidationError):
        ConteudoCreate(
            intencao="Ensinar organização",
            tema="Calendário editorial",
            perspectiva="Passos práticos para autônomos",
            modelo="AIDA",
            tom_de_voz="Educativo",
            formato="carrossel",
            tecnicas=[
                "copywriting",
                "storytelling",
                "persuasao",
                "pnl",
                "prova_social",
                "autoridade",
                "curiosidade",
                "escassez",
                "urgencia",
            ],
        )


def test_aceita_lote_com_story_e_narrativas_separadas():
    briefing = ConteudoCreate(
        intencao="Lançar um novo serviço",
        tema="Planejamento de conteúdo",
        perspectiva="Conversa direta com o cliente",
        modelo="BAB",
        tom_de_voz="Profissional",
        quantidades={"post_unico": 2, "carrossel": 1, "reels": 3, "story": 4},
        narrativas={
            "post_unico": "Direta",
            "carrossel": "Educacional",
            "reels": "Storytelling",
            "story": "Bastidores",
            "legenda": "Conversacional",
        },
        tamanho_legenda="longa",
    )

    assert briefing.quantidades.total == 10
    assert briefing.quantidades.story == 4
    assert briefing.narrativas.reels == "Storytelling"
    assert briefing.tamanho_legenda == "longa"


def test_exige_ao_menos_um_conteudo_no_lote():
    with pytest.raises(ValidationError):
        ConteudoCreate(
            intencao="Ensinar organização",
            tema="Calendário editorial",
            perspectiva="Passos práticos para autônomos",
            modelo="AIDA",
            tom_de_voz="Educativo",
        )


def test_limita_lote_a_vinte_conteudos():
    with pytest.raises(ValidationError):
        QuantidadesFormatos(post_unico=10, carrossel=10, reels=1)
