import threading
import time

from datetime import datetime

from config import (
    COLETA_WEB,
    FORMATO_DATA_HORA,
    FUSO_HORARIO,
    INTERVALO_COLETA,
    SEGUNDOS_ENTRE_TENTATIVAS
)

from banco import (
    conectar,
    buscar_data_ultima_medicao
)

import monitor


# ================================================================
# COLETA AUTOMÁTICA PELO SERVIDOR
# ================================================================
#
# O plano gratuito do PythonAnywhere não oferece tarefas agendadas
# para contas novas, então não há quem chame o monitor.py de tempos
# em tempos no servidor.
#
# A saída é o próprio servidor perceber que está na hora. A cada
# requisição ele olha a data da última medição e, se ela passou do
# intervalo configurado, dispara uma coleta.
#
# Três decisões importantes:
#
#   1. QUEM DECIDE É O SERVIDOR, NÃO O NAVEGADOR.
#      O painel já busca dados novos a cada 50 segundos. Essas
#      batidas na porta são só a oportunidade de verificar: o
#      navegador não pede coleta e nem sabe que ela existe. Se
#      cinco pessoas abrirem o painel juntas, continua sendo uma
#      coleta a cada 10 minutos.
#
#   2. A COLETA NÃO SEGURA A RESPOSTA.
#      Ela leva de 1 a 6 segundos, dependendo do servidor. Esperar
#      por ela deixaria a página travada. Então ela roda em uma
#      linha de execução separada e os dados aparecem na
#      atualização seguinte do painel.
#
#   3. UMA DE CADA VEZ.
#      Duas requisições simultâneas poderiam disparar duas coletas.
#      A verificação e a marcação acontecem dentro de uma tranca,
#      então só a primeira passa.
#
# LIMITAÇÃO, declarada de propósito: só coleta enquanto alguém
# estiver com o painel aberto. Sem ninguém olhando, não há
# requisição, e o histórico fica com buracos. Para cobrir esses
# períodos, um serviço externo gratuito pode abrir o endereço do
# sistema de tempos em tempos.


# Protege as duas variáveis abaixo
_tranca = threading.Lock()

# Uma coleta está em andamento neste momento
_coletando = False

# Relógio monotônico da última tentativa, para não repetir
# tentativa atrás de tentativa quando a coleta está falhando
_ultima_tentativa = None


# ================================================================
# HÁ QUANTO TEMPO FOI A ÚLTIMA MEDIÇÃO
# ================================================================

def segundos_desde_a_ultima_medicao(conexao):
    """
    Devolve os segundos decorridos desde a última medição.

    Devolve None quando não há nenhuma medição no histórico, ou
    quando a data gravada não pode ser lida.
    """

    texto = buscar_data_ultima_medicao(conexao)

    if not texto:
        return None

    try:

        medicao = datetime.strptime(
            texto,
            FORMATO_DATA_HORA
        ).replace(tzinfo=FUSO_HORARIO)

    except (TypeError, ValueError):

        return None

    agora = datetime.now(FUSO_HORARIO)

    return (agora - medicao).total_seconds()


def esta_na_hora(conexao):
    """
    Diz se já passou o intervalo configurado desde a última
    medição.

    Sem nenhuma medição no histórico, a resposta é sim: é a
    primeira coleta do sistema.
    """

    segundos = segundos_desde_a_ultima_medicao(conexao)

    if segundos is None:
        return True

    return segundos >= INTERVALO_COLETA


# ================================================================
# A COLETA EM SI
# ================================================================

def _coletar():
    """Executa a coleta e libera a tranca ao terminar."""

    global _coletando

    try:

        print("[COLETA AUTOMÁTICA] Iniciando.")

        total = monitor.coletar_uma_vez()

        print(
            f"[COLETA AUTOMÁTICA] Concluída: "
            f"{total} medições."
        )

    except Exception as erro:

        # Uma coleta que falha não pode derrubar o servidor web.
        # O erro vai para o log e a próxima tentativa acontece
        # depois do intervalo entre tentativas.
        print(
            f"[COLETA AUTOMÁTICA] [ERRO] A coleta falhou: {erro}"
        )

    finally:

        with _tranca:

            _coletando = False


def coletar_se_estiver_na_hora(em_segundo_plano=True):
    """
    Dispara uma coleta se já estiver na hora.

    É chamada a cada requisição do painel e da API. Devolve True
    se disparou uma coleta e False se não havia o que fazer.

    Nunca levanta exceção: o painel precisa abrir mesmo que a
    coleta não funcione.

    O parâmetro em_segundo_plano existe para os testes, que
    precisam esperar a coleta terminar para conferir o resultado.
    """

    global _coletando, _ultima_tentativa

    if not COLETA_WEB:
        return False

    agora = time.monotonic()

    with _tranca:

        # ------------------------------------------------------
        # Já tem uma coleta rodando
        # ------------------------------------------------------

        if _coletando:
            return False

        # ------------------------------------------------------
        # Tentou faz pouco tempo
        # ------------------------------------------------------
        # Sem isso, uma coleta que falha seria tentada de novo a
        # cada atualização do painel, a cada 50 segundos.

        if (
            _ultima_tentativa is not None
            and agora - _ultima_tentativa < SEGUNDOS_ENTRE_TENTATIVAS
        ):
            return False

        # ------------------------------------------------------
        # Ainda está dentro do intervalo
        # ------------------------------------------------------
        # A consulta fica dentro da tranca de propósito: assim
        # duas requisições simultâneas não enxergam o mesmo
        # "está na hora" e disparam duas coletas.

        try:

            conexao = conectar()

            na_hora = esta_na_hora(conexao)

            conexao.close()

        except Exception as erro:

            print(
                f"[COLETA AUTOMÁTICA] [ERRO] Não foi possível "
                f"consultar o banco: {erro}"
            )

            return False

        if not na_hora:
            return False

        _coletando = True

        _ultima_tentativa = agora

    # ----------------------------------------------------------
    # Fora da tranca: a coleta não segura a resposta
    # ----------------------------------------------------------

    if em_segundo_plano:

        try:

            threading.Thread(
                target=_coletar,
                name="coleta-automatica",
                daemon=True
            ).start()

        except Exception as erro:

            # Criar a linha de execução pode falhar se o servidor
            # estiver sem recursos. Isso não pode derrubar a
            # página: ela só deixa de ter dados novos.
            print(
                f"[COLETA AUTOMÁTICA] [ERRO] Não foi possível "
                f"iniciar a coleta: {erro}"
            )

            with _tranca:

                _coletando = False

            return False

    else:

        _coletar()

    return True
