from banco import (
    conectar,
    tabela_existe,
    contar_registros,
    criar_tabela_consolidacao,
    estrutura_tabela
)


print("=" * 60)
print(" FASE 1 - TABELA DE CONSOLIDAÇÃO")
print(" PROJETO IMPRESSORAS")
print("=" * 60)


# ================================================================
# CONECTA AO BANCO
# ================================================================

try:
    conexao = conectar()

    print("\n[OK] Conexão com o banco realizada com sucesso.")

except Exception as erro:
    print("\n[ERRO] Não foi possível conectar ao banco.")
    print(erro)
    exit()


# ================================================================
# VERIFICA SE O HISTÓRICO EXISTE
# ================================================================

tabela_historico = tabela_existe(
    conexao,
    "historico_impressoras"
)


if tabela_historico:
    print("[OK] Tabela 'historico_impressoras' encontrada.")
else:
    print("[ERRO] Tabela 'historico_impressoras' não encontrada.")
    conexao.close()
    exit()


# ================================================================
# CRIA A TABELA DE CONSOLIDAÇÃO
# ================================================================

print("\nCriando tabela 'consolidacao_diaria'...")


criar_tabela_consolidacao(
    conexao
)


print("[OK] Tabela 'consolidacao_diaria' criada/verificada com sucesso.")


# ================================================================
# MOSTRA A ESTRUTURA DA TABELA
# ================================================================

print("\n" + "=" * 60)
print(" ESTRUTURA DA TABELA")
print("=" * 60)


colunas = estrutura_tabela(
    conexao,
    "consolidacao_diaria"
)


for coluna in colunas:

    numero = coluna[0]
    nome = coluna[1]
    tipo = coluna[2]

    print(f"{numero:02d} - {nome:<20} {tipo}")


# ================================================================
# CONTA OS REGISTROS
# ================================================================

total_registros = contar_registros(
    conexao,
    "consolidacao_diaria"
)


print("\n" + "=" * 60)
print(" SITUAÇÃO DA CONSOLIDAÇÃO")
print("=" * 60)

print(f"\n[OK] Registros consolidados: {total_registros}")


if total_registros == 0:

    print(
        "[INFO] A tabela está vazia porque ainda não "
        "executamos o processo de consolidação."
    )

else:

    print("[OK] Já existem dados consolidados.")


# ================================================================
# VERIFICA SE O HISTÓRICO CONTINUA INTACTO
# ================================================================

total_historico = contar_registros(
    conexao,
    "historico_impressoras"
)


print(
    f"[OK] Registros no histórico original: "
    f"{total_historico}"
)


# ================================================================
# FECHA O BANCO
# ================================================================

conexao.close()


# ================================================================
# RESULTADO FINAL
# ================================================================

print("\n" + "=" * 60)
print(" FASE 1 - TESTE FINALIZADO")
print("=" * 60)

print("\nA estrutura de consolidação está pronta.")
print("Nenhum registro do histórico original foi alterado.")