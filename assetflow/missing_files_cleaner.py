import bpy
import os


def get_missing_files():
    missing = []

    for image in bpy.data.images:
        if image.source == 'FILE' and image.filepath and not image.packed_file:
            path = bpy.path.abspath(image.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'IMAGE',
                    'name': image.name,
                    'path': image.filepath,
                    'datablock': image
                })

    for library in bpy.data.libraries:
        if library.filepath:
            path = bpy.path.abspath(library.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'LIBRARY',
                    'name': library.name,
                    'path': library.filepath,
                    'datablock': library
                })


    if bpy.context.scene.sequence_editor:
        for strip in bpy.context.scene.sequence_editor.sequences_all:
            if strip.type in ('MOVIE', 'SOUND', 'IMAGE'):
                if hasattr(strip, 'filepath') and strip.filepath:
                    path = bpy.path.abspath(strip.filepath)
                    if not os.path.exists(path):
                        missing.append({
                            'type': f'SEQUENCE_{strip.type}',
                            'name': strip.name,
                            'path': strip.filepath,
                            'datablock': strip
                        })


    for text in bpy.data.texts:
        if text.filepath:
            path = bpy.path.abspath(text.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'SCRIPT',
                    'name': text.name,
                    'path': text.filepath,
                    'datablock': text
                })

    return missing


class ASSETFLOW_OT_scan_missing_files(bpy.types.Operator):

    bl_idname = "assetflow.scan_missing_files"
    bl_label = "Scan Missing Files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        missing = get_missing_files()
        context.scene.assetflow_missing_count = len(missing)


        context.scene.assetflow_missing_files.clear()
        for item in missing:
            entry = context.scene.assetflow_missing_files.add()
            entry.type = item['type']
            entry.name = item['name']
            entry.path = item['path']

        if missing:
            self.report({'WARNING'}, f"AssetFlow: Found {len(missing)} missing file(s)")
        else:
            self.report({'INFO'}, "AssetFlow: No missing files found")

        return {'FINISHED'}


class ASSETFLOW_OT_clean_missing_files(bpy.types.Operator):

    bl_idname = "assetflow.clean_missing_files"
    bl_label = "Clean All Missing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        missing = get_missing_files()

        if not missing:
            self.report({'INFO'}, "AssetFlow: Nothing to clean")
            return {'CANCELLED'}

        cleaned = 0

        for item in missing:
            db = item['datablock']
            try:
                if item['type'] == 'IMAGE':
                    bpy.data.images.remove(db)
                elif item['type'] == 'LIBRARY':
                    bpy.data.libraries.remove(db)
                elif item['type'].startswith('SEQUENCE_'):
                    context.scene.sequence_editor.sequences.remove(db)
                elif item['type'] == 'SCRIPT':
                    bpy.data.texts.remove(db)
                cleaned += 1
            except Exception as e:
                self.report({'WARNING'}, f"Could not remove {item['name']}: {e}")

        context.scene.assetflow_missing_files.clear()
        context.scene.assetflow_missing_count = 0

        self.report({'INFO'}, f"AssetFlow: Removed {cleaned} missing file reference(s)")
        return {'FINISHED'}


class ASSETFLOW_PG_missing_file_entry(bpy.types.PropertyGroup):
    type: bpy.props.StringProperty()
    name: bpy.props.StringProperty()
    path: bpy.props.StringProperty()


class ASSETFLOW_PT_missing_files(bpy.types.Panel):
    bl_label = "Missing Files Cleaner"
    bl_idname = "ASSETFLOW_PT_missing_files"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AssetFlow"
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        missing_files = context.scene.assetflow_missing_files
        count = context.scene.assetflow_missing_count

        col = layout.column(align=True)
        col.label(text="Missing Files Cleaner", icon='ORPHAN_DATA')
        col.separator()
        col.operator(
            "assetflow.scan_missing_files",
            text="Scan Missing Files",
            icon='VIEWZOOM'
        )

        if missing_files:
            col.separator()
            col.label(text=f"{count} missing file(s) found:", icon='ERROR')
            col.separator()

            for entry in missing_files:
                box = col.box()
                row = box.row()
                row.label(text=f"[{entry.type}]  {entry.name}", icon='CANCEL')
                box.label(text=entry.path)

            col.separator()
            col.operator(
                "assetflow.clean_missing_files",
                text=f"Clean All ({count})",
                icon='TRASH'
            )
        elif count == 0 and len(missing_files) == 0:
            col.separator()
            col.label(text="Run scan to check files", icon='INFO')


classes = (
    ASSETFLOW_PG_missing_file_entry,
    ASSETFLOW_OT_scan_missing_files,
    ASSETFLOW_OT_clean_missing_files,
    ASSETFLOW_PT_missing_files,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assetflow_missing_files = bpy.props.CollectionProperty(
        type=ASSETFLOW_PG_missing_file_entry
    )
    bpy.types.Scene.assetflow_missing_count = bpy.props.IntProperty(default=0)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.assetflow_missing_files
    del bpy.types.Scene.assetflow_missing_count