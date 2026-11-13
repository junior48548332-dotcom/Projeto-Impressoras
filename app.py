from flask import Flask, render_template, jsonify
import json

from config import (
    INTERVALO_ATUALIZACAO_DASHBOARD,
    MINUTOS_TOLERANCIA_DASHBOARD,
    SERVIDOR_HOST,
    SERVIDOR_PORTA,
    SERVIDOR_DEBUG
)

from agendador import coletar_se_estiver_na_hora

from banco import (
    conectar,
    buscar_impressoras,
    tabela_existe,
    contar_registros,
    buscar_ultimas_medicoes,
    buscar_data_ultima_medicao,
    buscar_indicadores_gerais,
    buscar_consumo_por_setor,
    buscar_top_impressoras,
    buscar_evolucao_consumo
)


app = Flask(__name__)

# Mantém os acentos legíveis nas respostas da API
app.json.ensure_ascii = False


# ================================================================
# CARREGA AS IMPRESSORAS
# ================================================================

def carregar_impressoras():

    # ------------------------------------------------------------
    # LÊ O CADASTRO DE IMPRESSORAS
    # ------------------------------------------------------------

    try:

        conexao = conectar()

        cadastro = buscar_impressoras(
            conexao
        )

        conexao.close()

    except Exception as erro:

        print(
            f"[ERRO] Não foi possível carregar o cadastro: {erro}"
        )

        return []


    if not cadastro:

        print(
            "[AVISO] Nenhuma impressora cadastrada. "
            "Execute: python importar_planilha.py"
        )


    # ------------------------------------------------------------
    # BUSCA A ÚLTIMA MEDIÇÃO DE CADA IMPRESSORA
    # ------------------------------------------------------------

    ultimas_medicoes = {}


    try:

        conexao = conectar()

        registros = buscar_ultimas_medicoes(
            conexao
        )


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


    for linha in cadastro:

        ip = linha["ip"]


        if ip in ultimas_medicoes:

            dados = ultimas_medicoes[ip].copy()


            # Mantém os dados do cadastro
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

        conexao = conectar()


        # --------------------------------------------------------
        # VERIFICA SE A TABELA EXISTE
        # --------------------------------------------------------

        if not tabela_existe(
            conexao,
            "consolidacao_diaria"
        ):

            conexao.close()

            return dados


        # --------------------------------------------------------
        # TOTAL DE REGISTROS CONSOLIDADOS
        # --------------------------------------------------------

        dados["total_registros"] = contar_registros(
            conexao,
            "consolidacao_diaria"
        )


        if dados["total_registros"] == 0:

            conexao.close()

            return dados


        # --------------------------------------------------------
        # INDICADORES GERAIS
        # --------------------------------------------------------

        resultado = buscar_indicadores_gerais(
            conexao
        )


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

        registros_setores = buscar_consumo_por_setor(
            conexao
        )


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

        registros_top = buscar_top_impressoras(
            conexao
        )


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

        registros_evolucao = buscar_evolucao_consumo(
            conexao
        )


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
# CONTADORES E ÚLTIMA ATUALIZAÇÃO
# ================================================================

def contar_status(impressoras):

    resumo = {
        "total": len(impressoras),
        "online": 0,
        "offline": 0,
        "atencao": 0,
        "criticas": 0
    }

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

            resumo["online"] += 1

        elif status_rede == "offline":

            resumo["offline"] += 1

        if status_geral == "critico":

            resumo["criticas"] += 1

        elif status_geral == "atencao":

            resumo["atencao"] += 1

    return resumo


def obter_ultima_atualizacao():

    try:

        conexao = conectar()

        ultima_atualizacao = buscar_data_ultima_medicao(
            conexao
        )

        conexao.close()

        return ultima_atualizacao

    except Exception as erro:

        print(
            f"[ERRO] Erro ao obter última atualização: "
            f"{erro}"
        )

        return None


# ================================================================
# ROTA PRINCIPAL
# ================================================================

@app.route("/")
def dashboard():

    # Se já passou o intervalo desde a última medição, dispara uma
    # coleta em segundo plano. Devolve na hora: a página não espera
    # pela coleta, e os dados novos aparecem na atualização
    # seguinte. Com a coleta automática desligada, não faz nada.
    coletar_se_estiver_na_hora()

    impressoras = carregar_impressoras()


    # ------------------------------------------------------------
    # CONTADORES E ÚLTIMA ATUALIZAÇÃO
    # ------------------------------------------------------------

    resumo = contar_status(impressoras)

    ultima_atualizacao = obter_ultima_atualizacao()


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

        total=resumo["total"],

        online=resumo["online"],

        offline=resumo["offline"],

        atencao=resumo["atencao"],

        criticas=resumo["criticas"],

        ultima_atualizacao=ultima_atualizacao,

        analise=analise,

        intervalo_atualizacao=INTERVALO_ATUALIZACAO_DASHBOARD,

        minutos_tolerancia=MINUTOS_TOLERANCIA_DASHBOARD
    )


# ================================================================
# ROTAS DA API
# ================================================================
#
# Devolvem os mesmos dados do dashboard em formato JSON, para
# que o JavaScript da página (ou outro sistema) possa consultar
# sem recarregar a tela.


@app.route("/api/impressoras")
def api_impressoras():
    """
    Situação atual de todas as impressoras.

    Exemplo de resposta:

    {
        "atualizado_em": "2026-10-16 09:30:00",
        "resumo": {
            "total": 48,
            "online": 46,
            "offline": 2,
            "atencao": 4,
            "criticas": 11
        },
        "impressoras": [ ... ]
    }
    """

    # É esta rota que o painel consulta a cada 50 segundos, então
    # é por aqui que a coleta automática costuma ser disparada.
    coletar_se_estiver_na_hora()

    impressoras = carregar_impressoras()

    return jsonify({

        "atualizado_em": obter_ultima_atualizacao(),

        "resumo": contar_status(impressoras),

        "impressoras": impressoras
    })


@app.route("/api/analise")
def api_analise():
    """
    Dados consolidados do histórico, usados na aba Análise.

    Os totais contam medições do período inteiro, não impressoras.

    Exemplo de resposta:

    {
        "total_registros": 48,
        "consumo_medio": 2.34,
        "total_criticas": 18,
        "total_atencoes": 11,
        "total_normais": 67,
        "total_online": 93,
        "total_offline": 3,
        "setores": [ {"local": "Diretoria", "consumo": 3.5} ],
        "top_impressoras": [ ... ],
        "evolucao": [ {"data": "2026-10-16", "consumo": 2.1} ]
    }
    """

    return jsonify(
        carregar_analise()
    )


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":

    app.run(
        debug=SERVIDOR_DEBUG,
        host=SERVIDOR_HOST,
        port=SERVIDOR_PORTA
    )