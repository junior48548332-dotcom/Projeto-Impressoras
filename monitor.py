import time
import sqlite3
import json
import pandas as pd

from datetime import datetime

from simulador import (
    gerar_suprimentos,
    classificar_nivel,
    simular_status_rede
)


# ================================================================
# CONFIGURAÇÕES
# ================================================================

ARQUIVO_EXCEL = "impressoras.xlsx"
BANCO_DADOS = "impressoras.db"

# Intervalo entre as verificações
# 600 segundos = 10 minutos
INTERVALO_SEGUNDOS = 600


# ================================================================
# CRIA O BANCO DE DADOS
# ================================================================

def criar_banco():

    conexao = sqlite3.connect(BANCO_DADOS)

    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_impressoras (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            data_hora TEXT NOT NULL,

            local TEXT,

            modelo TEXT,

            tipo TEXT,

            paper TEXT,

            serie TEXT,

            ip TEXT,

            status_rede TEXT,

            status_geral TEXT,

            suprimentos TEXT,

            status_suprimentos TEXT
        )
    """)

    conexao.commit()

    conexao.close()


# ================================================================
# SALVA UMA MEDIÇÃO
# ================================================================

def salvar_medicao(impressora):

    conexao = sqlite3.connect(BANCO_DADOS)

    cursor = conexao.cursor()

    data_hora = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO historico_impressoras (

            data_hora,
            local,
            modelo,
            tipo,
            paper,
            serie,
            ip,
            status_rede,
            status_geral,
            suprimentos,
            status_suprimentos

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data_hora,

        impressora["local"],

        impressora["modelo"],

        impressora["tipo"],

        impressora["paper"],

        impressora["serie"],

        impressora["ip"],

        impressora["status_rede"],

        impressora["status_geral"],

        json.dumps(
            impressora["suprimentos"],
            ensure_ascii=False
        ),

        json.dumps(
            impressora["status_suprimentos"],
            ensure_ascii=False
        )
    ))

    conexao.commit()

    conexao.close()


# ================================================================
# CARREGA AS IMPRESSORAS DO EXCEL
# ================================================================

def carregar_impressoras():

    print("\nLendo a planilha...")

    df = pd.read_excel(

        ARQUIVO_EXCEL,

        sheet_name="Impressoras ativas",

        header=1
    )

    # ------------------------------------------------------------
    # Mantém somente as 6 colunas utilizadas
    # ------------------------------------------------------------

    df = df.iloc[:, :6]

    # ------------------------------------------------------------
    # Padroniza os nomes
    # ------------------------------------------------------------

    df.columns = [

        "local",
        "modelo",
        "tipo",
        "paper",
        "serie",
        "ip"
    ]

    # ------------------------------------------------------------
    # Limpa os dados
    # ------------------------------------------------------------

    for coluna in df.columns:

        df[coluna] = (

            df[coluna]

            .fillna("")

            .astype(str)

            .str.strip()
        )

    # ------------------------------------------------------------
    # Remove linhas sem local ou IP
    # ------------------------------------------------------------

    df = df[

        (df["local"] != "") &

        (df["ip"] != "")
    ]

    impressoras = []

    # ============================================================
    # PROCESSA CADA IMPRESSORA
    # ============================================================

    for _, linha in df.iterrows():

        tipo = str(
            linha["tipo"]
        ).strip().upper()

        # --------------------------------------------------------
        # Suprimentos
        # --------------------------------------------------------

        suprimentos = gerar_suprimentos(tipo)

        # --------------------------------------------------------
        # Status da rede
        # --------------------------------------------------------

        status_rede = simular_status_rede()

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

    contador = 0

    # ============================================================
    # SALVA CADA IMPRESSORA
    # ============================================================

    for impressora in impressoras:

        salvar_medicao(impressora)

        contador += 1

        print(
            f"[{contador:02d}/{total}] "
            f"{impressora['local']} - "
            f"{impressora['ip']} - "
            f"{impressora['status_rede']} - "
            f"{impressora['status_geral']}"
        )

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

    criar_banco()

    print("\n" + "=" * 60)

    print(" MONITOR DE IMPRESSORAS")

    print("=" * 60)

    print(
        "\nIntervalo configurado: "
        "10 minutos"
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
                "10 minutos..."
            )

            time.sleep(
                INTERVALO_SEGUNDOS
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
                INTERVALO_SEGUNDOS
            )


# ================================================================
# INICIALIZAÇÃO
# ================================================================

if __name__ == "__main__":

    iniciar_monitoramento() 