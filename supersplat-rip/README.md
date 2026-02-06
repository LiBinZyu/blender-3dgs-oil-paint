# uperSplat Model Ripper


Simple tool to download and reconstruct 3D Gaussian Splatting models from SuperSplat URLs.

## Setup

1. Install Python (if not installed).
2. Open terminal in this folder.
3. Install dependencies:

```
   pip install -r requirements.txt
```

## Usage

## Method 1 (Interactive):
   python rip_supersplat.py
   > Enter the Model ID when prompted (e.g., 0101ad57).

## Method 2 (Command Line):
   python rip_supersplat.py [MODEL_ID]
   > Example: python rip_supersplat.py 3e11b126

## Output

- A new folder named [MODEL_ID] will be created.
- Inside you will find:
  - [MODEL_ID].ply : The reconstructed 3D model file.
  - xl.webp       : Preview image.


The script automatically detects storage versions (V3, V2, or Root/V1). Temporary files are automatically cleaned up after reconstruction.
