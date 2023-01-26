bl_info = {
    'name': "3DMigoto_GIMI_Tools",
    "author": "HazrateGolabi",
    'version': (0, 7, 0),
    'blender': (3, 4, 0),
    "location": "Properties Editor > Mesh data > Vertex Groups > Specials menu",
    'category': "Mesh",
}
import bpy
import itertools


class VGROUP_SN_merge(bpy.types.Operator):
    bl_description = "Merge the vertex groups with shared name"
    bl_idname = 'mesh.merge_shared_name_vgs'
    bl_label = "Merge shared name VGs"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return True

    def __init__(self):
        self.selected = list()

    def invoke(self, context, event):
        if event.alt:
            self.selected = [*{context.object, *context.selected_objects}]
        return self.execute(context)

    def execute(self, context):
        if not self.selected:
            self.selected = [context.object]

        for ob in self.selected:
            if not getattr(ob, 'type', None) == 'MESH':
                continue

            #myyy 
            vgroup_names = [x.name.split(".")[0] for x in ob.vertex_groups]
            for vname in vgroup_names:
                relevant = [x.name for x in ob.vertex_groups if x.name.split(".")[0] == f"{vname}"]
                if relevant:
                    vgroup = ob.vertex_groups.new(name=f"x{vname}")
                    for vert_id, vert in enumerate(ob.data.vertices):
                        available_groups = [v_group_elem.group for v_group_elem in vert.groups]

                        combined = 0
                        for v in relevant:
                            if ob.vertex_groups[v].index in available_groups:
                                combined += ob.vertex_groups[v].weight(vert_id)
                                if combined > 0:
                                    vgroup.add([vert_id], combined ,'ADD')
                    for vg in [x for x in ob.vertex_groups if x.name.split(".")[0] == f"{vname}"]:
                        ob.vertex_groups.remove(vg)
                    for vg in ob.vertex_groups:
                        if vg.name[0].lower() == "x":
                            vg.name = vg.name[1:]

            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}


class VGROUP_SN_merge_ONE(bpy.types.Operator):
    bl_description = "Merge the vertex groups with shared name with the active VG"
    bl_idname = 'mesh.merge_shared_name_vgs_one'
    bl_label = "Merge shared name VGs with the active VG"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return True

    def __init__(self):
        self.selected = list()

    def invoke(self, context, event):
        if event.alt:
            self.selected = [*{context.object, *context.selected_objects}]
        return self.execute(context)

    def execute(self, context):
        if not self.selected:
            self.selected = [context.object]
        for ob in self.selected:
            if not getattr(ob, 'type', None) == 'MESH':
                continue
            
            #myyy
            vname = ob.vertex_groups.active.name
            if "." in vname:
                vname = vname.split(".")[0]
            vgroup_names = [x.name.split(".")[0] for x in ob.vertex_groups]
            relevant = [x.name for x in ob.vertex_groups if x.name.split(".")[0] == f"{vname}"]
            
            if relevant:
                vgroup = ob.vertex_groups.new(name=f"x{vname}")
                for vert_id, vert in enumerate(ob.data.vertices):
                    available_groups = [v_group_elem.group for v_group_elem in vert.groups]
                    combined = 0
                    for v in relevant:
                        if ob.vertex_groups[v].index in available_groups:
                            combined += ob.vertex_groups[v].weight(vert_id)
                            if combined > 0:
                                vgroup.add([vert_id], combined ,'ADD')
                for vg in [x for x in ob.vertex_groups if x.name.split(".")[0] == f"{vname}"]:
                    ob.vertex_groups.remove(vg)
                for vg in ob.vertex_groups:
                    if vg.name[0].lower() == "x":
                        vg.name = vg.name[1:]

            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}


class VGROUP_SN_fill(bpy.types.Operator):
    bl_description = "Fill VGs from the lowest to highest existing one "
    bl_idname = 'mesh.fill_vg'
    bl_label = "Fill VGs"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return True

    def __init__(self):
        self.selected = list()

    def invoke(self, context, event):
        if event.alt:
            self.selected = [*{context.object, *context.selected_objects}]
        return self.execute(context)

    def execute(self, context):
        if not self.selected:
            self.selected = [context.object]
        for ob in self.selected:
            if not getattr(ob, 'type', None) == 'MESH':
                continue
            
            #myyy
            largest = 0
            for vg in ob.vertex_groups:
                try:
                    if int(vg.name.split(".")[0])>largest:
                        largest = int(vg.name.split(".")[0])
                except ValueError:
                    print("Vertex group not named as integer, skipping")

            missing = set([f"{i}" for i in range(largest+1)]) - set([x.name.split(".")[0] for x in ob.vertex_groups])
            for number in missing:
                ob.vertex_groups.new(name=f"{number}")
        
            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}


class VGROUP_SN_remove(bpy.types.Operator):
    bl_description = "Remove unused VGs checks ONLY the weight paints, not shapekeys and others"
    bl_idname = 'mesh.remove_vg'
    bl_label = "Remove unused VGs"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        return True

    def __init__(self):
        self.selected = list()

    def invoke(self, context, event):
        if event.alt:
            self.selected = [*{context.object, *context.selected_objects}]
        return self.execute(context)

    def execute(self, context):
        if not self.selected:
            self.selected = [context.object]
        for ob in self.selected:
            if not getattr(ob, 'type', None) == 'MESH':
                continue
            
            #myyy
            used_groups = set()

            # Used groups from weight paint
            for (id, vert) in enumerate(ob.data.vertices):
                for vg in vert.groups:
                    vgi = vg.group
                    used_groups.add(vgi)
            #removing
            for vg in list(reversed(ob.vertex_groups)):
                if vg.index not in used_groups:
                    ob.vertex_groups.remove(vg)
            
        bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}



def draw_menu(self, context):
    layout = self.layout
    layout.operator('mesh.merge_shared_name_vgs', icon='BRUSH_GRAB')
    layout.operator('mesh.merge_shared_name_vgs_one', icon='BRUSH_INFLATE')
    layout.operator('mesh.fill_vg', icon='BRUSH_FILL')
    layout.operator('mesh.remove_vg', icon='GPBRUSH_ERASE_STROKE')

def register():
    bpy.utils.register_class(VGROUP_SN_merge)
    bpy.utils.register_class(VGROUP_SN_merge_ONE)
    bpy.utils.register_class(VGROUP_SN_fill)
    bpy.utils.register_class(VGROUP_SN_remove)
    bpy.types.MESH_MT_vertex_group_context_menu.append(draw_menu)


def unregister():
    bpy.types.MESH_MT_vertex_group_context_menu.remove(draw_menu)
    bpy.utils.unregister_class(VGROUP_SN_remove)
    bpy.utils.unregister_class(VGROUP_SN_fill)
    bpy.utils.unregister_class(VGROUP_SN_merge_ONE)
    bpy.utils.unregister_class(VGROUP_SN_merge)
