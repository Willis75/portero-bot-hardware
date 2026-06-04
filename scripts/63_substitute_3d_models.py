"""
63_substitute_3d_models.py
Substituye paths de modelos 3D que no existen en la libreria stock de KiCad 10
por equivalentes visuales del mismo paquete. Solo cambia .step path; footprints
y pad layout NO se tocan.

Substituciones:
  J2 (RJ45 magjack):   Hanrun HR911105A  -> Pulse JK0654219NL (ambos magjack RJ45 horizontal)
  J3 (Micro-USB):       Wuerth 614105150721 -> Molex 47346-0001 (ambos receptaculo Micro-B)

Y1 (cristal 3225) sigue con su modelo original (existe en stock).

Idempotente: si los paths ya estan substituidos, no hace nada.

Run: python scripts/63_substitute_3d_models.py
"""
import os, re

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

SUBS = [
    ("Connector_RJ.3dshapes/RJ45_Hanrun_HR911105A_Horizontal.step",
     "Connector_RJ.3dshapes/RJ45_Pulse_JK0654219NL_Horizontal.step"),
    ("Connector_USB.3dshapes/USB_Micro-B_Wuerth_614105150721_Vertical.step",
     "Connector_USB.3dshapes/USB_Micro-B_Molex_47346-0001.step"),
    ("Inductor_SMD.3dshapes/L_6.3x6.3_H3.step",
     "Inductor_SMD.3dshapes/L_TechFuse_SL0630.step"),
]

with open(PCB, "r", encoding="utf-8") as f:
    txt = f.read()

changed = 0
for old, new in SUBS:
    if old in txt:
        txt = txt.replace(old, new)
        print(f"  {old}\n  -> {new}")
        changed += 1
    elif new in txt:
        print(f"  (already substituted) {new}")
    else:
        print(f"  WARNING: pattern not found: {old}")

if changed:
    with open(PCB, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"\nSaved: {PCB} ({changed} substitutions)")
else:
    print("\nNo changes.")
