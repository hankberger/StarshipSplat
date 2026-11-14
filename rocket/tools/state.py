import bpy
result = {"file": bpy.data.filepath, "n": len(bpy.data.objects), "cams": len([o for o in bpy.data.objects if o.type=="CAMERA"]),
          "types": sorted({o.type for o in bpy.data.objects}), "names": [o.name for o in bpy.data.objects][:8],
          "collections": [c.name for c in bpy.data.collections], "dirty": bpy.data.is_dirty}
