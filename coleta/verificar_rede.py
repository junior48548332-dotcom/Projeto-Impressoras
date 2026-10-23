"""
Verificação de conectividade com impressoras reais.

Tenta abrir uma conexão com cada IP para descobrir se a
impressora responde na rede. É um utilitário de apoio: não faz
parte do sistema e não é executado pelos testes automatizados,
porque depende de impressoras ligadas na rede da empresa.

Serve como ponto de partida para a coleta real (coleta/snmp.py),
que no futuro vai substituir o simulador.

Uso:

    python coleta/verificar_rede.py
"""

import socket
import time


def testar_impressora(ip, porta=80, timeout=2):
    inicio = time.time()

    try:
        conexao = socket.create_connection(
            (ip, porta),
            timeout=timeout
        )

        conexao.close()

        tempo = round(time.time() - inicio, 2)

        return True, tempo

    except (socket.timeout, ConnectionRefusedError, OSError):

        tempo = round(time.time() - inicio, 2)

        return False, tempo


# Vamos testar apenas 3 impressoras inicialmente
ips = [
    "10.149.120.17",
    "10.149.120.16",
    "10.149.120.18"
]


print()
print("=" * 60)
print("TESTE DE CONECTIVIDADE DAS IMPRESSORAS")
print("=" * 60)


for ip in ips:

    print()
    print(f"Testando: {ip}")

    online, tempo = testar_impressora(ip)

    if online:

        print(f"STATUS: ONLINE")
        print(f"Tempo de resposta: {tempo} segundos")

    else:

        print(f"STATUS: OFFLINE")
        print(f"Tempo de resposta: {tempo} segundos")


print()
print("=" * 60)
print("TESTE FINALIZADO")
print("=" * 60)