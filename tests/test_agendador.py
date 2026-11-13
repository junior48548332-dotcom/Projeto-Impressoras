"""
Testes da coleta automática pelo servidor.

O plano gratuito do PythonAnywhere não oferece tarefas agendadas
para contas novas, então o próprio servidor web verifica, a cada
requisição, se já passou o intervalo desde a última medição — e,
se passou, dispara uma coleta.

O que estes testes protegem:

    - a coleta não dispara antes da hora;
    - não dispara duas vezes ao mesmo tempo;
    - não fica tentando sem parar quando falha;
    - uma falha na coleta não derruba o painel;
    - vem desligada por padrão.
"""

from datetime import datetime, timedelta

import pytest

import agendador
import app as aplicacao
import banco
import config
import monitor


FORA_DO_INTERVALO = config.INTERVALO_COLETA + 60

DENTRO_DO_INTERVALO = 60


# ================================================================
# PREPARO
# ================================================================

@pytest.fixture(autouse=True)
def estado_limpo():
    """
    Zera o estado do agendador antes de cada teste.

    Ele guarda em memória se há coleta em andamento e quando foi a
    última tentativa. Sem zerar, um teste interferiria no outro.
    """

    agendador._coletando = False
    agendador._ultima_tentativa = None

    yield

    agendador._coletando = False
    agendador._ultima_tentativa = None


@pytest.fixture
def ligada(monkeypatch):
    """Liga a coleta automática, que vem desligada por padrão."""

    monkeypatch.setattr(agendador, "COLETA_WEB", True)


@pytest.fixture
def coleta_falsa(monkeypatch):
    """
    Substitui a coleta de verdade por um contador.

    Devolve uma lista: cada coleta disparada acrescenta um item.
    """

    chamadas = []

    def falsa():
        chamadas.append(1)
        return 48

    monkeypatch.setattr(monitor, "coletar_uma_vez", falsa)

    return chamadas


@pytest.fixture
def relogio_parado(monkeypatch):
    """
    Congela o relógio que o agendador consulta.

    Sem isso não dá para testar o limite exato do intervalo: a
    medição é gravada com precisão de segundos, então "exatamente
    600 segundos atrás" já viraria 600,003 na hora da conferência,
    e a diferença entre >= e > ficaria invisível.
    """

    def congelar(momento):

        class RelogioParado:

            @staticmethod
            def now(fuso=None):
                return momento

            @staticmethod
            def strptime(texto, formato):
                return datetime.strptime(texto, formato)

        monkeypatch.setattr(agendador, "datetime", RelogioParado)

    return congelar


@pytest.fixture
def medicao_em(gravar_medicao):
    """Grava uma medição a tantos segundos atrás."""

    def gravar(segundos_atras):
        momento = (
            datetime.now(config.FUSO_HORARIO)
            - timedelta(seconds=segundos_atras)
        )

        gravar_medicao(
            momento.strftime(config.FORMATO_DATA_HORA)
        )

    return gravar


# ================================================================
# HÁ QUANTO TEMPO FOI A ÚLTIMA MEDIÇÃO
# ================================================================

def test_historico_vazio_esta_na_hora(conexao):
    # Sem nenhuma medição, a primeira coleta é agora.
    assert agendador.segundos_desde_a_ultima_medicao(conexao) is None

    assert agendador.esta_na_hora(conexao) is True


def test_medicao_recente_nao_esta_na_hora(conexao, medicao_em):
    medicao_em(DENTRO_DO_INTERVALO)

    segundos = agendador.segundos_desde_a_ultima_medicao(conexao)

    assert 0 <= segundos < config.INTERVALO_COLETA

    assert agendador.esta_na_hora(conexao) is False


def test_medicao_antiga_esta_na_hora(conexao, medicao_em):
    medicao_em(FORA_DO_INTERVALO)

    segundos = agendador.segundos_desde_a_ultima_medicao(conexao)

    assert segundos >= config.INTERVALO_COLETA

    assert agendador.esta_na_hora(conexao) is True


MOMENTO_FIXO = datetime(
    2026, 11, 13, 12, 0, 0,
    tzinfo=config.FUSO_HORARIO
)


def test_limite_exato_do_intervalo(
    conexao, gravar_medicao, relogio_parado
):
    """No próprio limite já está na hora: a comparação é >=."""

    medicao = MOMENTO_FIXO - timedelta(
        seconds=config.INTERVALO_COLETA
    )

    gravar_medicao(medicao.strftime(config.FORMATO_DATA_HORA))

    relogio_parado(MOMENTO_FIXO)

    assert agendador.segundos_desde_a_ultima_medicao(conexao) == (
        config.INTERVALO_COLETA
    )

    assert agendador.esta_na_hora(conexao) is True


def test_um_segundo_antes_do_limite(
    conexao, gravar_medicao, relogio_parado
):
    medicao = MOMENTO_FIXO - timedelta(
        seconds=config.INTERVALO_COLETA - 1
    )

    gravar_medicao(medicao.strftime(config.FORMATO_DATA_HORA))

    relogio_parado(MOMENTO_FIXO)

    assert agendador.esta_na_hora(conexao) is False


def test_data_ilegivel_nao_quebra(conexao, impressora_exemplo):
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO historico_impressoras (data_hora, ip)
        VALUES ('nao e uma data', '192.168.0.2')
    """)

    conexao.commit()

    # Não pode levantar exceção; devolve None por não conseguir ler.
    assert agendador.segundos_desde_a_ultima_medicao(conexao) is None


# ================================================================
# O DISPARO
# ================================================================

def test_vem_desligada_por_padrao():
    # O padrão protege os testes e a máquina de desenvolvimento,
    # onde quem coleta é o monitor.py --continuo.
    assert config.COLETA_WEB is False


def test_desligada_nao_coleta(conexao, medicao_em, coleta_falsa):
    medicao_em(FORA_DO_INTERVALO)

    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is False

    assert coleta_falsa == []


def test_ligada_e_na_hora_coleta(
    conexao, medicao_em, coleta_falsa, ligada
):
    medicao_em(FORA_DO_INTERVALO)

    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is True

    assert len(coleta_falsa) == 1


def test_ligada_e_fora_de_hora_nao_coleta(
    conexao, medicao_em, coleta_falsa, ligada
):
    medicao_em(DENTRO_DO_INTERVALO)

    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is False

    assert coleta_falsa == []


def test_historico_vazio_dispara_a_primeira_coleta(
    conexao, coleta_falsa, ligada
):
    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is True

    assert len(coleta_falsa) == 1


# ================================================================
# PROTEÇÕES
# ================================================================

def test_nao_tenta_de_novo_logo_em_seguida(
    conexao, medicao_em, coleta_falsa, ligada
):
    """
    A coleta falsa não grava medição nenhuma, então o banco
    continua "na hora" depois da primeira tentativa. Sem a
    proteção, toda atualização do painel dispararia outra coleta.
    """

    medicao_em(FORA_DO_INTERVALO)

    primeira = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    segunda = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert primeira is True

    assert segunda is False

    assert len(coleta_falsa) == 1


def test_uma_coleta_de_cada_vez(
    conexao, medicao_em, coleta_falsa, ligada
):
    medicao_em(FORA_DO_INTERVALO)

    # Finge que uma coleta já está em andamento
    agendador._coletando = True

    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is False

    assert coleta_falsa == []


def test_coleta_que_falha_nao_levanta_excecao(
    conexao, medicao_em, ligada, monkeypatch
):
    def explodir():
        raise RuntimeError("simulador fora do ar")

    monkeypatch.setattr(monitor, "coletar_uma_vez", explodir)

    medicao_em(FORA_DO_INTERVALO)

    # O painel precisa abrir mesmo com a coleta quebrada.
    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is True

    # E a tranca tem de ser liberada, senão nunca mais coletaria.
    assert agendador._coletando is False


def test_erro_no_banco_nao_quebra(
    conexao, coleta_falsa, ligada, monkeypatch
):
    def sem_banco():
        raise OSError("banco indisponível")

    monkeypatch.setattr(agendador, "conectar", sem_banco)

    disparou = agendador.coletar_se_estiver_na_hora(
        em_segundo_plano=False
    )

    assert disparou is False

    assert coleta_falsa == []


# ================================================================
# LIGAÇÃO COM AS ROTAS
# ================================================================

@pytest.fixture
def agendador_falso(monkeypatch):
    """Conta quantas vezes as rotas chamam o agendador."""

    chamadas = []

    def falso(*args, **kwargs):
        chamadas.append(1)
        return False

    monkeypatch.setattr(
        aplicacao,
        "coletar_se_estiver_na_hora",
        falso
    )

    return chamadas


@pytest.fixture
def cliente():
    aplicacao.app.config["TESTING"] = True

    return aplicacao.app.test_client()


def test_rota_do_painel_chama_o_agendador(
    conexao, cliente, agendador_falso
):
    resposta = cliente.get("/")

    assert resposta.status_code == 200

    assert len(agendador_falso) == 1


def test_rota_da_api_chama_o_agendador(
    conexao, cliente, agendador_falso
):
    resposta = cliente.get("/api/impressoras")

    assert resposta.status_code == 200

    assert len(agendador_falso) == 1


def test_painel_abre_mesmo_com_a_coleta_quebrada(
    conexao, cliente, medicao_em, ligada, monkeypatch
):
    """
    Passa pelo agendador de verdade, em segundo plano, com a
    coleta quebrada. A página tem de abrir assim mesmo: ela
    apenas deixa de ter dados novos.
    """

    def explodir():
        raise RuntimeError("simulador fora do ar")

    monkeypatch.setattr(monitor, "coletar_uma_vez", explodir)

    medicao_em(FORA_DO_INTERVALO)

    resposta = cliente.get("/")

    assert resposta.status_code == 200


def test_falha_ao_iniciar_a_coleta_nao_quebra(
    conexao, medicao_em, ligada, monkeypatch
):
    """
    Criar a linha de execução pode falhar num servidor sem
    recursos. O erro não pode escapar para o Flask, e a tranca
    tem de ser liberada.
    """

    class ThreadQueNaoInicia:

        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            raise RuntimeError("sem recursos para outra thread")

    monkeypatch.setattr(
        agendador.threading,
        "Thread",
        ThreadQueNaoInicia
    )

    medicao_em(FORA_DO_INTERVALO)

    assert agendador.coletar_se_estiver_na_hora() is False

    assert agendador._coletando is False
