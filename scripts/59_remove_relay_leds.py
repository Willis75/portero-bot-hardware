"""
59 — Remove relay indicator LEDs and their series resistors.

Deletes from PCB:
  - LED2, LED3, LED4 (3x KT-0603R relay-status LEDs)
  - R10, R11, R12 (3x 1k current-limiting resistors)
  - All tracks/vias on nets RELAY1_LED, RELAY2_LED, RELAY3_LED
  - Tracks/vias dangling on RELAY1_GPIO/RELAY2_GPIO/RELAY3_GPIO that were
    routed only to the deleted R10/R11/R12 pads (they will be removed by
    cleaning all tracks on these GPIO nets — they will be re-routed by
    script 58c afterward).

Wait — RELAY2_GPIO and RELAY3_GPIO are ALREADY routed by freerouting
between U1.9-R8.1 and U1.10-R9.1 respectively. Removing R11/R12 should
only delete the *stub* that went to the removed pad. We will leave their
tracks intact; KiCad will mark the R11/R12 connection as unused.

Approach: delete the 6 footprints. Then clean tracks on:
  - RELAY1_LED, RELAY2_LED, RELAY3_LED (entire net)
  - RELAY1_GPIO (entire net — will be re-routed by 58c)
The RELAY2_GPIO and RELAY3_GPIO tracks remain — they connect U1.9↔R8.1
and U1.10↔R9.1 which are still valid net nodes.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)

REMOVE_REFS = {"LED2", "LED3", "LED4", "R10", "R11", "R12"}
PURGE_NETS  = {"RELAY1_LED", "RELAY2_LED", "RELAY3_LED", "RELAY1_GPIO", "BOOT", "BST_5V"}

# Snapshot first to avoid SWIG iterator corruption
fps_to_remove = []
for fp in board.GetFootprints():
    if fp.GetReference() in REMOVE_REFS:
        fps_to_remove.append(fp)

tracks_to_remove = []
for t in list(board.GetTracks()):
    if t.GetNetname() in PURGE_NETS:
        tracks_to_remove.append(t)

print(f"Removing {len(fps_to_remove)} footprints, {len(tracks_to_remove)} tracks/vias")

for fp in fps_to_remove:
    print(f"  - {fp.GetReference()} @({fp.GetPosition().x/1e6:.2f},{fp.GetPosition().y/1e6:.2f})")
    board.Remove(fp)

for t in tracks_to_remove:
    board.Remove(t)

board.Save(PCB)
print(f"\nSaved {PCB}")
