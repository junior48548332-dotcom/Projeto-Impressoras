from app import carregar_impressoras


impressoras = carregar_impressoras()

total_atencao = 0
total_critico = 0
total_normal = 0


for impressora in impressoras:

    status = impressora["status_suprimentos"].values()

    if "critico" in status:
        total_critico += 1

    elif "atencao" in status:
        total_atencao += 1

    else:
        total_normal += 1


print()
print("=" * 50)
print("RESUMO DAS IMPRESSORAS")
print("=" * 50)

print("Total:", len(impressoras))
print("Normais:", total_normal)
print("Atenção:", total_atencao)
print("Críticas:", total_critico)

print()
print("SOMA:", total_normal + total_atencao + total_critico)
print("=" * 50)