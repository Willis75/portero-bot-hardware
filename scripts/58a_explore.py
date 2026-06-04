"""
58a_explore — dump exact positions of:
  - Endpoint pads of RELAY1_GPIO / BOOT / BST_5V
  - All other pads within 8mm of each endpoint
  - All tracks/vias within 8mm of each endpoint (per layer)
  - All keep-out zones (rule areas) with polygon coordinates

Output: data/route_context.json
"""
import sys, json, math
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
OUT = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\data\route_context.json"

F = pcbnew.F_Cu
B = pcbnew.B_Cu
LAY = {F: "F", B: "B"}

board = pcbnew.LoadBoard(PCB)

ENDPOINTS = {
    "RELAY1_GPIO": [("R7", "1"), ("R10", "1"), ("U1", "8")],
    "BOOT":        [("R2", "2"), ("SW1", "1"), ("U1", "25")],
    "BST_5V":      [("C22", "1"), ("U4", "1")],
}

# Find endpoint pads
endpoint_pads = {}
fp_by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}

for net_name, refs in ENDPOINTS.items():
    endpoint_pads[net_name] = []
    for ref, padnum in refs:
        fp = fp_by_ref.get(ref)
        if not fp:
            print(f"WARN: footprint {ref} not found")
            continue
        for pad in fp.Pads():
            if pad.GetNumber() == padnum:
                pos = pad.GetCenter()
                sz = pad.GetSize()
                drill = pad.GetDrillSize() if pad.HasHole() else pcbnew.VECTOR2I(0, 0)
                shape = pad.GetShape()
                endpoint_pads[net_name].append({
                    "ref": ref,
                    "pad": padnum,
                    "x": pos.x / 1e6,
                    "y": pos.y / 1e6,
                    "w": sz.x / 1e6,
                    "h": sz.y / 1e6,
                    "drill_x": drill.x / 1e6 if drill else 0,
                    "drill_y": drill.y / 1e6 if drill else 0,
                    "shape": int(shape),
                    "on_F": pad.IsOnLayer(F),
                    "on_B": pad.IsOnLayer(B),
                    "is_pth": drill.x > 0,
                })
                break

# Helper: minimum distance from point to all endpoint pads of a given net
def min_dist_to_endpoints(x, y, net_name):
    pads = endpoint_pads.get(net_name, [])
    if not pads:
        return float("inf")
    return min(math.hypot(x - p["x"], y - p["y"]) for p in pads)

# For each net, dump all OTHER pads within radius
RADIUS = 8.0  # mm

nearby_pads_per_net = {}
for net_name in ENDPOINTS:
    nearby = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pos = pad.GetCenter()
            x, y = pos.x / 1e6, pos.y / 1e6
            if min_dist_to_endpoints(x, y, net_name) <= RADIUS:
                pnet = pad.GetNetname()
                if pnet == net_name:
                    continue  # skip own-net pads (already in endpoint_pads)
                sz = pad.GetSize()
                drill = pad.GetDrillSize() if pad.HasHole() else pcbnew.VECTOR2I(0, 0)
                nearby.append({
                    "ref": fp.GetReference(),
                    "pad": pad.GetNumber(),
                    "net": pnet,
                    "x": x,
                    "y": y,
                    "w": sz.x / 1e6,
                    "h": sz.y / 1e6,
                    "is_pth": drill.x > 0,
                    "on_F": pad.IsOnLayer(F),
                    "on_B": pad.IsOnLayer(B),
                })
    # sort by net then x,y
    nearby.sort(key=lambda p: (p["net"], p["x"], p["y"]))
    nearby_pads_per_net[net_name] = nearby

# Tracks and vias near endpoints (per layer)
nearby_tracks_per_net = {}
for net_name in ENDPOINTS:
    f_items = []
    b_items = []
    for t in board.GetTracks():
        tnet = t.GetNetname()
        if tnet == net_name:
            continue
        cls = t.GetClass()
        if cls == "PCB_VIA":
            pos = t.GetPosition()
            x, y = pos.x / 1e6, pos.y / 1e6
            if min_dist_to_endpoints(x, y, net_name) <= RADIUS:
                w = t.GetWidth() / 1e6
                item = {"kind": "via", "x": x, "y": y, "dia": w, "net": tnet}
                f_items.append(item)
                b_items.append(dict(item))
        elif cls == "PCB_TRACK":
            s = t.GetStart()
            e = t.GetEnd()
            x1, y1 = s.x / 1e6, s.y / 1e6
            x2, y2 = e.x / 1e6, e.y / 1e6
            # Use midpoint and endpoints for proximity
            midx = (x1 + x2) / 2
            midy = (y1 + y2) / 2
            mdist = min(
                min_dist_to_endpoints(x1, y1, net_name),
                min_dist_to_endpoints(x2, y2, net_name),
                min_dist_to_endpoints(midx, midy, net_name),
            )
            if mdist <= RADIUS:
                w = t.GetWidth() / 1e6
                item = {"kind": "seg", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "w": w, "net": tnet}
                if t.GetLayer() == F:
                    f_items.append(item)
                elif t.GetLayer() == B:
                    b_items.append(item)
    f_items.sort(key=lambda i: (i["net"], i.get("y", i.get("y1", 0))))
    b_items.sort(key=lambda i: (i["net"], i.get("y", i.get("y1", 0))))
    nearby_tracks_per_net[net_name] = {"F": f_items, "B": b_items}

# Keep-out zones
keepouts = []
for zone in board.Zones():
    is_rule = False
    try:
        is_rule = zone.GetIsRuleArea()
    except Exception:
        pass
    if not is_rule:
        continue
    # extract outline polygon
    poly = zone.Outline()
    pts = []
    if poly.OutlineCount() > 0:
        outline = poly.Outline(0)
        for i in range(outline.PointCount()):
            v = outline.CPoint(i)
            pts.append([v.x / 1e6, v.y / 1e6])
    flags = {}
    for attr in ("GetDoNotAllowTracks", "GetDoNotAllowVias", "GetDoNotAllowPads",
                 "GetDoNotAllowCopperPour", "GetDoNotAllowFootprints"):
        try:
            flags[attr] = getattr(zone, attr)()
        except Exception:
            pass
    layers = []
    try:
        ls = zone.GetLayerSet()
        for ln in (F, B):
            if ls.Contains(ln):
                layers.append(LAY[ln])
    except Exception:
        pass
    keepouts.append({
        "name": zone.GetZoneName() if hasattr(zone, "GetZoneName") else "",
        "layers": layers,
        "flags": flags,
        "polygon": pts,
    })

result = {
    "endpoints": endpoint_pads,
    "nearby_pads": nearby_pads_per_net,
    "nearby_tracks": nearby_tracks_per_net,
    "keepouts": keepouts,
}

with open(OUT, "w") as f:
    json.dump(result, f, indent=2)

# Console summary
print(f"Wrote {OUT}")
for net in ENDPOINTS:
    eps = endpoint_pads[net]
    nps = nearby_pads_per_net[net]
    nts = nearby_tracks_per_net[net]
    print(f"\n=== {net} ===")
    print(f"  endpoints ({len(eps)}):")
    for p in eps:
        layers = ("F" if p["on_F"] else "") + ("B" if p["on_B"] else "")
        print(f"    {p['ref']}.{p['pad']} @({p['x']:.3f},{p['y']:.3f}) {p['w']:.2f}x{p['h']:.2f} {layers} pth={p['is_pth']}")
    print(f"  nearby pads: {len(nps)}")
    print(f"  nearby F.Cu tracks/vias: {len(nts['F'])}, B.Cu: {len(nts['B'])}")

print(f"\n=== KEEP-OUTS: {len(keepouts)} ===")
for k in keepouts:
    print(f"  {k['name'] or '(unnamed)'} layers={k['layers']} pts={len(k['polygon'])} flags={k['flags']}")
