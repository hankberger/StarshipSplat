import bpy, json, time
def atlas(command, **args):
    bpy.ops.atlas.command(request_json=json.dumps({"command": command, "args": args}))
    r = json.loads(bpy.context.window_manager.atlas_result)
    if not r["ok"]: raise RuntimeError(r["error"]["message"])
    return r["result"]
t=time.time()
res = atlas("project.import", path=r"A:\Coding\Projects\atlastest\rocket\scene\cam_IDX.json")
result = {"res": res, "secs": round(time.time()-t,1), "n": len(bpy.data.objects)}
