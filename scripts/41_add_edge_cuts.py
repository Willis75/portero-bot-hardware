#!/usr/bin/env python3
"""
41_add_edge_cuts.py — Agrega contorno Edge.Cuts al PCB.
Calcula bounding box de footprints + 5mm de margen por lado.
"""
import re, os, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "kicad", "portero-bot-v2.kicad_pcb")

content = open(PCB, encoding="utf-8").read()

# Verificar que no haya ya Edge.Cuts
if '"Edge.Cuts"' in content and 'gr_rect' in content:
    # Check if there's already an Edge.Cuts rect
    if re.search(r'gr_rect[^)]+Edge\.Cuts', content, re.DOTALL):
        print("Edge.Cuts ya existe — sin cambios.")
        exit(0)

# Extraer posiciones de footprints
positions = []
for fp_start in [m.start() for m in re.finditer(r'\(footprint ', content)]:
    chunk = content[fp_start:fp_start+300]
    m = re.search(r'\(at ([\d.-]+) ([\d.-]+)', chunk)
    if m:
        positions.append((float(m.group(1)), float(m.group(2))))

xs = [p[0] for p in positions]
ys = [p[1] for p in positions]

MARGIN = 5.0
x0 = round(min(xs) - MARGIN, 2)
y0 = round(min(ys) - MARGIN, 2)
x1 = round(max(xs) + MARGIN, 2)
y1 = round(max(ys) + MARGIN, 2)
W = round(x1 - x0, 2)
H = round(y1 - y0, 2)

print(f"Board outline: ({x0}, {y0}) to ({x1}, {y1})  =  {W} x {H} mm")

edge = (
    f'  (gr_rect\n'
    f'    (start {x0} {y0})\n'
    f'    (end {x1} {y1})\n'
    f'    (stroke\n'
    f'      (width 0.05)\n'
    f'      (type default)\n'
    f'    )\n'
    f'    (fill no)\n'
    f'    (layer "Edge.Cuts")\n'
    f'    (uuid "{uuid.uuid4()}")\n'
    f'  )\n'
)

# Insertar antes del marcador final
TAIL_MARKER = "\t(embedded_fonts no)\n)\n"
idx = content.rfind(TAIL_MARKER)
if idx == -1:
    print("ERROR: marcador final no encontrado.")
    exit(1)

new_content = content[:idx] + edge + TAIL_MARKER
with open(PCB, "w", encoding="utf-8", newline="\n") as f:
    f.write(new_content)

print(f"OK  Edge.Cuts agregado: {W}×{H}mm")
