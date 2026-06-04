"""
75_fix_led_footprints.py
Bug: LED1 y LED5 tienen footprint L_6.3x6.3_H3 (inductor 6.3x6.3mm) en lugar de
LED 0603 chip. Pad gap 5.5mm vs 0.8mm requerido para LED 0603 -> JLCPCB rechazaria.

Fix: reemplaza con LED_0603_1608Metric manteniendo posicion + nets.
Tracks que conectaban a los pads viejos (X offset ~2.75mm) van a quedar
unconnected; hay que rerutearlos al nuevo pad position (offset ~0.875mm).
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
LED_FP_LIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints\LED_SMD.pretty"

board = pcbnew.LoadBoard(PCB)

# LED template loaded inline via FootprintLoad

# Tracks adjacent to LED pads to be re-routed
# Pad 1 of L_6.3x6.3_H3: at offset (-2.75, 0) from center
# Pad 2 of L_6.3x6.3_H3: at offset (+2.75, 0) from center
# LED_0603_1608Metric pads at offset (~-0.875, 0) and (+0.875, 0)
PAD_DELTA = 2.75 - 0.875  # 1.875mm shift needed

# Process each LED
for ref in ('LED1', 'LED5'):
    old_fp = None
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            old_fp = fp
            break
    assert old_fp, f'{ref} not found'

    pos = old_fp.GetPosition()
    val = old_fp.GetValue()
    angle = old_fp.GetOrientation()
    # Save pad nets
    pad_nets = {}
    pad_positions = {}
    for pad in old_fp.Pads():
        pad_nets[pad.GetPadName()] = pad.GetNet()
        pp = pad.GetPosition()
        pad_positions[pad.GetPadName()] = (pp.x, pp.y)

    print(f'{ref}: at ({pos.x/1e6:.3f},{pos.y/1e6:.3f}), pads: {[(pn, (p[0]/1e6, p[1]/1e6)) for pn, p in pad_positions.items()]}')

    # Remove tracks/vias connected exactly to old pad positions, save info
    # For each pad, find tracks ending at that pad position
    tracks_to_rewire = []  # list of (track, which_endpoint, new_pos, net)
    for pad_name, (old_x, old_y) in pad_positions.items():
        new_x = pos.x + (old_x - pos.x) * (0.875 / 2.75)  # scale toward center
        new_y = pos.y + (old_y - pos.y) * (0.875 / 2.75)
        net = pad_nets[pad_name]
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA): continue
            tn = t.GetNet()
            if not tn or net is None: continue
            if tn.GetNetCode() != net.GetNetCode(): continue
            s, e = t.GetStart(), t.GetEnd()
            if abs(s.x - old_x) < 50_000 and abs(s.y - old_y) < 50_000:
                tracks_to_rewire.append((t, 'start', new_x, new_y))
            if abs(e.x - old_x) < 50_000 and abs(e.y - old_y) < 50_000:
                tracks_to_rewire.append((t, 'end', new_x, new_y))

    print(f'  Tracks to rewire: {len(tracks_to_rewire)}')

    # Remove old footprint
    board.Remove(old_fp)

    # Load new LED footprint
    new_fp = pcbnew.FootprintLoad(LED_FP_LIB, 'LED_0603_1608Metric')
    new_fp.SetReference(ref)
    new_fp.SetValue(val)
    new_fp.SetPosition(pcbnew.VECTOR2I(pos.x, pos.y))
    new_fp.SetOrientation(angle)

    # Assign nets to new pads
    for pad in new_fp.Pads():
        pn = pad.GetPadName()
        if pn in pad_nets:
            pad.SetNet(pad_nets[pn])

    board.Add(new_fp)

    # Re-wire tracks: update endpoints to new pad positions
    for t, which, new_x, new_y in tracks_to_rewire:
        if which == 'start':
            t.SetStart(pcbnew.VECTOR2I(int(new_x), int(new_y)))
        else:
            t.SetEnd(pcbnew.VECTOR2I(int(new_x), int(new_y)))

    # Get new pad positions and print
    for pad in new_fp.Pads():
        p = pad.GetPosition()
        net_name = pad.GetNet().GetNetname() if pad.GetNet() else ''
        print(f'  new pad {pad.GetPadName()} @ ({p.x/1e6:.3f},{p.y/1e6:.3f}) net="{net_name}"')

pcbnew.SaveBoard(PCB, board)
print(f'\nSaved: {PCB}')
