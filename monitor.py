import sys
import time

from datetime import datetime

from config import INTERVALO_COLETA

from banco import (
    conectar,
    buscar_impressoras,
    criar_tabelas,
    salvar_medicao
)

from coleta.simulador import coletar

from consolidador import consolidar_ultimo_dia


# ================================================================
# CLASSIFICAÇÃO DOS SUPRIMENTOS
# ================================================================

def classificar_nivel(percentual):
    """
    Classifica o nível de um suprimento.

    Até 5%  = crítico
    Até 20% = atenção
    Acima de 20% = normal
    """

    percentual = float(percentual)

    if percentual <= 5:
        return "critico"

    elif percentual <= 20:
        return "atencao"

    else:
        return "normal"


# ================================================================
# CARREGA AS IMPRESSORAS DO CADASTRO
# ================================================================

def carregar_impressoras():

    print("\nLendo o cadastro de impressoras...")

    conexao = conectar()

    cadastro = buscar_impressoras(
        conexao
    )

    conexao.close()

    impressoras = []

    # ============================================================
    # PROCESSA CADA IMPRESSORA
    # ============================================================

    for linha in cadastro:

        tipo = str(
            linha["tipo"]
        ).strip().upper()

        # --------------------------------------------------------
        # Dados coletados da impressora
        # --------------------------------------------------------

        dados = coletar(linha)

        suprimentos = dados["suprimentos"]

        status_rede = dados["status_rede"]

        # --------------------------------------------------------
        # Classificação dos suprimentos
        # --------------------------------------------------------

        status_suprimentos = {}

        for nome, percentual in suprimentos.items():

            status_suprimentos[nome] = (
                classificar_nivel(percentual)
            )

        # --------------------------------------------------------
        # Status geral
        # --------------------------------------------------------

        if "critico" in status_suprimentos.values():

            status_geral = "critico"

        elif "atencao" in status_suprimentos.values():

            status_geral = "atencao"

        else:

            status_geral = "normal"

        # --------------------------------------------------------
        # Monta objeto
        # --------------------------------------------------------

        impressora = {

            "local": linha["local"],

            "modelo": linha["modelo"],

            "tipo": tipo,

            "paper": linha["paper"],

            "serie": linha["serie"],

            "ip": linha["ip"],

            "suprimentos": suprimentos,

            "status_suprimentos": status_suprimentos,

            "status_geral": status_geral,

            "status_rede": status_rede
        }

        impressoras.append(impressora)

    return impressoras


# ================================================================
# EXECUTA UMA VERIFICAÇÃO
# ================================================================

def executar_verificacao():

    print("\n" + "=" * 60)

    print(
        " INICIANDO NOVA VERIFICAÇÃO"
    )

    print(
        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    print("=" * 60)

    impressoras = carregar_impressoras()

    total = len(impressoras)

    print(
        f"\nImpressoras encontradas: {total}"
    )

    if total == 0:

        print(
            "[AVISO] Nenhuma impressora cadastrada. "
            "Execute: python importar_planilha.py"
        )

    contador = 0

    conexao = conectar()

    # ============================================================
    # SALVA CADA IMPRESSORA
    # ============================================================

    for impressora in impressoras:

        salvar_medicao(
            conexao,
            impressora
        )

        contador += 1

        print(
            f"[{contador:02d}/{total}] "
            f"{impressora['local']} - "
            f"{impressora['ip']} - "
            f"{impressora['status_rede']} - "
            f"{impressora['status_geral']}"
        )

    conexao.close()

    print("\n" + "-" * 60)

    print(
        f"VERIFICAÇÃO CONCLUÍDA: "
        f"{contador} medições salvas."
    )

    print("-" * 60)

    return contador


# ================================================================
# PREPARA O BANCO
# ================================================================

def preparar_banco():
    """Cria as tabelas, caso ainda não existam."""

    conexao = conectar()

    criar_tabelas(conexao)

    conexao.close()


# ================================================================
# COLETA + CONSOLIDAÇÃO
# ================================================================

def coletar_e_consolidar():
    """
    Faz uma coleta e consolida o dia dela em seguida.

    A consolidação é o que alimenta a aba Análise do dashboard.
    Rodando junto da coleta, os números ficam em dia sozinhos,
    sem ninguém precisar executar o consolidador na mão.

    Só o dia da coleta é consolidado. Os dias anteriores já
    estão fechados e não mudam mais.
    """

    total = executar_verificacao()

    conexao = conectar()

    processadas = consolidar_ultimo_dia(conexao)

    conexao.close()

    print(
        f"CONSOLIDAÇÃO DO DIA: "
        f"{processadas} impressoras processadas."
    )

    print("-" * 60)

    return total


# ================================================================
# COLETA ÚNICA
# ================================================================

def coletar_uma_vez():
    """
    Executa uma coleta e encerra.

    É o modo usado no servidor. A tarefa agendada roda o
    comando, espera ele terminar e anota o resultado, então um
    programa que nunca termina não serve para ela.
    """

    preparar_banco()

    return coletar_e_consolidar()


# ================================================================
# MONITORAMENTO CONTÍNUO
# ================================================================

def iniciar_monitoramento():
    """
    Coleta de tempos em tempos até receber CTRL + C.

    É o modo para uso local, com o terminal aberto.
    """

    preparar_banco()

    print("\n" + "=" * 60)

    print(" MONITOR DE IMPRESSORAS")

    print("=" * 60)

    print(
        "\nIntervalo configurado: "
        f"{INTERVALO_COLETA // 60} minutos"
    )

    print(
        "Para encerrar o monitoramento, "
        "pressione CTRL + C."
    )

    # ============================================================
    # LOOP PRINCIPAL
    # ============================================================

    while True:

        try:

            coletar_e_consolidar()

            print(
                "\nPróxima verificação em "
                f"{INTERVALO_COLETA // 60} minutos..."
            )

            time.sleep(
                INTERVALO_COLETA
            )

        except KeyboardInterrupt:

            print(
                "\n\nMonitoramento encerrado pelo usuário."
            )

            break

        except Exception as erro:

            print(
                "\n[ERRO] Ocorreu um problema:"
            )

            print(erro)

            print(
                "\nO monitor continuará tentando "
                "na próxima verificação."
            )

            time.sleep(
                INTERVALO_COLETA
            )


# ================================================================
# LINHA DE COMANDO
# ================================================================

MODO_CONTINUO = "--continuo"

PEDIDOS_DE_AJUDA = ("--ajuda", "-h")

ARGUMENTOS_VALIDOS = (MODO_CONTINUO,) + PEDIDOS_DE_AJUDA


def mostrar_ajuda():

    print(
        "\nMonitor de impressoras."
        "\n"
        "\n    python monitor.py              uma coleta e encerra"
        "\n    python monitor.py --continuo   coleta a cada "
        f"{INTERVALO_COLETA // 60} minutos"
        "\n    python monitor.py --ajuda      mostra esta mensagem"
        "\n"
        "\nSem argumentos, o programa faz uma coleta e termina."
        "\nEsse é o modo usado pela tarefa agendada do servidor."
    )


def main(argumentos):
    """
    Escolhe o modo de execução e devolve o código de saída.

    O código de saída importa na nuvem: o servidor usa ele para
    saber se a tarefa agendada funcionou (0) ou falhou (1).
    """

    # ============================================================
    # AJUDA
    # ============================================================

    for pedido in PEDIDOS_DE_AJUDA:

        if pedido in argumentos:

            mostrar_ajuda()

            return 0

    # ============================================================
    # ARGUMENTO ESCRITO ERRADO
    # ============================================================
    # Avisa em vez de fazer uma coleta única por engano, que
    # seria confuso para quem pediu o modo contínuo.

    for argumento in argumentos:

        if argumento not in ARGUMENTOS_VALIDOS:

            print(
                f"\n[ERRO] Argumento não reconhecido: {argumento}"
            )

            mostrar_ajuda()

            return 2

    # ============================================================
    # MODO CONTÍNUO
    # ============================================================

    if MODO_CONTINUO in argumentos:

        iniciar_monitoramento()

        return 0

    # ============================================================
    # COLETA ÚNICA
    # ============================================================

    try:

        coletar_uma_vez()

    except Exception as erro:

        print(
            "\n[ERRO] A coleta não foi concluída:"
        )

        print(erro)

        return 1

    return 0


# ================================================================
# INICIALIZAÇÃO
# ================================================================

if __name__ == "__main__":

    sys.exit(
        main(sys.argv[1:])
    )
