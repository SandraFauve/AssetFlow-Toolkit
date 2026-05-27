import bpy
import os


def get_missing_files():
    """Get only missing files that Blender's 'Report Missing Files' would show"""
    missing = []

    # Python scripts
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

    # Movie clips (motion tracking)
    for clip in bpy.data.movieclips:
        if clip.filepath:
            path = bpy.path.abspath(clip.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'MOVIE CLIP',
                    'name': clip.name,
                    'path': clip.filepath,
                    'datablock': clip
                })

    # Sounds (speakers)
    for sound in bpy.data.sounds:
        if sound.filepath and not sound.packed_file:
            path = bpy.path.abspath(sound.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'SOUND',
                    'name': sound.name,
                    'path': sound.filepath,
                    'datablock': sound
                })

    # Camera background images
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA' and obj.data.background_images:
            for bg_img in obj.data.background_images:
                if bg_img.image and bg_img.image.source == 'FILE':
                    image = bg_img.image
                    if image.filepath and not image.packed_file:
                        path = bpy.path.abspath(image.filepath)
                        if not os.path.exists(path):
                            missing.append({
                                'type': 'BG IMAGE',
                                'name': f"{obj.name} → {image.name}",
                                'path': image.filepath,
                                'datablock': image
                            })

    # Sequencer strips (video, sound, image sequences)
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
                            'datablock': strip,
                            'channel': strip.channel
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
                if db is None:
                    self.report({'WARNING'}, f"Manual cleanup needed: {item['name']}")
                    continue
                
                if item['type'] == 'SCRIPT':
                    bpy.data.texts.remove(db)
                elif item['type'] == 'MOVIE CLIP':
                    bpy.data.movieclips.remove(db)
                elif item['type'] == 'SOUND':
                    bpy.data.sounds.remove(db)
                elif item['type'] == 'BG IMAGE':
                    bpy.data.images.remove(db)
                elif item['type'].startswith('SEQUENCE_'):
                    seq_editor = context.scene.sequence_editor
                    if seq_editor:
                        strip = seq_editor.sequences_all.get(item['name'])
                        if strip:
                            seq_editor.sequences.remove(strip)
                
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