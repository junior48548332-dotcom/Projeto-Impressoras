import os

from datetime import timedelta, timezone

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
# FUSO HORÁRIO
# ================================================================
#
# O horário de cada medição é gravado no banco. Sem dizer de que
# fuso ele é, o sistema usaria o relógio do computador em que
# está rodando — e o servidor da nuvem roda em UTC, 3 horas à
# frente de Brasília.
#
# Isso estragaria duas coisas:
#
#   1. O painel mostraria a medição no futuro e avisaria
#      "sistema desatualizado" o tempo todo.
#
#   2. Pior: a consolidação agrupa por dia recortando o texto da
#      data. Com o servidor em UTC, o dia viraria às 21h de
#      Brasília, e uma coleta feita depois disso entraria no dia
#      seguinte, errando o relatório sem dar nenhum sinal.
#
# Por isso o fuso é declarado aqui, e não herdado do servidor.
#
# É um deslocamento fixo porque o Brasil não tem horário de
# verão desde 2019. Se voltar a ter, é esta linha que muda.
#
# Não é usado o zoneinfo da biblioteca padrão porque, no
# Windows, ele depende do pacote tzdata, que não vem junto com o
# Python — e o projeto é desenvolvido no Windows.

FUSO_HORARIO = timezone(
    timedelta(hours=-3),
    "Horário de Brasília"
)


# Formato em que a data e a hora são gravadas no banco.
#
# Ordena corretamente em ordem alfabética, e o dia é um recorte do
# texto: substr(data_hora, 1, 10). A consolidação depende disso.
FORMATO_DATA_HORA = "%Y-%m-%d %H:%M:%S"


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

# Usado também pela coleta automática, mais abaixo
VALORES_LIGADO = ("1", "true", "sim", "on")


def debug_ligado():
    """Lê a variável de ambiente que liga o modo de depuração."""

    valor = os.environ.get(VARIAVEL_DEBUG, "")

    return valor.strip().lower() in VALORES_LIGADO


SERVIDOR_DEBUG = debug_ligado()


# ================================================================
# COLETA AUTOMÁTICA PELO SERVIDOR
# ================================================================
#
# Com isto ligado, o próprio servidor web dispara uma coleta
# quando percebe que a última medição passou do INTERVALO_COLETA.
# Quem verifica é o servidor, a cada requisição; o navegador não
# pede coleta nenhuma.
#
# Existe porque o plano gratuito do PythonAnywhere não oferece
# tarefas agendadas para contas novas. A lógica fica no
# agendador.py.
#
# O padrão é DESLIGADO, por dois motivos:
#
#   1. Na máquina de desenvolvimento, quem coleta é o
#      monitor.py --continuo. O servidor web coletar junto seria
#      surpresa.
#
#   2. Os testes sobem o aplicativo com um banco temporário. Se a
#      coleta automática viesse ligada, eles gravariam medições
#      que não pediram.
#
# Para ligar no servidor, a forma mais simples é definir a
# variável no próprio arquivo WSGI:
#
#     import os
#     os.environ["IMPRESSORAS_COLETA_WEB"] = "1"

VARIAVEL_COLETA_WEB = "IMPRESSORAS_COLETA_WEB"


def coleta_web_ligada():
    """Lê a variável de ambiente que liga a coleta automática."""

    valor = os.environ.get(VARIAVEL_COLETA_WEB, "")

    return valor.strip().lower() in VALORES_LIGADO


COLETA_WEB = coleta_web_ligada()


# Tempo mínimo entre duas tentativas de coleta automática.
#
# Sem isso, uma coleta que falha seria tentada de novo a cada
# atualização do painel — a cada 50 segundos.
SEGUNDOS_ENTRE_TENTATIVAS = 60
