"""
Testes da consolidação que roda depois de cada coleta.

Depois de gravar as medições, o monitor consolida **apenas o
dia daquela coleta** (consolidador.consolidar_ultimo_dia).
Reprocessar o histórico inteiro a cada coleta funcionaria, mas
seria desperdício: os dias anteriores já estão fechados.

O dia escolhido vem da medição mais recente do banco, não do
relógio do sistema. Isso evita dois problemas:

    - a coleta que começa às 23h59 e termina à 00h00
    - o servidor da nuvem em um fuso horário diferente do seu

Os testes abaixo cobrem a escolha do dia e o conteúdo gravado.
"""

import banco

from consolidador import consolidar_ultimo_dia


def consolidacoes(conexao):
    """Devolve as consolidações no formato (data, local, ...)."""

    return banco.buscar_consolidacoes(conexao)


# ================================================================
# ESCOLHA DO DIA
# ================================================================

def test_consolida_o_dia_da_medicao_mais_recente(
    conexao,
    gravar_medicao
):
    gravar_medicao("2026-11-01 08:00:00")
    gravar_medicao("2026-11-01 18:00:00")
    gravar_medicao("2026-11-03 09:00:00")

    consolidar_ultimo_dia(conexao)

    gravadas = consolidacoes(conexao)

    assert len(gravadas) == 1
    assert gravadas[0][0] == "2026-11-03"


def test_nao_reprocessa_os_dias_anteriores(conexao, gravar_medicao):
    """
    O ganho da função é justamente não mexer no que já passou.

    Se ela voltar a consolidar o histórico inteiro, este teste
    encontra três dias em vez de um.
    """

    gravar_medicao("2026-11-01 08:00:00")
    gravar_medicao("2026-11-02 08:00:00")
    gravar_medicao("2026-11-03 08:00:00")

    consolidar_ultimo_dia(conexao)

    dias = [registro[0] for registro in consolidacoes(conexao)]

    assert dias == ["2026-11-03"]


def test_coleta_que_atravessa_a_meia_noite(conexao, gravar_medicao):
    """
    Uma coleta iniciada às 23h59 grava medições nos dois dias.
    O dia consolidado é o da medição mais recente.
    """

    gravar_medicao("2026-11-03 23:59:58", ip="192.168.0.2")
    gravar_medicao("2026-11-04 00:00:02", ip="192.168.0.3")

    consolidar_ultimo_dia(conexao)

    dias = [registro[0] for registro in consolidacoes(conexao)]

    assert dias == ["2026-11-04"]


def test_historico_vazio_nao_quebra(conexao):
    """
    Na primeira execução no servidor não existe medição alguma.
    A consolidação precisa apenas não fazer nada.
    """

    assert consolidar_ultimo_dia(conexao) == 0

    assert consolidacoes(conexao) == []


# ================================================================
# CONTEÚDO GRAVADO
# ================================================================

def test_conta_uma_impressora_por_registro(conexao, gravar_medicao):
    gravar_medicao("2026-11-03 08:00:00", ip="192.168.0.2", local="Diretoria")
    gravar_medicao("2026-11-03 08:00:00", ip="192.168.0.3", local="Fiscal")
    gravar_medicao("2026-11-03 08:00:00", ip="192.168.0.4", local="Almoxarifado")

    processadas = consolidar_ultimo_dia(conexao)

    assert processadas == 3
    assert len(consolidacoes(conexao)) == 3


def test_soma_online_e_offline_do_dia(conexao, gravar_medicao):
    gravar_medicao("2026-11-03 08:00:00", status_rede="online")
    gravar_medicao("2026-11-03 09:00:00", status_rede="online")
    gravar_medicao("2026-11-03 10:00:00", status_rede="offline")

    consolidar_ultimo_dia(conexao)

    registro = consolidacoes(conexao)[0]

    total_medicoes = registro[4]
    online = registro[5]
    offline = registro[6]

    assert total_medicoes == 3
    assert online == 2
    assert offline == 1


def test_calcula_o_consumo_entre_as_medicoes(conexao, gravar_medicao):
    """
    O toner cai de 60% para 54% em três medições, ou seja 3
    pontos por intervalo. O consumo médio do dia deve ser 3.
    """

    gravar_medicao(
        "2026-11-03 08:00:00",
        suprimentos={"toner_preto": 60}
    )
    gravar_medicao(
        "2026-11-03 09:00:00",
        suprimentos={"toner_preto": 57}
    )
    gravar_medicao(
        "2026-11-03 10:00:00",
        suprimentos={"toner_preto": 54}
    )

    consolidar_ultimo_dia(conexao)

    consumo_medio = consolidacoes(conexao)[0][10]

    assert consumo_medio == 3


def test_consolidar_de_novo_atualiza_em_vez_de_duplicar(
    conexao,
    gravar_medicao
):
    """
    Na nuvem a consolidação roda depois de **cada** coleta, no
    mesmo dia. Sem a atualização, o dia apareceria repetido na
    aba Análise a cada 10 minutos.
    """

    gravar_medicao("2026-11-03 08:00:00")

    consolidar_ultimo_dia(conexao)

    gravar_medicao("2026-11-03 09:00:00")

    consolidar_ultimo_dia(conexao)

    gravadas = consolidacoes(conexao)

    assert len(gravadas) == 1
    assert gravadas[0][4] == 2


# ================================================================
# CONSULTA DO BANCO
# ================================================================

def test_buscar_ultimo_dia_devolve_none_com_banco_vazio(conexao):
    assert banco.buscar_ultimo_dia_historico(conexao) is None


def test_buscar_ultimo_dia_ignora_a_ordem_de_gravacao(
    conexao,
    gravar_medicao
):
    """
    O dia mais recente é o da data, não o da última linha
    inserida. Gravamos fora de ordem de propósito.
    """

    gravar_medicao("2026-11-05 08:00:00")
    gravar_medicao("2026-11-01 08:00:00")

    assert banco.buscar_ultimo_dia_historico(conexao) == "2026-11-05"
