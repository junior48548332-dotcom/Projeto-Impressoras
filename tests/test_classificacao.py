"""
Testes da classificação dos suprimentos.

Regra do sistema (monitor.classificar_nivel):

    até 5%        -> critico
    de 5% a 20%   -> atencao
    acima de 20%  -> normal

Os limites (5 e 20) são o ponto mais delicado da regra, por isso
são testados um a um.
"""

import pytest

from monitor import classificar_nivel


# ================================================================
# FAIXAS
# ================================================================

@pytest.mark.parametrize("percentual", [0, 1, 3, 5])
def test_ate_cinco_por_cento_e_critico(percentual):
    assert classificar_nivel(percentual) == "critico"


@pytest.mark.parametrize("percentual", [6, 10, 15, 20])
def test_ate_vinte_por_cento_e_atencao(percentual):
    assert classificar_nivel(percentual) == "atencao"


@pytest.mark.parametrize("percentual", [21, 50, 80, 100])
def test_acima_de_vinte_por_cento_e_normal(percentual):
    assert classificar_nivel(percentual) == "normal"


# ================================================================
# LIMITES EXATOS
# ================================================================

@pytest.mark.parametrize("percentual,esperado", [
    (5, "critico"),
    (5.01, "atencao"),
    (20, "atencao"),
    (20.01, "normal"),
])
def test_limites_das_faixas(percentual, esperado):
    """Os valores 5 e 20 pertencem à faixa mais grave."""

    assert classificar_nivel(percentual) == esperado


# ================================================================
# FORMATOS ACEITOS
# ================================================================

@pytest.mark.parametrize("percentual", [3, 3.0, "3", "3.0"])
def test_aceita_numero_inteiro_decimal_ou_texto(percentual):
    """O valor pode vir do banco como texto e deve funcionar igual."""

    assert classificar_nivel(percentual) == "critico"


def test_valor_invalido_gera_erro():
    """Um valor que não é número precisa falhar de forma clara."""

    with pytest.raises(ValueError):
        classificar_nivel("sem nível")


# ================================================================
# SITUAÇÕES FORA DO ESPERADO
# ================================================================

def test_valor_negativo_e_tratado_como_critico():
    """Não deve acontecer, mas se acontecer o alerta é o mais grave."""

    assert classificar_nivel(-10) == "critico"


def test_resultado_e_sempre_um_dos_tres_status():
    """Nenhum percentual pode produzir um status desconhecido."""

    validos = {"critico", "atencao", "normal"}

    for percentual in range(0, 101):
        assert classificar_nivel(percentual) in validos


# ================================================================
# COERÊNCIA COM O RESTO DO SISTEMA
# ================================================================

def test_status_usados_pelo_dashboard():
    """
    O dashboard pinta os cards comparando com estes textos.
    Se algum nome mudar aqui, a cor some da tela.
    """

    assert classificar_nivel(2) == "critico"
    assert classificar_nivel(10) == "atencao"
    assert classificar_nivel(90) == "normal"
