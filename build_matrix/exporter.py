"""
BUILD-MATRIX.ai Exporter Engine
Exports 2D blueprints to PNG, SVG, PDF and 3D models to OBJ, GLTF, STL, and HTML viewports.
"""

import os
import zipfile
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import svgwrite
import trimesh
from typing import Dict, Any, Optional
from .models import BuildingModel, Blueprint2DConfig
from .drawing_2d import Blueprint2DRenderer
from .rendering_3d import Blueprint3DRenderer


import tempfile


class ExporterEngine:
    """Handles multi-format file exports for 2D blueprints and 3D architectural assets."""

    @classmethod
    def export_2d_png(cls, building: BuildingModel, filepath: str, floor: int = 1, config: Optional[Blueprint2DConfig] = None) -> str:
        """Exports 2D Blueprint to PNG raster file."""
        renderer = Blueprint2DRenderer(config=config)
        fig = renderer.render(building, floor=floor)
        fig.savefig(filepath, format="png", dpi=config.dpi if config else 200, bbox_inches="tight")
        plt.close(fig)
        return filepath

    @classmethod
    def export_2d_svg(cls, building: BuildingModel, filepath: str, floor: int = 1, config: Optional[Blueprint2DConfig] = None) -> str:
        """Exports 2D Blueprint to SVG vector file."""
        renderer = Blueprint2DRenderer(config=config)
        fig = renderer.render(building, floor=floor)
        fig.savefig(filepath, format="svg", bbox_inches="tight")
        plt.close(fig)
        return filepath

    @classmethod
    def export_2d_pdf(cls, building: BuildingModel, filepath: str, floor: int = 1, config: Optional[Blueprint2DConfig] = None) -> str:
        """Exports 2D Blueprint to PDF vector document."""
        renderer = Blueprint2DRenderer(config=config)
        fig = renderer.render(building, floor=floor)
        fig.savefig(filepath, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return filepath

    @classmethod
    def export_3d_obj(cls, building: BuildingModel, filepath: str) -> str:
        """Exports 3D building mesh to OBJ geometry file."""
        renderer = Blueprint3DRenderer(building)
        scene = renderer.build_trimesh_scene()
        obj_data = trimesh.exchange.obj.export_obj(scene)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(obj_data)
        return filepath

    @classmethod
    def export_3d_stl(cls, building: BuildingModel, filepath: str) -> str:
        """Exports 3D building mesh to STL 3D printing file."""
        renderer = Blueprint3DRenderer(building)
        scene = renderer.build_trimesh_scene()
        mesh = scene.to_geometry()
        mesh.export(filepath, file_type="stl")
        return filepath

    @classmethod
    def export_3d_gltf(cls, building: BuildingModel, filepath: str) -> str:
        """Exports 3D building mesh to GLTF / GLB web 3D model."""
        renderer = Blueprint3DRenderer(building)
        scene = renderer.build_trimesh_scene()
        glb_data = scene.export(file_type="glb")
        with open(filepath, "wb") as f:
            f.write(glb_data)
        return filepath

    @classmethod
    def export_3d_html(cls, building: BuildingModel, filepath: str) -> str:
        """Exports standalone 3D Three.js WebGL interactive viewer HTML file."""
        renderer = Blueprint3DRenderer(building)
        html_code = renderer.generate_threejs_html()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_code)
        return filepath

    @classmethod
    def export_bundle_zip(cls, building: BuildingModel, output_zip_path: str) -> str:
        """Packages all 2D and 3D architectural blueprint files into a single zip archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_png = os.path.join(temp_dir, "blueprint_2d.png")
            temp_svg = os.path.join(temp_dir, "blueprint_2d.svg")
            temp_pdf = os.path.join(temp_dir, "blueprint_2d.pdf")
            temp_obj = os.path.join(temp_dir, "model_3d.obj")
            temp_stl = os.path.join(temp_dir, "model_3d.stl")
            temp_html = os.path.join(temp_dir, "viewer_3d.html")

            cls.export_2d_png(building, temp_png)
            cls.export_2d_svg(building, temp_svg)
            cls.export_2d_pdf(building, temp_pdf)
            cls.export_3d_obj(building, temp_obj)
            cls.export_3d_stl(building, temp_stl)
            cls.export_3d_html(building, temp_html)

            with zipfile.ZipFile(output_zip_path, "w") as zipf:
                zipf.write(temp_png, arcname="blueprint_2d.png")
                zipf.write(temp_svg, arcname="blueprint_2d.svg")
                zipf.write(temp_pdf, arcname="blueprint_2d.pdf")
                zipf.write(temp_obj, arcname="model_3d.obj")
                zipf.write(temp_stl, arcname="model_3d.stl")
                zipf.write(temp_html, arcname="viewer_3d.html")

        return output_zip_path

