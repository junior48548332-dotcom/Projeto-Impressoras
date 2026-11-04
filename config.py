import os

from pathlib import Path


# ================================================================
# CONFIGURAÇÕES DO PROJETO
# ================================================================
#
# Todos os caminhos e intervalos do sistema ficam neste arquivo.
# Para mudar algum valor, altere somente aqui.


# ================================================================
# PASTA DO PROJETO
# ================================================================

# Pasta onde este arquivo está.
# Os caminhos abaixo partem dela, assim o sistema encontra os
# arquivos mesmo quando é executado a partir de outra pasta.
PASTA_PROJETO = Path(__file__).resolve().parent


# ================================================================
# PLANILHA
# ================================================================

# Planilha com o cadastro das impressoras
ARQUIVO_EXCEL = PASTA_PROJETO / "impressoras.xlsx"

# Aba que contém as impressoras ativas
ABA_PLANILHA = "Impressoras ativas"

# Linha do cabeçalho (0 = primeira linha, 1 = segunda linha)
LINHA_CABECALHO = 1


# ================================================================
# ARQUIVOS GERADOS PELO SISTEMA
# ================================================================

# Banco de dados SQLite
BANCO_DADOS = PASTA_PROJETO / "impressoras.db"

# Estado salvo do simulador (níveis de toner e status de rede)
ARQUIVO_ESTADO_SIMULACAO = PASTA_PROJETO / "estado_simulacao.json"


# ================================================================
# INTERVALOS (em segundos)
# ================================================================

# Tempo entre as coletas do monitor
# 600 segundos = 10 minutos
INTERVALO_COLETA = 600

# Tempo para o dashboard buscar os dados novos na API
INTERVALO_ATUALIZACAO_DASHBOARD = 50

# Tempo sem medição nova até o dashboard avisar que o sistema
# está desatualizado.
#
# Precisa ser maior que o intervalo entre as coletas, senão o
# aviso aparece sozinho no meio do caminho de uma coleta para a
# outra. Quando a coleta for agendada no servidor, este valor
# tem de acompanhar o horário escolhido lá.
MINUTOS_TOLERANCIA_DASHBOARD = 15


# ================================================================
# SERVIDOR WEB
# ================================================================

SERVIDOR_HOST = "127.0.0.1"

SERVIDOR_PORTA = 5000


# ================================================================
# MODO DE DEPURAÇÃO
# ================================================================
#
# Com o debug ligado, o Flask reinicia o servidor ao salvar um
# arquivo e mostra a página de erro detalhada. Essa página traz
# um console Python interativo: quem conseguir provocar um erro
# no site consegue executar comandos no servidor.
#
# Por isso o padrão é DESLIGADO. Em produção, nada precisa ser
# feito: basta não definir a variável de ambiente.
#
# Para ligar enquanto você desenvolve:
#
#     PowerShell:     $env:IMPRESSORAS_DEBUG = "1"
#     Linux / macOS:  export IMPRESSORAS_DEBUG=1

VARIAVEL_DEBUG = "IMPRESSORAS_DEBUG"

VALORES_LIGADO = ("1", "true", "sim", "on")


def debug_ligado():
    """Lê a variável de ambiente que liga o modo de depuração."""

    valor = os.environ.get(VARIAVEL_DEBUG, "")

    return valor.strip().lower() in VALORES_LIGADO


SERVIDOR_DEBUG = debug_ligado()
