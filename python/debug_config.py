import sys
import os

# Adicionar o diretório atual ao path para resolver imports de 'translated' e 'api'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from translated.plan1_tables import CABOS_POR_REDE, CABOS_TABLE, POSTE_TABLE, REDE_TABLE
    print("Imports bem-sucedidos!")
    
    cabos_nomes = [str(row[0]) for row in CABOS_TABLE if row and row[0]]
    redes_nomes = [str(row[0]) for row in REDE_TABLE if row and row[0]]
    postes_por_tipo = {
        str(tipo): [str(modelo[0]) for modelo in modelos if modelo and modelo[0]]
        for tipo, modelos in POSTE_TABLE.items()
    }
    
    config = {
        "redes": redes_nomes,
        "cabos": cabos_nomes,
        "postes": postes_por_tipo,
        "cabos_por_rede": CABOS_POR_REDE,
    }
    
    print(f"Config gerada com sucesso! Redes: {len(redes_nomes)}, Cabos: {len(cabos_nomes)}")
    print(f"Primeiras 5 redes: {redes_nomes[:5]}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
