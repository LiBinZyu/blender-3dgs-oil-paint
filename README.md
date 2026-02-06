# 3DGS Oil Painting Stylizer for Blender

This tool transforms Apple ML-Sharp 3D Gaussian Splatting models into oil painting-style 3D assets using Blender 4.5. The rendering logic utilizes a Look-Up Table (LUT) to store color data, mapping the UVs of instance planes directly to corresponding pixels. All calculations and optimizations are powered by Geometry Nodes, resulting in a lightweight shading setup that integrates seamlessly with other software. The final output can be exported as standard mesh formats, including FBX, OBJ, and GLB. The included `.blend` file contains the full setup for immediate use.

**3DGS 油画风格化 Blender 工具**

本工具基于 Blender 4.5 开发，旨在将 Apple ML-Sharp 3DGS 模型转化为具有油画质感的非真实感渲染（NPR）风格。其核心原理在于利用一张 LUT 贴图记录颜色数据，并通过几何节点（Geometry Nodes）将实例面片的 UV 精确映射至对应的像素点。这种处理方式不仅优化了模型结构，还确保了着色方案的极简性，使其能够完美兼容其他渲染引擎或设计工具。支持直接导出为 FBX、OBJ 和 GLB 等通用网格格式。随附的 `.blend` 文件即开即用。

**Click to go to the model page**

| | |
|:---:|:---:|
| [![Cat](img/cat.jpg)](https://sketchfab.com/3d-models/cat-3dgs-to-oil-painting-npr-style-552533b9bb6049ad9d941b637bc9a944) | [![Venus](img/venus.jpg)](https://sketchfab.com/3d-models/the-birth-of-venus-3dgs-npr-painting-style-f1e481dce56a4c5f91ba884dc21ec352) |
| [![Tomato](img/tomato.jpg)](https://sketchfab.com/3d-models/fruit-3dgs-oil-painting-9e460117c22042f380aaa8a169f8d1b7) | [![Boy with Basket](img/boybasket.jpg)](https://sketchfab.com/3d-models/3dgs-oil-paiting-boy-with-a-basket-of-fruit-9919fb190351484bbab96fb5ddc7711a) |


## How to use

- Open `3dgs2quad.blend`, import your 3dgs file (.ply) to current scene.
- Select your model, go to `Script` window, there should be a script showing, click `Run`.
- It is very fast, within 10s to complete, then you go to shader window and to check everything, adjust the geometry node parameters which should be automatically added to the model as modifier.

<div align="center" style="gap: 8px;">
  <img src="https://i.imgur.com/2GcG0Vg.png" width="80%" />
</div>