import bpy, json
from pathlib import Path
def atlas(command, **args):
    bpy.ops.atlas.command(request_json=json.dumps({"command": command, "args": args}))
    r = json.loads(bpy.context.window_manager.atlas_result)
    if not r["ok"]: raise RuntimeError(r["error"]["message"])
    return r["result"]
# start from an empty scene (default cube/light/camera only)
for o in list(bpy.data.objects):
    if o.name in ("Cube", "Light", "Camera"): bpy.data.objects.remove(o)
folder = Path(r"A:\Coding\Projects\atlastest\rocket\scene")
frames = json.loads((folder / "operation.json").read_text())["response"]["frames"]
(folder / "cameras.json").write_text(json.dumps({"frames": frames}))
res = atlas("project.import", path=str(folder))
bpy.ops.wm.save_as_mainfile(filepath=r"A:\Coding\Projects\atlastest\rocket\rocket_scene.blend")
result = {"import": str(res)[:1500], "objects": [o.name for o in bpy.data.objects][:12], "n": len(bpy.data.objects),
          "collections": [c.name for c in bpy.data.collections]}
