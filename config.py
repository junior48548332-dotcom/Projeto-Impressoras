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

# Tempo para o dashboard recarregar a página
INTERVALO_ATUALIZACAO_DASHBOARD = 50


# ================================================================
# SERVIDOR WEB
# ================================================================

SERVIDOR_HOST = "127.0.0.1"

SERVIDOR_PORTA = 5000

# Reinicia o servidor ao salvar arquivos e mostra erros detalhados.
# Deve ficar desligado (False) quando o sistema for publicado.
SERVIDOR_DEBUG = True
