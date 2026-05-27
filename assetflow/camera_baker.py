import bpy


class ASSETFLOW_OT_bake_camera(bpy.types.Operator):
    """Bake selected camera, maintaining its position even if parented to another object"""
    bl_idname = "assetflow.bake_camera"
    bl_label = "Bake Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get selected camera
        camera = context.active_object
        
        if not camera or camera.type != 'CAMERA':
            self.report({'ERROR'}, "AssetFlow: Select a camera to bake")
            return {'CANCELLED'}
        
        scene = context.scene
        camera_name = camera.name
        
        # Store original parent
        original_parent = camera.parent
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create empty1 at initial camera position (before unparenting)
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty1 = context.active_object
        empty1.matrix_world = camera.matrix_world.copy()
        empty1.name = f"{camera_name}_ref_initial"
        
        # Bake rotation to empty1
        rot_constraint = empty1.constraints.new(type='COPY_ROTATION')
        rot_constraint.target = camera
        context.view_layer.objects.active = empty1
        bpy.ops.object.visual_transform_apply()
        empty1.constraints.clear()
        
        # Unparent camera
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = camera
        camera.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR')
        
        # Bake camera animation
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        
        try:
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={'OBJECT'}
            )
        except Exception as e:
            bpy.data.objects.remove(empty1, do_unlink=True)
            self.report({'ERROR'}, f"AssetFlow: Bake failed - {str(e)}")
            return {'CANCELLED'}
        
        # Create empty2 at camera position after bake
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty2 = context.active_object
        empty2.matrix_world = camera.matrix_world.copy()
        empty2.name = f"{camera_name}-Handle"
        
        # Bake rotation to empty2
        rot_constraint2 = empty2.constraints.new(type='COPY_ROTATION')
        rot_constraint2.target = camera
        context.view_layer.objects.active = empty2
        bpy.ops.object.visual_transform_apply()
        empty2.constraints.clear()
        
        # Parent camera to empty2
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = camera
        camera.select_set(True)
        empty2.select_set(True)
        context.view_layer.objects.active = empty2
        bpy.ops.object.parent_set(type='OBJECT')
        
        # Add constraints to align empty2 to empty1 position
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = empty2
        empty2.select_set(True)
        
        loc_constraint = empty2.constraints.new(type='COPY_LOCATION')
        loc_constraint.target = empty1
        
        rot_constraint = empty2.constraints.new(type='COPY_ROTATION')
        rot_constraint.target = empty1
        
        # Apply constraints
        bpy.ops.object.visual_transform_apply()
        empty2.constraints.clear()
        
        # Remove empty1
        bpy.data.objects.remove(empty1, do_unlink=True)
        
        # Parent empty2 to original parent if it exists
        if original_parent:
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = empty2
            empty2.select_set(True)
            original_parent.select_set(True)
            context.view_layer.objects.active = original_parent
            bpy.ops.object.parent_set(type='OBJECT')
        
        self.report({'INFO'}, f"AssetFlow: Camera '{camera_name}' baked successfully | Handle: '{empty2.name}'")
        return {'FINISHED'}


class ASSETFLOW_PT_camera_baker(bpy.types.Panel):
    bl_label = "Camera Baker"
    bl_idname = "ASSETFLOW_PT_camera_baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AssetFlow"
    bl_order = 0

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Camera Baking", icon='CAMERA_DATA')
        col.separator()
        col.operator(
            "assetflow.bake_camera",
            text="Bake Selected Camera",
            icon='RENDER_ANIMATION'
        )
        col.separator()
        col.label(text="Creates a Handle (Empty)", icon='INFO')
        col.label(text="to control the baked camera.")


classes = (
    ASSETFLOW_OT_bake_camera,
    ASSETFLOW_PT_camera_baker,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)