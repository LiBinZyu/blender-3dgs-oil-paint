import bpy
import typing

def create_shader(material: bpy.types.Material, palette_img=None, alpha_img=None, normal_img=None):
    """
    Configure the shader node tree for the given material using the provided images.
    """
    material.use_nodes = True
    
    # Material Settings
    material.use_backface_culling = False
    material.show_transparent_back = False
    material.specular_intensity = 0.0 # Remove basic specular
    material.roughness = 0.4000000059604645

    # Blender 4.2+ Eevee Next changes
    if bpy.app.version < (4, 2, 0):
        material.blend_method = 'HASHED'
    else:
        # For Eevee Next / Cycles
        # Alpha Hashed is roughly equivalent to dithered transparency or just standard transparency
        material.blend_method = 'HASHED' 

    # Get node tree
    nt = material.node_tree
    nodes = nt.nodes
    links = nt.links
    
    # Clear existing nodes
    nodes.clear()

    # Node Material Output
    material_output = nodes.new("ShaderNodeOutputMaterial")
    material_output.name = "Material Output"
    material_output.is_active_output = True
    material_output.target = 'ALL'
    material_output.location = (200.0, 100.0)

    # Node Principled BSDF
    principled_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf.name = "Principled BSDF"
    principled_bsdf.location = (-220.6577606201172, 88.90316772460938)
    
    # Set BSDF Defaults safely
    # We only care about Base Color and Alpha. 
    # Rely on Blender defaults for other channels to avoid API breakage.
    pass 

    # 1. Palette Texture (Base Color) -> Image Texture
    # Driven by ColUV (UV Map.001)
    uv_map_palette = nodes.new("ShaderNodeUVMap")
    uv_map_palette.name = "UV Map.001"
    uv_map_palette.uv_map = "ColUV"
    uv_map_palette.location = (-1337.7823486328125, -268.6052551269531)

    tex_palette = nodes.new("ShaderNodeTexImage")
    tex_palette.name = "Image Texture"
    tex_palette.interpolation = 'Closest' # Important for palette
    tex_palette.projection = 'FLAT'
    tex_palette.extension = 'CLIP'
    tex_palette.location = (-1072.0728759765625, -81.77071380615234)
    
    if palette_img:
        tex_palette.image = palette_img

    # 2. Brush Alpha Texture (Alpha) -> Image Texture.002
    # Driven by UVMap (UV Map)
    uv_map_brush = nodes.new("ShaderNodeUVMap")
    uv_map_brush.name = "UV Map"
    uv_map_brush.uv_map = "UVMap" # Standard UV
    uv_map_brush.location = (-1346.5804443359375, 129.12290954589844)

    tex_alpha = nodes.new("ShaderNodeTexImage")
    tex_alpha.name = "Image Texture.002"
    tex_alpha.interpolation = 'Linear'
    tex_alpha.projection = 'FLAT'
    tex_alpha.extension = 'CLIP'
    tex_alpha.location = (-1068.1881103515625, 301.674072265625)
    
    if alpha_img:
        tex_alpha.image = alpha_img
    
    # Math Node for Alpha Multiplier (opacity attribute * texture alpha)
    # The snippet used simple mix or multiply? Snippet: Math.004 (Multiply)
    # Inputs: Attribute(opacity) and Image Texture.002(Color or Alpha?)
    # Usually we want brush alpha * particle opacity
    
    node_attr_opacity = nodes.new("ShaderNodeAttribute")
    node_attr_opacity.name = "Attribute"
    node_attr_opacity.attribute_name = "opacity"
    node_attr_opacity.attribute_type = 'GEOMETRY'
    node_attr_opacity.location = (-1045.623046875, 636.3995971679688)

    math_multiply = nodes.new("ShaderNodeMath")
    math_multiply.name = "Math.004"
    math_multiply.operation = 'MULTIPLY'
    math_multiply.location = (-618.5953369140625, 421.45977783203125)

    # 3. Normal Map -> Image Texture.003 + Normal Map Node
    # Driven by UVMap (same as brush)
    if normal_img:
        tex_normal = nodes.new("ShaderNodeTexImage")
        tex_normal.name = "Image Texture.003"
        tex_normal.image = normal_img
        # Ensure Non-Color
        if normal_img.colorspace_settings.name != 'Non-Color':
             try:
                normal_img.colorspace_settings.name = 'Non-Color'
             except:
                pass
        tex_normal.interpolation = 'Linear'
        tex_normal.extension = 'CLIP'
        tex_normal.location = (-1100.0, -440.0)

        node_normal_map = nodes.new("ShaderNodeNormalMap")
        node_normal_map.name = "Normal Map"
        node_normal_map.space = 'TANGENT'
        node_normal_map.uv_map = "UVMap"
        node_normal_map.inputs[0].default_value = 1.0 # Strength
        node_normal_map.location = (-800.0, -420.0)

        # Links for Normal
        # Use existing UV Map Brush
        links.new(uv_map_brush.outputs[0], tex_normal.inputs[0])
        links.new(tex_normal.outputs[0], node_normal_map.inputs[1])
        links.new(node_normal_map.outputs[0], principled_bsdf.inputs['Normal'])

    # Links for Palette (Base Color)
    links.new(uv_map_palette.outputs[0], tex_palette.inputs[0])
    links.new(tex_palette.outputs[0], principled_bsdf.inputs['Base Color'])
    # Optional: Emission?
    # links.new(tex_palette.outputs[0], principled_bsdf.inputs['Emission Color'])

    # Links for Alpha
    links.new(uv_map_brush.outputs[0], tex_alpha.inputs[0])
    
    # Multiply: Opacity Attribute (Fac) * Brush Texture (Color or Alpha?)
    # Generally alpha texture is grayscale in RGB or Alpha channel.
    # If using RGB image as alpha mask:
    links.new(node_attr_opacity.outputs[2], math_multiply.inputs[0]) # Fac
    links.new(tex_alpha.outputs[0], math_multiply.inputs[1]) # Color
    
    # Result to BSDF Alpha
    links.new(math_multiply.outputs[0], principled_bsdf.inputs['Alpha'])

    # Final Output
    links.new(principled_bsdf.outputs[0], material_output.inputs[0])

    return nodes