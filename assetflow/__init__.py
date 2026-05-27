bl_info = {
    "name": "AssetFlow Toolkit",
    "author": "Tu Nombre",
    "version": (1, 6, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > AssetFlow | Properties > Render > AssetFlow",
    "description": "Pipeline utilities for Blender production workflows",
    "category": "Pipeline",
}

from . import gp_cleaner
from . import render_builder
from . import missing_files_cleaner
from . import camera_baker


def register():
    gp_cleaner.register()
    render_builder.register()
    camera_baker.register()
    missing_files_cleaner.register()


def unregister():
    gp_cleaner.unregister()
    render_builder.unregister()
    camera_baker.unregister()
    missing_files_cleaner.unregister()