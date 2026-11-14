import bpy
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        sp = area.spaces.active
        sp.shading.type = "MATERIAL"
        sp.clip_end = 5000
        region = next(r for r in area.regions if r.type == "WINDOW")
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_all()
def _save():
    bpy.ops.wm.save_as_mainfile(filepath=r"A:\Coding\Projects\atlastest\rocket\rocket_scene.blend")
    return None
bpy.app.timers.register(_save, first_interval=0.5)
result = "queued save"
