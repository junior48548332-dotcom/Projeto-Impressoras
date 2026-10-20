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