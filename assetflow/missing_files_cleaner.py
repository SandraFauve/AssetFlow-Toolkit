import bpy
import os


def get_missing_files():
    missing = []

    # Imgages
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

    # Libraries 
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

    # Fonts
    for font in bpy.data.fonts:
        if font.filepath and font.filepath != '<builtin>':
            path = bpy.path.abspath(font.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'FONT',
                    'name': font.name,
                    'path': font.filepath,
                    'datablock': font
                })

    # VDB
    for volume in bpy.data.volumes:
        if volume.filepath:
            path = bpy.path.abspath(volume.filepath)
            if not os.path.exists(path):
                missing.append({
                    'type': 'VOLUME',
                    'name': volume.name,
                    'path': volume.filepath,
                    'datablock': volume
                })

    # video and sound
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

    # Scripts
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

    # Csimulation caches (fluid, cloth, particles)
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:

            # Fluid
            if modifier.type == 'FLUID':
                cache_dir = modifier.domain_settings.cache_directory
                if cache_dir:
                    path = bpy.path.abspath(cache_dir)
                    if not os.path.exists(path):
                        missing.append({
                            'type': 'CACHE_FLUID',
                            'name': f"{obj.name} → {modifier.name}",
                            'path': cache_dir,
                            'datablock': None
                        })

            # Cloth and Softbody
            if modifier.type in ('CLOTH', 'SOFT_BODY'):
                cache = modifier.point_cache
                if cache.use_disk_cache:
                    cache_path = bpy.path.abspath(f"//{cache.name}")
                    if not os.path.exists(cache_path):
                        missing.append({
                            'type': f'CACHE_{modifier.type}',
                            'name': f"{obj.name} → {modifier.name}",
                            'path': cache_path,
                            'datablock': None
                        })

            # Particles
            if modifier.type == 'PARTICLE_SYSTEM':
                cache = modifier.particle_system.point_cache
                if cache.use_disk_cache:
                    cache_path = bpy.path.abspath(f"//{cache.name}")
                    if not os.path.exists(cache_path):
                        missing.append({
                            'type': 'CACHE_PARTICLES',
                            'name': f"{obj.name} → {modifier.name}",
                            'path': cache_path,
                            'datablock': None
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
                if item['type'] == 'IMAGE':
                    bpy.data.images.remove(db)
                elif item['type'] == 'LIBRARY':
                    bpy.data.libraries.remove(db)
                elif item['type'] == 'SOUND':
                    bpy.data.sounds.remove(db)
                elif item['type'] == 'MOVIE CLIP':
                    bpy.data.movieclips.remove(db)
                elif item['type'] == 'FONT':
                    bpy.data.fonts.remove(db)
                elif item['type'] == 'VOLUME':
                    bpy.data.volumes.remove(db)
                elif item['type'].startswith('SEQUENCE_'):
                    seq_editor = context.scene.sequence_editor
                    strip = seq_editor.sequences_all.get(item['name'])
                    if strip:
                        seq_editor.sequences.remove(strip)
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