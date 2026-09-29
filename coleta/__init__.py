# ================================================================
# COLETA DOS DADOS DAS IMPRESSORAS
# ================================================================
#
# Esta pasta guarda as formas de obter os dados das impressoras.
#
# Hoje existe apenas o simulador, que inventa os valores:
#
#     from coleta.simulador import coletar
#
# Uma coleta real (por SNMP, por exemplo) pode ser adicionada
# aqui como coleta/snmp.py, oferecendo a mesma função
# coletar(impressora). Para trocar uma pela outra, basta mudar
# a linha de import no monitor.py.
