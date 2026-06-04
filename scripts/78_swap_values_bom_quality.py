"""
78_swap_values_bom_quality.py
Aplica cambios verificados via WebSearch/Fetch:
- D3/D4/D5: 1N4148WS-7-F -> 1N5819WS-7-F (Schottky 1A para flyback 24/7)
- LED1: 0603GBD0790S01 -> KT-0603YG (Vf=2V, funciona con 3V3 rail; Vf=3.3V original no enciende)
- LED5: LTST-C190KSKT -> KT-0603R (LCSC C2286 actual ya es KENTO Red)

NO cambia:
- 22uH C354622 (1.8A Isat suficiente para carga real ~0.7-1A peak)
- MP2307DN -> LF-P (pin-compatible LF-Z)
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
board = pcbnew.LoadBoard(PCB)

# Swap rules
SWAPS = {
    'D3': '1N5819WS-7-F',
    'D4': '1N5819WS-7-F',
    'D5': '1N5819WS-7-F',
    'LED1': 'KT-0603YG',  # yellow-green Vf~2V (funciona con 3V3 + R13 1k)
    'LED5': 'KT-0603R',   # confirma rojo
}

for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in SWAPS:
        old = fp.GetValue()
        fp.SetValue(SWAPS[ref])
        print(f'  {ref}: {old} -> {SWAPS[ref]}')

pcbnew.SaveBoard(PCB, board)
print(f'\nSaved: {PCB}')
