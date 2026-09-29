import json
from datetime import datetime

from banco import (
    conectar,
    tabela_existe,
    contar_registros,
    criar_tabela_consolidacao,
    buscar_dias_historico,
    buscar_impressoras_do_dia,
    buscar_medicoes_do_dia,
    salvar_consolidacao,
    buscar_consolidacoes
)


# ================================================================
# CONVERTE DATA/HORA
# ================================================================

def converter_data(data_hora):

    if not data_hora:
        return None

    try:
        return datetime.strptime(
            str(data_hora),
            "%Y-%m-%d %H:%M:%S"
        )

    except ValueError:

        try:
            return datetime.fromisoformat(
                str(data_hora)
            )

        except ValueError:
            return None


# ================================================================
# CALCULA CONSUMO DOS SUPRIMENTOS
# ================================================================

def calcular_consumo(suprimentos_inicial, suprimentos_final):

    if not suprimentos_inicial or not suprimentos_final:
        return 0

    try:

        inicial = json.loads(suprimentos_inicial)
        final = json.loads(suprimentos_final)

    except (TypeError, json.JSONDecodeError):

        return 0

    consumos = []

    for nome, valor_inicial in inicial.items():

        if nome not in final:
            continue

        try:

            valor_inicial = float(valor_inicial)
            valor_final = float(final[nome])

            consumo = valor_inicial - valor_final

            # Só considera redução como consumo.
            # Se o valor aumentou, consideramos reposição.
            if consumo > 0:
                consumos.append(consumo)

        except (ValueError, TypeError):
            continue

    if not consumos:
        return 0

    return sum(consumos) / len(consumos)


# ================================================================
# CLASSIFICA STATUS DOS SUPRIMENTOS
# ================================================================

def contar_status_suprimentos(registros):

    criticas = 0
    atencoes = 0
    normais = 0

    for registro in registros:

        status_json = registro[7]

        if not status_json:
            continue

        try:

            status = json.loads(status_json)

        except (TypeError, json.JSONDecodeError):

            continue

        possui_critico = False
        possui_atencao = False

        for nivel in status.values():

            nivel = str(nivel).lower().strip()

            if nivel == "critico":
                possui_critico = True

            elif nivel == "atencao":
                possui_atencao = True

        if possui_critico:

            criticas += 1

        elif possui_atencao:

            atencoes += 1

        else:

            normais += 1

    return criticas, atencoes, normais


# ================================================================
# CONSOLIDA UMA IMPRESSORA
# ================================================================

def consolidar_impressora(conexao, data, local, ip, modelo):

    registros = buscar_medicoes_do_dia(
        conexao,
        data,
        ip
    )

    if not registros:
        return False

    total_medicoes = len(registros)

    # ------------------------------------------------------------
    # CONTAGEM DA REDE
    # ------------------------------------------------------------

    online = 0
    offline = 0

    for registro in registros:

        status_rede = str(
            registro[4] or ""
        ).lower().strip()

        if status_rede == "online":

            online += 1

        elif status_rede == "offline":

            offline += 1

    # ------------------------------------------------------------
    # CONTAGEM DOS STATUS DOS SUPRIMENTOS
    # ------------------------------------------------------------

    criticas, atencoes, normais = contar_status_suprimentos(
        registros
    )

    # ------------------------------------------------------------
    # CÁLCULO DO CONSUMO
    # ------------------------------------------------------------

    consumos = []

    for i in range(1, len(registros)):

        registro_anterior = registros[i - 1]
        registro_atual = registros[i]

        consumo = calcular_consumo(
            registro_anterior[6],
            registro_atual[6]
        )

        if consumo > 0:
            consumos.append(consumo)

    if consumos:

        consumo_medio = (
            sum(consumos) / len(consumos)
        )

    else:

        consumo_medio = 0

    # ------------------------------------------------------------
    # ÚLTIMA MEDIÇÃO
    # ------------------------------------------------------------

    ultima_medicao = registros[-1][1]

    # ------------------------------------------------------------
    # SALVA A CONSOLIDAÇÃO
    # ------------------------------------------------------------
    # Se o dia já foi consolidado, o registro é atualizado.
    # Caso contrário, um novo registro é criado.

    salvar_consolidacao(conexao, {

        "data": data,

        "local": local,

        "ip": ip,

        "modelo": modelo,

        "total_medicoes": total_medicoes,

        "online": online,

        "offline": offline,

        "criticas": criticas,

        "atencoes": atencoes,

        "normais": normais,

        "consumo_medio": consumo_medio,

        "ultima_medicao": ultima_medicao
    })

    return True


# ================================================================
# CONSOLIDA UM DIA
# ================================================================

def consolidar_dia(conexao, data):

    impressoras = buscar_impressoras_do_dia(
        conexao,
        data
    )

    total_processadas = 0

    for local, ip, modelo in impressoras:

        resultado = consolidar_impressora(
            conexao,
            data,
            local,
            ip,
            modelo
        )

        if resultado:
            total_processadas += 1

    return total_processadas


# ================================================================
# MOSTRA RESULTADOS
# ================================================================

def mostrar_resultados(conexao):

    registros = buscar_consolidacoes(
        conexao
    )

    print("\n" + "=" * 60)
    print(" RESULTADOS DA CONSOLIDAÇÃO")
    print("=" * 60)

    if not registros:

        print("\n[AVISO] Nenhum registro consolidado.")

        return

    print(
        f"\n[OK] Total de registros consolidados: "
        f"{len(registros)}"
    )

    for registro in registros:

        (
            data,
            local,
            ip,
            modelo,
            total_medicoes,
            online,
            offline,
            criticas,
            atencoes,
            normais,
            consumo_medio,
            ultima_medicao
        ) = registro

        print("\n" + "-" * 60)

        print(f"Data             : {data}")
        print(f"Local            : {local}")
        print(f"Modelo           : {modelo}")
        print(f"IP               : {ip}")
        print(f"Medições         : {total_medicoes}")
        print(f"Online           : {online}")
        print(f"Offline          : {offline}")
        print(f"Críticas         : {criticas}")
        print(f"Atenções         : {atencoes}")
        print(f"Normais          : {normais}")
        print(
            f"Consumo médio    : "
            f"{consumo_medio:.2f}%"
        )
        print(f"Última medição   : {ultima_medicao}")


# ================================================================
# FUNÇÃO PRINCIPAL
# ================================================================

def main():

    print("=" * 60)
    print(" CONSOLIDADOR DIÁRIO")
    print(" PROJETO IMPRESSORAS")
    print("=" * 60)

    try:

        conexao = conectar()

        print(
            "\n[OK] Conexão com o banco realizada com sucesso."
        )

    except Exception as erro:

        print(
            "\n[ERRO] Não foi possível conectar ao banco."
        )

        print(erro)

        return

    try:

        # --------------------------------------------------------
        # VERIFICA HISTÓRICO
        # --------------------------------------------------------

        if not tabela_existe(
            conexao,
            "historico_impressoras"
        ):

            print(
                "[ERRO] Tabela "
                "'historico_impressoras' não encontrada."
            )

            conexao.close()

            return

        print(
            "[OK] Tabela 'historico_impressoras' encontrada."
        )

        # --------------------------------------------------------
        # CRIA CONSOLIDAÇÃO
        # --------------------------------------------------------

        criar_tabela_consolidacao(
            conexao
        )

        print(
            "[OK] Tabela 'consolidacao_diaria' "
            "verificada."
        )

        # --------------------------------------------------------
        # OBTÉM OS DIAS
        # --------------------------------------------------------

        dias = buscar_dias_historico(
            conexao
        )

        if not dias:

            print(
                "\n[AVISO] Nenhuma medição encontrada "
                "no histórico."
            )

            conexao.close()

            return

        print(
            f"\n[OK] Dias encontrados no histórico: "
            f"{len(dias)}"
        )

        # --------------------------------------------------------
        # PROCESSA CADA DIA
        # --------------------------------------------------------

        total_geral = 0

        for data in dias:

            print("\n" + "-" * 60)

            print(
                f"Consolidando o dia: {data}"
            )

            total = consolidar_dia(
                conexao,
                data
            )

            total_geral += total

            print(
                f"[OK] Impressoras processadas: "
                f"{total}"
            )

        # --------------------------------------------------------
        # MOSTRA RESULTADO
        # --------------------------------------------------------

        mostrar_resultados(
            conexao
        )

        # --------------------------------------------------------
        # VERIFICA HISTÓRICO ORIGINAL
        # --------------------------------------------------------

        total_historico = contar_registros(
            conexao,
            "historico_impressoras"
        )

        print("\n" + "=" * 60)
        print(" VERIFICAÇÃO FINAL")
        print("=" * 60)

        print(
            f"\n[OK] Registros no histórico original: "
            f"{total_historico}"
        )

        print(
            f"[OK] Impressoras processadas nesta execução: "
            f"{total_geral}"
        )

        print(
            "\n[OK] Processo de consolidação concluído."
        )

    except Exception as erro:

        print(
            "\n[ERRO] Ocorreu um erro durante "
            "a consolidação."
        )

        print(
            f"Detalhes: {erro}"
        )

    finally:

        conexao.close()

        print(
            "\n[OK] Banco de dados fechado."
        )


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":
    main()