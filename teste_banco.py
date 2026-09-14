import sqlite3
import json


BANCO_DADOS = "impressoras.db"


print("=" * 60)
print(" TESTE DO BANCO DE DADOS - PROJETO IMPRESSORAS")
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
# VERIFICA SE A TABELA EXISTE
# ================================================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='historico_impressoras'
""")

tabela = cursor.fetchone()


if tabela:

    print("[OK] Tabela 'historico_impressoras' encontrada.")

else:

    print("[ERRO] Tabela 'historico_impressoras' não encontrada.")

    conexao.close()

    exit()


# ================================================================
# CONTA OS REGISTROS
# ================================================================

cursor.execute("""
    SELECT COUNT(*)
    FROM historico_impressoras
""")

total_registros = cursor.fetchone()[0]


print(f"[OK] Total de registros no banco: {total_registros}")


# ================================================================
# CONTA IMPRESSORAS DIFERENTES
# ================================================================

cursor.execute("""
    SELECT COUNT(DISTINCT ip)
    FROM historico_impressoras
""")

total_impressoras = cursor.fetchone()[0]


print(
    f"[OK] Impressoras diferentes registradas: "
    f"{total_impressoras}"
)


# ================================================================
# MOSTRA AS ÚLTIMAS 5 MEDIÇÕES
# ================================================================

print("\n" + "=" * 60)
print(" ÚLTIMAS 5 MEDIÇÕES")
print("=" * 60)


cursor.execute("""
    SELECT
        data_hora,
        local,
        modelo,
        ip,
        status_rede,
        status_geral
    FROM historico_impressoras
    ORDER BY id DESC
    LIMIT 5
""")


registros = cursor.fetchall()


if not registros:

    print("\n[AVISO] Nenhuma medição encontrada.")

else:

    for registro in registros:

        data_hora = registro[0]
        local = registro[1]
        modelo = registro[2]
        ip = registro[3]
        status_rede = registro[4]
        status_geral = registro[5]

        print()
        print(f"Data/Hora : {data_hora}")
        print(f"Local     : {local}")
        print(f"Modelo    : {modelo}")
        print(f"IP        : {ip}")
        print(f"Rede      : {status_rede}")
        print(f"Status    : {status_geral}")


# ================================================================
# MOSTRA UMA MEDIÇÃO COMPLETA
# ================================================================

print("\n" + "=" * 60)
print(" EXEMPLO DE SUPRIMENTOS ARMAZENADOS")
print("=" * 60)


cursor.execute("""
    SELECT
        local,
        ip,
        suprimentos,
        status_suprimentos
    FROM historico_impressoras
    ORDER BY id DESC
    LIMIT 1
""")


registro = cursor.fetchone()


if registro:

    local = registro[0]
    ip = registro[1]
    suprimentos = registro[2]
    status_suprimentos = registro[3]

    print(f"\nLocal: {local}")
    print(f"IP: {ip}")

    print("\nSuprimentos:")

    try:

        dados_suprimentos = json.loads(suprimentos)

        for nome, percentual in dados_suprimentos.items():

            print(
                f"  {nome}: {percentual}%"
            )

    except Exception:

        print("  Não foi possível interpretar os suprimentos.")


    print("\nClassificação:")

    try:

        dados_status = json.loads(status_suprimentos)

        for nome, status in dados_status.items():

            print(
                f"  {nome}: {status}"
            )

    except Exception:

        print("  Não foi possível interpretar os status.")


# ================================================================
# FECHA O BANCO
# ================================================================

conexao.close()


# ================================================================
# RESULTADO FINAL
# ================================================================

print("\n" + "=" * 60)
print(" TESTE FINALIZADO")
print("=" * 60)

print("\nSe os dados acima apareceram corretamente,")
print("o banco de dados está funcionando corretamente.")