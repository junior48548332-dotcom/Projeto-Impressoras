import pandas as pd

from config import (
    ARQUIVO_EXCEL,
    ABA_PLANILHA,
    LINHA_CABECALHO
)


# ================================================================
# PLANILHA DE IMPRESSORAS
# ================================================================
#
# Lê o cadastro das impressoras no Excel e devolve uma lista
# com um dicionário para cada impressora:
#
#     {
#         "local": "Diretoria",
#         "modelo": "CX950",
#         "tipo": "COLOR",
#         "paper": "A3 / A4",
#         "serie": "0123ABCD0123",
#         "ip": "192.168.0.2"
#     }
#
# Se a planilha não puder ser aberta, a função gera um erro.
# Quem chama decide o que fazer com ele.


# Nomes dados às primeiras colunas da planilha, nesta ordem
COLUNAS = [
    "local",
    "modelo",
    "tipo",
    "paper",
    "serie",
    "ip"
]


def ler_planilha():

    # ------------------------------------------------------------
    # LÊ A PLANILHA
    # ------------------------------------------------------------

    df = pd.read_excel(
        ARQUIVO_EXCEL,
        sheet_name=ABA_PLANILHA,
        header=LINHA_CABECALHO
    )


    # ------------------------------------------------------------
    # PEGA SOMENTE AS COLUNAS UTILIZADAS
    # ------------------------------------------------------------

    df = df.iloc[:, :len(COLUNAS)]

    df.columns = COLUNAS


    # ------------------------------------------------------------
    # LIMPA OS DADOS
    # ------------------------------------------------------------

    for coluna in df.columns:

        df[coluna] = (
            df[coluna]
            .fillna("")
            .astype(str)
            .str.strip()
        )


    # ------------------------------------------------------------
    # REMOVE LINHAS SEM LOCAL OU IP
    # ------------------------------------------------------------

    df = df[
        (df["local"] != "") &
        (df["ip"] != "")
    ]


    # ------------------------------------------------------------
    # CONVERTE PARA LISTA DE DICIONÁRIOS
    # ------------------------------------------------------------

    return df.to_dict("records")
