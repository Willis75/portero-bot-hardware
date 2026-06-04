"""Delete zero-drill vias and all target net tracks. Save."""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)
TARGET_NETS = {"RELAY1_GPIO", "BOOT", "BST_5V"}

# Snapshot first to avoid iterator corruption after modifications
all_tracks = list(board.GetTracks())

to_remove = []
for t in all_tracks:
    cls = t.GetClass()
    net = t.GetNetname()
    # Remove target net items
    if net in TARGET_NETS:
        to_remove.append(t)
        continue
    # Remove zero-drill <no net> vias (use GetDrillValue, not GetWidth)
    if cls == "PCB_VIA" and net == "":
        try:
            drill = t.GetDrillValue()
            if drill < int(0.2 * 1e6):
                to_remove.append(t)
        except Exception:
            to_remove.append(t)

removed = 0
for t in to_remove:
    board.Remove(t)
    removed += 1

board.Save(PCB)
print(f"Removed {removed} items ({len([x for x in to_remove if x.GetClass()=='PCB_VIA' and x.GetNetname()=='' if True])} bad vias + target net tracks). Saved.")
