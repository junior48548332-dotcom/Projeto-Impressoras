import random
import json
import os
import time


# ============================================================
# CONFIGURAÇÕES DO SIMULADOR
# ============================================================

ARQUIVO_ESTADO = "estado_simulacao.json"

# Tempo mínimo entre ciclos do monitor.
# O monitor atual executa a cada 10 minutos.
INTERVALO_NOVO_CICLO = 30


# ============================================================
# FUNÇÕES INTERNAS
# ============================================================

def carregar_estado():
    """
    Carrega o estado anterior do simulador.

    Caso o arquivo ainda não exista, cria um estado vazio.
    """

    if not os.path.exists(ARQUIVO_ESTADO):
        return {
            "ultima_chamada": 0,
            "indice_impressora": 0,
            "suprimentos": {},
            "rede": {}
        }

    try:
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as arquivo:
            estado = json.load(arquivo)

        # Garante que todas as estruturas necessárias existam
        estado.setdefault("ultima_chamada", 0)
        estado.setdefault("indice_impressora", 0)
        estado.setdefault("suprimentos", {})
        estado.setdefault("rede", {})

        return estado

    except (json.JSONDecodeError, OSError):
        return {
            "ultima_chamada": 0,
            "indice_impressora": 0,
            "suprimentos": {},
            "rede": {}
        }


def salvar_estado(estado):
    """
    Salva o estado atual do simulador.
    """

    try:
        with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as arquivo:
            json.dump(
                estado,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

    except OSError:
        # Se não conseguir salvar, o monitor continua funcionando.
        pass


def preparar_ciclo(estado):
    """
    Identifica se estamos começando uma nova verificação.

    O monitor passa alguns segundos processando as 48 impressoras.
    Depois fica aproximadamente 10 minutos parado.

    Quando detectamos uma pausa maior que INTERVALO_NOVO_CICLO,
    reiniciamos o índice da impressora.
    """

    agora = time.time()

    ultima_chamada = estado.get("ultima_chamada", 0)

    if ultima_chamada == 0:
        estado["indice_impressora"] = 0

    elif agora - ultima_chamada > INTERVALO_NOVO_CICLO:
        estado["indice_impressora"] = 0

    estado["ultima_chamada"] = agora

    return estado


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


# ============================================================
# SUPRIMENTOS
# ============================================================

def gerar_suprimentos(tipo):
    """
    Gera e atualiza os suprimentos da impressora.

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

    tipo = str(tipo).strip().upper()

    estado = carregar_estado()

    estado = preparar_ciclo(estado)

    indice = estado["indice_impressora"]

    # A chave representa a posição da impressora na planilha.
    chave = str(indice)

    # --------------------------------------------------------
    # Se for a primeira vez que encontramos esta impressora,
    # criamos os níveis iniciais.
    # --------------------------------------------------------

    if chave not in estado["suprimentos"]:

        if tipo == "MONO":

            estado["suprimentos"][chave] = {
                "toner_preto": gerar_nivel_inicial(),
                "unidade_imagem": gerar_nivel_inicial()
            }

        else:

            estado["suprimentos"][chave] = {
                "toner_preto": gerar_nivel_inicial(),
                "toner_ciano": gerar_nivel_inicial(),
                "toner_magenta": gerar_nivel_inicial(),
                "toner_amarelo": gerar_nivel_inicial(),
                "unidade_imagem": gerar_nivel_inicial()
            }

    else:

        suprimentos = estado["suprimentos"][chave]

        # ----------------------------------------------------
        # Atualiza o consumo de cada suprimento
        # ----------------------------------------------------

        for nome in list(suprimentos.keys()):

            valor = suprimentos[nome]

            valor = reduzir_suprimento(valor)

            valor = talvez_repor_suprimento(valor)

            suprimentos[nome] = valor

        # ----------------------------------------------------
        # Caso a impressora tenha mudado de MONO para COLOR
        # ou vice-versa na planilha, ajustamos os campos.
        # ----------------------------------------------------

        if tipo == "MONO":

            suprimentos.pop("toner_ciano", None)
            suprimentos.pop("toner_magenta", None)
            suprimentos.pop("toner_amarelo", None)

            suprimentos.setdefault(
                "toner_preto",
                gerar_nivel_inicial()
            )

            suprimentos.setdefault(
                "unidade_imagem",
                gerar_nivel_inicial()
            )

        else:

            suprimentos.setdefault(
                "toner_preto",
                gerar_nivel_inicial()
            )

            suprimentos.setdefault(
                "toner_ciano",
                gerar_nivel_inicial()
            )

            suprimentos.setdefault(
                "toner_magenta",
                gerar_nivel_inicial()
            )

            suprimentos.setdefault(
                "toner_amarelo",
                gerar_nivel_inicial()
            )

            suprimentos.setdefault(
                "unidade_imagem",
                gerar_nivel_inicial()
            )

    resultado = estado["suprimentos"][chave].copy()

    # Avança para a próxima impressora
    estado["indice_impressora"] += 1

    salvar_estado(estado)

    return resultado


# ============================================================
# CLASSIFICAÇÃO DOS SUPRIMENTOS
# ============================================================

def classificar_nivel(percentual):
    """
    Classifica o nível de um suprimento.

    Até 5%  = crítico
    Até 20% = atenção
    Acima de 20% = normal
    """

    percentual = float(percentual)

    if percentual <= 5:
        return "critico"

    elif percentual <= 20:
        return "atencao"

    else:
        return "normal"


# ============================================================
# STATUS DA REDE
# ============================================================

def simular_status_rede():
    """
    Simula a disponibilidade da impressora.

    A maioria das vezes permanece online.

    Quando uma impressora fica offline, existe uma chance
    maior de ela continuar offline no próximo ciclo, mas
    eventualmente poderá voltar ao funcionamento.
    """

    estado = carregar_estado()

    # A função é chamada depois de gerar_suprimentos().
    # Portanto, o índice atual corresponde à impressora atual.
    indice = estado["indice_impressora"] - 1

    if indice < 0:
        indice = 0

    chave = str(indice)

    status_atual = estado["rede"].get(chave, "online")

    # --------------------------------------------------------
    # Se estava offline
    # --------------------------------------------------------

    if status_atual == "offline":

        # 65% de chance de continuar offline
        if random.random() < 0.65:
            novo_status = "offline"

        else:
            novo_status = "online"

    # --------------------------------------------------------
    # Se estava online
    # --------------------------------------------------------

    else:

        # 8% de chance de ficar offline
        if random.random() < 0.08:
            novo_status = "offline"

        else:
            novo_status = "online"

    estado["rede"][chave] = novo_status

    salvar_estado(estado)

    return novo_status


# ============================================================
# TESTE DO SIMULADOR
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(" TESTE DO SIMULADOR DE IMPRESSORAS")
    print("=" * 60)

    print()

    print("Teste MONO:")
    print(gerar_suprimentos("MONO"))

    print()

    print("Teste COLOR:")
    print(gerar_suprimentos("COLOR"))

    print()

    print("Classificação:")
    print("5%  ->", classificar_nivel(5))
    print("20% ->", classificar_nivel(20))
    print("50% ->", classificar_nivel(50))

    print()

    print("Status da rede:")
    print(simular_status_rede())

    print()

    print("Arquivo de estado:")
    print(ARQUIVO_ESTADO)

    print()

    print("=" * 60)