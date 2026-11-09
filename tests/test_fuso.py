"""
Testes do fuso horário das medições.

O sistema é desenvolvido no Brasil e publicado num servidor que
roda em UTC. Se a hora da medição viesse do relógio do servidor,
duas coisas quebrariam:

    1. O painel mostraria a medição 3 horas no futuro e avisaria
       "sistema desatualizado" o tempo todo.

    2. A consolidação agrupa por dia recortando o texto da data.
       Com o servidor em UTC, o dia viraria às 21h de Brasília, e
       uma coleta feita depois disso cairia no dia seguinte.

O segundo é o grave: erra o relatório sem dar nenhum sinal na
tela. Estes testes existem para que ele não volte.
"""

from datetime import datetime, timedelta, timezone

import io
import re

import pytest

import banco
import config
import consolidador


# ================================================================
# UM SERVIDOR FINGINDO RODAR EM UTC
# ================================================================

class ServidorEmUTC:
    """
    Substitui o datetime do banco.py por um que finge estar num
    servidor em UTC, como o da nuvem.

    O instante escolhido é proposital: 10/11 às 01:30 em UTC é
    09/11 às 22:30 em Brasília. Ou seja, é um horário em que os
    dois fusos discordam até do **dia**.
    """

    INSTANTE = datetime(
        2026, 11, 10, 1, 30, 0,
        tzinfo=timezone.utc
    )

    # Como o sistema deve gravar: hora de Brasília
    ESPERADO = "2026-11-09 22:30:00"

    # Como estaria errado: hora do servidor
    SE_ESTIVESSE_ERRADO = "2026-11-10 01:30:00"

    @classmethod
    def now(cls, fuso=None):
        if fuso is None:
            # datetime.now() sem argumento devolve a hora local
            # do servidor — em UTC, e sem dizer que é UTC.
            return cls.INSTANTE.replace(tzinfo=None)

        return cls.INSTANTE.astimezone(fuso)


@pytest.fixture
def servidor_em_utc(monkeypatch):
    """Faz o banco.py enxergar o relógio de um servidor em UTC."""

    monkeypatch.setattr(banco, "datetime", ServidorEmUTC)

    return ServidorEmUTC


# ================================================================
# O FUSO CONFIGURADO
# ================================================================

def test_fuso_do_projeto_e_o_de_brasilia():
    deslocamento = config.FUSO_HORARIO.utcoffset(None)

    assert deslocamento == timedelta(hours=-3)


def test_fuso_tem_nome_legivel():
    # Aparece em mensagens de erro e ao depurar; sem nome, o
    # Python mostraria apenas "UTC-03:00".
    assert "Bras" in config.FUSO_HORARIO.tzname(None)


# ================================================================
# A HORA GRAVADA
# ================================================================

def test_medicao_usa_o_fuso_do_projeto_e_nao_o_do_servidor(
    conexao, impressora_exemplo, servidor_em_utc
):
    banco.salvar_medicao(conexao, impressora_exemplo)

    registros = banco.buscar_medicoes_recentes(conexao, 1)

    gravado = registros[0][0]

    assert gravado == servidor_em_utc.ESPERADO

    assert gravado != servidor_em_utc.SE_ESTIVESSE_ERRADO


def test_formato_gravado_continua_sem_o_fuso(
    conexao, impressora_exemplo, servidor_em_utc
):
    # A consolidação recorta a data com substr(data_hora, 1, 10).
    # Se o fuso fosse parar no texto, o recorte continuaria certo,
    # mas a comparação entre datas deixaria de funcionar.
    banco.salvar_medicao(conexao, impressora_exemplo)

    gravado = banco.buscar_medicoes_recentes(conexao, 1)[0][0]

    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
        gravado
    ), f"formato inesperado: {gravado}"


def test_hora_gravada_acompanha_o_relogio_do_sistema(
    conexao, impressora_exemplo
):
    # Sem nenhum relógio falso: a medição tem de ficar perto da
    # hora de agora no fuso do projeto.
    antes = datetime.now(config.FUSO_HORARIO)

    banco.salvar_medicao(conexao, impressora_exemplo)

    gravado = datetime.strptime(
        banco.buscar_medicoes_recentes(conexao, 1)[0][0],
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=config.FUSO_HORARIO)

    diferenca = abs((gravado - antes).total_seconds())

    assert diferenca < 60, (
        "a medição foi gravada com mais de um minuto de "
        f"diferença da hora atual: {diferenca} segundos"
    )


# ================================================================
# O DIA DA CONSOLIDAÇÃO
# ================================================================

def test_dia_da_consolidacao_segue_o_fuso_do_projeto(
    conexao, impressora_exemplo, servidor_em_utc
):
    """
    Uma coleta às 22h30 de Brasília pertence ao dia 09, mesmo
    que no servidor já seja dia 10.
    """

    banco.salvar_medicao(conexao, impressora_exemplo)

    dia = banco.buscar_ultimo_dia_historico(conexao)

    assert dia == "2026-11-09"


def test_consolidacao_grava_no_dia_de_brasilia(
    conexao, impressora_exemplo, servidor_em_utc
):
    banco.salvar_medicao(conexao, impressora_exemplo)

    consolidador.consolidar_ultimo_dia(conexao)

    registros = banco.buscar_consolidacoes(conexao)

    assert len(registros) == 1

    assert registros[0][0] == "2026-11-09"


# ================================================================
# ARAME FARPADO
# ================================================================

ARQUIVOS_DO_SISTEMA = [
    "banco.py",
    "monitor.py",
    "app.py",
    "consolidador.py",
    "importar_planilha.py",
    "planilha.py",
    "config.py",
]


def test_nenhum_relogio_sem_fuso_no_codigo():
    """
    Impede que alguém volte a escrever datetime.now() sem fuso.

    É assim que o defeito entraria de novo: a chamada funciona
    na máquina de quem desenvolve e só erra no servidor.
    """

    culpados = []

    for nome in ARQUIVOS_DO_SISTEMA:
        caminho = config.PASTA_PROJETO / nome

        if not caminho.exists():
            continue

        codigo = io.open(caminho, encoding="utf-8").read()

        for numero, linha in enumerate(codigo.splitlines(), 1):
            if re.search(r"datetime\.now\(\s*\)", linha):
                culpados.append(f"{nome}:{numero}")

    assert not culpados, (
        "datetime.now() sem fuso horário em: "
        + ", ".join(culpados)
        + ". Use datetime.now(FUSO_HORARIO), do config.py."
    )
