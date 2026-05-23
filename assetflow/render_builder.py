import bpy
from bpy.props import StringProperty, EnumProperty


class ASSETFLOW_PG_render_settings(bpy.types.PropertyGroup):
    base_path: StringProperty(
        name="Base Path",
        description="Base output path for all renders",
        default="//renders/",
        subtype='DIR_PATH'
    )

    file_format: EnumProperty(
        name="Format",
        items=[
            ('PNG',                 "PNG",            ""),
            ('OPEN_EXR',            "EXR",            ""),
            ('OPEN_EXR_MULTILAYER', "EXR Multilayer", ""),
            ('JPEG',                "JPEG",           ""),
            ('TIFF',                "TIFF",           ""),
        ],
        default='PNG'
    )
    color_depth: EnumProperty(
        name="Color Depth",
        items=[
            ('8',  "8 bit",  ""),
            ('16', "16 bit", ""),
            ('32', "32 bit", ""),
        ],
        default='16'
    )

def build_file_output(context, rl_nodes):
    settings = context.scene.assetflow_render
    tree = context.scene.node_tree

    fo_node = tree.nodes.new('CompositorNodeOutputFile')
    fo_node.label = "AssetFlow_Output"
    fo_node.base_path = settings.base_path          
    fo_node.format.file_format = settings.file_format  
    fo_node.format.color_depth = settings.color_depth  

    max_x = max(n.location.x for n in rl_nodes)
    avg_y = sum(n.location.y for n in rl_nodes) / len(rl_nodes)
    fo_node.location = (max_x + 400, avg_y)

    fo_node.file_slots.remove(fo_node.inputs[0])

    for rl_node in rl_nodes:
        name = rl_node.layer if rl_node.layer else rl_node.label
        fo_node.file_slots.new(f"{name}/{name}_")
        slot_index = len(fo_node.file_slots) - 1
        if rl_node.outputs.get('Image'):
            tree.links.new(rl_node.outputs['Image'], fo_node.inputs[slot_index])

    return fo_node

class ASSETFLOW_OT_build_full_compositor(bpy.types.Operator):

    bl_idname = "assetflow.build_full_compositor"
    bl_label = "Build Compositor Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        if not scene.use_nodes:
            scene.use_nodes = True

        view_layers = scene.view_layers
        if not view_layers:
            self.report({'WARNING'}, "No View Layers found in scene")
            return {'CANCELLED'}
        
        nodes = scene.node_tree.nodes
        rl_nodes = []
        y_offset = 0

        for vl in view_layers:
            rl_node = nodes.new('CompositorNodeRLayers')
            rl_node.layer = vl.name
            rl_node.location = (0, y_offset)
            rl_node.label = vl.name
            rl_nodes.append(rl_node)
            y_offset -= 300

        build_file_output(context, rl_nodes)

        self.report(
            {'INFO'},
            f"AssetFlow: Built compositor for {len(rl_nodes)} View Layer(s)"
        )
        return {'FINISHED'}
    
class ASSETFLOW_OT_build_file_output_only(bpy.types.Operator):

    bl_idname = "assetflow.build_file_output_only"
    bl_label = "Build File Output Only"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = bpy.context.scene

        if not scene.use_nodes:
            scene.use_nodes = True

        rl_nodes = [n for n in scene.node_tree.nodes if n.type == 'R_LAYERS']

        if not rl_nodes:
            self.report({'WARNING'}, "No Render Layer nodes found in compositor")
            return {'CANCELLED'}

        build_file_output(bpy.context, rl_nodes)

        self.report(
            {'INFO'},
            f"AssetFlow: Linked {len(rl_nodes)} existing Render Layer(s) → 1 File Output"
        )
        return {'FINISHED'}

class ASSETFLOW_PT_render_builder(bpy.types.Panel):
    bl_label = "Render Output Builder"
    bl_idname = "ASSETFLOW_PT_render_builder"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        settings = context.scene.assetflow_render

        col = layout.column(align=True)
        col.label(text="Render Layer Organization", icon='RENDERLAYERS')
        col.separator()
        col.prop(settings, "base_path")
        col.prop(settings, "file_format")
        col.prop(settings, "color_depth")
        col.operator(
            "assetflow.build_full_compositor",
            text="Build Render Output Nodes",
            icon='NODETREE'
        )
        col.operator(                          
            "assetflow.build_file_output_only",
            text="Build File Output Only",
            icon='FILE_TICK'
        )
        col.separator()
        col.label(text="One File Output node for all layers:", icon='INFO')
        col.label(text="renders/LayerName/LayerName_")


classes = (
    ASSETFLOW_PG_render_settings,  
    ASSETFLOW_OT_build_full_compositor,
    ASSETFLOW_OT_build_file_output_only,
    ASSETFLOW_PT_render_builder,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assetflow_render = bpy.props.PointerProperty( 
        type=ASSETFLOW_PG_render_settings
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.assetflow_render