r"""
Fix vias with zero/micro diameter placed by freerouting.
Resizes any via with diameter < 0.4mm to JLCPCB standard (0.6mm / 0.3mm drill).
Run: "C:\Program Files\KiCad\10.0\bin\python.exe" scripts/51_fix_via_sizes.py
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"

VIA_DIAM_MM  = 0.6   # JLCPCB standard
VIA_DRILL_MM = 0.3

board = pcbnew.LoadBoard(PCB)

fixed = 0
for track in board.GetTracks():
    if track.GetClass() == "PCB_VIA":
        diam_mm = track.GetWidth() / 1e6
        if diam_mm < 0.4:
            track.SetWidth(int(VIA_DIAM_MM * 1e6))
            track.SetDrill(int(VIA_DRILL_MM * 1e6))
            fixed += 1

print(f"Fixed {fixed} vias -> {VIA_DIAM_MM}mm diam / {VIA_DRILL_MM}mm drill")

board.Save(PCB)
print(f"Saved: {PCB}")
print("-> File -> Revert in KiCad, then re-run DRC.")
