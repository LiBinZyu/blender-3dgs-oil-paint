import bpy
import numpy as np
import colorsys
import time
import sys
import struct
import mathutils

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

class GS_Processor:
    PALETTE_SIZE = 256
    GRID_FALLBACK_LEVEL = 40  # 40^3 = 64000 points
    
    # 预设资源名称 (必须在 .blend 文件中存在)
    TEMPLATE_MAT_NAME = "GSmat_brush1"
    TEMPLATE_GN_NAME = "GS_Instancer_Lut"

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
        start_time = time.time()
        
        # 1. 读取 PLY
        cls.log(f"Loading: {filepath}")
        ply_data, n_points = read_ply_data(filepath)
        
        # 2. 提取并处理基础数据 (NumPy Vectorization)
        # Position
        xyz = np.stack((ply_data['x'], ply_data['y'], ply_data['z']), axis=1)
        
        # Opacity (Sigmoid)
        if 'opacity' in ply_data.dtype.names:
            opacities = 1 / (1 + np.exp(-ply_data['opacity']))
        else:
            opacities = np.ones(n_points)

        # Scale (Exp)
        # 注意: ply 中通常是 scale_0, scale_1, scale_2
        scale_names = [n for n in ply_data.dtype.names if n.startswith('scale')]
        if len(scale_names) >= 3:
            s_raw = np.stack([ply_data[n] for n in scale_names[:3]], axis=1)
            scales = np.exp(s_raw)
        else:
            scales = np.ones((n_points, 3)) * 0.01

        # Rotation (Quaternion -> Euler)
        # 注意: Blender Quaternion is (W, X, Y, Z), 3DGS is usually (W, X, Y, Z) or (X, Y, Z, W) depending on training
        # Standard Inria 3DGS is (W, X, Y, Z) (Real part first)
        rot_names = [n for n in ply_data.dtype.names if n.startswith('rot')]
        rot_euler_data = np.zeros((n_points, 3), dtype=np.float32)
        
        if len(rot_names) >= 4:
            quats = np.stack([ply_data[n] for n in rot_names[:4]], axis=1)
            
            # 批量归一化
            norms = np.linalg.norm(quats, axis=1, keepdims=True)
            quats /= (norms + 1e-8) # 避免除零
            
            # 为了速度，这里我们依然要在 Python 循环里转 Euler，
            # 虽然慢一点，但比 Geometry Nodes 算要稳定得多
            # 如果想极致优化，可以用 scipy.spatial.transform.Rotation，但尽量不引入 scipy 依赖
            for i in range(n_points):
                # mathutils 顺序: w, x, y, z
                q = mathutils.Quaternion(quats[i]) 
                e = q.to_euler()
                rot_euler_data[i] = (e.x, e.y, e.z)

        # 3. 颜色处理 (SH -> RGB)
        # 简化版：只取 SH 的 DC 分量 (0阶球谐)
        if 'f_dc_0' in ply_data.dtype.names:
            SH_C0 = 0.28209479177387814
            r = ply_data['f_dc_0'] * SH_C0 + 0.5
            g = ply_data['f_dc_1'] * SH_C0 + 0.5
            b = ply_data['f_dc_2'] * SH_C0 + 0.5
            cols = np.stack((r, g, b), axis=1)
        elif 'red' in ply_data.dtype.names: # 某些变体直接存颜色
            cols = np.stack((ply_data['red'], ply_data['green'], ply_data['blue']), axis=1) / 255.0
        else:
            cols = np.ones((n_points, 3))

        cols = np.clip(cols, 0.0, 1.0)

        # ---------------------------------------------------------
        # 4. 烘焙算法 (移植自你的代码)
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
        cls._write_attribute(mesh, "rot_euler", 'FLOAT_VECTOR', rot_euler_data)
        cls._write_attribute(mesh, "opacity", 'FLOAT', opacities)
        
        # 计算并写入 Palette UV
        u_coords = ((final_point_ranks % cls.PALETTE_SIZE) + 0.5) / cls.PALETTE_SIZE
        v_coords = ((final_point_ranks // cls.PALETTE_SIZE) + 0.5) / cls.PALETTE_SIZE
        uv_data = np.stack((u_coords, v_coords), axis=1)
        # Pad to 3D vector for FLOAT_VECTOR attribute (Blender prefers 3D for vectors usually, but UV can be 2D. 
        # However, to be safe with standard vector nodes, we often use 3D with Z=0)
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
        
        # Generate pixels
        pixels = np.ones(cls.PALETTE_SIZE * cls.PALETTE_SIZE * 4, dtype=np.float32)
        srgb_cols = cls.linear_to_srgb(final_palette_colors)
        
        count = len(srgb_cols)
        # Construct flat array [R, G, B, A, R, G, B, A...]
        # Assign RGB
        flat_rgb = srgb_cols.flatten() # [r0, g0, b0, r1, g1, b1...]
        
        # Slow python loop assignment is too slow for 65k pixels? 
        # NumPy trickery for RGBA interleaving:
        rgba_buffer = np.zeros((count, 4), dtype=np.float32)
        rgba_buffer[:, :3] = srgb_cols
        rgba_buffer[:, 3] = 1.0
        
        pixels[:count*4] = rgba_buffer.flatten()
        image.pixels.foreach_set(pixels)
        image.pack()
        
        # B. 复制并设置材质
        if cls.TEMPLATE_MAT_NAME in bpy.data.materials:
            template_mat = bpy.data.materials[cls.TEMPLATE_MAT_NAME]
            new_mat = template_mat.copy()
            new_mat.name = f"GSmat_{obj.name}"
            obj.data.materials.append(new_mat)
            
            # Find Image Node and replace
            found_node = False
            if new_mat.use_nodes:
                for node in new_mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        node.image = image
                        found_node = True
                        break
            if not found_node:
                cls.log("WARNING: Could not find an Image Texture node in the material to assign the Palette!")
        else:
            cls.log(f"ERROR: Template Material '{cls.TEMPLATE_MAT_NAME}' not found in file!")

        # ---------------------------------------------------------
        # 7. Geometry Nodes Setup
        # ---------------------------------------------------------
        if cls.TEMPLATE_GN_NAME in bpy.data.node_groups:
            mod = obj.modifiers.new("GS_Instancer", 'NODES')
            mod.node_group = bpy.data.node_groups[cls.TEMPLATE_GN_NAME]
        else:
            cls.log(f"ERROR: Template Geometry Node '{cls.TEMPLATE_GN_NAME}' not found!")

        # 旋转物体以修正坐标系 (Rotate object -90 on X)
        obj.rotation_euler = (np.radians(-90), 0, 0)
        
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
        # 这是一个小 trick，直接调用 Blender 的通用导出菜单
        # 或者直接调用最常用的 GLTF 导出
        bpy.ops.wm.call_menu(name="TOPBAR_MT_file_export")
        return {'FINISHED'}

class GS_PT_Panel(bpy.types.Panel):
    bl_label = "3DGS Palette Tools"
    bl_idname = "GS_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GS Tools"

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="1. Import & Bake", icon='IMPORT')
        box.operator(GS_OT_Import.bl_idname, text="Load .ply")
        
        box = layout.box()
        box.label(text="2. Settings", icon='MODIFIER')
        obj = context.active_object
        
        # 如果选中了带有 GN 修改器的物体，显示一些快捷操作
        if obj and obj.modifiers.get("GS_Instancer"):
            mod = obj.modifiers["GS_Instancer"]
            # 这里假设 GN 有一些对外暴露的 Input
            # 用户可以在这里不用进修改器面板就能改
            # layout.prop(mod, "show_viewport", text="Show Splats")
            pass
        else:
            box.label(text="Select imported object", icon='INFO')
            
        box = layout.box()
        box.label(text="3. Export", icon='EXPORT')
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
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()