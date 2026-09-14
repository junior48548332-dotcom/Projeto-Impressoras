import sqlite3


BANCO_DADOS = "impressoras.db"


print("=" * 60)
print(" FASE 1 - TABELA DE CONSOLIDAÇÃO")
print(" PROJETO IMPRESSORAS")
print("=" * 60)


# ================================================================
# CONECTA AO BANCO
# ================================================================

try:
    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()

    print("\n[OK] Conexão com o banco realizada com sucesso.")

except Exception as erro:
    print("\n[ERRO] Não foi possível conectar ao banco.")
    print(erro)
    exit()


# ================================================================
# VERIFICA SE O HISTÓRICO EXISTE
# ================================================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name = 'historico_impressoras'
""")

tabela_historico = cursor.fetchone()


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


cursor.execute("""
    CREATE TABLE IF NOT EXISTS consolidacao_diaria (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        data TEXT NOT NULL,

        local TEXT,

        ip TEXT,

        modelo TEXT,

        total_medicoes INTEGER DEFAULT 0,

        online INTEGER DEFAULT 0,

        offline INTEGER DEFAULT 0,

        criticas INTEGER DEFAULT 0,

        atencoes INTEGER DEFAULT 0,

        normais INTEGER DEFAULT 0,

        consumo_medio REAL DEFAULT 0,

        ultima_medicao TEXT

    )
""")


conexao.commit()


print("[OK] Tabela 'consolidacao_diaria' criada/verificada com sucesso.")


# ================================================================
# MOSTRA A ESTRUTURA DA TABELA
# ================================================================

print("\n" + "=" * 60)
print(" ESTRUTURA DA TABELA")
print("=" * 60)


cursor.execute("""
    PRAGMA table_info(consolidacao_diaria)
""")


colunas = cursor.fetchall()


for coluna in colunas:

    numero = coluna[0]
    nome = coluna[1]
    tipo = coluna[2]

    print(f"{numero:02d} - {nome:<20} {tipo}")


# ================================================================
# CONTA OS REGISTROS
# ================================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM consolidacao_diaria
""")


total_registros = cursor.fetchone()[0]


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

cursor.execute("""
    SELECT COUNT(*)
    FROM historico_impressoras
""")


total_historico = cursor.fetchone()[0]


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