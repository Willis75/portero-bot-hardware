#!/usr/bin/env python3
"""
30_gen_schematic.py — Genera el esquematico KiCad desde el netlist + master.

Entrada : data/nets_clean.json, data/master.json
Salida  : kicad/portero-bot-v2.kicad_sch
          kicad/portero-bot-v2.kicad_pro

Metodo: cada componente = simbolo "caja" con pines numerados por el PAD real
del footprint (mapas oficiales de KiCad para los ICs). La conectividad se hace
por ETIQUETAS GLOBALES (dos pines con la misma etiqueta = misma red). Los pines
de potencia con varios pads se expanden a TODOS sus pads.

Limitaciones conocidas (revisar en KiCad con ERC):
- J2 (RJ45 HR911105A): pines anonimos en Flux -> pads sin mapear.
- Polaridad LEDs/diodos y pines del rele: best-effort, confirmar con footprint.
"""
import json, os, re, uuid
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); KIC = os.path.join(ROOT, "kicad"); os.makedirs(KIC, exist_ok=True)
master = {m["ref"]: m for m in json.load(open(os.path.join(DATA, "master.json"), encoding="utf-8"))}
nets = json.load(open(os.path.join(DATA, "nets_clean.json"), encoding="utf-8"))
def U(): return str(uuid.uuid4())
RT = U()

ESP32={'3V3':['2'],'EN':['3'],'IO32':['8'],'IO33':['9'],'IO25':['10'],'IO26':['11'],'IO27':['12'],
 'IO0':['25'],'IO5':['29'],'IO18':['30'],'IO19':['31'],'IO23':['37'],'TXD0':['35'],'RXD0':['34'],'GND':['1','15','38','39']}
W5500={'TXN':['1'],'TXP':['2'],'RXN':['5'],'RXP':['6'],'AVDD':['4','8','11','15','17','21'],
 'AGND':['3','9','14','16','19','48'],'VDD':['28'],'GND':['29'],'EXRES1':['10'],'TOCAP':['20'],
 '1V2O':['22'],'RSVD':['23','38','39','40','41','42'],'XI/CLKIN':['30'],'XO':['31'],'~SCS':['32'],
 'SCLK':['33'],'MISO':['34'],'MOSI':['35'],'~INT':['36'],'~RST':['37'],'PMODE2':['43'],'PMODE1':['44'],'PMODE0':['45']}
CH340={'GND':['1'],'TXD':['2'],'RXD':['3'],'V3':['4'],'UD+':['5'],'UD-':['6'],'VCC':['16']}
MP2307={'BS':['1'],'IN':['2'],'SW':['3'],'GND':['4'],'FB':['5'],'EN':['7'],'EPAD':['9']}
XTAL={'1':['1'],'3':['3'],'GND':['2','4']}
OPTO={'ANODE':['1'],'CATHODE':['2'],'EMITTER':['3'],'COLLECTOR':['4']}
TRANS={'E':['1'],'B':['2'],'C':['3']}
RELAY={'A1':['1'],'A2':['2'],'COM':['3'],'NC':['4'],'NO':['5']}
LED={'A':['2'],'K':['1']}; DIODE={'A':['2'],'K':['1'],'1':['1'],'2':['2']}
USB={'VBUS':['1'],'UD-':['2'],'D-':['2'],'UD+':['3'],'D+':['3'],'ID':['4'],'GND':['5'],
 'S1':['6'],'S2':['6'],'S3':['6'],'S4':['6'],'S5':['6'],'S6':['6']}
def padmap(ref, func):
    if ref=='U1': return ESP32.get(func,[func])
    if ref=='U2': return W5500.get(func,[func])
    if ref=='U3': return CH340.get(func,[func])
    if ref in ('U4','U5'): return MP2307.get(func,[func])
    if ref=='Y1': return XTAL.get(func,[func])
    if ref.startswith('ISO'): return OPTO.get(func,[func])
    if ref.startswith('Q'): return TRANS.get(func,[func])
    if re.match(r'^K\d+$',ref): return RELAY.get(func,[func])
    if ref.startswith('LED'): return LED.get(func,[func])
    if ref.startswith('D'): return DIODE.get(func,[func])
    if ref=='J3': return USB.get(func,[func])
    if ref=='J2':
        if re.fullmatch(r'\d+', str(func)): return [str(func)]
        if str(func).upper() == 'SHIELD': return ['SH']
        return [func]
    if re.match(r'^[RCLF]\d+$',ref): return {'P1':['1'],'P2':['2']}.get(func,[func])
    if ref=='J7': return {'Pin_1':['1'],'Pin_2':['2'],'Pin_3':['3'],'Pin_4':['4']}.get(func,[func])
    return [func]

comp_nodes={}
for n in nets:
    for pin in n["pins"]:
        ref,func = pin.rsplit(".",1)
        if ref in master: comp_nodes.setdefault(ref,[]).append((func,n["name"]))

comp_pins={}; flag=set()
for ref,nodes in comp_nodes.items():
    pins=[]; used=set()
    for func,net in nodes:
        for pad in padmap(ref,func):
            num=pad
            if num in used:
                k=2
                while f"{pad}_{k}" in used: k+=1
                num=f"{pad}_{k}"
            if not re.match(r'^\d',str(pad)): flag.add(ref)
            used.add(num); pins.append((num,func,net))
    comp_pins[ref]=pins

PIT=7.62; ROWH=63.5; PAGEW=1050.0; X0=25.4; Y0=30.0
order=sorted(comp_pins,key=lambda r:(re.match(r'[A-Z]+',r).group(),int(re.search(r'\d+',r).group())))
placed=[]; x=X0; y=Y0
for ref in order:
    w=max(len(comp_pins[ref])-1,0)*PIT+15.24
    if x+w>PAGEW: x=X0; y+=ROWH
    placed.append((ref,x,y)); x+=w+7.62
PAGEH=y+ROWH+20; pos={r:(a,b) for r,a,b in placed}
fpc=lambda s:s.split(' (')[0]

def lib_symbol(ref):
    pins=comp_pins[ref]; endx=(len(pins)-1)*PIT+1.27
    s=[f'    (symbol "portero:{ref}" (pin_numbers hide) (pin_names (offset 1.016) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)',
       f'      (property "Reference" "{ref[0]}" (at 0 5.08 0) (effects (font (size 1.27 1.27))))',
       f'      (property "Value" "{ref}" (at 0 3.0 0) (effects (font (size 1.27 1.27))))',
       f'      (symbol "{ref}_0_1"',
       f'        (rectangle (start -1.27 2.54) (end {endx:.2f} 13.97) (stroke (width 0.254) (type default)) (fill (type background))))',
       f'      (symbol "{ref}_1_1"']
    for i,(num,name,net) in enumerate(pins):
        s.append(f'        (pin passive line (at {i*PIT:.2f} 0 270) (length 2.54)')
        s.append(f'          (name "{name}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
    s += ['      )','    )']
    return "\n".join(s)

def inst(ref):
    X,Y=pos[ref]; m=master[ref]
    s=[f'  (symbol (lib_id "portero:{ref}") (at {X:.2f} {Y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
       f'    (uuid "{U()}")',
       f'    (property "Reference" "{ref}" (at {X:.2f} {Y-9:.2f} 0) (effects (font (size 1.27 1.27))))',
       f'    (property "Value" "{m["value"]}" (at {X:.2f} {Y-6.5:.2f} 0) (effects (font (size 1.27 1.27))))',
       f'    (property "Footprint" "{fpc(m["fp_corr"])}" (at {X:.2f} {Y-4:.2f} 0) (effects (font (size 1.0 1.0)) (hide yes)))']
    for num,name,net in comp_pins[ref]:
        s.append(f'    (pin "{num}" (uuid "{U()}"))')
    s.append(f'    (instances (project "portero" (path "/{RT}" (reference "{ref}") (unit 1))))')
    s.append('  )')
    return "\n".join(s)

def conns(ref):
    X,Y=pos[ref]; out=[]
    for i,(num,name,net) in enumerate(comp_pins[ref]):
        px=X+i*PIT
        out.append(f'  (wire (pts (xy {px:.2f} {Y:.2f}) (xy {px:.2f} {Y+5.08:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
        out.append(f'  (global_label "{net}" (shape input) (at {px:.2f} {Y+5.08:.2f} 270) (fields_autoplaced yes) (effects (font (size 1.0 1.0)) (justify left)) (uuid "{U()}"))')
    return "\n".join(out)

doc=['(kicad_sch (version 20231120) (generator "claude") (generator_version "8.0")',
     f'  (uuid "{RT}")', f'  (paper "User" {PAGEW+50:.1f} {PAGEH:.1f})', '  (lib_symbols']
doc += [lib_symbol(r) for r in order]; doc.append('  )')
doc += [inst(r) for r in order]; doc += [conns(r) for r in order]
doc += ['  (sheet_instances (path "/" (page "1")))', ')']
open(os.path.join(KIC,"portero-bot-v2.kicad_sch"),"w", encoding="utf-8").write("\n".join(doc))

pro_path = os.path.join(KIC, "portero-bot-v2.kicad_pro")
if not os.path.exists(pro_path):
    proj={"board":{"design_settings":{}},"boards":[],"libraries":{"pinned_footprint_libs":[],"pinned_symbol_libs":[]},
     "meta":{"filename":"portero-bot-v2.kicad_pro","version":1},
     "net_settings":{"classes":[{"name":"Default","clearance":0.1,"track_width":0.25,"via_diameter":0.6,"via_drill":0.3}]},
     "schematic":{"legacy_lib_list":[]},"sheets":[[RT,""]],"text_variables":{}}
    json.dump(proj, open(pro_path,"w"), indent=2)
else:
    print(f"  (skipping .kicad_pro: file exists, preserving DRC/netclass/via config)")
print(f"OK  componentes={len(order)}  pines={sum(len(v) for v in comp_pins.values())}  pads-no-numericos={sorted(flag)}")
