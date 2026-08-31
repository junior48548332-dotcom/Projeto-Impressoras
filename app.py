import flask
from flask import render_template
import pandas as pd

from simulador import (
    gerar_suprimentos,
    classificar_nivel,
    simular_status_rede
)

app = flask.Flask(__name__)


def carregar_impressoras():
    arquivo = "impressoras.xlsx"

    df = pd.read_excel(
        arquivo,
        header=None,
        skiprows=2
        
    )
    df = df.fillna("")

    # Se a planilha tiver 7 colunas,
    # adicionamos a coluna observacao.
    if len(df.columns) == 7:
        df["observacao"] = ""

    # Mantém somente as 8 colunas esperadas.
    df = df.iloc[:, :8]

    df.columns = [
        "local",
        "modelo",
        "tipo",
        "paper",
        "serie",
        "ip",
        "fila",
        "observacao"
    ]

    # Remove linhas sem local ou IP.
    df = df.dropna(
        subset=["local", "ip"]
    )

    impressoras = []

    for _, linha in df.iterrows():

        tipo = str(
            linha["tipo"]
        ).strip().upper()

        # Gera os níveis dos suprimentos.
        suprimentos = gerar_suprimentos(tipo)

        # Simula o status da rede.
        status_rede = simular_status_rede()

        # Classifica cada suprimento.
        status_suprimentos = {}

        for nome, percentual in suprimentos.items():

            status_suprimentos[nome] = classificar_nivel(
                percentual
            )

        # Define o status geral da impressora.
        if "critico" in status_suprimentos.values():

            status_geral = "critico"

        elif "atencao" in status_suprimentos.values():

            status_geral = "atencao"

        else:

            status_geral = "normal"

        impressora = {
            "local": linha["local"],
            "modelo": linha["modelo"],
            "tipo": tipo,
            "paper": linha["paper"],
            "serie": linha["serie"],
            "ip": linha["ip"],
            "fila": linha["fila"],
            "observacao": linha["observacao"],

            "suprimentos": suprimentos,

            "status_suprimentos": status_suprimentos,

            "status_geral": status_geral,

            "status_rede": status_rede
        }

        impressoras.append(impressora)

    return impressoras


@app.route("/")
def dashboard():

    impressoras = carregar_impressoras()

    # Contadores
    total_online = 0
    total_offline = 0
    total_atencao = 0
    total_critico = 0

    for impressora in impressoras:

        # Status da rede
        if impressora["status_rede"] == "online":

            total_online += 1

        else:

            total_offline += 1

        # Status dos suprimentos
        status = impressora[
            "status_suprimentos"
        ].values()

        if "critico" in status:

            total_critico += 1

        elif "atencao" in status:

            total_atencao += 1

    return render_template(
        "dashboard.html",

        impressoras=impressoras,

        total_online=total_online,

        total_offline=total_offline,

        total_atencao=total_atencao,

        total_critico=total_critico
    )


if __name__ == "__main__":

    app.run(debug=True)