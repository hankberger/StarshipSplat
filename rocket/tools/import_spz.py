import bpy
def _go():
    sc = bpy.context.scene
    for label, path in (("Splats 360", r"A:\Coding\Projects\atlastest\rocket\splats_360\refinedSplats_2000000.spz"),
                        ("Splats real frames only", r"A:\Coding\Projects\atlastest\rocket\splats_real\refinedSplats_2000000.spz")):
        before = set(bpy.data.objects)
        bpy.ops.wm.spz_import(filepath=path)
        col = bpy.data.collections.new(label); sc.collection.children.link(col)
        for o in set(bpy.data.objects) - before:
            for c in list(o.users_collection): c.objects.unlink(o)
            col.objects.link(o); o.name = label
        if label != "Splats 360":
            col.hide_viewport = True; col.hide_render = True
    bpy.ops.wm.save_mainfile()
    return None
bpy.app.timers.register(_go, first_interval=0.3)
result = {"queued": True}
