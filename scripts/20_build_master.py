#!/usr/bin/env python3
"""
20_build_master.py — Cruza el netlist con valores (Pick&Place) y part numbers
(BOM JLCPCB), aplica footprints corregidos y normaliza valores raros de Flux.

Entrada : data/instances.json
          source-flux/gerbers/pick_and_place.csv
          source-flux/gerbers/BOM/...-JLCPCB.csv
Salida  : data/master.json   (lista de componentes lista para el esquematico)
"""
import csv, json, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
GERB = os.path.join(ROOT, "source-flux", "gerbers")

insts = json.load(open(os.path.join(DATA, "instances.json")))

val = {}
with open(os.path.join(GERB, "pick_and_place.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        val[r["Designator"].strip('"')] = r["Value"].strip('"')

lcsc = {}
bom = glob.glob(os.path.join(GERB, "BOM", "*JLCPCB.csv"))
if bom:
    with open(bom[0], encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            part = r.get("LCSC Part #", "").strip('"')
            for d in r["Designator"].strip('"').replace(" ", "").split(","):
                if d:
                    lcsc[d] = part

def footprint(d):
    if d.startswith("R"): return "Resistor_SMD:R_0603_1608Metric"
    if d.startswith("LED"): return "LED_SMD:LED_0603_1608Metric"
    if d.startswith("L"): return "Inductor_SMD:L_6.3x6.3_H3"
    if d.startswith("C"):
        if d in ("C16","C17","C20","C21","C22","C23"):
            return "Capacitor_SMD:C_1210_3225Metric"
        return "Capacitor_SMD:C_0603_1608Metric"
    if d.startswith("LED"): return "LED_SMD:LED_0603_1608Metric"
    m = {"U1":"RF_Module:ESP32-WROOM-32","U2":"Package_QFP:LQFP-48_7x7mm_P0.5mm",
         "U3":"Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
         "U4":"Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm",
         "U5":"Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm",
         "Y1":"Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
         "J1":"Connector_BarrelJack:BarrelJack_Horizontal",
         "J2":"Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal",
         "J3":"Connector_USB:USB_Micro-B_Wuerth_614105150721_Vertical",
         "J4":"TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal",
         "J5":"TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal",
         "J6":"TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal",
         "J7":"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
         "K1":"Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C",
         "K2":"Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C",
         "K3":"Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C",
         "Q1":"Package_TO_SOT_THT:TO-92_Inline","Q2":"Package_TO_SOT_THT:TO-92_Inline","Q3":"Package_TO_SOT_THT:TO-92_Inline",
         "D1":"Diode_SMD:D_SMA","D2":"Diode_SMD:D_SMA","D3":"Diode_SMD:D_SOD-323","D4":"Diode_SMD:D_SOD-323","D5":"Diode_SMD:D_SOD-323",
         "F1":"Fuse:Fuse_1206_3216Metric",
         "ISO1":"Package_DIP:DIP-4_W7.62mm","ISO2":"Package_DIP:DIP-4_W7.62mm","ISO3":"Package_DIP:DIP-4_W7.62mm",
         "SW1":"Button_Switch_SMD:SW_Push_SPST_NO_Alps_SKRK",
         "SW2":"Button_Switch_SMD:SW_Push_SPST_NO_Alps_SKRK"}
    return m.get(d, "?")

DECOUPLING_CAPS = ("C2","C3","C6","C7","C8","C9","C10","C11")

def value(d):
    if d in DECOUPLING_CAPS: return "100nF"   # Flux los marcó 100uF en error; son desacople
    v = val.get(d, "")
    v = v.replace("muF", "uF")
    if "Mohms" in v: v = v.replace("0.01Mohms", "10k")
    v = v.replace("ohms", "").replace("kohms", "k")
    return v or insts[d]

def note(d):
    if d in ("C16","C17","C20","C21","C22","C23"): return "Bulk buck: 100uF/35V ceramico 1210"
    if d in DECOUPLING_CAPS: return "Desacople: corregido 100uF→100nF (Flux error)"
    if d in ("L1","L2"): return "Inductor de potencia 22uH 6x6mm Isat>=2A"
    if d == "F1": return "PTC 1.5A hold"
    if d in ("D3","D4","D5"): return "Flyback rele: 1N4148 SOD-323 ok (carga DC baja)"
    return ""

parts = sorted(insts, key=lambda s: (re.match(r"[A-Z]+", s).group(), int(re.search(r"\d+", s).group())))
master = [dict(ref=d, value=value(d), part=insts[d], fp_corr=footprint(d),
              lcsc=lcsc.get(d, ""), nota=note(d)) for d in parts]
json.dump(master, open(os.path.join(DATA, "master.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"OK  componentes={len(master)}")
