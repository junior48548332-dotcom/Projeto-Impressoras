import sqlite3
import json

from datetime import datetime

from config import BANCO_DADOS, FUSO_HORARIO


# ================================================================
# BANCO DE DADOS
# ================================================================
#
# Todo o acesso ao banco SQLite fica neste arquivo:
# conexão, criação das tabelas e consultas.
#
# Os outros arquivos não escrevem SQL. Eles abrem uma conexão,
# chamam as funções daqui e fecham a conexão no final:
#
#     conexao = conectar()
#
#     registros = buscar_ultimas_medicoes(conexao)
#
#     conexao.close()


# Tabelas existentes no sistema
TABELAS = (
    "impressoras",
    "historico_impressoras",
    "consolidacao_diaria"
)


# ================================================================
# CONEXÃO
# ================================================================

def conectar():

    return sqlite3.connect(
        BANCO_DADOS
    )


# ================================================================
# CRIAÇÃO DAS TABELAS
# ================================================================

def criar_tabela_impressoras(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS impressoras (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            local TEXT NOT NULL,

            modelo TEXT,

            tipo TEXT,

            paper TEXT,

            serie TEXT,

            ip TEXT NOT NULL UNIQUE
        )
    """)

    conexao.commit()


def criar_tabela_historico(conexao):

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


def criar_tabelas(conexao):

    criar_tabela_impressoras(conexao)

    criar_tabela_historico(conexao)

    criar_tabela_consolidacao(conexao)


# ================================================================
# INFORMAÇÕES DAS TABELAS
# ================================================================

def validar_tabela(nome_tabela):

    # O nome de uma tabela não pode ir como parâmetro "?" no SQL,
    # então ele é colocado direto no texto da consulta.
    # Por segurança, só aceitamos as tabelas conhecidas.

    if nome_tabela not in TABELAS:

        raise ValueError(
            f"Tabela desconhecida: {nome_tabela}"
        )


def tabela_existe(conexao, nome_tabela):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
    """, (nome_tabela,))

    return cursor.fetchone() is not None


def contar_registros(conexao, nome_tabela):

    validar_tabela(nome_tabela)

    cursor = conexao.cursor()

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM {nome_tabela}
    """)

    return cursor.fetchone()[0] or 0


def estrutura_tabela(conexao, nome_tabela):

    validar_tabela(nome_tabela)

    cursor = conexao.cursor()

    cursor.execute(f"""
        PRAGMA table_info({nome_tabela})
    """)

    return cursor.fetchall()


# ================================================================
# CADASTRO DAS IMPRESSORAS
# ================================================================

# Colunas do cadastro, na ordem usada nas consultas
COLUNAS_CADASTRO = [
    "local",
    "modelo",
    "tipo",
    "paper",
    "serie",
    "ip"
]


def substituir_impressoras(conexao, impressoras):

    # Apaga o cadastro atual e grava a nova lista, na mesma ordem.
    # As duas operações são confirmadas juntas: se algo der errado,
    # o rollback desfaz tudo e o cadastro anterior é mantido.

    cursor = conexao.cursor()

    try:

        cursor.execute("""
            DELETE FROM impressoras
        """)

        cursor.executemany("""
            INSERT INTO impressoras (
                local,
                modelo,
                tipo,
                paper,
                serie,
                ip
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                impressora["local"],
                impressora["modelo"],
                impressora["tipo"],
                impressora["paper"],
                impressora["serie"],
                impressora["ip"]
            )
            for impressora in impressoras
        ])

        conexao.commit()

    except Exception:

        conexao.rollback()

        raise


def buscar_impressoras(conexao):

    # Devolve uma lista com um dicionário por impressora,
    # na mesma ordem da planilha importada.
    # Se a planilha ainda não foi importada, devolve lista vazia.

    if not tabela_existe(conexao, "impressoras"):

        return []

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            local,
            modelo,
            tipo,
            paper,
            serie,
            ip
        FROM impressoras
        ORDER BY id
    """)

    return [
        dict(zip(COLUNAS_CADASTRO, registro))
        for registro in cursor.fetchall()
    ]


# ================================================================
# HISTÓRICO DAS IMPRESSORAS
# ================================================================

def salvar_medicao(conexao, impressora):

    cursor = conexao.cursor()

    # O fuso vem do config.py, não do relógio do servidor: na
    # nuvem ele roda em UTC e a medição ficaria 3 horas à frente.
    data_hora = datetime.now(FUSO_HORARIO).strftime(
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


def buscar_ultimas_medicoes(conexao):

    # Última medição de cada impressora (maior id de cada IP)

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            local,
            modelo,
            tipo,
            paper,
            serie,
            ip,
            status_rede,
            status_geral,
            suprimentos,
            status_suprimentos,
            data_hora
        FROM historico_impressoras
        WHERE id IN (
            SELECT MAX(id)
            FROM historico_impressoras
            GROUP BY ip
        )
    """)

    return cursor.fetchall()


def buscar_data_ultima_medicao(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT MAX(data_hora)
        FROM historico_impressoras
    """)

    return cursor.fetchone()[0]


def contar_impressoras_registradas(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COUNT(DISTINCT ip)
        FROM historico_impressoras
    """)

    return cursor.fetchone()[0]


def buscar_medicoes_recentes(conexao, limite=5):

    cursor = conexao.cursor()

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
        LIMIT ?
    """, (limite,))

    return cursor.fetchall()


def buscar_ultima_medicao_completa(conexao):

    cursor = conexao.cursor()

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

    return cursor.fetchone()


def buscar_dias_historico(conexao):

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


def buscar_ultimo_dia_historico(conexao):
    """
    Devolve o dia da medição mais recente, ou None se o
    histórico estiver vazio.

    Serve para consolidar só o dia que acabou de receber
    medições, sem reprocessar o histórico inteiro.
    """

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT substr(MAX(data_hora), 1, 10)
        FROM historico_impressoras
        WHERE data_hora IS NOT NULL
    """)

    registro = cursor.fetchone()

    if not registro or not registro[0]:
        return None

    return registro[0]


def buscar_impressoras_do_dia(conexao, data):

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


def buscar_medicoes_do_dia(conexao, data, ip):

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
# CONSOLIDAÇÃO DIÁRIA
# ================================================================

def salvar_consolidacao(conexao, dados):

    # Atualiza a consolidação do dia se ela já existir.
    # Caso contrário, cria um novo registro.

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id
        FROM consolidacao_diaria
        WHERE data = ?
        AND ip = ?
        LIMIT 1
    """, (dados["data"], dados["ip"]))

    existente = cursor.fetchone()

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
            dados["local"],
            dados["modelo"],
            dados["total_medicoes"],
            dados["online"],
            dados["offline"],
            dados["criticas"],
            dados["atencoes"],
            dados["normais"],
            dados["consumo_medio"],
            dados["ultima_medicao"],
            existente[0]
        ))

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
            dados["data"],
            dados["local"],
            dados["ip"],
            dados["modelo"],
            dados["total_medicoes"],
            dados["online"],
            dados["offline"],
            dados["criticas"],
            dados["atencoes"],
            dados["normais"],
            dados["consumo_medio"],
            dados["ultima_medicao"]
        ))

    conexao.commit()


def buscar_consolidacoes(conexao):

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

    return cursor.fetchall()


# ================================================================
# ANÁLISE (DASHBOARD)
# ================================================================

def buscar_indicadores_gerais(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            AVG(consumo_medio),
            SUM(criticas),
            SUM(atencoes),
            SUM(normais),
            SUM(online),
            SUM(offline)
        FROM consolidacao_diaria
    """)

    return cursor.fetchone()


def buscar_consumo_por_setor(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            local,
            AVG(consumo_medio) AS consumo
        FROM consolidacao_diaria
        GROUP BY local
        ORDER BY consumo DESC
    """)

    return cursor.fetchall()


def buscar_top_impressoras(conexao, limite=10):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            local,
            ip,
            modelo,
            consumo_medio,
            total_medicoes
        FROM consolidacao_diaria
        ORDER BY consumo_medio DESC
        LIMIT ?
    """, (limite,))

    return cursor.fetchall()


def buscar_evolucao_consumo(conexao):

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            data,
            AVG(consumo_medio)
        FROM consolidacao_diaria
        GROUP BY data
        ORDER BY data
    """)

    return cursor.fetchall()
