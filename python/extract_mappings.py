import openpyxl

def identify_mapping():
    wb = openpyxl.load_workbook('../AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm', data_only=True)
    ws = wb['Plan4']
    
    # Vamos mapear as colunas de Plan4 que parecem conter as listas de cabos por tipo.
    # Baseado em auditorias anteriores:
    # Coluna A: Redes (Tipo)
    # Coluna F: Modelos Poste
    # Outras colunas podem ser listas nomeadas para INDIRETO() no Excel.
    
    mapping = {}
    networks = []
    # Captura todos os nomes de ranges definidos
    for name, nr in wb.defined_names.items():
        try:
            dests = list(nr.destinations)
            if not dests: continue
            sheetname, coord = dests[0]
            ws = wb[sheetname]
            cells = ws[coord.replace('$', '')]
            values = []
            if hasattr(cells, '__iter__'):
                 if isinstance(cells, tuple):
                     if hasattr(cells[0], '__iter__'):
                         values = [r[0].value for r in cells if r[0].value]
                     else:
                         values = [c.value for c in cells if c.value]
                 else:
                     values = [cells.value] if cells.value else []
            else:
                 values = [cells.value] if cells.value else []
            
            if name == 'Tipo':
                networks = values
                print(f"Networks (Tipo): {networks}")
            
            mapping[name] = values
        except: pass
    
    print("\nMapping found for Network Types:")
    for net in networks:
        clean_net = str(net).strip()
        if clean_net in mapping:
            print(f"'{clean_net}': {mapping[clean_net]}")
        else:
            # Tenta sem espaços ou normalizado
            norm_net = "".join(clean_net.split())
            if norm_net in mapping:
                print(f"'{clean_net}' (mapped as {norm_net}): {mapping[norm_net]}")
            else:
                print(f"'{clean_net}': No specific range found")
    
    return mapping

identify_mapping()
