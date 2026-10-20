"""
Testes do cálculo de consumo (consolidador.calcular_consumo).

A função compara duas medições seguidas da mesma impressora e
devolve quanto os suprimentos caíram, em média:

    toner caiu de 60% para 57%  ->  consumo de 3

Se o nível subiu, houve troca do suprimento, e isso não é
consumo. Esses casos são ignorados.

Os dois parâmetros chegam como texto JSON, porque é assim que
os suprimentos são guardados no banco.
"""

import json

import pytest

from consolidador import calcular_consumo


def suprimentos(**valores):
    """Monta o texto JSON como ele é gravado no banco."""

    return json.dumps(valores, ensure_ascii=False)


# ================================================================
# CÁLCULO NORMAL
# ================================================================

def test_queda_de_um_suprimento():
    inicial = suprimentos(toner_preto=60)
    final = suprimentos(toner_preto=57)

    assert calcular_consumo(inicial, final) == 3


def test_media_entre_varios_suprimentos():
    """Caiu 3 em um e 5 no outro: a média é 4."""

    inicial = suprimentos(toner_preto=60, unidade_imagem=80)
    final = suprimentos(toner_preto=57, unidade_imagem=75)

    assert calcular_consumo(inicial, final) == 4


def test_impressora_colorida_com_cinco_suprimentos():
    inicial = suprimentos(
        toner_preto=50,
        toner_ciano=40,
        toner_magenta=30,
        toner_amarelo=20,
        unidade_imagem=10
    )

    final = suprimentos(
        toner_preto=48,
        toner_ciano=38,
        toner_magenta=28,
        toner_amarelo=18,
        unidade_imagem=8
    )

    # todos caíram 2
    assert calcular_consumo(inicial, final) == 2


def test_aceita_valores_em_texto():
    """O banco pode devolver os percentuais como texto."""

    inicial = suprimentos(toner_preto="60")
    final = suprimentos(toner_preto="57.5")

    assert calcular_consumo(inicial, final) == 2.5


# ================================================================
# REPOSIÇÃO DE SUPRIMENTO
# ================================================================

def test_aumento_de_nivel_nao_conta_como_consumo():
    """Subir de 4% para 95% é troca de toner, não consumo."""

    inicial = suprimentos(toner_preto=4)
    final = suprimentos(toner_preto=95)

    assert calcular_consumo(inicial, final) == 0


def test_media_ignora_o_suprimento_reposto():
    """
    O preto foi trocado (sobe) e a unidade de imagem caiu 2.
    O resultado deve ser 2, e não a média com o valor negativo.
    """

    inicial = suprimentos(toner_preto=3, unidade_imagem=50)
    final = suprimentos(toner_preto=90, unidade_imagem=48)

    assert calcular_consumo(inicial, final) == 2


def test_sem_mudanca_de_nivel():
    inicial = suprimentos(toner_preto=60, unidade_imagem=80)
    final = suprimentos(toner_preto=60, unidade_imagem=80)

    assert calcular_consumo(inicial, final) == 0


# ================================================================
# LISTAS DIFERENTES DE SUPRIMENTOS
# ================================================================

def test_suprimento_que_sumiu_na_segunda_medicao():
    """A impressora mudou de COLOR para MONO: o ciano não existe mais."""

    inicial = suprimentos(toner_preto=60, toner_ciano=40)
    final = suprimentos(toner_preto=56)

    # considera apenas o preto, que caiu 4
    assert calcular_consumo(inicial, final) == 4


def test_suprimento_novo_na_segunda_medicao():
    """Suprimento que não existia antes não entra na conta."""

    inicial = suprimentos(toner_preto=60)
    final = suprimentos(toner_preto=58, toner_ciano=90)

    assert calcular_consumo(inicial, final) == 2


# ================================================================
# DADOS AUSENTES OU INVÁLIDOS
# ================================================================

@pytest.mark.parametrize("inicial,final", [
    (None, None),
    (None, suprimentos(toner_preto=50)),
    (suprimentos(toner_preto=50), None),
    ("", ""),
    ("", suprimentos(toner_preto=50)),
])
def test_medicao_faltando_resulta_em_zero(inicial, final):
    """A primeira medição do dia não tem anterior para comparar."""

    assert calcular_consumo(inicial, final) == 0


@pytest.mark.parametrize("texto", [
    "isto não é json",
    "{quebrado",
])
def test_json_invalido_resulta_em_zero(texto):
    """Dado corrompido no banco não pode derrubar a consolidação."""

    assert calcular_consumo(texto, suprimentos(toner_preto=50)) == 0
    assert calcular_consumo(suprimentos(toner_preto=50), texto) == 0


def test_valor_que_nao_e_numero_e_ignorado():
    """O preto tem valor inválido; a conta usa só a unidade de imagem."""

    inicial = suprimentos(toner_preto="vazio", unidade_imagem=50)
    final = suprimentos(toner_preto="vazio", unidade_imagem=47)

    assert calcular_consumo(inicial, final) == 3


def test_dicionario_vazio_resulta_em_zero():
    assert calcular_consumo(suprimentos(), suprimentos()) == 0


# ================================================================
# GARANTIAS GERAIS
# ================================================================

def test_consumo_nunca_e_negativo():
    """Qualquer combinação de níveis deve produzir zero ou mais."""

    for inicio in range(0, 101, 10):
        for fim in range(0, 101, 10):

            resultado = calcular_consumo(
                suprimentos(toner_preto=inicio),
                suprimentos(toner_preto=fim)
            )

            assert resultado >= 0


def test_consumo_de_uma_medicao_real_do_banco():
    """Formato igual ao que o monitor grava, com acentos e nomes reais."""

    inicial = '{"toner_preto": 62, "unidade_imagem": 88}'
    final = '{"toner_preto": 60, "unidade_imagem": 84}'

    # caiu 2 e 4: média 3
    assert calcular_consumo(inicial, final) == 3
