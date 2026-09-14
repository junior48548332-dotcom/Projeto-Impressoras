from flask import Flask, render_template
import pandas as pd
import sqlite3
import json


app = Flask(__name__)


# ================================================================
# CONFIGURAÇÕES
# ================================================================

ARQUIVO_EXCEL = "impressoras.xlsx"
BANCO_DADOS = "impressoras.db"


# ================================================================
# CARREGA IMPRESSORAS DO EXCEL
# ================================================================

def carregar_impressoras():

    # ------------------------------------------------------------
    # LÊ A PLANILHA
    # ------------------------------------------------------------

    try:

        df = pd.read_excel(
            ARQUIVO_EXCEL,
            sheet_name="Impressoras ativas",
            header=1
        )

    except Exception as erro:

        print(
            f"[ERRO] Não foi possível carregar o Excel: {erro}"
        )

        return []


    # ------------------------------------------------------------
    # PEGA AS PRIMEIRAS 6 COLUNAS
    # ------------------------------------------------------------

    df = df.iloc[:, :6]

    df.columns = [
        "local",
        "modelo",
        "tipo",
        "paper",
        "serie",
        "ip"
    ]


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
    # BUSCA A ÚLTIMA MEDIÇÃO DE CADA IMPRESSORA
    # ------------------------------------------------------------

    ultimas_medicoes = {}


    try:

        conexao = sqlite3.connect(
            BANCO_DADOS
        )

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


        registros = cursor.fetchall()


        for registro in registros:

            (
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
            ) = registro


            try:

                dados_suprimentos = json.loads(
                    suprimentos
                ) if suprimentos else {}

            except Exception:

                dados_suprimentos = {}


            try:

                dados_status_suprimentos = json.loads(
                    status_suprimentos
                ) if status_suprimentos else {}

            except Exception:

                dados_status_suprimentos = {}


            ultimas_medicoes[str(ip)] = {

                "local": local,

                "modelo": modelo,

                "tipo": tipo,

                "paper": paper,

                "serie": serie,

                "ip": ip,

                "status_rede": status_rede,

                "status_geral": status_geral,

                "suprimentos": dados_suprimentos,

                "status_suprimentos":
                    dados_status_suprimentos,

                "data_hora": data_hora
            }


        conexao.close()


    except Exception as erro:

        print(
            f"[ERRO] Erro ao consultar o banco: {erro}"
        )


    # ------------------------------------------------------------
    # MONTA LISTA FINAL
    # ------------------------------------------------------------

    impressoras = []


    for _, linha in df.iterrows():

        ip = linha["ip"]


        if ip in ultimas_medicoes:

            dados = ultimas_medicoes[ip].copy()


            # Mantém os dados cadastrados no Excel
            dados["local"] = linha["local"]
            dados["modelo"] = linha["modelo"]
            dados["tipo"] = linha["tipo"]
            dados["paper"] = linha["paper"]
            dados["serie"] = linha["serie"]
            dados["ip"] = ip


        else:

            # ----------------------------------------------------
            # CASO AINDA NÃO EXISTA MEDIÇÃO
            # ----------------------------------------------------

            dados = {

                "local": linha["local"],

                "modelo": linha["modelo"],

                "tipo": linha["tipo"],

                "paper": linha["paper"],

                "serie": linha["serie"],

                "ip": ip,

                "status_rede": "desconhecido",

                "status_geral": "normal",

                "suprimentos": {},

                "status_suprimentos": {},

                "data_hora": None
            }


        impressoras.append(dados)


    return impressoras


# ================================================================
# CARREGA DADOS CONSOLIDADOS
# ================================================================

def carregar_analise():

    dados = {

        "total_registros": 0,

        "consumo_medio": 0,

        "total_criticas": 0,

        "total_atencoes": 0,

        "total_normais": 0,

        "total_online": 0,

        "total_offline": 0,

        "setores": [],

        "top_impressoras": [],

        "evolucao": []
    }


    try:

        conexao = sqlite3.connect(
            BANCO_DADOS
        )

        cursor = conexao.cursor()


        # --------------------------------------------------------
        # VERIFICA SE A TABELA EXISTE
        # --------------------------------------------------------

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'consolidacao_diaria'
        """)


        tabela = cursor.fetchone()


        if not tabela:

            conexao.close()

            return dados


        # --------------------------------------------------------
        # TOTAL DE REGISTROS CONSOLIDADOS
        # --------------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM consolidacao_diaria
        """)


        dados["total_registros"] = (
            cursor.fetchone()[0] or 0
        )


        if dados["total_registros"] == 0:

            conexao.close()

            return dados


        # --------------------------------------------------------
        # INDICADORES GERAIS
        # --------------------------------------------------------

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


        resultado = cursor.fetchone()


        dados["consumo_medio"] = (
            float(resultado[0] or 0)
        )

        dados["total_criticas"] = (
            int(resultado[1] or 0)
        )

        dados["total_atencoes"] = (
            int(resultado[2] or 0)
        )

        dados["total_normais"] = (
            int(resultado[3] or 0)
        )

        dados["total_online"] = (
            int(resultado[4] or 0)
        )

        dados["total_offline"] = (
            int(resultado[5] or 0)
        )


        # --------------------------------------------------------
        # CONSUMO POR SETOR
        # --------------------------------------------------------

        cursor.execute("""
            SELECT
                local,
                AVG(consumo_medio) AS consumo
            FROM consolidacao_diaria
            GROUP BY local
            ORDER BY consumo DESC
        """)


        registros_setores = cursor.fetchall()


        for local, consumo in registros_setores:

            dados["setores"].append({

                "local": local,

                "consumo": round(
                    float(consumo or 0),
                    2
                )
            })


        # --------------------------------------------------------
        # TOP IMPRESSORAS
        # --------------------------------------------------------

        cursor.execute("""
            SELECT
                local,
                ip,
                modelo,
                consumo_medio,
                total_medicoes
            FROM consolidacao_diaria
            ORDER BY consumo_medio DESC
            LIMIT 10
        """)


        registros_top = cursor.fetchall()


        for registro in registros_top:

            (
                local,
                ip,
                modelo,
                consumo,
                medicoes
            ) = registro


            dados["top_impressoras"].append({

                "local": local,

                "ip": ip,

                "modelo": modelo,

                "consumo": round(
                    float(consumo or 0),
                    2
                ),

                "medicoes": medicoes
            })


        # --------------------------------------------------------
        # EVOLUÇÃO POR DIA
        # --------------------------------------------------------

        cursor.execute("""
            SELECT
                data,
                AVG(consumo_medio)
            FROM consolidacao_diaria
            GROUP BY data
            ORDER BY data
        """)


        registros_evolucao = cursor.fetchall()


        for data, consumo in registros_evolucao:

            dados["evolucao"].append({

                "data": data,

                "consumo": round(
                    float(consumo or 0),
                    2
                )
            })


        conexao.close()


    except Exception as erro:

        print(
            f"[ERRO] Erro ao carregar análise: {erro}"
        )


    return dados


# ================================================================
# ROTA PRINCIPAL
# ================================================================

@app.route("/")
def dashboard():

    impressoras = carregar_impressoras()


    # ------------------------------------------------------------
    # CONTADORES DA DASHBOARD
    # ------------------------------------------------------------

    total = len(impressoras)

    online = 0

    offline = 0

    atencao = 0

    criticas = 0


    for impressora in impressoras:

        status_rede = str(
            impressora.get(
                "status_rede",
                ""
            )
        ).lower()


        status_geral = str(
            impressora.get(
                "status_geral",
                ""
            )
        ).lower()


        if status_rede == "online":

            online += 1

        elif status_rede == "offline":

            offline += 1


        if status_geral == "critico":

            criticas += 1

        elif status_geral == "atencao":

            atencao += 1


    # ------------------------------------------------------------
    # ÚLTIMA ATUALIZAÇÃO
    # ------------------------------------------------------------

    ultima_atualizacao = None


    try:

        conexao = sqlite3.connect(
            BANCO_DADOS
        )

        cursor = conexao.cursor()


        cursor.execute("""
            SELECT MAX(data_hora)
            FROM historico_impressoras
        """)


        resultado = cursor.fetchone()


        if resultado:

            ultima_atualizacao = resultado[0]


        conexao.close()


    except Exception as erro:

        print(
            f"[ERRO] Erro ao obter última atualização: "
            f"{erro}"
        )


    # ------------------------------------------------------------
    # CARREGA DADOS DA ANÁLISE
    # ------------------------------------------------------------

    analise = carregar_analise()


    # ------------------------------------------------------------
    # ENVIA TUDO PARA A DASHBOARD
    # ------------------------------------------------------------

    return render_template(

        "dashboard.html",

        impressoras=impressoras,

        total=total,

        online=online,

        offline=offline,

        atencao=atencao,

        criticas=criticas,

        ultima_atualizacao=ultima_atualizacao,

        analise=analise
    )


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )