import sqlite3
import json
from datetime import datetime


# ================================================================
# CONFIGURAÇÕES
# ================================================================

BANCO_DADOS = "impressoras.db"


# ================================================================
# CONECTA AO BANCO
# ================================================================

def conectar_banco():
    return sqlite3.connect(BANCO_DADOS)


# ================================================================
# GARANTE QUE A TABELA EXISTE
# ================================================================

def criar_tabela_consolidacao(conexao):

    cursor = conexao.cursor()

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
# BUSCA OS DIAS EXISTENTES NO HISTÓRICO
# ================================================================

def obter_dias(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT substr(data_hora, 1, 10)
        FROM historico_impressoras
        WHERE data_hora IS NOT NULL
        ORDER BY data_hora
    """)

    return [
        registro[0]
        for registro in cursor.fetchall()
        if registro[0]
    ]


# ================================================================
# BUSCA AS IMPRESSORAS
# ================================================================

def obter_impressoras(conexao, data):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT
            local,
            ip,
            modelo
        FROM historico_impressoras
        WHERE substr(data_hora, 1, 10) = ?
        ORDER BY local
    """, (data,))

    return cursor.fetchall()


# ================================================================
# BUSCA MEDIÇÕES DE UMA IMPRESSORA
# ================================================================

def obter_medicoes(conexao, data, ip):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            data_hora,
            local,
            modelo,
            status_rede,
            status_geral,
            suprimentos,
            status_suprimentos
        FROM historico_impressoras
        WHERE substr(data_hora, 1, 10) = ?
        AND ip = ?
        ORDER BY data_hora ASC
    """, (data, ip))

    return cursor.fetchall()


# ================================================================
# CONSOLIDA UMA IMPRESSORA
# ================================================================

def consolidar_impressora(conexao, data, local, ip, modelo):

    registros = obter_medicoes(
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
    # VERIFICA SE JÁ EXISTE CONSOLIDAÇÃO
    # ------------------------------------------------------------

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id
        FROM consolidacao_diaria
        WHERE data = ?
        AND ip = ?
        LIMIT 1
    """, (data, ip))

    existente = cursor.fetchone()

    # ------------------------------------------------------------
    # ATUALIZA REGISTRO EXISTENTE
    # ------------------------------------------------------------

    if existente:

        cursor.execute("""
            UPDATE consolidacao_diaria
            SET
                local = ?,
                modelo = ?,
                total_medicoes = ?,
                online = ?,
                offline = ?,
                criticas = ?,
                atencoes = ?,
                normais = ?,
                consumo_medio = ?,
                ultima_medicao = ?
            WHERE id = ?
        """, (
            local,
            modelo,
            total_medicoes,
            online,
            offline,
            criticas,
            atencoes,
            normais,
            consumo_medio,
            ultima_medicao,
            existente[0]
        ))

    # ------------------------------------------------------------
    # INSERE NOVO REGISTRO
    # ------------------------------------------------------------

    else:

        cursor.execute("""
            INSERT INTO consolidacao_diaria (
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
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
        ))

    conexao.commit()

    return True


# ================================================================
# CONSOLIDA UM DIA
# ================================================================

def consolidar_dia(conexao, data):

    impressoras = obter_impressoras(
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

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
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
        FROM consolidacao_diaria
        ORDER BY data DESC, local
    """)

    registros = cursor.fetchall()

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

        conexao = conectar_banco()

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

        cursor = conexao.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'historico_impressoras'
        """)

        if not cursor.fetchone():

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

        dias = obter_dias(
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

        cursor.execute("""
            SELECT COUNT(*)
            FROM historico_impressoras
        """)

        total_historico = cursor.fetchone()[0]

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