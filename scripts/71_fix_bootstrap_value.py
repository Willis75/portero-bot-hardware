"""
71_fix_bootstrap_value.py
Cambia valor C22 y C23 (bootstrap caps MP2307) de 100uF a 100nF.
Datasheet MP2307 requiere BST cap = 100nF ceramico. 100uF rompe el switching.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
board = pcbnew.LoadBoard(PCB)

for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in ('C22', 'C23'):
        old = fp.GetValue()
        fp.SetValue('100nF')
        print(f'  {ref}: {old} -> 100nF')

pcbnew.SaveBoard(PCB, board)
print(f'Saved: {PCB}')
