"""Find all zones (copper + keep-out) with their actual layer/flags."""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)

F = pcbnew.F_Cu; B = pcbnew.B_Cu
LAY = {F: "F.Cu", B: "B.Cu"}

print(f"Total zones: {board.GetAreaCount()}")
for i in range(board.GetAreaCount()):
    z = board.GetArea(i)
    name = ""
    try: name = z.GetZoneName()
    except: pass
    layers = []
    try:
        ls = z.GetLayerSet()
        for ln in (F, B):
            if ls.Contains(ln):
                layers.append(LAY[ln])
    except: pass
    is_keep = False
    try: is_keep = z.GetIsRuleArea()
    except: pass
    net = ""
    try: net = z.GetNetname()
    except: pass
    flags = {}
    for a in ("GetDoNotAllowTracks","GetDoNotAllowVias","GetDoNotAllowPads",
              "GetDoNotAllowCopperPour","GetDoNotAllowFootprints"):
        try: flags[a] = getattr(z, a)()
        except: pass
    # bbox
    bbox = z.GetBoundingBox()
    xmin = bbox.GetX()/1e6; ymin = bbox.GetY()/1e6
    xmax = (bbox.GetX()+bbox.GetWidth())/1e6
    ymax = (bbox.GetY()+bbox.GetHeight())/1e6
    print(f"#{i} name={name!r} net={net!r} layers={layers} rule={is_keep} flags={flags}")
    print(f"   bbox=({xmin:.2f},{ymin:.2f})-({xmax:.2f},{ymax:.2f})")
