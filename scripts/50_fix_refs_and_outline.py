r"""
Fix refs with spaces/special-chars + add Edge.Cuts outline.
Run with KiCad Python: "C:\Program Files\KiCad\10.0\bin\python.exe" scripts/50_fix_refs_and_outline.py
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"

board = pcbnew.LoadBoard(PCB)

# ------------------------------------------------------------------
# 1. Normalize footprint references
# ------------------------------------------------------------------
# Map: (old_ref_fragment, approx_x_mm, approx_y_mm) -> new_ref
# Tolerancia 3mm para localizar el footprint correcto

REMAP = [
    ("3V on",    80.2, 124.0, "LED1"),
    ("5V on",    80.2, 132.5, "LED5"),
    ("Boot",    136.7, 132.0, "SW1"),
    ("Reset",   136.7, 138.0, "SW2"),
    # LEDs con "Entrada"/"Salida"/"Peatonal"
    ("Entrada",  89.5, 107.5, "LED2"),
    ("Salida",   89.5, 118.5, "LED3"),
    ("Peatonal", 89.5, 129.5, "LED4"),
    # Borneras
    ("Entrada",  86.0,  64.3, "J4"),
    ("Salida",   86.0,  76.5, "J5"),
    ("Peatonal", 86.0,  88.7, "J6"),
    # Mounting holes REF**
    ("REF**",    74.5,  52.0, "MH1"),
    ("REF**",    74.5, 146.5, "MH2"),
    ("REF**",   182.0,  52.0, "MH3"),
    ("REF**",   182.0, 146.5, "MH4"),
]

TOL = 3e6  # 3mm in nm

def near(fp, x_mm, y_mm):
    pos = fp.GetPosition()
    return abs(pos.x - int(x_mm * 1e6)) < TOL and abs(pos.y - int(y_mm * 1e6)) < TOL

changed = []
for (old_frag, x, y, new_ref) in REMAP:
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if old_frag.lower() in ref.lower() and near(fp, x, y):
            if ref != new_ref:
                fp.SetReference(new_ref)
                changed.append(f"  {ref!r} -> {new_ref!r}  @ ({x}, {y})")
            break

if changed:
    print(f"[refs] Changed {len(changed)} references:")
    for c in changed:
        print(c)
else:
    print("[refs] All references already normalized.")

# ------------------------------------------------------------------
# 2. Verify / add Edge.Cuts outline
# ------------------------------------------------------------------
has_edge = any(
    d.GetLayer() == pcbnew.Edge_Cuts
    for d in board.GetDrawings()
)

if has_edge:
    print("[outline] Edge.Cuts already present.")
else:
    print("[outline] Adding Edge.Cuts SHAPE_T_RECT 117.5x104.5mm ...")
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(int(0.05 * 1e6))
    rect.SetStart(pcbnew.VECTOR2I(int(69.5 * 1e6), int(47.0 * 1e6)))
    rect.SetEnd(pcbnew.VECTOR2I(int(187.0 * 1e6), int(151.5 * 1e6)))
    board.Add(rect)
    print("[outline] Edge.Cuts added.")

# ------------------------------------------------------------------
# 3. Save
# ------------------------------------------------------------------
board.Save(PCB)
print(f"\n[done] Saved: {PCB}")
print("-> Do File -> Revert in KiCad, then re-run DRC.")
