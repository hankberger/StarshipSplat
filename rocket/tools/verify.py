import bpy, json
out = {"version": bpy.app.version_string, "online_access": bpy.app.online_access,
       "file": bpy.data.filepath, "objects": len(bpy.data.objects)}
try:
    bpy.ops.atlas.command.get_rna_type(); out["atlas_operator"] = True
    bpy.ops.atlas.command(request_json=json.dumps({"command": "frames.list", "args": {}}))
    out["frames_list"] = json.loads(bpy.context.window_manager.atlas_result)
except Exception as e:
    out["atlas_error"] = repr(e)
result = out
