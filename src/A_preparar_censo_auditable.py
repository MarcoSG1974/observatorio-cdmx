import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
ARCHIVO_ENTRADA = 'conjunto_de_datos_ageb_urbana_09_cpv2020.csv'
ARCHIVO_SALIDA = 'CNPV_CDMX_AGEBS_Limpio.csv'
ARCHIVO_AUDITORIA = 'Auditoria_Limpieza_Censo.csv'

print("🔄 Iniciando pipeline de limpieza V3 (Enfoque CDMX)...")

# ==========================================
# 2. SELECCIÓN DE VARIABLES
# ==========================================
columnas_geograficas = ['ENTIDAD', 'NOM_ENT', 'MUN', 'NOM_MUN', 'LOC', 'NOM_LOC', 'AGEB', 'MZA']

columnas_demograficas = [
    'POBTOT', 'POBFEM', 'POBMAS',
    'P_0A2', 'P_0A2_F', 'P_0A2_M', 'P_3A5', 'P_3A5_F', 'P_3A5_M',
    'P_6A11', 'P_6A11_F', 'P_6A11_M', 'P_12A14', 'P_12A14_F', 'P_12A14_M',
    'P_15A17', 'P_15A17_F', 'P_15A17_M', 'P_60YMAS', 'P_60YMAS_F', 'P_60YMAS_M',
    'PCON_DISC', 'PCDISC_MOT', 'PCDISC_VIS', 'PCDISC_LENG', 'PCDISC_AUD', 'PCDISC_MOT2', 'PCDISC_MEN',
    'PEA', 'PEA_F', 'PEA_M', 'PE_INAC', 'PE_INAC_F', 'PE_INAC_M',
    'POCUPADA', 'POCUPADA_F', 'POCUPADA_M', 'PDESOCUP', 'PDESOCUP_F', 'PDESOCUP_M',
    'TOTHOG', 'HOGJEF_F', 'HOGJEF_M', 'VIVTOT', 'TVIVHAB', 'PROM_OCUP', 'PRO_OCUP_C',
    'VPH_PISODT', 'VPH_PISOTI', 'VPH_1DOR', 'VPH_2YMASD', 'VPH_1CUART', 'VPH_2CUART', 'VPH_3YMASC',
    'VPH_C_ELEC', 'VPH_S_ELEC', 'VPH_AGUADV', 'VPH_AEASP', 'VPH_AGUAFV', 'VPH_TINACO', 'VPH_CISTER',
    'VPH_EXCSA', 'VPH_LETR', 'VPH_DRENAJ', 'VPH_NODREN', 'VPH_C_SERV', 'VPH_NDEAED', 'VPH_DSADMA', 'VPH_NDACMM',
    'VPH_SNBIEN', 'VPH_REFRI', 'VPH_LAVAD', 'VPH_HMICRO', 'VPH_AUTOM', 'VPH_MOTO', 'VPH_BICI', 'VPH_RADIO',
    'VPH_TV', 'VPH_PC', 'VPH_TELEF', 'VPH_CEL', 'VPH_INTER', 'VPH_STVP', 'VPH_SPMVPI', 'VPH_CVJ',
    'VPH_SINRTV', 'VPH_SINLTC', 'VPH_SINCINT', 'VPH_SINTIC'
]

columnas_clave = columnas_geograficas + columnas_demograficas

# Cargar datos
try:
    df = pd.read_csv(ARCHIVO_ENTRADA, usecols=columnas_clave, low_memory=False, dtype=str)
    print(f"✅ Carga inicial completada. Registros totales: {len(df):,}")
except FileNotFoundError:
    print(f"❌ Error: No se encontró '{ARCHIVO_ENTRADA}'.")
    exit()

# ==========================================
# 3. FILTRADO ESTRICTO: SOLO CDMX Y SOLO AGEBs
# ==========================================
print("\n🔎 Filtrando exclusivamente CDMX y nivel AGEB...")

# 1. Solo Ciudad de México (Entidad 09)
df = df[df['ENTIDAD'] == '09'].copy()

# 2. Solo totales de AGEB (MZA == '000' y AGEB != '0000' para descartar totales de municipio/entidad)
df = df[(df['MZA'] == '000') & (df['AGEB'] != '0000')].copy()

print(f"📊 Registros filtrados (AGEBs urbanas de CDMX): {len(df):,}")

if len(df) == 0:
    print("❌ Error: El filtro dejó el DataFrame vacío.")
    exit()

# ==========================================
# 4. CONVERSIÓN Y LÍNEA BASE
# ==========================================
print("\n Convirtiendo variables a numérico...")
for col in columnas_demograficas:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

pobtot_inicial = df['POBTOT'].sum()
print(f"📍 LÍNEA BASE 1 - POBTOT Inicial (CDMX): {pobtot_inicial:,}")

# ==========================================
# 5. IMPUTACIÓN ARITMÉTICA (Despeje simple)
# ==========================================
print("🧮 Aplicando imputación aritmética...")

grupos_trio = [
    ('P_0A2', 'P_0A2_F', 'P_0A2_M'), ('P_3A5', 'P_3A5_F', 'P_3A5_M'),
    ('P_6A11', 'P_6A11_F', 'P_6A11_M'), ('P_12A14', 'P_12A14_F', 'P_12A14_M'),
    ('P_15A17', 'P_15A17_F', 'P_15A17_M'), ('P_60YMAS', 'P_60YMAS_F', 'P_60YMAS_M'),
    ('PEA', 'PEA_F', 'PEA_M'), ('PE_INAC', 'PE_INAC_F', 'PE_INAC_M'),
    ('POCUPADA', 'POCUPADA_F', 'POCUPADA_M'), ('PDESOCUP', 'PDESOCUP_F', 'PDESOCUP_M')
]

for total, fem, masc in grupos_trio:
    df.loc[df[fem].isna() & df[total].notna() & df[masc].notna(), fem] = df[total] - df[masc]
    df.loc[df[masc].isna() & df[total].notna() & df[fem].notna(), masc] = df[total] - df[fem]

# ==========================================
# 6. IMPUTACIÓN ESTADÍSTICA (Ratio POBFEM/POBTOT)
# ==========================================
print("📐 Aplicando imputación estadística (Ratio por sexo)...")

def imputar_ratio(row, total_col, f_col, m_col):
    if row[total_col] > 0 and (pd.isna(row[f_col]) or pd.isna(row[m_col])):
        ratio_f = row['POBFEM'] / row['POBTOT'] if row['POBTOT'] > 0 else 0.51
        f_val = round(row[total_col] * ratio_f)
        return pd.Series([f_val, row[total_col] - f_val])
    return pd.Series([row[f_col], row[m_col]])

for total, fem, masc in grupos_trio:
    df[[fem, masc]] = df.apply(lambda r: imputar_ratio(r, total, fem, masc), axis=1)

# ==========================================
# 7. LIMPIEZA FINAL INTELIGENTE (Sin Hard Drop destructivo)
# ==========================================
print("\n🧹 Aplicando limpieza final inteligente...")

# En lugar de borrar filas, rellenamos los NaN residuales con 0. 
# En datos de conteo censal, un asterisco residual tras imputación se asume conservadoramente como 0 
# para no perder la AGEB completa por una variable secundaria.
df_final = df.fillna(0).copy()

# Aseguramos que las columnas demográficas sean enteros
for col in columnas_demograficas:
    df_final[col] = df_final[col].astype(int)

pobtot_final = df_final['POBTOT'].sum()
print(f"📍 LÍNEA BASE 2 - POBTOT Final (tras imputación completa): {pobtot_final:,}")
print(f"   (Registros finales: {len(df_final):,})")

# ==========================================
# 8. REPORTE DE AUDITORÍA Y GUARDADO
# ==========================================
auditoria = {
    'Etapa': ['Inicial (Filtro CDMX + AGEB)', 'Final (Imputación completa)'],
    'Registros': [len(df), len(df_final)],
    'POBTOT_Suma': [pobtot_inicial, pobtot_final],
    'Porcentaje_Poblacion': ['100%', f"{(pobtot_final/pobtot_inicial)*100:.2f}%"]
}
df_auditoria = pd.DataFrame(auditoria)
df_auditoria.to_csv(ARCHIVO_AUDITORIA, index=False, encoding='utf-8-sig')

df_final.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')

print("\n" + "="*60)
print(" ✅ PIPELINE COMPLETADO EXITOSAMENTE")
print("="*60)
print(f"📂 Dataset limpio guardado como: {ARCHIVO_SALIDA}")
print(f"📋 Auditoría guardada como: {ARCHIVO_AUDITORIA}")
print(f"👥 Población total procesada: {pobtot_final:,} (Debería ser ~9.2 millones para CDMX)")
print("="*60)