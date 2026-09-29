import random
import json
import os

from config import ARQUIVO_ESTADO_SIMULACAO


# ================================================================
# SIMULADOR DE IMPRESSORAS
# ================================================================
#
# Finge ser as impressoras da rede: gera o nível dos suprimentos
# e o status de rede de cada uma.
#
# O monitor usa apenas a função coletar():
#
#     dados = coletar(
#         {"ip": "192.168.0.2", "tipo": "COLOR"}
#     )
#
#     {
#         "status_rede": "online",
#         "suprimentos": {
#             "toner_preto": 62,
#             "unidade_imagem": 88
#         }
#     }
#
# Cada impressora é identificada pelo IP, então mudar a ordem
# das linhas da planilha não embaralha os dados.
#
# Uma coleta real (por SNMP) pode substituir este arquivo:
# basta oferecer a mesma função coletar(impressora).


# Versão do arquivo de estado.
# Estados gravados por versões antigas do simulador usavam a
# posição na planilha como chave e são descartados.
VERSAO_ESTADO = 2


# ================================================================
# ESTADO DA SIMULAÇÃO
# ================================================================
#
# Os níveis precisam cair aos poucos a cada coleta, então o
# simulador guarda os valores anteriores em um arquivo JSON.


def estado_vazio():

    return {
        "versao": VERSAO_ESTADO,
        "suprimentos": {},
        "rede": {}
    }


def carregar_estado():

    if not os.path.exists(ARQUIVO_ESTADO_SIMULACAO):
        return estado_vazio()

    try:
        with open(ARQUIVO_ESTADO_SIMULACAO, "r", encoding="utf-8") as arquivo:
            estado = json.load(arquivo)

    except (json.JSONDecodeError, OSError):
        return estado_vazio()

    # Arquivo de uma versão anterior: começa do zero
    if estado.get("versao") != VERSAO_ESTADO:
        return estado_vazio()

    # Garante que todas as estruturas necessárias existam
    estado.setdefault("suprimentos", {})
    estado.setdefault("rede", {})

    return estado


def salvar_estado(estado):

    try:
        with open(ARQUIVO_ESTADO_SIMULACAO, "w", encoding="utf-8") as arquivo:
            json.dump(
                estado,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

    except OSError:
        # Se não conseguir salvar, o monitor continua funcionando.
        pass


# ================================================================
# NÍVEIS DOS SUPRIMENTOS
# ================================================================

def gerar_nivel_inicial():
    """
    Gera um nível inicial mais realista.

    Evita que todas as impressoras comecem necessariamente
    em valores completamente aleatórios.
    """

    chance = random.random()

    if chance < 0.10:
        return random.randint(0, 20)

    elif chance < 0.30:
        return random.randint(21, 50)

    else:
        return random.randint(51, 100)


def reduzir_suprimento(valor):
    """
    Reduz gradualmente um suprimento.

    A maior parte das verificações apresenta uma pequena redução.
    Algumas vezes o consumo pode ser um pouco maior.
    """

    chance = random.random()

    if chance < 0.65:
        consumo = random.randint(0, 2)

    elif chance < 0.95:
        consumo = random.randint(2, 5)

    else:
        consumo = random.randint(5, 8)

    novo_valor = valor - consumo

    if novo_valor < 0:
        novo_valor = 0

    return novo_valor


def talvez_repor_suprimento(valor):
    """
    Simula uma eventual troca/reposição de suprimento.

    A reposição não acontece imediatamente ao chegar a zero.
    Existe uma pequena probabilidade a cada ciclo.
    """

    if valor <= 5 and random.random() < 0.08:
        return random.randint(80, 100)

    return valor


def nomes_dos_suprimentos(tipo):
    """
    Impressoras MONO:
    - toner preto
    - unidade de imagem

    Impressoras COLOR:
    - toner preto
    - toner ciano
    - toner magenta
    - toner amarelo
    - unidade de imagem
    """

    if tipo == "MONO":

        return [
            "toner_preto",
            "unidade_imagem"
        ]

    return [
        "toner_preto",
        "toner_ciano",
        "toner_magenta",
        "toner_amarelo",
        "unidade_imagem"
    ]


def atualizar_suprimentos(estado, ip, tipo):

    nomes = nomes_dos_suprimentos(tipo)

    anteriores = estado["suprimentos"].get(ip, {})

    suprimentos = {}

    for nome in nomes:

        # ----------------------------------------------------
        # Primeira coleta desta impressora, ou suprimento que
        # ela não tinha antes (tipo alterado na planilha).
        # ----------------------------------------------------

        if nome not in anteriores:

            suprimentos[nome] = gerar_nivel_inicial()

            continue

        # ----------------------------------------------------
        # Coletas seguintes: o nível cai aos poucos e, de vez
        # em quando, o suprimento é reposto.
        # ----------------------------------------------------

        valor = reduzir_suprimento(
            anteriores[nome]
        )

        suprimentos[nome] = talvez_repor_suprimento(
            valor
        )

    # Suprimentos que não pertencem mais ao tipo da impressora
    # ficam de fora, porque só copiamos os nomes da lista acima.

    estado["suprimentos"][ip] = suprimentos

    return suprimentos


# ================================================================
# STATUS DA REDE
# ================================================================

def atualizar_status_rede(estado, ip):
    """
    Simula a disponibilidade da impressora.

    A maioria das vezes permanece online.

    Quando uma impressora fica offline, existe uma chance
    maior de ela continuar offline no próximo ciclo, mas
    eventualmente poderá voltar ao funcionamento.
    """

    status_atual = estado["rede"].get(ip, "online")

    if status_atual == "offline":

        # 65% de chance de continuar offline
        if random.random() < 0.65:
            novo_status = "offline"

        else:
            novo_status = "online"

    else:

        # 8% de chance de ficar offline
        if random.random() < 0.08:
            novo_status = "offline"

        else:
            novo_status = "online"

    estado["rede"][ip] = novo_status

    return novo_status


# ================================================================
# COLETA
# ================================================================

def coletar(impressora):
    """
    Devolve os dados simulados de uma impressora do cadastro.
    """

    ip = str(
        impressora["ip"]
    ).strip()

    tipo = str(
        impressora.get("tipo", "")
    ).strip().upper()

    estado = carregar_estado()

    suprimentos = atualizar_suprimentos(
        estado,
        ip,
        tipo
    )

    status_rede = atualizar_status_rede(
        estado,
        ip
    )

    salvar_estado(estado)

    return {
        "status_rede": status_rede,
        "suprimentos": suprimentos
    }


# ================================================================
# TESTE DO SIMULADOR
# ================================================================

if __name__ == "__main__":

    print("=" * 60)
    print(" TESTE DO SIMULADOR DE IMPRESSORAS")
    print("=" * 60)

    print()

    print("Impressora MONO:")
    print(
        coletar({
            "ip": "192.168.0.101",
            "tipo": "MONO"
        })
    )

    print()

    print("Impressora COLOR:")
    print(
        coletar({
            "ip": "192.168.0.102",
            "tipo": "COLOR"
        })
    )

    print()

    print("Arquivo de estado:")
    print(ARQUIVO_ESTADO_SIMULACAO)

    print()

    print("=" * 60)
