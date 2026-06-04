"""
77_fill_bom_lcsc.py
Llena LCSC# del BOM template con valores verificados via WebSearch (JLCPCB Basic Library).
"""
import csv

# Map (value, footprint) -> (LCSC#, JLCPCB tier, fabricante, notas)
LCSC_MAP = {
    # SMD Confirmados
    ('100nF', 'C_0603_1608Metric'): ('C14663', 'Basic', 'YAGEO CC0603KRX7R9BB104', 'X7R 50V 10%'),
    ('10nF',  'C_0603_1608Metric'): ('C57112', 'Basic', 'FENGHUA 0603B103K500NT', 'X7R 50V'),
    ('1uF',   'C_0603_1608Metric'): ('C15849', 'Basic', 'Samsung CL10A105KB8NNNC', 'X5R 50V'),
    ('4.7uF', 'C_0603_1608Metric'): ('C19666', 'Basic', 'Samsung CL10A475KO8NNNC', 'X5R 16V'),
    ('22pF',  'C_0603_1608Metric'): ('C1653',  'Basic', 'Samsung CL10C220JB8NNNC', 'C0G 50V (xtal)'),
    ('100uF', 'C_1210_3225Metric'): ('C2840614', 'Verify', 'Samsung CL32A107KAJNNNE', 'X5R 25V'),
    ('100nF', 'C_1210_3225Metric'): ('', 'BUSCAR', '', 'BUSCAR: 100nF 1210 50V X7R - C22/C23 BOOTSTRAP critico'),
    ('10k',   'R_0603_1608Metric'): ('C25804', 'Basic', 'UNI-Royal 0603WAF1002T5E', '1% 100mW'),
    ('1k',    'R_0603_1608Metric'): ('C21190', 'Basic', 'UNI-Royal 0603WAF1001T5E', '1% 100mW'),
    ('330',   'R_0603_1608Metric'): ('C23138', 'Basic', 'UNI-Royal 0603WAF3300T5E', '1% 100mW'),
    ('12.4k', 'R_0603_1608Metric'): ('C25867', 'Verify', 'UNI-Royal 0603WAF1242T5E', 'BUSCAR: confirmar en JLCPCB'),
    ('26.1k', 'R_0603_1608Metric'): ('', 'BUSCAR', '', 'BUSCAR: 26.1k 0603 1% (FB divider 3V3)'),
    ('44.2k', 'R_0603_1608Metric'): ('', 'BUSCAR', '', 'BUSCAR: 44.2k 0603 1% (FB divider 5V)'),
    ('1N4148WS-7-F', 'D_SOD-323'): ('C8598', 'Basic', 'Jiangsu Changjing B5819W SL', 'CAMBIAR a 1N5819WS Schottky 1A (24/7 mejor)'),
    ('SS34-E3/57T', 'D_SMA'): ('C8678', 'Basic', 'MDD SS34', 'Schottky 3A 40V'),
    ('SMAJ24CA-TR', 'D_SMA'): ('C148223', 'Extended', 'Littelfuse SMAJ24CA', 'TVS bidirectional'),
    ('CH340C', 'SOIC-16_3.9x9.9mm_P1.27mm'): ('C84681', 'Extended', 'WCH CH340C', 'USB-UART'),
    ('W5500', 'LQFP-48_7x7mm_P0.5mm'): ('C32843', 'Extended', 'WIZnet W5500', 'Ethernet MAC+PHY'),
    ('ESP32-WROOM-32E-N16', 'ESP32-WROOM-32'): ('C701343', 'Extended', 'Espressif ESP32-WROOM-32E-N16', '16MB Flash'),
    ('MP2307DN-HW-LF-Z', 'SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm'): ('C6306034', 'Extended', 'MPS MP2307DN-LF-P', 'Verificar pin-compat con LF-P vs HW-LF-Z'),
    ('NX3225GA-25MHZ-STD-CRG-2', 'Crystal_SMD_3225-4Pin_3.2x2.5mm'): ('C438901', 'Extended', 'NDK NX3225GA-25MHZ-STD-CRG-2', '25MHz exact part'),
    ('22uH', 'L_6.3x6.3_H3'): ('C354622', 'Verify', 'CENKER CKCS6028-22uH/M', 'Verificar 2A+ Isat'),
    ('PC817X1CSP9F', 'DIP-4_W7.62mm'): ('', 'BUSCAR', '', 'BUSCAR: PC817 SHARP DIP-4 (THT puede ir DNP)'),
    ('0603GBD0790S01', 'LED_0603_1608Metric'): ('C72043', 'Verify', 'Lite-On LTST-C190KGKT', 'LED VERDE 0603'),
    ('LTST-C190KSKT', 'LED_0603_1608Metric'): ('C2286', 'Verify', 'Lite-On LTST-C190KRKT', 'LED ROJO 0603'),

    # THT components - DNP for JLCPCB Assembly
    ('0ZCC0150BF2C', 'Fuse_1206_3216Metric'): ('DNP', 'Manual', 'Bel Fuse 0ZCC0150BF2C', 'PTC 1.5A fuse - soldar manual'),
    ('2N2222A', 'TO-92_Inline'): ('DNP', 'Manual', '2N2222A TO-92', 'Soldar manual'),
    ('DC005', 'BarrelJack_Horizontal'): ('DNP', 'Manual', 'DC005 barrel jack 9-24V', 'Soldar manual'),
    ('HR911105A', 'RJ45_Hanrun_HR911105A_Horizontal'): ('DNP', 'Manual', 'Hanrun HR911105A', 'RJ45 magjack - soldar manual'),
    ('KF301-2P', 'TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal'): ('DNP', 'Manual', 'KF301-2P 5.08mm', 'Terminal block portones'),
    ('KH-6X6X5H-STM', 'SW_Push_SPST_NO_Alps_SKRK'): ('DNP', 'Manual', 'KH-6X6X5H tactile sw', 'BOOT/RESET buttons'),
    ('Pin Header 01x04 2.54mm Vertical', 'PinHeader_1x04_P2.54mm_Vertical'): ('DNP', 'Manual', 'Pin header 1x4 2.54mm', 'Debug header J7'),
    ('SRD-05VDC-SL-C', 'Relay_SPDT_SANYOU_SRD_Series_Form_C'): ('DNP', 'Manual', 'SANYOU SRD-05VDC-SL-C', 'Relay coil 5V'),
    ('USB Micro B', 'USB_Micro-B_Wuerth_614105150721_Vertical'): ('DNP', 'Manual', 'USB Micro-B THT', 'Connector flash USB'),
}

# Read template
with open('kicad/gerbers/portero-bot-v2-BOM-TEMPLATE.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Update with LCSC info
filled = 0
todo = 0
for row in rows:
    val = row['Comment']
    fpid = row['Footprint']
    key = (val, fpid)
    if key in LCSC_MAP:
        lcsc, tier, mfg, note = LCSC_MAP[key]
        row['LCSC Part #'] = lcsc
        # Append tier/mfg info to Notes
        existing_note = row['Notes']
        new_note = f'[{tier}] {mfg} — {note}'
        if existing_note:
            new_note = existing_note + ' || ' + new_note
        row['Notes'] = new_note
        if lcsc and lcsc != 'DNP':
            filled += 1
        elif not lcsc:
            todo += 1

# Write final BOM
OUTPUT = 'kicad/gerbers/portero-bot-v2-BOM-FINAL.csv'
with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'DNP', 'Search Query', 'Notes']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f'Generated: {OUTPUT}')
print(f'  Filled (LCSC#): {filled}')
print(f'  To search (manual): {todo}')
print(f'  DNP/Manual: {sum(1 for r in rows if r["LCSC Part #"] == "DNP")}')
