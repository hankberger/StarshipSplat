import bpy
result = {"collections": {c.name: [len(c.objects), c.hide_viewport] for c in bpy.data.collections}, "dirty": bpy.data.is_dirty, "file": bpy.data.filepath}
