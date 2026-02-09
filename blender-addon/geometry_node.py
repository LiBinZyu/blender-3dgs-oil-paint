import bpy
import mathutils
import os
import typing


def correctrot_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize correctRot node group"""
    correctrot_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="correctRot")

    correctrot_1.color_tag = 'NONE'
    correctrot_1.description = ""
    correctrot_1.default_group_node_width = 140

    # correctrot_1 interface

    # Socket rot
    rot_socket = correctrot_1.interface.new_socket(name="rot", in_out='OUTPUT', socket_type='NodeSocketRotation')
    rot_socket.default_value = (0.0, 0.0, 0.0)
    rot_socket.attribute_domain = 'POINT'
    rot_socket.default_input = 'VALUE'
    rot_socket.structure_type = 'AUTO'

    # Socket correctedRot
    correctedrot_socket = correctrot_1.interface.new_socket(name="correctedRot", in_out='OUTPUT', socket_type='NodeSocketRotation')
    correctedrot_socket.default_value = (0.0, 0.0, 0.0)
    correctedrot_socket.attribute_domain = 'POINT'
    correctedrot_socket.default_input = 'VALUE'
    correctedrot_socket.structure_type = 'AUTO'

    # Socket rot_eular
    rot_eular_socket = correctrot_1.interface.new_socket(name="rot_eular", in_out='INPUT', socket_type='NodeSocketVector')
    rot_eular_socket.default_value = (0.0, 0.0, 0.0)
    rot_eular_socket.min_value = -3.4028234663852886e+38
    rot_eular_socket.max_value = 3.4028234663852886e+38
    rot_eular_socket.subtype = 'NONE'
    rot_eular_socket.attribute_domain = 'POINT'
    rot_eular_socket.default_input = 'VALUE'
    rot_eular_socket.structure_type = 'AUTO'

    # Socket enable_lookat
    enable_lookat_socket = correctrot_1.interface.new_socket(name="enable_lookat", in_out='INPUT', socket_type='NodeSocketBool')
    enable_lookat_socket.default_value = False
    enable_lookat_socket.attribute_domain = 'POINT'
    enable_lookat_socket.default_input = 'VALUE'
    enable_lookat_socket.structure_type = 'AUTO'

    # Socket look_at_target
    look_at_target_socket = correctrot_1.interface.new_socket(name="look_at_target", in_out='INPUT', socket_type='NodeSocketCollection')
    look_at_target_socket.attribute_domain = 'POINT'
    look_at_target_socket.default_input = 'VALUE'
    look_at_target_socket.structure_type = 'AUTO'

    # Socket look_at_range
    look_at_range_socket = correctrot_1.interface.new_socket(name="look_at_range", in_out='INPUT', socket_type='NodeSocketFloat')
    look_at_range_socket.default_value = 30.0
    look_at_range_socket.min_value = -10000.0
    look_at_range_socket.max_value = 10000.0
    look_at_range_socket.subtype = 'NONE'
    look_at_range_socket.attribute_domain = 'POINT'
    look_at_range_socket.default_input = 'VALUE'
    look_at_range_socket.structure_type = 'AUTO'

    # Socket look_at_intensity
    look_at_intensity_socket = correctrot_1.interface.new_socket(name="look_at_intensity", in_out='INPUT', socket_type='NodeSocketFloat')
    look_at_intensity_socket.default_value = 0.10000000149011612
    look_at_intensity_socket.min_value = -10000.0
    look_at_intensity_socket.max_value = 10000.0
    look_at_intensity_socket.subtype = 'NONE'
    look_at_intensity_socket.attribute_domain = 'POINT'
    look_at_intensity_socket.default_input = 'VALUE'
    look_at_intensity_socket.structure_type = 'AUTO'

    # Socket rotation_randomize_intensity
    rotation_randomize_intensity_socket = correctrot_1.interface.new_socket(name="rotation_randomize_intensity", in_out='INPUT', socket_type='NodeSocketFloat')
    rotation_randomize_intensity_socket.default_value = 0.10000000149011612
    rotation_randomize_intensity_socket.min_value = -10000.0
    rotation_randomize_intensity_socket.max_value = 10000.0
    rotation_randomize_intensity_socket.subtype = 'NONE'
    rotation_randomize_intensity_socket.attribute_domain = 'POINT'
    rotation_randomize_intensity_socket.default_input = 'VALUE'
    rotation_randomize_intensity_socket.structure_type = 'AUTO'

    # Initialize correctrot_1 nodes

    # Node Group Input
    group_input = correctrot_1.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Node Group Output
    group_output = correctrot_1.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # Node Position.001
    position_001 = correctrot_1.nodes.new("GeometryNodeInputPosition")
    position_001.name = "Position.001"

    # Node Collection Info.001
    collection_info_001 = correctrot_1.nodes.new("GeometryNodeCollectionInfo")
    collection_info_001.name = "Collection Info.001"
    collection_info_001.transform_space = 'RELATIVE'
    # Separate Children
    collection_info_001.inputs[1].default_value = True
    # Reset Children
    collection_info_001.inputs[2].default_value = False

    # Node Realize Instances.001
    realize_instances_001 = correctrot_1.nodes.new("GeometryNodeRealizeInstances")
    realize_instances_001.name = "Realize Instances.001"
    # Selection
    realize_instances_001.inputs[1].default_value = True
    # Realize All
    realize_instances_001.inputs[2].default_value = True
    # Depth
    realize_instances_001.inputs[3].default_value = 0

    # Node Geometry Proximity
    geometry_proximity = correctrot_1.nodes.new("GeometryNodeProximity")
    geometry_proximity.name = "Geometry Proximity"
    geometry_proximity.target_element = 'FACES'
    # Group ID
    geometry_proximity.inputs[1].default_value = 0
    # Sample Group ID
    geometry_proximity.inputs[3].default_value = 0

    # Node Vector Math.002
    vector_math_002 = correctrot_1.nodes.new("ShaderNodeVectorMath")
    vector_math_002.label = "Direction Vector"
    vector_math_002.name = "Vector Math.002"
    vector_math_002.operation = 'SUBTRACT'

    # Node Vector Math.003
    vector_math_003 = correctrot_1.nodes.new("ShaderNodeVectorMath")
    vector_math_003.name = "Vector Math.003"
    vector_math_003.operation = 'DISTANCE'

    # Node Map Range
    map_range = correctrot_1.nodes.new("ShaderNodeMapRange")
    map_range.name = "Map Range"
    map_range.clamp = True
    map_range.data_type = 'FLOAT'
    map_range.interpolation_type = 'SMOOTHSTEP'
    # From Min
    map_range.inputs[1].default_value = 0.0
    # To Min
    map_range.inputs[3].default_value = 1.0
    # To Max
    map_range.inputs[4].default_value = 0.0

    # Node Math.002
    math_002 = correctrot_1.nodes.new("ShaderNodeMath")
    math_002.label = "Apply Intensity"
    math_002.name = "Math.002"
    math_002.operation = 'MULTIPLY'
    math_002.use_clamp = False

    # Node Math.003
    math_003 = correctrot_1.nodes.new("ShaderNodeMath")
    math_003.label = "Master Switch"
    math_003.name = "Math.003"
    math_003.operation = 'MULTIPLY'
    math_003.use_clamp = False

    # Node Align Rotation to Vector.001
    align_rotation_to_vector_001 = correctrot_1.nodes.new("FunctionNodeAlignRotationToVector")
    align_rotation_to_vector_001.name = "Align Rotation to Vector.001"
    align_rotation_to_vector_001.axis = 'Z'
    align_rotation_to_vector_001.pivot_axis = 'AUTO'

    # Node Random Value.001
    random_value_001 = correctrot_1.nodes.new("FunctionNodeRandomValue")
    random_value_001.name = "Random Value.001"
    random_value_001.data_type = 'FLOAT_VECTOR'
    # Min
    random_value_001.inputs[0].default_value = (-0.5, -0.5, -0.5)
    # Max
    random_value_001.inputs[1].default_value = (0.5, 0.5, 0.5)
    # ID
    random_value_001.inputs[7].default_value = 0
    # Seed
    random_value_001.inputs[8].default_value = 0

    # Node Vector Math.004
    vector_math_004 = correctrot_1.nodes.new("ShaderNodeVectorMath")
    vector_math_004.name = "Vector Math.004"
    vector_math_004.operation = 'SCALE'

    # Node Vector Math.005
    vector_math_005 = correctrot_1.nodes.new("ShaderNodeVectorMath")
    vector_math_005.label = "Add Random Jitter"
    vector_math_005.name = "Vector Math.005"
    vector_math_005.operation = 'ADD'

    # Node Domain Size
    domain_size = correctrot_1.nodes.new("GeometryNodeAttributeDomainSize")
    domain_size.name = "Domain Size"
    domain_size.component = 'INSTANCES'

    # Node Compare
    compare = correctrot_1.nodes.new("FunctionNodeCompare")
    compare.name = "Compare"
    compare.data_type = 'INT'
    compare.mode = 'ELEMENT'
    compare.operation = 'GREATER_THAN'
    # B_INT
    compare.inputs[3].default_value = 0

    # Node Boolean Math
    boolean_math = correctrot_1.nodes.new("FunctionNodeBooleanMath")
    boolean_math.name = "Boolean Math"
    boolean_math.operation = 'AND'

    # Node Frame
    frame = correctrot_1.nodes.new("NodeFrame")
    frame.label = "toggle collection influence"
    frame.name = "Frame"
    frame.label_size = 20
    frame.shrink = True

    # Node Frame.001
    frame_001 = correctrot_1.nodes.new("NodeFrame")
    frame_001.label = "randomize"
    frame_001.name = "Frame.001"
    frame_001.label_size = 20
    frame_001.shrink = True

    # Node Euler to Rotation
    euler_to_rotation = correctrot_1.nodes.new("FunctionNodeEulerToRotation")
    euler_to_rotation.name = "Euler to Rotation"

    # Set parents
    correctrot_1.nodes["Math.003"].parent = correctrot_1.nodes["Frame"]
    correctrot_1.nodes["Random Value.001"].parent = correctrot_1.nodes["Frame.001"]
    correctrot_1.nodes["Vector Math.004"].parent = correctrot_1.nodes["Frame.001"]
    correctrot_1.nodes["Domain Size"].parent = correctrot_1.nodes["Frame"]
    correctrot_1.nodes["Compare"].parent = correctrot_1.nodes["Frame"]
    correctrot_1.nodes["Boolean Math"].parent = correctrot_1.nodes["Frame"]

    # Set locations
    correctrot_1.nodes["Group Input"].location = (-1563.3389892578125, 814.1387939453125)
    correctrot_1.nodes["Group Output"].location = (842.268310546875, 885.2894897460938)
    correctrot_1.nodes["Position.001"].location = (-1143.3389892578125, 514.1387939453125)
    correctrot_1.nodes["Collection Info.001"].location = (-1143.3389892578125, 314.1387939453125)
    correctrot_1.nodes["Realize Instances.001"].location = (-983.3390502929688, 294.1387939453125)
    correctrot_1.nodes["Geometry Proximity"].location = (-783.3390502929688, 374.1387939453125)
    correctrot_1.nodes["Vector Math.002"].location = (-523.3390502929688, 554.1387939453125)
    correctrot_1.nodes["Vector Math.003"].location = (-543.3390502929688, 254.1387939453125)
    correctrot_1.nodes["Map Range"].location = (-343.3390197753906, 334.1387939453125)
    correctrot_1.nodes["Math.002"].location = (-160.0, 340.0)
    correctrot_1.nodes["Math.003"].location = (749.0, -35.79999542236328)
    correctrot_1.nodes["Align Rotation to Vector.001"].location = (220.0, 820.0)
    correctrot_1.nodes["Random Value.001"].location = (29.0, -75.79998779296875)
    correctrot_1.nodes["Vector Math.004"].location = (189.0, -35.79998779296875)
    correctrot_1.nodes["Vector Math.005"].location = (596.6609497070312, 814.1387939453125)
    correctrot_1.nodes["Domain Size"].location = (29.0, -135.79998779296875)
    correctrot_1.nodes["Compare"].location = (189.0, -135.79998779296875)
    correctrot_1.nodes["Boolean Math"].location = (449.0, -75.79999542236328)
    correctrot_1.nodes["Frame"].location = (-709.0, 95.79999542236328)
    correctrot_1.nodes["Frame.001"].location = (231.0, 635.7999877929688)
    correctrot_1.nodes["Euler to Rotation"].location = (-1132.3309326171875, 820.7578125)

    # Initialize correctrot_1 links

    # position_001.Position -> geometry_proximity.Sample Position
    correctrot_1.links.new(
        correctrot_1.nodes["Position.001"].outputs[0],
        correctrot_1.nodes["Geometry Proximity"].inputs[2]
    )
    # geometry_proximity.Position -> vector_math_002.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Geometry Proximity"].outputs[0],
        correctrot_1.nodes["Vector Math.002"].inputs[0]
    )
    # position_001.Position -> vector_math_002.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Position.001"].outputs[0],
        correctrot_1.nodes["Vector Math.002"].inputs[1]
    )
    # geometry_proximity.Position -> vector_math_003.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Geometry Proximity"].outputs[0],
        correctrot_1.nodes["Vector Math.003"].inputs[0]
    )
    # position_001.Position -> vector_math_003.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Position.001"].outputs[0],
        correctrot_1.nodes["Vector Math.003"].inputs[1]
    )
    # vector_math_003.Value -> map_range.Value
    correctrot_1.links.new(
        correctrot_1.nodes["Vector Math.003"].outputs[1],
        correctrot_1.nodes["Map Range"].inputs[0]
    )
    # map_range.Result -> math_002.Value
    correctrot_1.links.new(
        correctrot_1.nodes["Map Range"].outputs[0],
        correctrot_1.nodes["Math.002"].inputs[0]
    )
    # math_002.Value -> math_003.Value
    correctrot_1.links.new(
        correctrot_1.nodes["Math.002"].outputs[0],
        correctrot_1.nodes["Math.003"].inputs[0]
    )
    # vector_math_002.Vector -> align_rotation_to_vector_001.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Vector Math.002"].outputs[0],
        correctrot_1.nodes["Align Rotation to Vector.001"].inputs[2]
    )
    # math_003.Value -> align_rotation_to_vector_001.Factor
    correctrot_1.links.new(
        correctrot_1.nodes["Math.003"].outputs[0],
        correctrot_1.nodes["Align Rotation to Vector.001"].inputs[1]
    )
    # random_value_001.Value -> vector_math_004.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Random Value.001"].outputs[0],
        correctrot_1.nodes["Vector Math.004"].inputs[0]
    )
    # align_rotation_to_vector_001.Rotation -> vector_math_005.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Align Rotation to Vector.001"].outputs[0],
        correctrot_1.nodes["Vector Math.005"].inputs[0]
    )
    # vector_math_004.Vector -> vector_math_005.Vector
    correctrot_1.links.new(
        correctrot_1.nodes["Vector Math.004"].outputs[0],
        correctrot_1.nodes["Vector Math.005"].inputs[1]
    )
    # collection_info_001.Instances -> realize_instances_001.Geometry
    correctrot_1.links.new(
        correctrot_1.nodes["Collection Info.001"].outputs[0],
        correctrot_1.nodes["Realize Instances.001"].inputs[0]
    )
    # realize_instances_001.Geometry -> geometry_proximity.Geometry
    correctrot_1.links.new(
        correctrot_1.nodes["Realize Instances.001"].outputs[0],
        correctrot_1.nodes["Geometry Proximity"].inputs[0]
    )
    # group_input.rotation_randomize_intensity -> vector_math_004.Scale
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[5],
        correctrot_1.nodes["Vector Math.004"].inputs[3]
    )
    # group_input.look_at_range -> map_range.From Max
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[3],
        correctrot_1.nodes["Map Range"].inputs[2]
    )
    # group_input.look_at_intensity -> math_002.Value
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[4],
        correctrot_1.nodes["Math.002"].inputs[1]
    )
    # group_input.look_at_target -> collection_info_001.Collection
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[2],
        correctrot_1.nodes["Collection Info.001"].inputs[0]
    )
    # collection_info_001.Instances -> domain_size.Geometry
    correctrot_1.links.new(
        correctrot_1.nodes["Collection Info.001"].outputs[0],
        correctrot_1.nodes["Domain Size"].inputs[0]
    )
    # domain_size.Instance Count -> compare.A
    correctrot_1.links.new(
        correctrot_1.nodes["Domain Size"].outputs[5],
        correctrot_1.nodes["Compare"].inputs[2]
    )
    # group_input.enable_lookat -> boolean_math.Boolean
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[1],
        correctrot_1.nodes["Boolean Math"].inputs[0]
    )
    # boolean_math.Boolean -> math_003.Value
    correctrot_1.links.new(
        correctrot_1.nodes["Boolean Math"].outputs[0],
        correctrot_1.nodes["Math.003"].inputs[1]
    )
    # compare.Result -> boolean_math.Boolean
    correctrot_1.links.new(
        correctrot_1.nodes["Compare"].outputs[0],
        correctrot_1.nodes["Boolean Math"].inputs[1]
    )
    # vector_math_005.Vector -> group_output.correctedRot
    correctrot_1.links.new(
        correctrot_1.nodes["Vector Math.005"].outputs[0],
        correctrot_1.nodes["Group Output"].inputs[1]
    )
    # euler_to_rotation.Rotation -> align_rotation_to_vector_001.Rotation
    correctrot_1.links.new(
        correctrot_1.nodes["Euler to Rotation"].outputs[0],
        correctrot_1.nodes["Align Rotation to Vector.001"].inputs[0]
    )
    # euler_to_rotation.Rotation -> group_output.rot
    correctrot_1.links.new(
        correctrot_1.nodes["Euler to Rotation"].outputs[0],
        correctrot_1.nodes["Group Output"].inputs[0]
    )
    # group_input.rot_eular -> euler_to_rotation.Euler
    correctrot_1.links.new(
        correctrot_1.nodes["Group Input"].outputs[0],
        correctrot_1.nodes["Euler to Rotation"].inputs[0]
    )

    return correctrot_1


def deletepoints_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize deletePoints node group"""
    deletepoints_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="deletePoints")

    deletepoints_1.color_tag = 'NONE'
    deletepoints_1.description = ""
    deletepoints_1.default_group_node_width = 140

    # deletepoints_1 interface

    # Socket Geometry
    geometry_socket = deletepoints_1.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'
    geometry_socket.default_input = 'VALUE'
    geometry_socket.structure_type = 'AUTO'

    # Socket Geometry
    geometry_socket_1 = deletepoints_1.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'
    geometry_socket_1.default_input = 'VALUE'
    geometry_socket_1.structure_type = 'AUTO'

    # Socket opacity
    opacity_socket = deletepoints_1.interface.new_socket(name="opacity", in_out='INPUT', socket_type='NodeSocketFloat')
    opacity_socket.default_value = 0.0
    opacity_socket.min_value = -10000.0
    opacity_socket.max_value = 10000.0
    opacity_socket.subtype = 'NONE'
    opacity_socket.attribute_domain = 'POINT'
    opacity_socket.default_input = 'VALUE'
    opacity_socket.structure_type = 'AUTO'

    # Socket opacity_threshold
    opacity_threshold_socket = deletepoints_1.interface.new_socket(name="opacity_threshold", in_out='INPUT', socket_type='NodeSocketFloat')
    opacity_threshold_socket.default_value = 0.3400001525878906
    opacity_threshold_socket.min_value = -10000.0
    opacity_threshold_socket.max_value = 10000.0
    opacity_threshold_socket.subtype = 'NONE'
    opacity_threshold_socket.attribute_domain = 'POINT'
    opacity_threshold_socket.default_input = 'VALUE'
    opacity_threshold_socket.structure_type = 'AUTO'

    # Socket scale
    scale_socket = deletepoints_1.interface.new_socket(name="scale", in_out='INPUT', socket_type='NodeSocketVector')
    scale_socket.default_value = (0.0, 0.0, 0.0)
    scale_socket.min_value = -3.4028234663852886e+38
    scale_socket.max_value = 3.4028234663852886e+38
    scale_socket.subtype = 'NONE'
    scale_socket.attribute_domain = 'POINT'
    scale_socket.default_input = 'VALUE'
    scale_socket.structure_type = 'AUTO'

    # Socket scale_threshold
    scale_threshold_socket = deletepoints_1.interface.new_socket(name="scale_threshold", in_out='INPUT', socket_type='NodeSocketFloat')
    scale_threshold_socket.default_value = 0.0
    scale_threshold_socket.min_value = -3.4028234663852886e+38
    scale_threshold_socket.max_value = 3.4028234663852886e+38
    scale_threshold_socket.subtype = 'NONE'
    scale_threshold_socket.attribute_domain = 'POINT'
    scale_threshold_socket.default_input = 'VALUE'
    scale_threshold_socket.structure_type = 'AUTO'

    # Socket overall_delete
    overall_delete_socket = deletepoints_1.interface.new_socket(name="overall_delete", in_out='INPUT', socket_type='NodeSocketFloat')
    overall_delete_socket.default_value = 0.5
    overall_delete_socket.min_value = -10000.0
    overall_delete_socket.max_value = 10000.0
    overall_delete_socket.subtype = 'NONE'
    overall_delete_socket.attribute_domain = 'POINT'
    overall_delete_socket.default_input = 'VALUE'
    overall_delete_socket.structure_type = 'AUTO'

    # Initialize deletepoints_1 nodes

    # Node Group Output
    group_output = deletepoints_1.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # Node Group Input
    group_input = deletepoints_1.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Node Delete Geometry
    delete_geometry = deletepoints_1.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry.name = "Delete Geometry"
    delete_geometry.hide = True
    delete_geometry.domain = 'POINT'
    delete_geometry.mode = 'ALL'

    # Node Compare.001
    compare_001 = deletepoints_1.nodes.new("FunctionNodeCompare")
    compare_001.name = "Compare.001"
    compare_001.hide = True
    compare_001.data_type = 'FLOAT'
    compare_001.mode = 'ELEMENT'
    compare_001.operation = 'LESS_THAN'

    # Node Compare
    compare = deletepoints_1.nodes.new("FunctionNodeCompare")
    compare.name = "Compare"
    compare.hide = True
    compare.data_type = 'VECTOR'
    compare.mode = 'ELEMENT'
    compare.operation = 'LESS_THAN'

    # Node Delete Geometry.001
    delete_geometry_001 = deletepoints_1.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry_001.name = "Delete Geometry.001"
    delete_geometry_001.hide = True
    delete_geometry_001.domain = 'POINT'
    delete_geometry_001.mode = 'ALL'

    # Node Delete Geometry.002
    delete_geometry_002 = deletepoints_1.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry_002.name = "Delete Geometry.002"
    delete_geometry_002.hide = True
    delete_geometry_002.domain = 'POINT'
    delete_geometry_002.mode = 'ALL'

    # Node Random Value.001
    random_value_001 = deletepoints_1.nodes.new("FunctionNodeRandomValue")
    random_value_001.name = "Random Value.001"
    random_value_001.hide = True
    random_value_001.data_type = 'BOOLEAN'
    # ID
    random_value_001.inputs[7].default_value = 0
    # Seed
    random_value_001.inputs[8].default_value = 0

    # Node Math.004
    math_004 = deletepoints_1.nodes.new("ShaderNodeMath")
    math_004.name = "Math.004"
    math_004.hide = True
    math_004.operation = 'MULTIPLY'
    math_004.use_clamp = True
    # Value_001
    math_004.inputs[1].default_value = 0.009999999776482582

    # Set locations
    deletepoints_1.nodes["Group Output"].location = (430.0, 0.0)
    deletepoints_1.nodes["Group Input"].location = (-440.0, 0.0)
    deletepoints_1.nodes["Delete Geometry"].location = (-240.0, 50.0)
    deletepoints_1.nodes["Compare.001"].location = (-240.0, 90.0)
    deletepoints_1.nodes["Compare"].location = (0.0, 50.0)
    deletepoints_1.nodes["Delete Geometry.001"].location = (0.0, 10.0)
    deletepoints_1.nodes["Delete Geometry.002"].location = (240.0, -90.0)
    deletepoints_1.nodes["Random Value.001"].location = (240.0, -50.0)
    deletepoints_1.nodes["Math.004"].location = (240.0, -10.0)

    # Initialize deletepoints_1 links

    # compare_001.Result -> delete_geometry.Selection
    deletepoints_1.links.new(
        deletepoints_1.nodes["Compare.001"].outputs[0],
        deletepoints_1.nodes["Delete Geometry"].inputs[1]
    )
    # delete_geometry_001.Geometry -> delete_geometry_002.Geometry
    deletepoints_1.links.new(
        deletepoints_1.nodes["Delete Geometry.001"].outputs[0],
        deletepoints_1.nodes["Delete Geometry.002"].inputs[0]
    )
    # compare.Result -> delete_geometry_001.Selection
    deletepoints_1.links.new(
        deletepoints_1.nodes["Compare"].outputs[0],
        deletepoints_1.nodes["Delete Geometry.001"].inputs[1]
    )
    # delete_geometry.Geometry -> delete_geometry_001.Geometry
    deletepoints_1.links.new(
        deletepoints_1.nodes["Delete Geometry"].outputs[0],
        deletepoints_1.nodes["Delete Geometry.001"].inputs[0]
    )
    # random_value_001.Value -> delete_geometry_002.Selection
    deletepoints_1.links.new(
        deletepoints_1.nodes["Random Value.001"].outputs[3],
        deletepoints_1.nodes["Delete Geometry.002"].inputs[1]
    )
    # math_004.Value -> random_value_001.Probability
    deletepoints_1.links.new(
        deletepoints_1.nodes["Math.004"].outputs[0],
        deletepoints_1.nodes["Random Value.001"].inputs[6]
    )
    # group_input.scale_threshold -> compare.B
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[4],
        deletepoints_1.nodes["Compare"].inputs[5]
    )
    # group_input.opacity -> compare_001.A
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[1],
        deletepoints_1.nodes["Compare.001"].inputs[0]
    )
    # group_input.scale -> compare.A
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[3],
        deletepoints_1.nodes["Compare"].inputs[4]
    )
    # group_input.overall_delete -> math_004.Value
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[5],
        deletepoints_1.nodes["Math.004"].inputs[0]
    )
    # group_input.opacity_threshold -> compare_001.B
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[2],
        deletepoints_1.nodes["Compare.001"].inputs[1]
    )
    # group_input.Geometry -> delete_geometry.Geometry
    deletepoints_1.links.new(
        deletepoints_1.nodes["Group Input"].outputs[0],
        deletepoints_1.nodes["Delete Geometry"].inputs[0]
    )
    # delete_geometry_002.Geometry -> group_output.Geometry
    deletepoints_1.links.new(
        deletepoints_1.nodes["Delete Geometry.002"].outputs[0],
        deletepoints_1.nodes["Group Output"].inputs[0]
    )

    return deletepoints_1


def gs_instancer_lut_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize GS_Instancer_Lut node group"""
    gs_instancer_lut_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="GS_Instancer_Lut")

    gs_instancer_lut_1.color_tag = 'NONE'
    gs_instancer_lut_1.description = ""
    gs_instancer_lut_1.default_group_node_width = 140
    gs_instancer_lut_1.is_modifier = True

    # gs_instancer_lut_1 interface

    # Socket Geometry
    geometry_socket = gs_instancer_lut_1.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'
    geometry_socket.default_input = 'VALUE'
    geometry_socket.structure_type = 'AUTO'

    # Socket Geometry
    geometry_socket_1 = gs_instancer_lut_1.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    geometry_socket_1.attribute_domain = 'POINT'
    geometry_socket_1.default_input = 'VALUE'
    geometry_socket_1.structure_type = 'AUTO'

    # Socket opacity_threshold
    opacity_threshold_socket = gs_instancer_lut_1.interface.new_socket(name="opacity_threshold", in_out='INPUT', socket_type='NodeSocketFloat')
    opacity_threshold_socket.default_value = 0.20000000298023224
    opacity_threshold_socket.min_value = 0.0
    opacity_threshold_socket.max_value = 1.0
    opacity_threshold_socket.subtype = 'NONE'
    opacity_threshold_socket.attribute_domain = 'POINT'
    opacity_threshold_socket.default_input = 'VALUE'
    opacity_threshold_socket.structure_type = 'AUTO'

    # Socket instance_size
    instance_size_socket = gs_instancer_lut_1.interface.new_socket(name="instance_size", in_out='INPUT', socket_type='NodeSocketFloat')
    instance_size_socket.default_value = 1.0
    instance_size_socket.min_value = 0.009999999776482582
    instance_size_socket.max_value = 2.0
    instance_size_socket.subtype = 'DISTANCE'
    instance_size_socket.attribute_domain = 'POINT'
    instance_size_socket.description = "Side length of the plane in the X direction"
    instance_size_socket.default_input = 'VALUE'
    instance_size_socket.structure_type = 'AUTO'

    # Socket size_threshold
    size_threshold_socket = gs_instancer_lut_1.interface.new_socket(name="size_threshold", in_out='INPUT', socket_type='NodeSocketFloat')
    size_threshold_socket.default_value = 0.0
    size_threshold_socket.min_value = 0.0
    size_threshold_socket.max_value = 1.0
    size_threshold_socket.subtype = 'FACTOR'
    size_threshold_socket.attribute_domain = 'POINT'
    size_threshold_socket.default_input = 'VALUE'
    size_threshold_socket.structure_type = 'AUTO'

    # Socket instance
    instance_socket = gs_instancer_lut_1.interface.new_socket(name="instance", in_out='INPUT', socket_type='NodeSocketObject')
    instance_socket.attribute_domain = 'POINT'
    instance_socket.default_input = 'VALUE'
    instance_socket.structure_type = 'AUTO'

    # Socket enable_lookat
    enable_lookat_socket = gs_instancer_lut_1.interface.new_socket(name="enable_lookat", in_out='INPUT', socket_type='NodeSocketBool')
    enable_lookat_socket.default_value = False
    enable_lookat_socket.attribute_domain = 'POINT'
    enable_lookat_socket.default_input = 'VALUE'
    enable_lookat_socket.structure_type = 'AUTO'

    # Socket look_at_target
    look_at_target_socket = gs_instancer_lut_1.interface.new_socket(name="look_at_target", in_out='INPUT', socket_type='NodeSocketCollection')
    look_at_target_socket.attribute_domain = 'POINT'
    look_at_target_socket.default_input = 'VALUE'
    look_at_target_socket.structure_type = 'AUTO'

    # Socket look_at_range
    look_at_range_socket = gs_instancer_lut_1.interface.new_socket(name="look_at_range", in_out='INPUT', socket_type='NodeSocketFloat')
    look_at_range_socket.default_value = 30.0
    look_at_range_socket.min_value = 0.0
    look_at_range_socket.max_value = 500.0
    look_at_range_socket.subtype = 'DISTANCE'
    look_at_range_socket.attribute_domain = 'POINT'
    look_at_range_socket.default_input = 'VALUE'
    look_at_range_socket.structure_type = 'AUTO'

    # Socket look_at_intensity
    look_at_intensity_socket = gs_instancer_lut_1.interface.new_socket(name="look_at_intensity", in_out='INPUT', socket_type='NodeSocketFloat')
    look_at_intensity_socket.default_value = 0.5
    look_at_intensity_socket.min_value = 0.0
    look_at_intensity_socket.max_value = 1.0
    look_at_intensity_socket.subtype = 'NONE'
    look_at_intensity_socket.attribute_domain = 'POINT'
    look_at_intensity_socket.default_input = 'VALUE'
    look_at_intensity_socket.structure_type = 'AUTO'

    # Socket rotation_randomize_intensity
    rotation_randomize_intensity_socket = gs_instancer_lut_1.interface.new_socket(name="rotation_randomize_intensity", in_out='INPUT', socket_type='NodeSocketFloat')
    rotation_randomize_intensity_socket.default_value = 0.10000000149011612
    rotation_randomize_intensity_socket.min_value = -1.0
    rotation_randomize_intensity_socket.max_value = 1.0
    rotation_randomize_intensity_socket.subtype = 'NONE'
    rotation_randomize_intensity_socket.attribute_domain = 'POINT'
    rotation_randomize_intensity_socket.default_input = 'VALUE'
    rotation_randomize_intensity_socket.structure_type = 'AUTO'

    # Socket overall_delete
    overall_delete_socket = gs_instancer_lut_1.interface.new_socket(name="overall_delete", in_out='INPUT', socket_type='NodeSocketFloat')
    overall_delete_socket.default_value = 10.0
    overall_delete_socket.min_value = 0.0
    overall_delete_socket.max_value = 100.0
    overall_delete_socket.subtype = 'PERCENTAGE'
    overall_delete_socket.attribute_domain = 'POINT'
    overall_delete_socket.default_input = 'VALUE'
    overall_delete_socket.structure_type = 'AUTO'

    # Socket Material
    material_socket = gs_instancer_lut_1.interface.new_socket(name="Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    material_socket.attribute_domain = 'POINT'
    material_socket.default_input = 'VALUE'
    material_socket.structure_type = 'AUTO'

    # Initialize gs_instancer_lut_1 nodes

    # Node Group Input
    group_input = gs_instancer_lut_1.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Node Group Output
    group_output = gs_instancer_lut_1.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # Node Instance on Points
    instance_on_points = gs_instancer_lut_1.nodes.new("GeometryNodeInstanceOnPoints")
    instance_on_points.name = "Instance on Points"
    # Selection
    instance_on_points.inputs[1].default_value = True
    # Pick Instance
    instance_on_points.inputs[3].default_value = False
    # Instance Index
    instance_on_points.inputs[4].default_value = 0

    # Node Store Named Attribute
    store_named_attribute = gs_instancer_lut_1.nodes.new("GeometryNodeStoreNamedAttribute")
    store_named_attribute.name = "Store Named Attribute"
    store_named_attribute.data_type = 'FLOAT2'
    store_named_attribute.domain = 'CORNER'
    # Selection
    store_named_attribute.inputs[1].default_value = True
    # Name
    store_named_attribute.inputs[2].default_value = "ColUV"

    # Node Named Attribute
    named_attribute = gs_instancer_lut_1.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute.name = "Named Attribute"
    named_attribute.data_type = 'FLOAT_VECTOR'
    # Name
    named_attribute.inputs[0].default_value = "palette_uv"

    # Node Set Material
    set_material = gs_instancer_lut_1.nodes.new("GeometryNodeSetMaterial")
    set_material.name = "Set Material"
    # Selection
    set_material.inputs[1].default_value = True

    # Node Realize Instances
    realize_instances = gs_instancer_lut_1.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.name = "Realize Instances"
    # Selection
    realize_instances.inputs[1].default_value = True
    # Realize All
    realize_instances.inputs[2].default_value = True
    # Depth
    realize_instances.inputs[3].default_value = 0

    # Node Object Info
    object_info = gs_instancer_lut_1.nodes.new("GeometryNodeObjectInfo")
    object_info.name = "Object Info"
    object_info.hide = True
    object_info.transform_space = 'ORIGINAL'
    # As Instance
    object_info.inputs[1].default_value = False

    # Node Group.002
    group_002 = gs_instancer_lut_1.nodes.new("GeometryNodeGroup")
    group_002.name = "Group.002"
    group_002.node_tree = bpy.data.node_groups[node_tree_names[correctrot_1_node_group]]

    # Node Group.003
    group_003 = gs_instancer_lut_1.nodes.new("GeometryNodeGroup")
    group_003.name = "Group.003"
    group_003.node_tree = bpy.data.node_groups[node_tree_names[deletepoints_1_node_group]]

    # Node Vector Curves
    vector_curves = gs_instancer_lut_1.nodes.new("ShaderNodeVectorCurve")
    vector_curves.name = "Vector Curves"
    # Mapping settings
    vector_curves.mapping.extend = 'EXTRAPOLATED'
    vector_curves.mapping.tone = 'STANDARD'
    vector_curves.mapping.black_level = (0.0, 0.0, 0.0)
    vector_curves.mapping.white_level = (1.0, 1.0, 1.0)
    vector_curves.mapping.clip_min_x = 0.0
    vector_curves.mapping.clip_min_y = 0.0
    vector_curves.mapping.clip_max_x = 1.0
    vector_curves.mapping.clip_max_y = 1.0
    vector_curves.mapping.use_clip = True
    # Curve 0
    vector_curves_curve_0 = vector_curves.mapping.curves[0]
    vector_curves_curve_0_point_0 = vector_curves_curve_0.points[0]
    vector_curves_curve_0_point_0.location = (-1.0, -1.0)
    vector_curves_curve_0_point_0.handle_type = 'AUTO'
    vector_curves_curve_0_point_1 = vector_curves_curve_0.points[1]
    vector_curves_curve_0_point_1.location = (1.0, 1.0)
    vector_curves_curve_0_point_1.handle_type = 'AUTO'
    # Curve 1
    vector_curves_curve_1 = vector_curves.mapping.curves[1]
    vector_curves_curve_1_point_0 = vector_curves_curve_1.points[0]
    vector_curves_curve_1_point_0.location = (-1.0, -1.0)
    vector_curves_curve_1_point_0.handle_type = 'AUTO'
    vector_curves_curve_1_point_1 = vector_curves_curve_1.points[1]
    vector_curves_curve_1_point_1.location = (1.0, 1.0)
    vector_curves_curve_1_point_1.handle_type = 'VECTOR'
    # Curve 2
    vector_curves_curve_2 = vector_curves.mapping.curves[2]
    vector_curves_curve_2_point_0 = vector_curves_curve_2.points[0]
    vector_curves_curve_2_point_0.location = (-1.0, -1.0)
    vector_curves_curve_2_point_0.handle_type = 'AUTO'
    vector_curves_curve_2_point_1 = vector_curves_curve_2.points[1]
    vector_curves_curve_2_point_1.location = (1.0, 1.0)
    vector_curves_curve_2_point_1.handle_type = 'AUTO'
    # Update curve after changes
    vector_curves.mapping.update()
    # Fac
    vector_curves.inputs[0].default_value = 1.0

    # Node Named Attribute.013
    named_attribute_013 = gs_instancer_lut_1.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute_013.name = "Named Attribute.013"
    named_attribute_013.data_type = 'FLOAT_VECTOR'
    # Name
    named_attribute_013.inputs[0].default_value = "scale"

    # Node Named Attribute.014
    named_attribute_014 = gs_instancer_lut_1.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute_014.name = "Named Attribute.014"
    named_attribute_014.data_type = 'FLOAT_VECTOR'
    # Name
    named_attribute_014.inputs[0].default_value = "rot_euler"

    # Node Vector Math.001
    vector_math_001 = gs_instancer_lut_1.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'SCALE'

    # Node Named Attribute.001
    named_attribute_001 = gs_instancer_lut_1.nodes.new("GeometryNodeInputNamedAttribute")
    named_attribute_001.name = "Named Attribute.001"
    named_attribute_001.data_type = 'FLOAT'
    # Name
    named_attribute_001.inputs[0].default_value = "opacity"

    # Set locations
    gs_instancer_lut_1.nodes["Group Input"].location = (-1546.7109375, 186.5460968017578)
    gs_instancer_lut_1.nodes["Group Output"].location = (592.4782104492188, -228.50343322753906)
    gs_instancer_lut_1.nodes["Instance on Points"].location = (-380.0, -120.0)
    gs_instancer_lut_1.nodes["Store Named Attribute"].location = (231.6966552734375, -175.98529052734375)
    gs_instancer_lut_1.nodes["Named Attribute"].location = (12.478230476379395, -348.50341796875)
    gs_instancer_lut_1.nodes["Set Material"].location = (412.4782409667969, -228.50343322753906)
    gs_instancer_lut_1.nodes["Realize Instances"].location = (-27.52176856994629, -128.50343322753906)
    gs_instancer_lut_1.nodes["Object Info"].location = (-742.7268676757812, 189.27001953125)
    gs_instancer_lut_1.nodes["Group.002"].location = (-1146.6014404296875, -174.99168395996094)
    gs_instancer_lut_1.nodes["Group.003"].location = (-744.6276245117188, 146.45167541503906)
    gs_instancer_lut_1.nodes["Vector Curves"].location = (-855.8612670898438, -447.5713806152344)
    gs_instancer_lut_1.nodes["Named Attribute.013"].location = (-1552.8326416015625, -538.5982055664062)
    gs_instancer_lut_1.nodes["Named Attribute.014"].location = (-1548.29296875, -399.6018371582031)
    gs_instancer_lut_1.nodes["Vector Math.001"].location = (-1145.755859375, -500.0528564453125)
    gs_instancer_lut_1.nodes["Named Attribute.001"].location = (-1557.5028076171875, -672.39208984375)

    # Initialize gs_instancer_lut_1 links

    # realize_instances.Geometry -> store_named_attribute.Geometry
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Realize Instances"].outputs[0],
        gs_instancer_lut_1.nodes["Store Named Attribute"].inputs[0]
    )
    # named_attribute.Attribute -> store_named_attribute.Value
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Named Attribute"].outputs[0],
        gs_instancer_lut_1.nodes["Store Named Attribute"].inputs[3]
    )
    # set_material.Geometry -> group_output.Geometry
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Set Material"].outputs[0],
        gs_instancer_lut_1.nodes["Group Output"].inputs[0]
    )
    # object_info.Geometry -> instance_on_points.Instance
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Object Info"].outputs[4],
        gs_instancer_lut_1.nodes["Instance on Points"].inputs[2]
    )
    # group_input.instance -> object_info.Object
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[4],
        gs_instancer_lut_1.nodes["Object Info"].inputs[0]
    )
    # group_003.Geometry -> instance_on_points.Points
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group.003"].outputs[0],
        gs_instancer_lut_1.nodes["Instance on Points"].inputs[0]
    )
    # store_named_attribute.Geometry -> set_material.Geometry
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Store Named Attribute"].outputs[0],
        gs_instancer_lut_1.nodes["Set Material"].inputs[0]
    )
    # group_input.look_at_intensity -> group_002.look_at_intensity
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[8],
        gs_instancer_lut_1.nodes["Group.002"].inputs[4]
    )
    # group_input.rotation_randomize_intensity -> group_002.rotation_randomize_intensity
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[9],
        gs_instancer_lut_1.nodes["Group.002"].inputs[5]
    )
    # group_input.look_at_range -> group_002.look_at_range
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[7],
        gs_instancer_lut_1.nodes["Group.002"].inputs[3]
    )
    # group_input.size_threshold -> group_003.scale_threshold
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[3],
        gs_instancer_lut_1.nodes["Group.003"].inputs[4]
    )
    # group_input.overall_delete -> group_003.overall_delete
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[10],
        gs_instancer_lut_1.nodes["Group.003"].inputs[5]
    )
    # group_input.opacity_threshold -> group_003.opacity_threshold
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[1],
        gs_instancer_lut_1.nodes["Group.003"].inputs[2]
    )
    # group_input.Geometry -> group_003.Geometry
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[0],
        gs_instancer_lut_1.nodes["Group.003"].inputs[0]
    )
    # group_input.look_at_target -> group_002.look_at_target
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[6],
        gs_instancer_lut_1.nodes["Group.002"].inputs[2]
    )
    # group_input.enable_lookat -> group_002.enable_lookat
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[5],
        gs_instancer_lut_1.nodes["Group.002"].inputs[1]
    )
    # group_input.Material -> set_material.Material
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[11],
        gs_instancer_lut_1.nodes["Set Material"].inputs[2]
    )
    # instance_on_points.Instances -> realize_instances.Geometry
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Instance on Points"].outputs[0],
        gs_instancer_lut_1.nodes["Realize Instances"].inputs[0]
    )
    # named_attribute_013.Attribute -> vector_math_001.Vector
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Named Attribute.013"].outputs[0],
        gs_instancer_lut_1.nodes["Vector Math.001"].inputs[0]
    )
    # named_attribute_014.Attribute -> group_002.rot_eular
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Named Attribute.014"].outputs[0],
        gs_instancer_lut_1.nodes["Group.002"].inputs[0]
    )
    # group_002.correctedRot -> instance_on_points.Rotation
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group.002"].outputs[1],
        gs_instancer_lut_1.nodes["Instance on Points"].inputs[5]
    )
    # vector_math_001.Vector -> group_003.scale
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Vector Math.001"].outputs[0],
        gs_instancer_lut_1.nodes["Group.003"].inputs[3]
    )
    # vector_math_001.Vector -> vector_curves.Vector
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Vector Math.001"].outputs[0],
        gs_instancer_lut_1.nodes["Vector Curves"].inputs[1]
    )
    # vector_curves.Vector -> instance_on_points.Scale
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Vector Curves"].outputs[0],
        gs_instancer_lut_1.nodes["Instance on Points"].inputs[6]
    )
    # group_input.instance_size -> vector_math_001.Scale
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Group Input"].outputs[2],
        gs_instancer_lut_1.nodes["Vector Math.001"].inputs[3]
    )
    # named_attribute_001.Attribute -> group_003.opacity
    gs_instancer_lut_1.links.new(
        gs_instancer_lut_1.nodes["Named Attribute.001"].outputs[0],
        gs_instancer_lut_1.nodes["Group.003"].inputs[1]
    )


    return gs_instancer_lut_1


def create_gs_node_system():
    # Maps node tree creation functions to the node tree 
    # name, such that we don't recreate node trees unnecessarily
    node_tree_names : dict[typing.Callable, str] = {}

    correctrot = correctrot_1_node_group(node_tree_names)
    node_tree_names[correctrot_1_node_group] = correctrot.name

    deletepoints = deletepoints_1_node_group(node_tree_names)
    node_tree_names[deletepoints_1_node_group] = deletepoints.name

    gs_instancer_lut = gs_instancer_lut_1_node_group(node_tree_names)
    node_tree_names[gs_instancer_lut_1_node_group] = gs_instancer_lut.name
    
    return gs_instancer_lut

if __name__ == "__main__":
    create_gs_node_system()


