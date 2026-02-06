import bpy
import numpy as np
import colorsys
import time
import sys

# --- 配置 ---
PALETTE_SIZE = 256
TEXTURE_NAME = "Gaussian_Palette_Lut"
UV_ATTR_NAME = "palette_uv"
GEO_NODES_NAME = "GS_Instancer_Lut"

# 256*256 = 65536 像素。
# 40^3 = 64000。这是网格法的物理极限。
GRID_FALLBACK_LEVEL = 40 

def log(msg):
    print(f"[GS_Tool] {msg}")
    sys.stdout.flush()

def main():
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        log("错误: 请选中一个 Mesh 对象")
        return

    mesh = obj.data
    n_points = len(mesh.vertices)
    log(f"目标模型: {obj.name}, 点数: {n_points}")
    
    # 屏蔽修改器以加速
    original_mod_states = {}
    for mod in obj.modifiers:
        original_mod_states[mod.name] = mod.show_viewport
        mod.show_viewport = False
    
    start_t = time.time()

    # ---------------------------------------------------------
    # 1. 读取原始数据
    # ---------------------------------------------------------
    log("1. 读取点云颜色数据...")
    cols = np.zeros(n_points * 4, dtype=np.float32)
    
    if "Col" in mesh.attributes:
        mesh.attributes['Col'].data.foreach_get('color', cols)
        cols = cols.reshape((-1, 4))[:, :3] 
    elif "f_dc_0" in mesh.attributes:
        log("  - 从球谐系数转换颜色...")
        fdc0 = np.zeros(n_points, dtype=np.float32)
        fdc1 = np.zeros(n_points, dtype=np.float32)
        fdc2 = np.zeros(n_points, dtype=np.float32)
        mesh.attributes['f_dc_0'].data.foreach_get('value', fdc0)
        mesh.attributes['f_dc_1'].data.foreach_get('value', fdc1)
        mesh.attributes['f_dc_2'].data.foreach_get('value', fdc2)
        
        SH_C0 = 0.28209479177387814
        r = fdc0 * SH_C0 + 0.5
        g = fdc1 * SH_C0 + 0.5
        b = fdc2 * SH_C0 + 0.5
        cols = np.stack((r, g, b), axis=1)
    
    cols = np.clip(cols, 0.0, 1.0)

    # ---------------------------------------------------------
    # 2. 尝试无损精确匹配 (Exact Match Mode)
    # ---------------------------------------------------------
    log("2. 分析颜色构成 (尝试无损模式)...")
    
    # 将浮点颜色转为 8-bit 整数 (0-255)
    cols_u8 = (cols * 255.0).astype(np.int32)
    
    # 位压缩: 将 RGB 三个通道压入一个 Int32，极大加速去重
    # R<<16 | G<<8 | B
    packed_colors = (cols_u8[:, 0] << 16) | (cols_u8[:, 1] << 8) | cols_u8[:, 2]
    
    # 获取所有不重复的颜色及其反向索引
    # inverse_indices 直接告诉我们每个点对应 unique_packed 中的哪一个
    unique_packed, inverse_indices = np.unique(packed_colors, return_inverse=True)
    
    unique_count = len(unique_packed)
    max_pixels = PALETTE_SIZE * PALETTE_SIZE
    
    log(f"  - 发现 {unique_count} 种独特颜色 (贴图容量: {max_pixels})")

    # ---------------------------------------------------------
    # 3. 分支判断：使用 无损模式 还是 网格模式
    # ---------------------------------------------------------
    final_palette_colors = None # 存储最终贴图用的 RGB (Nx3 float)
    final_point_ranks = None    # 存储每个点对应贴图的第几个像素 (N int)

    if unique_count <= max_pixels:
        log(">>> [模式A: 无损] 颜色数量在范围内，使用精确颜色。")
        
        # 解压回 float RGB 用于排序
        u_r = (unique_packed >> 16) & 0xFF
        u_g = (unique_packed >> 8) & 0xFF
        u_b = unique_packed & 0xFF
        unique_rgb_float = np.stack((u_r, u_g, u_b), axis=1) / 255.0
        
        # --- 排序 (Hue Sort) ---
        log("  - 正在按色相排序...")
        # 构造列表进行排序: (Hue, Sat, Val, Original_Index)
        sort_list = []
        for i in range(unique_count):
            r, g, b = unique_rgb_float[i]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            sort_list.append((h, s, v, i))
        
        sort_list.sort(key=lambda x: (x[0], x[1], x[2]))
        
        # 提取排序后的颜色
        sorted_indices = [x[3] for x in sort_list] # 此时 sorted_indices[rank] = old_unique_id
        final_palette_colors = unique_rgb_float[sorted_indices]
        
        # --- 重映射索引 ---
        # 目前 inverse_indices 指向的是 old_unique_id
        # 我们需要它指向 new_rank
        # 建立映射表: map[old_unique_id] = new_rank
        rank_map = np.zeros(unique_count, dtype=np.int32)
        for rank, old_id in enumerate(sorted_indices):
            rank_map[old_id] = rank
            
        # 转换所有点的索引
        final_point_ranks = rank_map[inverse_indices]
        
    else:
        log(f">>> [模式B: 高密网格] 颜色溢出，切换到 {GRID_FALLBACK_LEVEL}阶 高密度网格拟合...")
        
        # 使用 40x40x40 网格 (64000色)
        # 这比 32x32x32 (32768色) 精度高一倍，且刚好塞进贴图
        
        # 1. 生成 LUT 颜色表
        q_level = GRID_FALLBACK_LEVEL
        q_range = np.arange(q_level)
        R_grid, G_grid, B_grid = np.meshgrid(q_range, q_range, q_range, indexing='ij')
        
        # 展平
        colors_flat_int = np.stack([R_grid.flatten(), G_grid.flatten(), B_grid.flatten()], axis=1)
        colors_flat_float = colors_flat_int / (q_level - 1) # 0.0 - 1.0
        
        total_lut_colors = len(colors_flat_float) # 64000
        
        # 2. 对 LUT 进行 Hue 排序
        log("  - 构建并排序 LUT...")
        lut_sort_list = []
        for i in range(total_lut_colors):
            r, g, b = colors_flat_float[i]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            lut_sort_list.append((h, s, v, i))
        
        lut_sort_list.sort(key=lambda x: (x[0], x[1], x[2]))
        
        sorted_lut_indices = [x[3] for x in lut_sort_list]
        final_palette_colors = colors_flat_float[sorted_lut_indices]
        
        # 3. 构建 3D 查找表 (Grid -> Rank)
        # 输入: r_idx, g_idx, b_idx -> 输出: Rank in Palette
        lut_3d_map = np.zeros((q_level, q_level, q_level), dtype=np.int32)
        
        original_to_rank = np.zeros(total_lut_colors, dtype=np.int32)
        for rank, old_id in enumerate(sorted_lut_indices):
            original_to_rank[old_id] = rank
            
        lut_3d_map = original_to_rank.reshape((q_level, q_level, q_level))
        
        # 4. 查表计算所有点的 Rank
        log("  - 查表映射百万点云...")
        # 量化原始数据到 0..39
        indices = (cols * (q_level - 0.0001)).astype(np.int32)
        # Fancy Indexing 极速查表
        final_point_ranks = lut_3d_map[indices[:, 0], indices[:, 1], indices[:, 2]]

    # ---------------------------------------------------------
    # 4. 生成贴图 & UV
    # ---------------------------------------------------------
    log("4. 写入纹理与UV...")
    
    # A. 写入图片
    if TEXTURE_NAME in bpy.data.images:
        old_image = bpy.data.images[TEXTURE_NAME]
        # 如果图片已经被创建了，但尺寸不对或者数据坏了，直接移除重建是最安全的
        bpy.data.images.remove(old_image)
        
    # 创建全新的图片
    image = bpy.data.images.new(TEXTURE_NAME, PALETTE_SIZE, PALETTE_SIZE)
    # --- 修改结束 ---

    # 把最终调色板颜色从线性空间转换到 sRGB 空间
    srgb_colors = linear_to_srgb(final_palette_colors)
    
    pixels = np.zeros(PALETTE_SIZE * PALETTE_SIZE * 4, dtype=np.float32)
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
    
    # B. 计算 UV
    # UV指向像素中心
    u_coords = ((final_point_ranks % PALETTE_SIZE) + 0.5) / PALETTE_SIZE
    v_coords = ((final_point_ranks // PALETTE_SIZE) + 0.5) / PALETTE_SIZE
    
    uv_data = np.zeros(n_points * 3, dtype=np.float32)
    uv_data[0::3] = u_coords
    uv_data[1::3] = v_coords
    
    if UV_ATTR_NAME not in mesh.attributes:
        mesh.attributes.new(name=UV_ATTR_NAME, type='FLOAT_VECTOR', domain='POINT')
    mesh.attributes[UV_ATTR_NAME].data.foreach_set('vector', uv_data)
    
    # 恢复状态
    for mod_name, state in original_mod_states.items():
        if mod_name in obj.modifiers:
            obj.modifiers[mod_name].show_viewport = state

    log(f"完成! 耗时: {time.time() - start_t:.2f}s")
    ensure_geo_nodes(obj)

def ensure_geo_nodes(obj):
    mod = obj.modifiers.get("GS_Nodes")
    if not mod:
        mod = obj.modifiers.new("GS_Nodes", 'NODES')
    
    node_group = bpy.data.node_groups.get(GEO_NODES_NAME)
    if not node_group:
        node_group = bpy.data.node_groups.new(GEO_NODES_NAME, 'GeometryNodeTree')
    mod.node_group = node_group
    
def linear_to_srgb(linear):
    # linear, numpy array, 0..1
    a = 0.055
    srgb = np.where(
        linear <= 0.0031308,
        linear * 12.92,
        (1.0 + a) * np.power(linear, 1.0 / 2.4) - a
    )
    return np.clip(srgb, 0.0, 1.0)

if __name__ == "__main__":
    main()