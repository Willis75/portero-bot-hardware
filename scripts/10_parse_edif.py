#!/usr/bin/env python3
"""
10_parse_edif.py — Extrae el netlist del esquematico de Flux (.edif).

Entrada : source-flux/portero-bot-v2.edif
Salida  : data/nets_clean.json   (60 redes con sus pines reales)
          data/instances.json    (designador -> tipo de componente)

Notas:
- En Flux las redes pueden cruzar varios bloques mediante "Net Portal".
- Cada bloque (Net ...) ya es una red completa; NO se deben unir entre si.
- El RJ45 (J2) tiene todos sus pines llamados "~" (anonimos en Flux):
  por eso J2 aparece en varias redes con el mismo nombre de pin.
"""
import re, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIF = os.path.join(ROOT, "source-flux", "portero-bot-v2.edif")
DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)

txt = open(EDIF, encoding="utf-8").read()

# --- instancias: nombre -> cellRef ---
inst_cell = {}
for m in re.finditer(
    r'\(instance\s+("[^"]+"|\S+?)\s*\(viewRef schematic \(cellRef\s+("[^"]+"|\S+?)\s*\(libraryRef',
    txt):
    inst_cell[m.group(1).strip('"')] = m.group(2).strip('"')

# --- redes: cada bloque (Net NAME (joined ...)) es una red completa ---
contents = txt[txt.find("(contents"):]
idxs = [m.start() for m in re.finditer(r"\(Net\s", contents)] + [len(contents)]
PORTAL, NC, GND = "Net Portal", "No Connect", "Ground"
nets = []
for a, b in zip(idxs, idxs[1:]):
    chunk = contents[a:b]
    name = re.match(r'\(Net\s+("[^"]+"|\S+)', chunk).group(1).strip('"')
    refs = re.findall(
        r'\(portRef\s+("[^"]+"|[^\s()]+)\s*\(instanceRef\s+("[^"]+"|[^\s()]+)\)', chunk)
    pins, seen = [], set()
    for p, i in refs:
        p, i = p.strip('"'), i.strip('"')
        c = inst_cell.get(i, "")
        if c in (PORTAL, NC, GND):  # portales/no-connect/ground se omiten
            continue
        if " - " in i:              # nombres tipo "X pin - Y pin" = portal
            continue
        key = (i, p)
        if key not in seen:
            seen.add(key); pins.append({"ref": i, "pin": p})
    nets.append({"name": name, "pins": [f'{x["ref"]}.{x["pin"]}' for x in pins]})

# componentes reales (designadores estandar)
real = {d: c for d, c in inst_cell.items()
        if re.match(r"^[A-Z]+\d+$", d) and c not in (PORTAL, NC)}

json.dump(nets, open(os.path.join(DATA, "nets_clean.json"), "w"),
          indent=1, ensure_ascii=False)
json.dump(real, open(os.path.join(DATA, "instances.json"), "w"),
          indent=1, ensure_ascii=False)
print(f"OK  redes={len(nets)}  componentes={len(real)}")
