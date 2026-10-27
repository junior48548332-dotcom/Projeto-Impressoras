"""
Testes de contraste das cores (WCAG 2.1, nível AA).

A norma exige uma diferença mínima de luminosidade entre o texto
e o fundo:

    4.5:1  texto normal          (critério 1.4.3)
    3.0:1  texto grande e ícones (critérios 1.4.3 e 1.4.11)

Se alguém trocar uma cor do dashboard por uma mais clara, estes
testes falham e avisam antes de o problema chegar na tela.

As bordas dos cards não entram na lista: a situação da impressora
é indicada pelo ícone e pelo texto dentro do card, então a borda
é decoração.
"""

import io

import pytest

import config


CSS = config.PASTA_PROJETO / "static" / "css" / "dashboard.css"


# ================================================================
# CÁLCULO DA WCAG
# ================================================================

def componentes(cor):
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def luminancia(cor):
    canais = []

    for valor in componentes(cor):
        c = valor / 255
        canais.append(
            c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        )

    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def contraste(frente, fundo):
    a = luminancia(frente)
    b = luminancia(fundo)

    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


# ================================================================
# COMBINAÇÕES USADAS NO DASHBOARD
# ================================================================

# (descrição, cor do texto, cor do fundo, mínimo exigido)
COMBINACOES = [
    ("Texto geral da página", "#1f2937", "#f4f6f8", 4.5),
    ("Título principal", "#111827", "#ffffff", 3.0),
    ("Subtítulo", "#6b7280", "#ffffff", 4.5),
    ("Relógio e informações do sistema", "#374151", "#ffffff", 4.5),
    ("Contador de atualização", "#2563eb", "#ffffff", 4.5),
    ("Aba inativa", "#374151", "#f9fafb", 4.5),
    ("Aba ativa", "#ffffff", "#1f2937", 4.5),

    ("Contador TOTAL", "#374151", "#ffffff", 3.0),
    ("Contador ONLINE", "#15803d", "#ffffff", 3.0),
    ("Contador OFFLINE", "#6b7280", "#ffffff", 3.0),
    ("Contador ATENÇÃO", "#a16207", "#ffffff", 3.0),
    ("Contador CRÍTICAS", "#dc2626", "#ffffff", 3.0),
    ("Título dos contadores", "#6b7280", "#ffffff", 4.5),

    ("Card normal", "#166534", "#ecfdf3", 4.5),
    ("Card atenção", "#92400e", "#fffbeb", 4.5),
    ("Card crítico", "#991b1b", "#fef2f2", 4.5),
    ("Card offline", "#4b5563", "#f3f4f6", 4.5),

    ("Ponto do sistema (atualizado)", "#16a34a", "#ffffff", 3.0),
    ("Ponto do sistema (desatualizado)", "#dc2626", "#ffffff", 3.0),

    ("Texto da análise", "#1f2937", "#ffffff", 4.5),
    ("Legenda dos indicadores", "#6b7280", "#ffffff", 4.5),
    ("Barra verde", "#15803d", "#e5e7eb", 3.0),
    ("Barra amarela", "#a16207", "#e5e7eb", 3.0),
    ("Barra vermelha", "#dc2626", "#e5e7eb", 3.0),
    ("Cabeçalho da tabela", "#111827", "#f8fafc", 4.5),

    ("Foco do teclado", "#1d4ed8", "#ffffff", 3.0),
]


# ================================================================
# CONFERÊNCIA DO CÁLCULO
# ================================================================

def test_calculo_bate_com_os_extremos_conhecidos():
    """Preto no branco dá 21:1; a mesma cor dá 1:1."""

    assert contraste("#000000", "#ffffff") == pytest.approx(21, abs=0.01)
    assert contraste("#ffffff", "#ffffff") == pytest.approx(1, abs=0.01)


def test_calculo_nao_depende_da_ordem():
    assert contraste("#1f2937", "#ffffff") == pytest.approx(
        contraste("#ffffff", "#1f2937")
    )


# ================================================================
# CONTRASTE DE CADA COMBINAÇÃO
# ================================================================

@pytest.mark.parametrize(
    "descricao,frente,fundo,minimo",
    COMBINACOES,
    ids=[combinacao[0] for combinacao in COMBINACOES]
)
def test_contraste_minimo(descricao, frente, fundo, minimo):
    valor = contraste(frente, fundo)

    assert valor >= minimo, (
        f"{descricao}: {frente} sobre {fundo} dá {valor:.2f}:1, "
        f"abaixo do mínimo de {minimo}:1 exigido pela WCAG"
    )


# ================================================================
# LIGAÇÃO COM O CSS
# ================================================================

def test_cores_testadas_existem_no_css():
    """
    Garante que a lista acima acompanha o CSS de verdade.

    Se alguém trocar uma cor no arquivo e esquecer de atualizar
    aqui, este teste avisa.
    """

    css = io.open(CSS, encoding="utf-8").read().lower()

    ignoradas = {
        "#ffffff",   # branco usado como fundo de referência
        "#f9fafb",
        "#f8fafc",
        "#f4f6f8",
        "#e5e7eb",
        "#ecfdf3",
        "#fffbeb",
        "#fef2f2",
        "#f3f4f6",
    }

    usadas = {
        cor.lower()
        for _, frente, fundo, _ in COMBINACOES
        for cor in (frente, fundo)
    }

    faltando = sorted(
        cor for cor in usadas - ignoradas if cor not in css
    )

    assert faltando == [], (
        f"cores testadas que não existem mais no CSS: {faltando}"
    )


def test_css_nao_usa_cinza_claro_demais_em_texto():
    """
    O cinza #9ca3af tem apenas 2.54:1 no branco e já foi usado
    em textos do projeto. Não deve voltar.
    """

    css = io.open(CSS, encoding="utf-8").read().lower()

    assert "color: #9ca3af" not in css
