"""The paper-diorama kit every Blender scene shares: a cream table and wall, paper cards cut from
transparent PNGs, soft table-top light, and the render settings. Units are metres; the camera looks
along +Y, Z is up. Colours are the brief's hex values, converted to linear for the shader.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = Path(__file__).resolve().parent.parent  # marketing/launch-video
PAPER, INK, GREEN, YELLOW = "F7F1E8", "403C36", "297A5C", "E8C77A"
TABLE, WALL = "EDE4D6", "F2EADF"  # the look reference's table and wall creams


def lin(hexc: str, a: float = 1.0) -> tuple[float, float, float, float]:
    def ch(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (ch(int(hexc[0:2], 16)), ch(int(hexc[2:4], 16)), ch(int(hexc[4:6], 16)), a)


def reset() -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def _fibre(nt, strength: float):
    """Paper grain: fine noise into a bump, so light rakes across fibres instead of a flat fill."""
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 900.0
    noise.inputs["Detail"].default_value = 8.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    return bump


def paper_material(
    name: str,
    color: str | None = None,
    image: str | None = None,
    glow: float = 0.0,
    tint: str | None = None,
    sat: float = 1.0,
):
    """Matte paper: no specular, no sheen, a little fibre bump. Image cards take colour and alpha
    from the PNG. `glow` adds emission in the card's own colour (a lit phone screen). `tint`
    multiplies an image card's colour; `sat` pulls Gemini's browns back to ink."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    nt.links.new(_fibre(nt, 0.12).outputs["Normal"], bsdf.inputs["Normal"])
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(HERE / image))
        tex.interpolation = "Cubic"
        col = tex.outputs["Color"]
        if sat != 1.0:
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = sat
            nt.links.new(col, hs.inputs["Color"])
            col = hs.outputs["Color"]
        if tint:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            nt.links.new(col, mix.inputs["A"])
            mix.inputs["B"].default_value = lin(tint)
            col = mix.outputs["Result"]
        nt.links.new(col, bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    else:
        bsdf.inputs["Base Color"].default_value = lin(color)
    if glow:
        bsdf.inputs["Emission Color"].default_value = lin(color)
        bsdf.inputs["Emission Strength"].default_value = glow
    return mat


def _obj(name, mesh_op, mat, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
    mesh_op()
    ob = bpy.context.active_object
    ob.name = name
    ob.location, ob.rotation_euler, ob.scale = loc, [math.radians(r) for r in rot], scale
    ob.data.materials.append(mat)
    return ob


def card(
    name: str,
    image: str,
    height: float,
    x: float,
    y: float,
    z: float = 0.0,
    lean: float = 0.0,
    turn: float = 0.0,
    flat: bool = False,
    tint: str | None = None,
    sat: float = 1.0,
):
    """A paper cut-out standing on its bottom edge at (x, y, z), `height` tall, width from the PNG.
    `lean` tips it back (degrees), `turn` rotates it about Z. `flat` lays it on the surface."""
    img = bpy.data.images.load(str(HERE / image), check_existing=True)
    w = height * img.size[0] / img.size[1]
    rot = (0, 0, turn) if flat else (90 - lean, 0, turn)
    # Seat the lowest opaque pixel on the surface: PNGs carry clear rows under the object
    # (the kettle has 52), which would otherwise leave the card hanging in the air.
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., 3]
    drop = (
        height * int(np.argmax(a.max(axis=1) > 0.5)) / img.size[1]
    )  # Blender rows start at the bottom
    loc = (x, y, z + 0.0006) if flat else (x, y, z - drop * math.cos(math.radians(lean)))
    ob = _obj(
        name,
        lambda: bpy.ops.mesh.primitive_plane_add(size=1),
        paper_material(name, image=image, tint=tint, sat=sat),
        loc,
        rot,
        (w, height, 1),
    )
    if not flat:  # pivot on the bottom edge: cards fold up from the table
        ob.data.transform(Matrix.Translation((0, 0.5, 0)))
    thick = ob.modifiers.new("paper", "SOLIDIFY")  # card stock, so edges catch light
    thick.thickness, thick.offset = 0.0015, 0
    return ob


def box(name: str, color: str, size, loc, rot=(0, 0, 0), glow: float = 0.0, round_: float = 0.0):
    """A paper block, `size` baked into the mesh so `round_` (corner radius, metres) stays round."""
    ob = _obj(
        name,
        lambda: bpy.ops.mesh.primitive_cube_add(size=1),
        paper_material(name, color, glow=glow),
        loc,
        rot,
    )
    ob.data.transform(Matrix.Diagonal((*size, 1)))
    if round_:
        bev = ob.modifiers.new("round", "BEVEL")
        bev.width, bev.segments, bev.affect = round_, 8, "EDGES"
        bev.limit_method = "ANGLE"
    return ob


def disc(
    name: str,
    color: str,
    radius: float,
    thick: float,
    x: float,
    y: float,
    z: float = 0.0,
    upright: bool = False,
    glow: float = 0.0,
):
    """A round paper piece lying on a surface (a trivet), top at z + thick; or `upright`,
    centred at z,
    facing the camera (a paper sun)."""
    loc, rot = ((x, y, z), (90, 0, 0)) if upright else ((x, y, z + thick / 2), (0, 0, 0))
    return _obj(
        name,
        lambda: bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1, depth=1),
        paper_material(name, color, glow=glow),
        loc,
        rot,
        (radius, radius, thick),
    )


def phone(
    name: str,
    x: float,
    y: float,
    z: float,
    w: float = 0.11,
    lean: float = 15.0,
    turn: float = 0.0,
    body: str = INK,
    lit: float = 1.2,
    stand: bool = True,
    corner: float = 0.14,
):
    """A phone standing on its bottom edge, tipped back `lean` degrees, screen to the camera:
    an ink body, a plain warm yellow face (glowing when `lit` > 0, dark ink when 0), and a small
    cream paper stand behind it. Never anything on the screen.
    `lean=90, stand=False, z=0.0045` lays it face up on a surface;
    `corner` (a fraction of the width) tells two makes apart."""
    h, t = w * 2.0, 0.009
    rot = Euler((math.radians(-lean), 0, math.radians(turn)))
    m = rot.to_matrix()
    centre = Vector((x, y, z)) + m @ Vector((0, 0, h / 2))
    deg = (-lean, 0, turn)
    box(name, body, (w, t, h), centre, deg, round_=w * corner)
    face = centre + m @ Vector((0, -t / 2 - 0.0006, 0))
    box(
        name + "-screen",
        YELLOW if lit else "2E2B27",
        (w * 0.84, 0.001, h * 0.88),
        face,
        deg,
        glow=lit,
        round_=w * 0.08,
    )
    if stand:  # a cream paper wedge behind, out of sight from the front
        back = Vector((x, y, z)) + m @ Vector((0, t / 2 + 0.035, 0))
        box(
            name + "-stand",
            PAPER,
            (w * 0.6, 0.05, h * 0.42),
            (back.x, back.y + 0.012, z + h * 0.18),
            (-lean - 30, 0, turn),
        )


def stage(table_front: float = -0.6, wall_y: float = 0.62):
    """Table top at z=0 with a visible front edge, and a plain wall behind it."""
    box(
        "table",
        TABLE,
        (6, wall_y - table_front + 1, 0.12),
        (0, (table_front + wall_y + 1) / 2, -0.06),
    )
    box("wall", WALL, (6, 0.05, 3), (0, wall_y + 0.025, 1.5))


def light(key=(-1.6, -1.4, 2.3), power: float = 110.0, fill: float = 0.16):
    """One big soft key from the upper left (gentle paper shadows) and a warm ambient fill."""
    bpy.ops.object.light_add(type="AREA", location=key)
    k = bpy.context.active_object
    k.data.shape, k.data.size = "DISK", 1.3
    k.data.energy, k.data.color = power, (1.0, 0.96, 0.9)
    k.rotation_euler = (math.radians(40), math.radians(-35), math.radians(-30))
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.95, 0.9, 0.84, 1)
    bg.inputs["Strength"].default_value = fill
    bpy.context.scene.world = world
    return k


def key(ob, path: str, frame: int, value) -> None:
    """Set and keyframe one property, eased (Bezier, Blender's default)."""
    setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame)


def key_socket(mat_name: str, socket: str, frame: int, value) -> None:
    sock = bpy.data.materials[mat_name].node_tree.nodes["Principled BSDF"].inputs[socket]
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)


def camera(loc, target, lens: float = 50.0):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    cam.data.lens = lens
    aim = cam.constraints.new("TRACK_TO")
    bpy.ops.object.empty_add(location=target)
    aim.target = bpy.context.active_object
    aim.track_axis, aim.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    bpy.context.scene.camera = cam
    return cam, aim.target


def render_settings(
    samples: int = 96, width: int = 1920, height: int = 1080, engine: str = "CYCLES"
) -> None:
    """CYCLES by default; EEVEE (raytraced, soft shadows) if Cycles ever gets too slow."""
    sc = bpy.context.scene
    if engine == "CYCLES":
        sc.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type != "CPU"  # GPU only; the CPU slows Metal renders down
        sc.cycles.device = "GPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.adaptive_threshold = 0.02
    else:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = samples
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
        sc.eevee.shadow_ray_count = 3
        sc.eevee.shadow_step_count = 12
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.fps = 30
    sc.view_settings.view_transform = "Standard"  # the brief's hex values, not a film curve
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False


def still(path: str, frame: int = 1) -> None:
    sc = bpy.context.scene
    sc.frame_set(frame)
    sc.render.filepath = str(HERE / path)
    bpy.ops.render.render(write_still=True)


def frames(folder: str, count: int) -> None:
    """Render frames 1..count to <folder>/0001.png and on."""
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, count
    sc.render.filepath = str(HERE / folder) + "/"
    bpy.ops.render.render(animation=True)


def run(build, shots: dict[str, int]) -> None:
    """Shared command line for every set script, after Blender's `--`:
    <shot> still [frame] [out.png]   one frame (default the shot's middle) to out/stills/<shot>.png
    <shot> frames [WxH]              every frame to out/frames/<shot>[-WxH]/
    `build(shot)` builds and animates the set for that shot; `shots` maps shot id to frames."""
    import sys

    args = sys.argv[sys.argv.index("--") + 1 :]
    shot, mode = args[0], args[1] if len(args) > 1 else "still"
    if shot not in shots:
        raise SystemExit(f"unknown shot {shot}; this set renders {sorted(shots)}")
    reset()
    build(shot)
    count = shots[shot]
    if mode == "frames":
        size = args[2] if len(args) > 2 else "1920x1080"
        w, h = (int(v) for v in size.split("x"))
        render_settings(samples=48, width=w, height=h)
        frames(f"out/frames/{shot}" + ("" if size == "1920x1080" else f"-{size}"), count)
    else:
        render_settings()
        frame = int(args[2]) if len(args) > 2 else count // 2
        still(args[3] if len(args) > 3 else f"out/stills/{shot}.png", frame)
