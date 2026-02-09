import bpy
import numpy as np
import colorsys
import time
import sys
import struct
import mathutils
import os
import bpy.utils.previews
import bpy.utils.previews
from .geometry_node import create_gs_node_system
from .shader import create_shader

bl_info = {
    "name": "3DGS Oil Paint",
    "author": "Bingru Li",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > UI > 3DGS Oil Paint",
    "description": "Import 3DGS PLY, bake Palette Texture and setup Geometry Nodes.",
    "category": "Import-Export",
}

# ==============================================================================
#  MINIMAL PLY READER (Embedded to avoid dependencies)
# ==============================================================================

def read_ply_data(filepath):
    """
    一个极简的高性能 PLY 读取器，专门针对 3DGS 格式优化。
    返回一个字典，包含 numpy arrays。
    """
    with open(filepath, 'rb') as f:
        # Header Parsing
        header_lines = []
        while True:
            line = f.readline().strip().decode('ascii')
            header_lines.append(line)
            if line == 'end_header':
                break
        
        # Parse elements
        vertex_count = 0
        properties = []
        for line in header_lines:
            if line.startswith('element vertex'):
                vertex_count = int(line.split()[-1])
            elif line.startswith('property'):
                parts = line.split()
                name = parts[-1]
                dtype = parts[1]
                properties.append((name, dtype))
        
        # Define Numpy Dtype
        # Mapping PLY types to Numpy types
        type_map = {
            'float': 'f4', 'float32': 'f4',
            'double': 'f8', 'float64': 'f8',
            'uchar': 'u1', 'uint8': 'u1',
            'int': 'i4', 'int32': 'i4'
        }
        
        dtype_list = []
        for name, dtype_str in properties:
            dtype_list.append((name, type_map.get(dtype_str, 'f4')))
            
        # Read Data
        # 3DGS files are usually little-endian
        data = np.fromfile(f, dtype=dtype_list, count=vertex_count)
        
    return data, vertex_count

# ==============================================================================
#  CORE LOGIC: BAKER & IMPORTER
# ==============================================================================


# ==============================================================================
#  ASSET MANAGEMENT
# ==============================================================================

# ==============================================================================
#  ASSET MANAGEMENT
# ==============================================================================

preview_collections = {}

class AssetManager:
    _cached_meshes = []
    _last_scan_time = 0
    
    @classmethod
    def get_asset_path(cls):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "asset.blend")

    @classmethod
    def get_brush_path(cls, subfolder):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "brush", subfolder)

    @classmethod
    def scan_assets(cls, context):
        # Cache for 2 seconds to avoid spamming disk
        if time.time() - cls._last_scan_time < 2.0 and cls._cached_meshes:
            return

        asset_path = cls.get_asset_path()
        if not os.path.exists(asset_path):
            print(f"Asset file missing: {asset_path}")
            return

        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            cls._cached_meshes = [(m, m, "") for m in data_from.meshes]
        
        cls._last_scan_time = time.time()

    @classmethod
    def import_all_assets(cls):
        """Import ALL meshes from asset.blend into the current project"""
        asset_path = cls.get_asset_path()
        if not os.path.exists(asset_path):
            print(f"Asset file missing: {asset_path}")
            return

        # Prepare lists of assets to load
        meshes_to_load = []

        # First inspect what's available
        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            for m in data_from.meshes:
                if m not in bpy.data.meshes:
                    meshes_to_load.append(m)
            
            data_to.meshes = meshes_to_load
            
        print(f"[AssetManager] Imported {len(meshes_to_load)} new meshes.")

    @classmethod
    def get_mesh_items(cls, scene, context):
        cls.scan_assets(context)
        return cls._cached_meshes if cls._cached_meshes else [("NONE", "None", "")]

# Helper callbacks for EnumProperty (must be module-level functions to avoid registration issues)
# Helper callbacks for EnumProperty (must be module-level functions to avoid registration issues)
def get_brush_textures_callback(self, context):
    brush_path = AssetManager.get_brush_path("tex_alpha")
    
    if not os.path.exists(brush_path):
        return [("NONE", "Path Missing", "", 0, 0)]

    # 1. Get raw file list
    try:
        raw_files = sorted(os.listdir(brush_path))
    except Exception as e:
        print(f"[GS_Tool_DEBUG] Error scanning: {e}")
        return [("NONE", "Scan Error", "", 0, 0)]

    # 2. Filter images
    valid_exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')
    image_files = []
    for f in raw_files:
        if f.startswith('.') or f.startswith('_'): 
            continue
        if f.lower().endswith(valid_exts):
            image_files.append(f)
            
    if not image_files:
        return [("NONE", "No Images Found", "", 0, 0)]

    # 3. Ensure Preview Collection
    pcoll = preview_collections.get("main")
    if not pcoll:
        print("[GS_Tool_DEBUG] Re-creating pcoll...")
        try:
            pcoll = bpy.utils.previews.new()
            pcoll.brush_dir = ""
            preview_collections["main"] = pcoll
        except:
            return [("NONE", "Pcoll Error", "", 0, 0)]

    # 4. Build Items List (Standard 5-tuple)
    items = []
    for i, name in enumerate(image_files):
        # Unique ID is file name
        filepath = os.path.join(brush_path, name)
        
        # Load into pcoll if missing
        if name not in pcoll:
            try:
                pcoll.load(name, filepath, 'IMAGE')
            except Exception as e:
                print(f"[GS_Tool_DEBUG] Failed to load {name}: {e}")
                continue
        
        # Get icon ID
        icon_id = pcoll[name].icon_id
        
        # Add to list: (identifier, name, description, icon, unique_number)
        # Using filename as both ID and Name to keep things simple
        items.append((name, name, "", icon_id, i))
        
    return items if items else [("NONE", "None", "", 0, 0)]

def get_meshes_callback(self, context):
    return AssetManager.get_mesh_items(self, context)



# ==============================================================================
#  CORE LOGIC: BAKER & IMPORTER
# ==============================================================================

class GS_Processor:
    PALETTE_SIZE = 256
    GRID_FALLBACK_LEVEL = 40

    @staticmethod
    def log(msg):
        print(f"[GS_Tool] {msg}")

    @staticmethod
    def linear_to_srgb(linear):
        a = 0.055
        srgb = np.where(
            linear <= 0.0031308,
            linear * 12.92,
            (1.0 + a) * np.power(linear, 1.0 / 2.4) - a
        )
        return np.clip(srgb, 0.0, 1.0)





    @classmethod
    def process_and_bake(cls, context, filepath):
        # 0. 获取用户选择的资源
        target_mat_name = context.scene.gs_target_material
        target_mesh_name = context.scene.gs_target_mesh
        target_mesh_name = context.scene.gs_target_mesh
        z_is_minimum = getattr(context.scene, "gs_z_is_minimum", True)
        y_up_to_z_up = getattr(context.scene, "gs_y_up_to_z_up", True)
        source_is_linear = getattr(context.scene, "gs_source_is_linear", True)
        
        # Valid check for NONE
        if target_mat_name == "NONE":
            target_mat_name = None
        if target_mesh_name == "NONE":
            target_mesh_name = None
        
        cls.log(f"Target Material: {target_mat_name}")
        cls.log(f"Target Mesh: {target_mesh_name}")
        cls.log(f"Z is Minimum: {z_is_minimum}")
        cls.log(f"Y-up to Z-up: {y_up_to_z_up}")
        cls.log(f"Source is Linear: {source_is_linear}")
        
        # Step 1: Ensure Library Assets are Loaded
        AssetManager.import_all_assets()
        
        # Step 2: Retrieve the selected assets from bpy.data
        template_mat = None
        template_mesh = None
        
        if target_mat_name and target_mat_name in bpy.data.materials:
            template_mat = bpy.data.materials[target_mat_name]
        
        if target_mesh_name and target_mesh_name in bpy.data.meshes:
            template_mesh = bpy.data.meshes[target_mesh_name]
        
        if target_mat_name and not template_mat:
            cls.log(f"ERROR: Material '{target_mat_name}' not found locally after import!")
        
        start_time = time.time()
        
        # 1. 读取 PLY
        cls.log(f"Loading: {filepath}")
        ply_data, n_points = read_ply_data(filepath)
        
        # 2. 提取并处理基础数据 (NumPy Vectorization)
        # Position
        xyz = np.stack((ply_data['x'], ply_data['y'], ply_data['z']), axis=1)
        
        # Opacity
        if 'opacity' in ply_data.dtype.names:
            log_opacities = ply_data['opacity']
            opacities = 1 / (1 + np.exp(-log_opacities))
        else:
            log_opacities = np.zeros(n_points)
            opacities = np.ones(n_points)

        # Scale
        scale_names = [n for n in ply_data.dtype.names if n.startswith('scale')]
        if len(scale_names) >= 3:
            log_scales = np.stack([ply_data[n] for n in scale_names[:3]], axis=1)
            scales = np.exp(log_scales)
        else:
            log_scales = np.ones((n_points, 3)) * -4.6 
            scales = np.ones((n_points, 3)) * 0.01

        # Rotation
        rot_names = [n for n in ply_data.dtype.names if n.startswith('rot')]
        quats = np.zeros((n_points, 4), dtype=np.float32)
        quats[:, 0] = 1.0
        
        if len(rot_names) >= 4:
            quats = np.stack([ply_data[n] for n in rot_names[:4]], axis=1)
            # Reference script does NOT normalize explicitly

        # ---------------------------------------------------------
        # Optional: Force Z to be the smallest scale axis
        # ---------------------------------------------------------
        if z_is_minimum:
            cls.log("Applying Z-Minimum logic (reorienting splats)...")
            # Find closest axis to "flat" dimension
            # We want scale.z to be the minimum of (x, y, z)
            min_indices = np.argmin(scales, axis=1) # 0=x, 1=y, 2=z
            
            # Masks
            mask_x = (min_indices == 0)
            mask_y = (min_indices == 1)
            
            # --- 1. Adjust Scales ---
            # If X is min: swap X and Z
            # scales[mask_x] = (z, y, x)
            if np.any(mask_x):
                # Copy original
                s_x = scales[mask_x].copy()
                ls_x = log_scales[mask_x].copy()
                # Swap col 0 and 2
                scales[mask_x, 0] = s_x[:, 2]
                scales[mask_x, 2] = s_x[:, 0]
                log_scales[mask_x, 0] = ls_x[:, 2]
                log_scales[mask_x, 2] = ls_x[:, 0]
                
            # If Y is min: swap Y and Z? 
            # Strategy: Rotate -90 on X axis maps Y->Z, Z->-Y
            # So New Z gets Old Y. New Y gets Old Z.
            # scales[mask_y] = (x, z, y)
            if np.any(mask_y):
                s_y = scales[mask_y].copy()
                ls_y = log_scales[mask_y].copy()
                # Swap col 1 and 2
                scales[mask_y, 1] = s_y[:, 2]
                scales[mask_y, 2] = s_y[:, 1]
                log_scales[mask_y, 1] = ls_y[:, 2]
                log_scales[mask_y, 2] = ls_y[:, 1]

            # --- 2. Adjust Rotations ---
            # We must apply a local rotation P such that R_new = R_old * P
            # q_new = q_old * q_p
            
            # Define fix quaternions (w, x, y, z)
            # Fix X->Z: Ry(90) -> (cos(45), 0, sin(45), 0) -> (0.7071, 0, 0.7071, 0)
            q_fix_x = np.array([0.70710678, 0.0, 0.70710678, 0.0], dtype=np.float32)
            
            # Fix Y->Z: Rx(-90) -> (cos(-45), sin(-45), 0, 0) -> (0.7071, -0.7071, 0, 0)
            q_fix_y = np.array([0.70710678, -0.70710678, 0.0, 0.0], dtype=np.float32)
            
            # Prepare array of adjustment quaternions
            q_adj = np.zeros((n_points, 4), dtype=np.float32)
            q_adj[:, 0] = 1.0 # default identity
            
            q_adj[mask_x] = q_fix_x
            q_adj[mask_y] = q_fix_y
            
            # Vectorized Quaternion Multiply
            # q1 (quats) * q2 (q_adj)
            w1, x1, y1, z1 = quats[:, 0], quats[:, 1], quats[:, 2], quats[:, 3]
            w2, x2, y2, z2 = q_adj[:, 0], q_adj[:, 1], q_adj[:, 2], q_adj[:, 3]
            
            q_new = np.empty_like(quats)
            q_new[:, 0] = w1*w2 - x1*x2 - y1*y2 - z1*z2
            q_new[:, 1] = w1*x2 + x1*w2 + y1*z2 - z1*y2
            q_new[:, 2] = w1*y2 - x1*z2 + y1*w2 + z1*x2
            q_new[:, 3] = w1*z2 + x1*y2 - y1*x2 + z1*w2
            
            quats = q_new

        # Compute Euler (after potential modification)
        rot_euler_data = np.zeros((n_points, 3), dtype=np.float32)
        for i in range(n_points):
            q = mathutils.Quaternion(quats[i]) 
            e = q.to_euler()
            rot_euler_data[i] = (e.x, e.y, e.z)

        # 3. 颜色处理 (SH -> RGB)
        if 'f_dc_0' in ply_data.dtype.names:
            SH_C0 = 0.28209479177387814
            r = ply_data['f_dc_0'] * SH_C0 + 0.5
            g = ply_data['f_dc_1'] * SH_C0 + 0.5
            b = ply_data['f_dc_2'] * SH_C0 + 0.5
            cols = np.stack((r, g, b), axis=1)
        elif 'red' in ply_data.dtype.names:
            cols = np.stack((ply_data['red'], ply_data['green'], ply_data['blue']), axis=1) / 255.0
        else:
            cols = np.ones((n_points, 3))

        cols = np.clip(cols, 0.0, 1.0)

        # Apply Gamma Correction if source is Linear
        if source_is_linear:
            cls.log("Applying Linear -> sRGB conversion...")
            cols = cls.linear_to_srgb(cols)
        else:
            cls.log("Source is sRGB. Skipping gamma correction.")

        # ---------------------------------------------------------
        # 4. 烘焙算法 (移植自 3dgs2quad.py)
        # ---------------------------------------------------------
        cls.log("Analyzing colors for Palette baking...")
        
        # 转为 Int 进行去重分析
        cols_u8 = (cols * 255.0).astype(np.int32)
        packed_colors = (cols_u8[:, 0] << 16) | (cols_u8[:, 1] << 8) | cols_u8[:, 2]
        unique_packed, inverse_indices = np.unique(packed_colors, return_inverse=True)
        unique_count = len(unique_packed)
        max_pixels = cls.PALETTE_SIZE * cls.PALETTE_SIZE
        
        final_palette_colors = None
        final_point_ranks = None

        if unique_count <= max_pixels:
            cls.log(f"Mode A: Lossless ({unique_count} colors)")
            u_r = (unique_packed >> 16) & 0xFF
            u_g = (unique_packed >> 8) & 0xFF
            u_b = unique_packed & 0xFF
            unique_rgb_float = np.stack((u_r, u_g, u_b), axis=1) / 255.0
            
            # Sort
            sort_list = []
            for i in range(unique_count):
                r, g, b = unique_rgb_float[i]
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                sort_list.append((h, s, v, i))
            sort_list.sort(key=lambda x: (x[0], x[1], x[2]))
            
            sorted_indices = [x[3] for x in sort_list]
            final_palette_colors = unique_rgb_float[sorted_indices]
            
            # Re-map indices
            rank_map = np.zeros(unique_count, dtype=np.int32)
            for rank, old_id in enumerate(sorted_indices):
                rank_map[old_id] = rank
            final_point_ranks = rank_map[inverse_indices]
            
        else:
            cls.log(f"Mode B: Grid Quantization ({unique_count} colors -> Grid)")
            q_level = cls.GRID_FALLBACK_LEVEL
            
            # 生成 LUT
            q_range = np.arange(q_level)
            R, G, B = np.meshgrid(q_range, q_range, q_range, indexing='ij')
            colors_flat = np.stack([R.flatten(), G.flatten(), B.flatten()], axis=1) / (q_level - 1)
            
            # Sort LUT
            lut_sort_list = []
            for i in range(len(colors_flat)):
                r, g, b = colors_flat[i]
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                lut_sort_list.append((h, s, v, i))
            lut_sort_list.sort(key=lambda x: (x[0], x[1], x[2]))
            
            sorted_lut_indices = [x[3] for x in lut_sort_list]
            final_palette_colors = colors_flat[sorted_lut_indices]
            
            # 3D Mapping
            original_to_rank = np.zeros(len(colors_flat), dtype=np.int32)
            for rank, old_id in enumerate(sorted_lut_indices):
                original_to_rank[old_id] = rank
            lut_3d_map = original_to_rank.reshape((q_level, q_level, q_level))
            
            # Map Points
            indices = (cols * (q_level - 0.0001)).astype(np.int32)
            final_point_ranks = lut_3d_map[indices[:, 0], indices[:, 1], indices[:, 2]]

        # ---------------------------------------------------------
        # 5. 创建 Blender 对象
        # ---------------------------------------------------------
        cls.log("Creating Mesh...")
        mesh = bpy.data.meshes.new(name="GS_Mesh")
        mesh.from_pydata(xyz.tolist(), [], [])
        mesh.update()
        
        # 写入 Attributes
        cls._write_attribute(mesh, "scale", 'FLOAT_VECTOR', scales)
        cls._write_attribute(mesh, "logscale", 'FLOAT_VECTOR', log_scales)
        cls._write_attribute(mesh, "rot_euler", 'FLOAT_VECTOR', rot_euler_data)
        
        cls._write_attribute(mesh, "quatxyz", 'FLOAT_VECTOR', quats[:, :3])
        cls._write_attribute(mesh, "quatw", 'FLOAT', quats[:, 3])
        
        cls._write_attribute(mesh, "opacity", 'FLOAT', opacities)
        cls._write_attribute(mesh, "log_opacity", 'FLOAT', log_opacities)
        
        # 计算并写入 Palette UV
        u_coords = ((final_point_ranks % cls.PALETTE_SIZE) + 0.5) / cls.PALETTE_SIZE
        v_coords = ((final_point_ranks // cls.PALETTE_SIZE) + 0.5) / cls.PALETTE_SIZE
        uv_data = np.stack((u_coords, v_coords), axis=1)
        uv_data_3d = np.zeros((n_points, 3), dtype=np.float32)
        uv_data_3d[:, :2] = uv_data
        cls._write_attribute(mesh, "palette_uv", 'FLOAT_VECTOR', uv_data_3d)

        # ---------------------------------------------------------
        # 6. 创建 Texture 和 Material
        # ---------------------------------------------------------
        obj_name = bpy.path.display_name_from_filepath(filepath)
        obj = bpy.data.objects.new(obj_name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # A. 创建 Texture
        tex_name = f"{obj.name}_Palette_Lut"
        if tex_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[tex_name])
            
        image = bpy.data.images.new(tex_name, cls.PALETTE_SIZE, cls.PALETTE_SIZE)
        
        pixels = np.zeros(cls.PALETTE_SIZE * cls.PALETTE_SIZE * 4, dtype=np.float32)
        pixels[3::4] = 1.0 # Alpha
        
        count = len(final_palette_colors)
        flat_colors = np.zeros(count * 4, dtype=np.float32)
        flat_colors[0::4] = final_palette_colors[:, 0]
        flat_colors[1::4] = final_palette_colors[:, 1]
        flat_colors[2::4] = final_palette_colors[:, 2]
        flat_colors[3::4] = 1.0
        
        pixels[:count*4] = flat_colors
        image.pixels.foreach_set(pixels)
        image.pack()
        
        # B. 创建并设置材质 (Shader Node Tree setup)
        # Create new material
        mat_name = f"GSmat_{obj.name}"
        new_mat = bpy.data.materials.new(name=mat_name)
        
        obj.data.materials.append(new_mat)
        
        # Prepare Images
        img_alpha = None
        img_normal = None
        
        # 2. Brush Alpha Texture
        if target_mat_name and target_mat_name != "NONE":
            alpha_path = os.path.join(AssetManager.get_brush_path("tex_alpha"), target_mat_name)
            if os.path.exists(alpha_path):
                # Load Image
                img_name = target_mat_name
                if img_name in bpy.data.images:
                    img_alpha = bpy.data.images[img_name]
                    if img_alpha.filepath != alpha_path:
                         try: img_alpha = bpy.data.images.load(alpha_path)
                         except: pass
                else:
                    try: img_alpha = bpy.data.images.load(alpha_path)
                    except: pass
        
        # 3. Normal Map
        # 3. Normal Map
        if target_mat_name and target_mat_name != "NONE":
            # Search logic
            normal_dir = AssetManager.get_brush_path("tex_normal")
            base_name = os.path.splitext(target_mat_name)[0] # e.g. "brush01"
            
            found_normal_path = None
            if os.path.exists(normal_dir):
                # User request: "same name (excluding format name)"
                valid_exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff')
                for f in os.listdir(normal_dir):
                    if f.startswith('.') or f.startswith('_'): continue
                    
                    f_name, f_ext = os.path.splitext(f)
                    if f_name == base_name and f.lower().endswith(valid_exts): 
                        found_normal_path = os.path.join(normal_dir, f)
                        break
            
            if found_normal_path:
                # Correctly handle loading to avoid mixing up with Alpha texture of same name
                # We cannot just look up by name because alpha and normal might both be "brush01.png"
                img_normal = None
                
                # 1. Try to find existing loaded image with exact path match
                norm_abspath = os.path.abspath(found_normal_path)
                for img in bpy.data.images:
                    if img.filepath:
                        if os.path.abspath(img.filepath) == norm_abspath:
                            img_normal = img
                            break
                
                # 2. If not found, load it
                if not img_normal:
                    try: 
                        img_normal = bpy.data.images.load(found_normal_path)
                    except Exception as e: 
                        cls.log(f"Failed to load normal map: {e}")
                
                if img_normal:
                    cls.log(f"Loaded Normal Map: {img_normal.name} (Source: tex_normal)")
            else:
                cls.log(f"No Normal Map found for {base_name} in tex_normal")

        # Call shader creation (from shader.py)
        try:
            create_shader(new_mat, palette_img=image, alpha_img=img_alpha, normal_img=img_normal)
        except Exception as e:
            cls.log(f"Error creating shader nodes: {e}")
            import traceback
            traceback.print_exc()

        # ---------------------------------------------------------
        # 7. Geometry Nodes Setup
        # ---------------------------------------------------------
        
        # Create Instance Object if mesh is selected
        instance_obj = None
        if template_mesh:
            instance_obj = bpy.data.objects.new(f"Inst_{obj_name}", template_mesh)
            # Link to scene but hide it? Or put in a special collection?
            # Putting it in current collection but hidden
            context.collection.objects.link(instance_obj)
            instance_obj.hide_viewport = True
            instance_obj.hide_render = True
        
        # Generate Fresh Node Tree
        gn_tree = create_gs_node_system()
        gn_tree.name = f"GS_Instancer_{obj_name}" # Rename to be unique
        
        mod = obj.modifiers.new("GS_Instancer", 'NODES')
        mod.node_group = gn_tree
        
        # Assign Inputs
        if instance_obj:
            try:
                # Find the socket identifier or name
                # GN inputs can be accessed by name if unique, but identifier is robust
                # We can iterate the interface
                for item in gn_tree.interface.items_tree:
                    if item.name == "instance" and item.bl_socket_idname == 'NodeSocketObject':
                         mod[item.identifier] = instance_obj
                    elif item.name == "Material" and item.bl_socket_idname == 'NodeSocketMaterial':
                         if new_mat:
                            mod[item.identifier] = new_mat
            except Exception as e:
                cls.log(f"Error setting GN inputs: {e}")
        else:
             cls.log("WARNING: No Instance Object to assign to GN!")

        # 旋转物体以修正坐标系 (Rotate object -90 on X)
        if y_up_to_z_up:
            obj.rotation_euler = (np.radians(-90), 0, 0)
        else:
            obj.rotation_euler = (0, 0, 0)
        
        cls.log(f"Done. {time.time()-start_time:.2f}s")
        return {'FINISHED'}

    @staticmethod
    def _write_attribute(mesh, name, type_enum, data):
        attr = mesh.attributes.new(name=name, type=type_enum, domain='POINT')
        if type_enum == 'FLOAT_VECTOR':
            attr.data.foreach_set('vector', data.flatten())
        elif type_enum == 'FLOAT':
            attr.data.foreach_set('value', data.flatten())

# ==============================================================================
#  OPERATOR & UI
# ==============================================================================

class GS_OT_Import(bpy.types.Operator):
    """Import 3DGS PLY and Bake Palette"""
    bl_idname = "gs_tools.import_ply"
    bl_label = "Import 3DGS & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        return GS_Processor.process_and_bake(context, self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class GS_OT_Export(bpy.types.Operator):
    """Open standard Export Menu"""
    bl_idname = "gs_tools.export_menu"
    bl_label = "Export Model..."
    
    def execute(self, context):
        bpy.ops.wm.call_menu(name="TOPBAR_MT_file_export")
        return {'FINISHED'}

class GS_PT_Panel(bpy.types.Panel):
    bl_label = "3DGS Palette Tools"
    bl_idname = "GS_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3DGS Oil Paint"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.label(text="Import & Bake", icon='IMPORT')
        
        row = box.row()
        row.label(text="Brush Texture:")
        # Debug Path in UI
        box.label(text=f"Scan: {AssetManager.get_brush_path('tex_alpha')}")
        box.template_icon_view(scene, "gs_target_material", show_labels=True, scale=3.0)
        
        box.prop(scene, "gs_target_mesh", text="Mesh")
        box.prop(scene, "gs_z_is_minimum", text="[Suggested] Z is Minimum") # Added checkbox
        box.prop(scene, "gs_y_up_to_z_up", text="Y-up to Z-up")
        box.prop(scene, "gs_source_is_linear", text="Source is Linear Color Space")
        box.operator(GS_OT_Import.bl_idname, text="Load .ply")
        
        box = layout.box()
        obj = context.active_object
        
        if obj and obj.modifiers.get("GS_Instancer"):
            box.label(text="Instancer Active", icon='CHECKMARK')
        else:
            box.label(text="Select object and edit modifier", icon='INFO')
            
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        box.operator(GS_OT_Export.bl_idname, text="Export...")

# ==============================================================================
#  REGISTRATION
# ==============================================================================

classes = (
    GS_OT_Import,
    GS_OT_Export,
    GS_PT_Panel,
)

def register():
    print("[GS_Tool] Registering...")
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
            
        # Ensure preview collection is ready
        if "main" not in preview_collections:
            print("[GS_Tool] Creating new preview collection 'main'")
            pcoll = bpy.utils.previews.new()
            pcoll.brush_dir = ""
            preview_collections["main"] = pcoll
        else:
             print("[GS_Tool] Preview collection 'main' already exists")

        bpy.types.Scene.gs_target_material = bpy.props.EnumProperty(
            name="Brush Texture",
            description="Select brush alpha texture",
            items=get_brush_textures_callback
        )
        bpy.types.Scene.gs_target_mesh = bpy.props.EnumProperty(
            name="Target Mesh",
            description="Select mesh from asset.blend for the splat instance",
            items=get_meshes_callback
        )
        bpy.types.Scene.gs_z_is_minimum = bpy.props.BoolProperty(
            name="Z is Minimum",
            description="Ensure Z scale is always the smallest dimension (axis swap)",
            default=True
        )
        bpy.types.Scene.gs_y_up_to_z_up = bpy.props.BoolProperty(
            name="Y-up to Z-up",
            description="Rotate object -90 degrees on X axis to convert Y-up to Z-up",
            default=True
        )
        bpy.types.Scene.gs_source_is_linear = bpy.props.BoolProperty(
            name="Source is Linear",
            description="If checked, source colors are treated as Linear and converted to sRGB for baking. If unchecked, source is assumed to be sRGB.",
            default=False
        )
        print("[GS_Tool] Registration complete.")
    except Exception as e:
        print(f"[GS_Tool] ERROR during registration: {e}")
        import traceback
        traceback.print_exc()

def unregister():
    print("[GS_Tool] Unregistering...")
    try:
        for cls in classes:
            bpy.utils.unregister_class(cls)
            
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()

        del bpy.types.Scene.gs_target_material
        del bpy.types.Scene.gs_target_mesh
        del bpy.types.Scene.gs_z_is_minimum
        del bpy.types.Scene.gs_y_up_to_z_up
        
        if hasattr(bpy.types.Scene, "gs_source_is_linear"):
            del bpy.types.Scene.gs_source_is_linear
        
        # Clean up old property if it exists (robustness)
        if hasattr(bpy.types.Scene, "gs_source_color_space"):
            del bpy.types.Scene.gs_source_color_space
            
    except Exception as e:
        print(f"[GS_Tool] ERROR during unregistration: {e}")

if __name__ == "__main__":
    register()