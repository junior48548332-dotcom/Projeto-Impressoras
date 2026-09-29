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


# ================================================================
# MONITORAMENTO CONTÍNUO
# ================================================================

def iniciar_monitoramento():

    conexao = conectar()

    criar_tabelas(conexao)

    conexao.close()

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

            executar_verificacao()

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
# INICIALIZAÇÃO
# ================================================================

if __name__ == "__main__":

    iniciar_monitoramento() 