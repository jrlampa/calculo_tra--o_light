import pandas as pd

df = pd.read_csv('legacy_audit_report_ap_cosmo.csv')

total = len(df)
ok_count = len(df[df['Status Paridade'] == 'OK'])
failed_count = len(df[df['Status Paridade'] == 'FAILED'])
error_count = len(df[df['Status Paridade'] == 'ERROR'])

overload_detected = len(df[df['Erros Humanos Detectados'].str.contains('SOBRECARGA', na=False)])
none_type_errors = len(df[df['Erros Humanos Detectados'].str.contains('NoneType', na=False)])

print(f"Total: {total}")
print(f"Paridade OK: {ok_count} ({ok_count/total:.1%})")
print(f"Divergentes (FAILED): {failed_count} ({failed_count/total:.1%})")
print(f"Erros de Execução (ERROR): {error_count} ({error_count/total:.1%})")
print(f"--- Detalhes ---")
print(f"Sobrecargas Detectadas (Regra 5%): {overload_detected}")
print(f"Arquivos com Dados Incompletos (NoneType): {none_type_errors}")

# Média de divergência nos FAILED (excluindo os OK que tem 0)
mean_divergence = df[df['Status Paridade'] == 'FAILED']['Divergencia'].mean()
print(f"Média de Divergência nos FAILED: {mean_divergence:.4f} daN")
