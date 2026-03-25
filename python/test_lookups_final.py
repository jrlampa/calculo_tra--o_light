import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from translated.plan1_tables import lookup_rede_qtd_cabos, lookup_cable_diam, lookup_cable_peso
    
    rede = "Nua"
    cabo = "ACSR 4/0"
    
    qtd = lookup_rede_qtd_cabos(rede)
    diam = lookup_cable_diam(cabo)
    peso = lookup_cable_peso(cabo)
    
    print(f"Rede '{rede}': Qtd={qtd}")
    print(f"Cabo '{cabo}': Diam={diam}, Peso={peso}")
    
    if qtd is None or diam is None or peso is None:
        print("ERRO: Um dos lookups falhou!")
        sys.exit(1)
    else:
        print("Lookups bem-sucedidos!")
        
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
