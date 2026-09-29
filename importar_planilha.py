from planilha import ler_planilha

from banco import (
    conectar,
    criar_tabelas,
    substituir_impressoras
)


# ================================================================
# IMPORTAÇÃO DO CADASTRO
# ================================================================
#
# Lê a planilha de impressoras e grava o cadastro no banco,
# na tabela "impressoras". O dashboard e o monitor usam o
# cadastro do banco, não a planilha.
#
# Execute sempre que a planilha for alterada:
#
#     python importar_planilha.py
#
# O cadastro anterior é substituído pelo conteúdo da planilha.
# O histórico de medições não é alterado.


# ================================================================
# VERIFICA IPs REPETIDOS
# ================================================================

def encontrar_ips_repetidos(impressoras):

    vistos = set()

    repetidos = []

    for impressora in impressoras:

        ip = impressora["ip"]

        if ip in vistos and ip not in repetidos:

            repetidos.append(ip)

        vistos.add(ip)

    return repetidos


# ================================================================
# IMPORTA A PLANILHA
# ================================================================

def importar():

    impressoras = ler_planilha()

    # ------------------------------------------------------------
    # O IP identifica cada impressora no sistema,
    # então não pode se repetir.
    # ------------------------------------------------------------

    repetidos = encontrar_ips_repetidos(
        impressoras
    )

    if repetidos:

        raise ValueError(
            "IPs repetidos na planilha: "
            + ", ".join(repetidos)
        )

    # ------------------------------------------------------------
    # GRAVA NO BANCO
    # ------------------------------------------------------------

    conexao = conectar()

    try:

        criar_tabelas(conexao)

        substituir_impressoras(
            conexao,
            impressoras
        )

    finally:

        conexao.close()

    return len(impressoras)


# ================================================================
# FUNÇÃO PRINCIPAL
# ================================================================

def main():

    print("=" * 60)
    print(" IMPORTAÇÃO DA PLANILHA")
    print(" PROJETO IMPRESSORAS")
    print("=" * 60)

    try:

        total = importar()

    except Exception as erro:

        print(
            "\n[ERRO] Não foi possível importar a planilha."
        )

        print(
            f"Detalhes: {erro}"
        )

        print(
            "\nO cadastro no banco não foi alterado."
        )

        return

    print(
        f"\n[OK] Impressoras importadas: {total}"
    )

    print(
        "[OK] Cadastro atualizado no banco de dados."
    )


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":
    main()
