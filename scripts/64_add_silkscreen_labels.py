"""
64_add_silkscreen_labels.py
Agrega etiquetas en F.Silkscreen para identificar borneras de rele y botones.

Mapeo (confirmado 2026-06-04):
  J4 / K1 -> ENTRADA  (vehicular)
  J5 / K2 -> SALIDA   (vehicular)
  J6 / K3 -> PEATONAL
  SW1     -> RESET    (ESP32)
  SW2     -> BOOT     (ESP32, combo con RESET para flash)

Las etiquetas se colocan junto al componente. Idempotente: si una etiqueta
con el mismo texto ya existe a <2mm de la posicion target, no la duplica.

Run: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/64_add_silkscreen_labels.py
"""
import os
import pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

# (texto, x_mm, y_mm, rot_deg, size_mm, thickness_mm)
# Posiciones: encima de cada bornera y junto a cada boton.
LABELS = [
    ("ENTRADA",  86.0, 60.5, 0, 1.2, 0.2),
    ("SALIDA",   86.0, 72.7, 0, 1.2, 0.2),
    ("PEATONAL", 86.0, 84.9, 0, 1.2, 0.2),
    ("RESET",   132.5, 132.0, 0, 1.0, 0.15),
    ("BOOT",    132.5, 138.0, 0, 1.0, 0.15),
]

def mm(v):  # mm -> nanometros
    return int(round(v * 1_000_000))

board = pcbnew.LoadBoard(PCB)
silk = board.GetLayerID("F.Silkscreen")

# Comprobar existentes para idempotencia
existing = []
for drw in board.GetDrawings():
    if isinstance(drw, pcbnew.PCB_TEXT) and drw.GetLayer() == silk:
        existing.append((drw.GetText(), drw.GetPosition().x, drw.GetPosition().y))

added = 0
skipped = 0
for text, x, y, rot, size, thick in LABELS:
    tx_nm, ty_nm = mm(x), mm(y)
    dup = any(t == text and abs(px - tx_nm) < 2_000_000 and abs(py - ty_nm) < 2_000_000
              for (t, px, py) in existing)
    if dup:
        print(f"  (skip) {text} @ ({x},{y}) ya existe")
        skipped += 1
        continue
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(text)
    txt.SetLayer(silk)
    txt.SetPosition(pcbnew.VECTOR2I(tx_nm, ty_nm))
    txt.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    txt.SetTextThickness(mm(thick))
    txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    txt.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    board.Add(txt)
    print(f"  + {text} @ ({x},{y}) F.Silkscreen size={size}mm")
    added += 1

print(f"\nAdded {added}, skipped {skipped}.")
pcbnew.SaveBoard(PCB, board)
print(f"Saved: {PCB}")
