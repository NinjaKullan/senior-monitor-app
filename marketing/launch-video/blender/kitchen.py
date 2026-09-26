"""Mom's kitchen: shots 2 (a busy morning), 6 (a morning that isn't hers), 7 (Kettle asks;
a thumbs up) and 10b (her own smart plug and speaker, the lamp switching on).

blender -b -P blender/kitchen.py -- <02|06|07|10b> [still [frame] [out.png] | frames [WxH]]
"""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

TOP = 0.50  # worktop height
FRAMES = {"02": 141, "06": 141, "07": 267, "10b": 135}  # 4.7, 4.7, 8.9 (07a + 07b), 4.5 s
PHONE = (-0.27, 0.22)


def build(shot: str) -> None:
    P.stage()
    P.card("counter", "assets/layers/counter.png", 0.53, 0.0, 0.14)
    P.box("worktop", P.PAPER, (1.12, 0.34, 0.012), (0.0, 0.31, TOP - 0.006))
    P.card(
        "window", "assets/layers/window.png", 0.25, -0.02, 0.595, z=0.56
    )  # low, clear of the caption band
    P.kettle(0.30, 0.30, TOP)
    P.card("plant", "assets/layers/plant.png", 0.26, -0.40, 0.40, z=TOP)
    P.contact("plant-contact", -0.40, 0.40, TOP, 0.06, 0.022)
    mug_x = -0.12 if shot != "07" else 0.06  # in the close-up the mug steps aside for the thumbs up
    P.card("mug", "assets/layers/mug.png", 0.11, mug_x, 0.33, z=TOP)
    P.contact("mug-contact", mug_x - 0.01, 0.33, TOP, 0.05, 0.02)
    # Her phone on a little paper stand, warm screen to the camera.
    # Shot 6: dark, the day not started.
    P.phone("phone", *PHONE, TOP, w=0.11, lean=14, lit=0.35 if shot != "06" else 0.0)
    P.light()
    n = FRAMES[shot]

    if shot == "02":  # slow push-in; steam rises; her phone lights up
        cam, _ = P.camera((0.0, -3.0, 1.12), (0.0, 0.3, 0.50))
        P.key(cam, "location", 1, (0.0, -3.0, 1.12))
        P.key(cam, "location", n, (0.03, -2.78, 1.08))
        steam = P.card("steam", "assets/layers/steam.png", 0.15, 0.415, 0.31, z=TOP + 0.183)
        full = tuple(steam.scale)
        P.key(steam, "scale", 1, (full[0] * 0.6, full[1] * 0.6, 1))
        P.key(steam, "scale", 30, full)
        P.key(steam, "location", 30, tuple(steam.location))
        P.key(
            steam,
            "location",
            n,
            (steam.location.x + 0.01, steam.location.y, steam.location.z + 0.03),
        )
        for f, glow in ((1, 0.0), (48, 0.0), (60, 0.35)):  # her phone wakes at about 1.6 s
            P.light_screen("phone", f, glow)
    elif shot == "06":  # held low and still, a whisper of drift; no steam
        cam, _ = P.camera((-0.05, -2.9, 1.0), (0.0, 0.3, 0.52))
        P.key(cam, "location", 1, (-0.05, -2.9, 1.0))
        P.key(cam, "location", n, (0.05, -2.9, 1.0))
    elif shot == "10b":  # closer, held still: her lamp on a smart plug switches on softly
        lamp_on = household(0.10, 0.40)
        P.camera((0.04, -1.15, 0.98), (0.07, 0.40, 0.62))
        lamp_on(35, 65)
    else:  # close on the phone: a message arrives, a thumbs up folds up
        cam, _ = P.camera((-0.30, -1.35, 1.02), (-0.18, 0.25, 0.66))
        P.key(cam, "location", 1, (-0.30, -1.35, 1.02))
        P.key(cam, "location", n, (-0.20, -1.28, 1.00))
        # Kettle's message arrives on her phone, then a thumbs up folds up beside it.
        msg = P.bubble("message", "phone")
        P.key(msg, "scale", 12, (0.01, 0.01, 0.01))
        P.key(msg, "scale", 30, (1, 1, 1))
        thumbs = P.card("thumbs", "assets/layers/thumbs.png", 0.14, -0.12, 0.26, z=TOP, lean=88)
        P.key(thumbs, "rotation_euler", 66, (math.radians(2), 0, 0))
        P.key(thumbs, "rotation_euler", 90, (math.radians(90), 0, 0))


def household(x: float, y: float):
    """Shot 10b's props, all paper, no logos or brand shapes: a table lamp at (x, y) on the
    worktop, its cord running along the counter and up the wall to a plain smart plug in the
    outlet, and a small round speaker beside it. Returns lamp_on(start, end), which keys the
    shade's glow and the bulb light from off to on between those frames."""
    shade_mat = P.paper_material("shade", P.PAPER, glow=0.001)
    shade_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = P.lin(
        "F6D98E"
    )
    P.disc("lamp-base", P.GREEN, 0.042, 0.016, x, y, TOP)
    P.contact("lamp-contact", x, y, TOP, 0.06, 0.03, strength=0.45)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.17, location=(x, y, TOP + 0.101))
    bpy.context.active_object.data.materials.append(P.paper_material("lamp-stem", P.INK))
    bpy.ops.mesh.primitive_cone_add(
        vertices=48, radius1=0.078, radius2=0.046, depth=0.095, end_fill_type="NOTHING",
        location=(x, y, TOP + 0.23),
    )  # fmt: skip
    shade = bpy.context.active_object
    shade.data.materials.append(shade_mat)
    shade.modifiers.new("paper", "SOLIDIFY").thickness = 0.002
    bpy.ops.object.light_add(type="POINT", location=(x, y, TOP + 0.21))
    bulb = bpy.context.active_object
    bulb.data.color, bulb.data.shadow_soft_size = (1.0, 0.85, 0.6), 0.02

    # The outlet on the wall behind, and the plug in its lower socket.
    wall = 0.617
    ox, oz = x + 0.075, TOP + 0.085
    P.box("outlet", "FBF7EF", (0.06, 0.004, 0.095), (ox, wall, oz), round_=0.006)
    for dx in (-0.008, 0.008):  # the free upper socket's two slots
        P.box(f"slot{dx}", "3A3631", (0.003, 0.002, 0.011), (ox + dx, wall - 0.003, oz + 0.025))
    P.box("plug", P.PAPER, (0.036, 0.022, 0.044), (ox, wall - 0.013, oz - 0.018), round_=0.008)

    # The cord: from the lamp's base, along the worktop, up the wall into the plug.
    curve = bpy.data.curves.new("cord", "CURVE")
    curve.dimensions, curve.bevel_depth, curve.bevel_resolution = "3D", 0.0028, 4
    spline = curve.splines.new("BEZIER")
    points = [(x + 0.03, y + 0.02, TOP + 0.003), (ox, wall - 0.03, TOP + 0.003),
              (ox, wall - 0.006, TOP + 0.02), (ox, wall - 0.012, oz - 0.04)]  # fmt: skip
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):  # noqa: B905 (same length by construction)
        bp.co, bp.handle_left_type, bp.handle_right_type = co, "AUTO", "AUTO"
    cord = bpy.data.objects.new("cord", curve)
    bpy.context.collection.objects.link(cord)
    cord.data.materials.append(P.paper_material("cord", P.INK))

    # A small round speaker: a squat sage cylinder with soft edges, nothing on it.
    sx = x - 0.13
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=0.045, depth=0.05, location=(sx, y - 0.04, TOP + 0.025)
    )
    speaker = bpy.context.active_object
    speaker.data.materials.append(P.paper_material("speaker", "9DB39B"))
    bev = speaker.modifiers.new("soft", "BEVEL")
    bev.width, bev.segments = 0.012, 6
    P.contact("speaker-contact", sx, y - 0.04, TOP, 0.055, 0.024, strength=0.45)

    def lamp_on(start: int, end: int) -> None:
        glow = shade_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        for frame, level in ((1, 0.0), (start, 0.0), (end, 1.0)):
            glow.default_value = 0.55 * level
            glow.keyframe_insert("default_value", frame=frame)
            bulb.data.energy = 2.2 * level
            bulb.data.keyframe_insert("energy", frame=frame)

    return lamp_on


P.run(build, FRAMES)
