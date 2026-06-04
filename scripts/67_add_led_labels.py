"""
67_add_led_labels.py
Agrega silkscreen labels "PWR 3V3" junto a LED1 y "PWR 5V" junto a LED5.
Idempotente: si el texto ya existe en posicion cercana, no duplica.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

# (texto, x_mm, y_mm, rot_deg, size_mm, thickness_mm)
LABELS = [
    ("PWR 3V3", 83.0, 124.0, 0, 1.0, 0.15),  # junto a LED1
    ("PWR 5V",  83.0, 132.5, 0, 1.0, 0.15),  # junto a LED5
]

board = pcbnew.LoadBoard(PCB)
added = 0
skipped = 0

# Detectar duplicados existentes en F.Silkscreen
existing = []
for drw in board.GetDrawings():
    if isinstance(drw, pcbnew.PCB_TEXT) and drw.GetLayer() == pcbnew.F_SilkS:
        existing.append((drw.GetText(), drw.GetPosition().x, drw.GetPosition().y))

for text, x, y, rot, size, thick in LABELS:
    nm_x, nm_y = int(x*1e6), int(y*1e6)
    dup = any(t == text and abs(px - nm_x) < 500_000 and abs(py - nm_y) < 500_000 for t, px, py in existing)
    if dup:
        skipped += 1
        print(f"  = exists \"{text}\" near ({x},{y})")
        continue
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText(text)
    txt.SetPosition(pcbnew.VECTOR2I(nm_x, nm_y))
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetTextSize(pcbnew.VECTOR2I(int(size*1e6), int(size*1e6)))
    txt.SetTextThickness(int(thick*1e6))
    txt.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    txt.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    board.Add(txt)
    added += 1
    print(f"  + \"{text}\" @ ({x},{y}) size={size}mm")

print(f"\nAdded {added}, skipped {skipped}.")
pcbnew.SaveBoard(PCB, board)
print(f"Saved: {PCB}")
