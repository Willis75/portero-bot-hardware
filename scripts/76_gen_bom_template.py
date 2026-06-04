"""
76_gen_bom_template.py
Genera BOM editable con columnas pre-llenadas para JLCPCB:
- Comment (valor)
- Designator (refs agrupadas)
- Footprint
- LCSC Part # (vacio, el user llena)
- DNP (Yes/No - si se va a JLCPCB Assembly o se solda manual)
- Search Query (busqueda sugerida para JLCPCB Parts Library)
- Notes (recomendaciones especificas)

Output: kicad/gerbers/portero-bot-v2-BOM-TEMPLATE.csv
"""
import csv, os

# THT components que NO van a JLCPCB Assembly
DNP_REFS = set('Q1 Q2 Q3 K1 K2 K3 J1 J3 J4 J5 J6 J7 F1 SW1 SW2 J2'.split())

# Notes per (value, footprint) — recomendaciones
NOTES = {
    ('100uF', 'C_1210_3225Metric'): 'Aluminum polymer OK; X5R/X7R 25V min',
    ('100nF', 'C_1210_3225Metric'): 'X7R/X5R 25V min (bootstrap)',
    ('100nF', 'C_0603_1608Metric'): 'X7R 50V, Basic Part',
    ('22uH',  'L_6.3x6.3_H3'): 'Power inductor 2A+ Isat (Wurth 7440 series, Bourns SRR6038)',
    ('1N4148WS-7-F', 'D_SOD-323'): 'UPGRADE A 1N5819WS Schottky 1A flyback (mas robusto 24/7)',
    ('SS34-E3/57T', 'D_SMA'): 'SS34 generico Vishay/onsemi OK',
    ('SMAJ24CA-TR', 'D_SMA'): 'SMAJ24CA bidirectional TVS',
    ('MP2307DN-HW-LF-Z', 'SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm'): 'MPS Semi exact part, verificar version',
    ('W5500', 'LQFP-48_7x7mm_P0.5mm'): 'WIZnet original (no clon)',
    ('ESP32-WROOM-32E-N16', 'ESP32-WROOM-32'): 'CRITICO: N16 = 16MB flash, no N4/N8',
    ('CH340C', 'SOIC-16_3.9x9.9mm_P1.27mm'): 'WCH original, no CH340G/N',
    ('NX3225GA-25MHZ-STD-CRG-2', 'Crystal_SMD_3225-4Pin_3.2x2.5mm'): '25MHz 20ppm, 4-pad SMD',
    ('0603GBD0790S01', 'LED_0603_1608Metric'): 'LED verde 0603 cualquier marca',
    ('LTST-C190KSKT', 'LED_0603_1608Metric'): 'LED rojo 0603 cualquier marca',
    ('PC817X1CSP9F', 'DIP-4_W7.62mm'): 'Sharp/Lite-On PC817 DIP-4 (THT) - puede ir DNP',
    ('22pF', 'C_0603_1608Metric'): 'C0G/NP0 50V (cristal load cap)',
}

# Search query suggestions
def search_query(val, fpid):
    val_lc = val.lower()
    if val_lc in ('100nf', '10nf', '1uf', '4.7uf', '22pf') and '0603' in fpid:
        return f'{val} 0603 X7R Basic'
    if val_lc == '100uf' and '1210' in fpid:
        return '100uF 1210 25V X5R Basic'
    if val_lc == '100nf' and '1210' in fpid:
        return '100nF 1210 50V X7R'
    if 'k' in val_lc or val_lc.replace('.','').isdigit():
        return f'{val}ohm 0603 1% Basic'
    if val_lc == '22uh':
        return '22uH 6x6 SMD power inductor 2A+'
    if 'esp32-wroom-32e-n16' in val_lc:
        return 'ESP32-WROOM-32E-N16'
    if val_lc == 'w5500':
        return 'W5500 WIZnet LQFP-48'
    if val_lc == 'ch340c':
        return 'CH340C SOIC-16 WCH'
    if 'mp2307' in val_lc:
        return 'MP2307DN MPS SOIC-8 EP'
    if val_lc.startswith('1n4148'):
        return '1N4148WS SOD-323 (o cambiar a 1N5819WS)'
    if val_lc.startswith('ss34'):
        return 'SS34 SMA Schottky 3A 40V'
    if val_lc.startswith('smaj24'):
        return 'SMAJ24CA SMA TVS bidirectional'
    if val_lc.startswith('pc817'):
        return 'PC817 DIP-4 optocoupler'
    if 'crystal' in val_lc or 'mhz' in val_lc or 'nx3225' in val_lc:
        return '25MHz crystal SMD 3.2x2.5mm 4pad'
    if 'led' in val_lc or '0603gbd' in val_lc or 'ltst-c190' in val_lc:
        return f'LED 0603 (color: {"green" if "GBD" in val else "red"})'
    return val

# Read existing BOM
with open('kicad/gerbers/portero-bot-v2-BOM.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Write template
OUTPUT = 'kicad/gerbers/portero-bot-v2-BOM-TEMPLATE.csv'
with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'DNP', 'Search Query', 'Notes'])
    for row in rows:
        val = row['Comment']
        refs = row['Designator']
        fpid = row['Footprint']
        # Determine DNP: if any ref is in DNP set, mark as Yes
        ref_list = [r.strip() for r in refs.split(',')]
        is_dnp = 'Yes' if any(r in DNP_REFS for r in ref_list) else 'No'
        query = search_query(val, fpid)
        note = NOTES.get((val, fpid), '')
        w.writerow([val, refs, fpid, '', is_dnp, query, note])

print(f'Generated: {OUTPUT}')

# Stats
with open(OUTPUT, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
dnp = sum(1 for r in rows if r['DNP'] == 'Yes')
smd = len(rows) - dnp
print(f'  Total: {len(rows)} groups')
print(f'  SMD (a JLCPCB): {smd} groups')
print(f'  THT/Manual (DNP): {dnp} groups')
