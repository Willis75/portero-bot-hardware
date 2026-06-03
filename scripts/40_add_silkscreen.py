#!/usr/bin/env python3
"""
40_add_silkscreen.py — Inserta gr_text en F.SilkS para etiquetar componentes clave.
Usa UTF-8 sin BOM para compatibilidad con KiCad.
"""
import os, re, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "kicad", "portero-bot-v2.kicad_pcb")

def U(): return str(uuid.uuid4())

# (x, y, texto, angulo=0)
LABELS = [
    # Botones
    (136.735, 128.5,  "BOOT",      0),
    (136.735, 137.9,  "RESET",     0),
    # LEDs columna izquierda
    (80.45,   121.0,  "3V3",       0),
    (80.5,    129.5,  "ENTRADA",   0),
    # LEDs columna derecha
    (89.0,    105.3,  "SALIDA",    0),
    (89.0,    113.1,  "PEATONAL",  0),
    (89.0,    121.0,  "5V",        0),
    # Relés
    (101.35,  62.0,   "ENTRADA",   0),
    (101.35,  79.0,   "SALIDA",    0),
    (101.35,  96.0,   "PEATONAL",  0),
    # Borneras terminales
    (83.5,    61.3,   "ENTRADA",  90),
    (83.5,    73.5,   "SALIDA",   90),
    (83.5,    85.7,   "PEATONAL", 90),
]

def gr_text(x, y, text, angle=0):
    return (
        f'  (gr_text "{text}" (at {x:.3f} {y:.3f} {angle}) (layer "F.SilkS") (uuid "{U()}")\n'
        f'    (effects (font (size 1 1) (thickness 0.15))))\n'
    )

content = open(PCB, encoding="utf-8").read()

# Verificar que no estén ya presentes (idempotente)
if "BOOT" in content and "gr_text" in content:
    # Buscar si ya hay gr_text de silkscreen nuestros
    if 'gr_text "BOOT"' in content:
        print("Las etiquetas ya existen en el archivo — sin cambios.")
        exit(0)

new_texts = "".join(gr_text(x, y, t, a) for x, y, t, a in LABELS)

# Insertar ANTES del último (embedded_fonts no) en el archivo (el raíz, no los de footprints)
TAIL_MARKER = "\t(embedded_fonts no)\n)\n"
idx = content.rfind(TAIL_MARKER)
if idx == -1:
    print("ERROR: no encontré el marcador final del PCB.")
    exit(1)
new_content = content[:idx] + new_texts + TAIL_MARKER

# Escribir SIN BOM
with open(PCB, "w", encoding="utf-8", newline="\n") as f:
    f.write(new_content)

print(f"OK  {len(LABELS)} etiquetas agregadas al silkscreen F.SilkS")
