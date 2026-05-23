import bpy
from bpy.props import BoolProperty


class ASSETFLOW_OT_remove_gp_vertex_paint(bpy.types.Operator):
    """Remove all vertex paint data from Grease Pencil objects in the scene"""
    bl_idname = "assetflow.remove_gp_vertex_paint"
    bl_label = "Clean Vertex Paint"
    bl_options = {'REGISTER', 'UNDO'}

    remove_fill: BoolProperty(
        name="Remove Fill Color",
        description="Clear vertex color from stroke fills",
        default=True
    )
    remove_stroke: BoolProperty(
        name="Remove Stroke Color",
        description="Clear vertex color from stroke points",
        default=True
    )

    def execute(self, context):
        gp_objects = [obj for obj in bpy.data.grease_pencils]

        if not gp_objects:
            self.report({'WARNING'}, "No Grease Pencil objects found in scene")
            return {'CANCELLED'}

        gp_count = 0
        stroke_count = 0
        point_count = 0

        for gp in gp_objects:
            gp_count += 1
            for layer in gp.layers:
                for frame in layer.frames:
                    for stroke in frame.strokes:
                        if self.remove_fill:
                            stroke.vertex_color_fill = (0.0, 0.0, 0.0, 0.0)
                            stroke_count += 1
                        if self.remove_stroke:
                            for point in stroke.points:
                                point.vertex_color = (0.0, 0.0, 0.0, 0.0)
                                point_count += 1

        self.report(
            {'INFO'},
            f"AssetFlow: Cleaned {gp_count} GP object(s) | "
            f"{stroke_count} strokes | {point_count} points"
        )
        return {'FINISHED'}


class ASSETFLOW_PT_gp_cleaner(bpy.types.Panel):
    bl_label = "GP Vertex Paint Cleaner"
    bl_idname = "ASSETFLOW_PT_gp_cleaner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AssetFlow"
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Grease Pencil Cleanup", icon='BRUSH_DATA')
        col.separator()
        col.operator(
            "assetflow.remove_gp_vertex_paint",
            text="Clean All Vertex Paint",
            icon='TRASH'
        )
        col.separator()
        col.label(text="Clears vertex color data from", icon='INFO')
        col.label(text="all GP objects before export.")


classes = (
    ASSETFLOW_OT_remove_gp_vertex_paint,
    ASSETFLOW_PT_gp_cleaner,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)