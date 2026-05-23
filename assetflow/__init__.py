bl_info = {
    "name": "AssetFlow Toolkit",
    "author": "Tu Nombre",
    "version": (1, 1, 1),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > AssetFlow | Properties > Render > AssetFlow",
    "description": "Pipeline utilities for Blender production workflows",
    "category": "Pipeline",
}

from . import gp_cleaner
from . import render_builder


def register():
    gp_cleaner.register()
    render_builder.register()


def unregister():
    gp_cleaner.unregister()
    render_builder.unregister()