import random


def gerar_suprimentos(tipo):

    # Impressora monocromática
    if tipo == "MONO":

        return {
            "toner_preto": random.randint(0, 100),
            "unidade_imagem": random.randint(0, 100),
        }

    # Impressora colorida
    else:

        return {
            "toner_preto": random.randint(0, 100),
            "toner_ciano": random.randint(0, 100),
            "toner_magenta": random.randint(0, 100),
            "toner_amarelo": random.randint(0, 100),
            "unidade_imagem": random.randint(0, 100),
        }


def classificar_nivel(percentual):

    if percentual <= 5:
        return "critico"

    elif percentual <= 20:
        return "atencao"

    else:
        return "normal"


def simular_status_rede():

    # Simulação de disponibilidade da impressora
    if random.random() < 0.90:
        return "online"
    else:
        return "offline"