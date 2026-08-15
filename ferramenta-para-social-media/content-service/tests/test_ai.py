import json
from types import SimpleNamespace

import pytest

from app.ai import OmniRouteError, _criar_prompt, _extrair_json, _prompt_imagem
from app.schemas import GeracaoImagemRequest


def test_extrai_json_com_bloco_markdown():
    resposta = _extrair_json('```json\n{"conteudos": []}\n```')
    assert resposta == {"conteudos": []}


def test_rejeita_resposta_sem_conteudos():
    with pytest.raises(OmniRouteError):
        _extrair_json('{"resultado": []}')


def test_prompt_inclui_regras_e_quantidades():
    conteudo = SimpleNamespace(
        intencao="Ensinar",
        tema="Calendário editorial",
        perspectiva="Prática",
        modelo="AIDA",
        tom_de_voz="Educativo",
        tecnicas=["copywriting"],
        observacoes=None,
        quantidades={"post_unico": 1, "carrossel": 2, "reels": 0, "story": 0},
        narrativas={"post_unico": "Direta", "legenda": "Conversacional"},
        tamanho_legenda="media",
    )

    prompt = _criar_prompt(conteudo)
    assert "hook forte com no máximo 125 caracteres" in prompt
    assert json.dumps(conteudo.quantidades, ensure_ascii=False) in prompt
    assert "eu falando diretamente com você" in prompt


def test_prompt_imagem_inclui_identidade_visual():
    conteudo = SimpleNamespace(
        tema="Calendário editorial",
        intencao="Ensinar",
        perspectiva="Prática",
        tom_de_voz="Educativo",
    )
    opcoes = GeracaoImagemRequest(
        paleta=["#112233", "#ffffff"],
        tipografia="Montserrat",
        prompt_adicional="Fundo minimalista",
    )

    prompt = _prompt_imagem(conteudo, opcoes)
    assert "#112233, #ffffff" in prompt
    assert "Montserrat" in prompt
    assert "Fundo minimalista" in prompt
