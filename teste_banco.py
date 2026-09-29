import json

from banco import (
    conectar,
    tabela_existe,
    contar_registros,
    contar_impressoras_registradas,
    buscar_medicoes_recentes,
    buscar_ultima_medicao_completa
)


print("=" * 60)
print(" TESTE DO BANCO DE DADOS - PROJETO IMPRESSORAS")
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
# VERIFICA SE A TABELA EXISTE
# ================================================================

tabela = tabela_existe(
    conexao,
    "historico_impressoras"
)


if tabela:

    print("[OK] Tabela 'historico_impressoras' encontrada.")

else:

    print("[ERRO] Tabela 'historico_impressoras' não encontrada.")

    conexao.close()

    exit()


# ================================================================
# CONTA OS REGISTROS
# ================================================================

total_registros = contar_registros(
    conexao,
    "historico_impressoras"
)


print(f"[OK] Total de registros no banco: {total_registros}")


# ================================================================
# CONTA IMPRESSORAS DIFERENTES
# ================================================================

total_impressoras = contar_impressoras_registradas(
    conexao
)


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


registros = buscar_medicoes_recentes(
    conexao,
    limite=5
)


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


registro = buscar_ultima_medicao_completa(
    conexao
)


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