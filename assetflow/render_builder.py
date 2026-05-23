import bpy


class ASSETFLOW_OT_setup_render_output(bpy.types.Operator):
    """Create one Render Layer node per View Layer, all connected to a single File Output"""
    bl_idname = "assetflow.setup_render_output"
    bl_label = "Build Render Output Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        if not scene.use_nodes:
            scene.use_nodes = True

        tree = scene.node_tree
        nodes = tree.nodes
        links = tree.links
        view_layers = scene.view_layers

        if not view_layers:
            self.report({'WARNING'}, "No View Layers found in scene")
            return {'CANCELLED'}

        # Create single File Output node
        fo_node = nodes.new('CompositorNodeOutputFile')
        fo_node.base_path = "//renders/"
        fo_node.label = "AssetFlow_Output"
        fo_node.location = (500, 0)

        # Remove the default empty slot
        fo_node.file_slots.remove(fo_node.inputs[0])

        y_offset = 0
        NODE_SPACING = 300

        for vl in view_layers:
            name = vl.name

            # One Render Layers node per View Layer
            rl_node = nodes.new('CompositorNodeRLayers')
            rl_node.layer = name
            rl_node.location = (0, y_offset)
            rl_node.label = name

            # Add slot to the shared File Output
            fo_node.file_slots.new(f"{name}/{name}_")

            # Link Image → new slot
            slot_index = len(fo_node.file_slots) - 1
            if rl_node.outputs.get('Image'):
                links.new(rl_node.outputs['Image'], fo_node.inputs[slot_index])

            y_offset -= NODE_SPACING

        # Center the File Output node vertically
        fo_node.location = (500, y_offset / 2)

        self.report(
            {'INFO'},
            f"AssetFlow: Built {len(view_layers)} Render Layer node(s) → 1 File Output"
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

        col = layout.column(align=True)
        col.label(text="Render Layer Organization", icon='RENDERLAYERS')
        col.separator()
        col.operator(
            "assetflow.setup_render_output",
            text="Build Render Output Nodes",
            icon='NODETREE'
        )
        col.separator()
        col.label(text="One File Output node for all layers:", icon='INFO')
        col.label(text="renders/LayerName/LayerName_")


classes = (
    ASSETFLOW_OT_setup_render_output,
    ASSETFLOW_PT_render_builder,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)