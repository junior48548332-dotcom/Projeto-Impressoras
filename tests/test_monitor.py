"""
Testes dos modos de execução do monitor.

O monitor tem dois modos:

    python monitor.py              uma coleta e encerra
    python monitor.py --continuo   repete até receber CTRL + C

O primeiro é o que a tarefa agendada do servidor usa. Se ele
voltar a nunca terminar, a tarefa fica pendurada e a coleta
na nuvem para de funcionar — por isso estes testes existem.

Nenhum teste aqui espera o intervalo de verdade: o time.sleep
é substituído, senão cada teste levaria 10 minutos.
"""

import pytest

import banco
import monitor


# ================================================================
# BANCO E COLETA DE MENTIRA
# ================================================================

@pytest.fixture
def coleta_falsa(banco_vazio, cadastro_exemplo, monkeypatch):
    """
    Deixa o monitor rodar contra um banco temporário, com um
    cadastro pronto e sem sortear níveis de toner.

    Devolve a lista de impressoras que o cadastro traz, para o
    teste conferir quantas medições deveriam ser gravadas.
    """

    monitor.preparar_banco()

    conexao = banco.conectar()

    banco.substituir_impressoras(conexao, cadastro_exemplo)

    conexao.close()

    def coletar(impressora):
        return {
            "status_rede": "online",
            "suprimentos": {
                "toner_preto": 50,
                "unidade_imagem": 70
            }
        }

    monkeypatch.setattr(monitor, "coletar", coletar)

    return cadastro_exemplo


@pytest.fixture
def sem_espera(monkeypatch):
    """
    Troca o time.sleep por uma função que conta as chamadas.

    Devolve a lista de esperas pedidas, para o teste conferir
    se o intervalo configurado foi respeitado.
    """

    esperas = []

    monkeypatch.setattr(
        monitor.time,
        "sleep",
        lambda segundos: esperas.append(segundos)
    )

    return esperas


# ================================================================
# COLETA ÚNICA
# ================================================================

def test_coleta_unica_grava_uma_medicao_por_impressora(coleta_falsa):

    total = monitor.coletar_uma_vez()

    assert total == len(coleta_falsa)

    conexao = banco.conectar()

    gravadas = banco.contar_registros(
        conexao,
        "historico_impressoras"
    )

    conexao.close()

    assert gravadas == len(coleta_falsa)


def test_coleta_unica_cria_as_tabelas(banco_vazio, monkeypatch):
    """
    No servidor o banco começa vazio. A coleta precisa criar as
    tabelas sozinha, sem depender de outro comando antes.
    """

    monkeypatch.setattr(
        monitor,
        "coletar",
        lambda impressora: {"status_rede": "online", "suprimentos": {}}
    )

    monitor.coletar_uma_vez()

    conexao = banco.conectar()

    for tabela in (
        "impressoras",
        "historico_impressoras",
        "consolidacao_diaria"
    ):
        assert banco.tabela_existe(conexao, tabela), tabela

    conexao.close()


def test_coleta_unica_nao_espera(coleta_falsa, sem_espera):
    """A coleta única não pode dormir: ela tem que terminar."""

    monitor.coletar_uma_vez()

    assert sem_espera == []


# ================================================================
# CONSOLIDAÇÃO JUNTO DA COLETA
# ================================================================

def test_coleta_consolida_o_dia(coleta_falsa):
    """
    A aba Análise do dashboard lê a consolidação. No servidor
    ninguém roda o consolidador na mão, então a coleta precisa
    consolidar sozinha — senão a Análise fica congelada.
    """

    monitor.coletar_uma_vez()

    conexao = banco.conectar()

    consolidadas = banco.buscar_consolidacoes(conexao)

    conexao.close()

    assert len(consolidadas) == len(coleta_falsa)


def test_modo_continuo_tambem_consolida(coleta_falsa, monkeypatch):
    """
    Sai do laço na primeira espera, depois de uma coleta de
    verdade, e confere que a consolidação aconteceu.
    """

    def parar_na_primeira_espera(segundos):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        monitor.time,
        "sleep",
        parar_na_primeira_espera
    )

    monitor.main([monitor.MODO_CONTINUO])

    conexao = banco.conectar()

    consolidadas = banco.buscar_consolidacoes(conexao)

    conexao.close()

    assert len(consolidadas) == len(coleta_falsa)


def test_consolidacao_cobre_as_medicoes_da_coleta(coleta_falsa):
    """
    Duas coletas no mesmo dia precisam virar duas medições em
    um único registro consolidado, não dois registros.
    """

    monitor.coletar_uma_vez()
    monitor.coletar_uma_vez()

    conexao = banco.conectar()

    consolidadas = banco.buscar_consolidacoes(conexao)

    conexao.close()

    assert len(consolidadas) == len(coleta_falsa)

    for registro in consolidadas:
        total_medicoes = registro[4]

        assert total_medicoes == 2


# ================================================================
# ESCOLHA DO MODO
# ================================================================

def test_sem_argumentos_faz_uma_coleta_e_encerra(coleta_falsa, monkeypatch):
    """
    Este é o teste mais importante do arquivo: é o modo que a
    tarefa agendada usa.

    O time.sleep é trocado por uma função que acusa o problema.
    Assim, se o modo padrão voltar a entrar em laço, o teste
    falha na hora em vez de rodar para sempre.
    """

    def nao_deve_esperar(segundos):
        # pytest.fail interrompe o teste mesmo dentro de um
        # try/except, que é o caso do laço do modo contínuo.
        pytest.fail(
            "o modo padrão entrou em laço: chamou time.sleep"
        )

    monkeypatch.setattr(monitor.time, "sleep", nao_deve_esperar)

    codigo = monitor.main([])

    assert codigo == 0

    conexao = banco.conectar()

    gravadas = banco.contar_registros(
        conexao,
        "historico_impressoras"
    )

    conexao.close()

    assert gravadas == len(coleta_falsa)


def test_modo_continuo_repete_a_coleta(coleta_falsa, sem_espera, monkeypatch):
    """
    O modo contínuo roda para sempre. Para testá-lo, deixamos a
    terceira coleta levantar KeyboardInterrupt, que é o mesmo
    que o CTRL + C faz, e conferimos que o laço parou.
    """

    chamadas = []

    def verificacao_controlada():

        chamadas.append(1)

        if len(chamadas) == 3:
            raise KeyboardInterrupt

        return len(coleta_falsa)

    monkeypatch.setattr(
        monitor,
        "executar_verificacao",
        verificacao_controlada
    )

    codigo = monitor.main([monitor.MODO_CONTINUO])

    assert codigo == 0
    assert len(chamadas) == 3


def test_modo_continuo_espera_o_intervalo_configurado(
    coleta_falsa,
    sem_espera,
    monkeypatch
):
    chamadas = []

    def verificacao_controlada():

        chamadas.append(1)

        if len(chamadas) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        monitor,
        "executar_verificacao",
        verificacao_controlada
    )

    monitor.main([monitor.MODO_CONTINUO])

    assert sem_espera == [monitor.INTERVALO_COLETA]


def test_modo_continuo_segue_depois_de_um_erro(
    coleta_falsa,
    sem_espera,
    monkeypatch
):
    """
    Uma falha de rede não pode derrubar o monitor: ele espera e
    tenta de novo na próxima verificação.
    """

    chamadas = []

    def verificacao_controlada():

        chamadas.append(1)

        if len(chamadas) == 1:
            raise RuntimeError("rede fora do ar")

        if len(chamadas) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        monitor,
        "executar_verificacao",
        verificacao_controlada
    )

    codigo = monitor.main([monitor.MODO_CONTINUO])

    assert codigo == 0
    assert len(chamadas) == 2


# ================================================================
# CÓDIGO DE SAÍDA
# ================================================================

def test_falha_na_coleta_devolve_codigo_de_erro(monkeypatch):
    """
    O servidor usa o código de saída para saber se a tarefa
    agendada funcionou. Falha precisa devolver um valor
    diferente de zero.
    """

    def quebrar():
        raise RuntimeError("banco indisponível")

    monkeypatch.setattr(monitor, "coletar_uma_vez", quebrar)

    assert monitor.main([]) != 0


def test_falha_na_coleta_nao_interrompe_o_programa(monkeypatch, capsys):
    """O erro é explicado na tela, não despejado como traceback."""

    def quebrar():
        raise RuntimeError("banco indisponível")

    monkeypatch.setattr(monitor, "coletar_uma_vez", quebrar)

    monitor.main([])

    saida = capsys.readouterr().out

    assert "banco indisponível" in saida


# ================================================================
# ARGUMENTOS
# ================================================================

@pytest.mark.parametrize("pedido", ["--ajuda", "-h"])
def test_ajuda_nao_coleta_nada(pedido, coleta_falsa, capsys):

    codigo = monitor.main([pedido])

    assert codigo == 0

    conexao = banco.conectar()

    gravadas = banco.contar_registros(
        conexao,
        "historico_impressoras"
    )

    conexao.close()

    assert gravadas == 0

    assert "--continuo" in capsys.readouterr().out


def test_argumento_errado_nao_coleta_por_engano(coleta_falsa, capsys):
    """
    Quem digita "--continua" quer o modo contínuo. Fazer uma
    coleta única calada seria pior do que avisar.
    """

    codigo = monitor.main(["--continua"])

    assert codigo != 0

    conexao = banco.conectar()

    gravadas = banco.contar_registros(
        conexao,
        "historico_impressoras"
    )

    conexao.close()

    assert gravadas == 0

    assert "--continua" in capsys.readouterr().out
