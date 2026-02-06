
import os
import sys
import shutil
import requests
import json
import numpy as np
from PIL import Image
from io import BytesIO

# --- V4 Logic Functions ---

def inverse_sigmoid(x):
    # Clip to avoid inf
    x = np.clip(x, 1e-4, 1.0 - 1e-4)
    return np.log(x / (1.0 - x))

def download_file(url, filepath):
    print(f"⬇️ {os.path.basename(filepath)}...", end="\r")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(r.content)
            print(f"✅ {os.path.basename(filepath)}   ")
            return True
        else:
            print(f"⚠️ {os.path.basename(filepath)} (Status {r.status_code})")
            return False
    except Exception as e:
        print(f"Error downloading {filepath}: {e}")
        return False

def process_model(model_id):
    # 1. Setup Folder
    folder = model_id
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # 1.5 Determine Version (Check meta.json location)
    base_url_v3 = f"https://d28zzqy0iyovbz.cloudfront.net/{model_id}/v3"
    base_url_v2 = f"https://d28zzqy0iyovbz.cloudfront.net/{model_id}/v2"
    base_url_root = f"https://d28zzqy0iyovbz.cloudfront.net/{model_id}"
    
    # Try versions
    print(f"Checking version for {model_id}...")
    if requests.head(f"{base_url_v3}/meta.json").status_code == 200:
        base_url = base_url_v3
        print("Detected V3 storage.")
    elif requests.head(f"{base_url_v2}/meta.json").status_code == 200:
        base_url = base_url_v2
        print("Detected V2 storage.")
    elif requests.head(f"{base_url_root}/meta.json").status_code == 200:
        base_url = base_url_root
        print("Detected V1/Root storage.")
    else:
        print("Could not find meta.json in V3, V2 or Root. Model ID might be invalid or access denied.")
        return

    # 2. Download Assets
    required_files = [
        "meta.json", 
        "means_u.webp", 
        "means_l.webp", 
        "scales.webp", 
        "quats.webp", 
        "sh0.webp"
    ]
    
    # Try Download Preview (XL)
    # Usually in root for V1, or V2 for V2.
    xl_target = os.path.join(folder, "xl.webp")
    if not download_file(f"{base_url}/xl.webp", xl_target):
         download_file(f"{base_url_root}/xl.webp", xl_target) # Fallback to root for image

    # Download Required
    all_good = True
    for f in required_files:
        if not download_file(f"{base_url}/{f}", os.path.join(folder, f)):
            all_good = False
            break
    
    if not all_good:
        print("Missing required files, cannot proceed.")
        return

    print("Reconstructing model using V4 logic...")

    # 3. Load Meta
    with open(os.path.join(folder, "meta.json"), "r") as f:
        meta = json.load(f)
        
    count = meta.get("count", 0)
    if count == 0:
        # Fallback to means size
        img = Image.open(os.path.join(folder, "means_u.webp"))
        count = img.width * img.height
        
    # Helper to load image array trimmed to count
    def load_img(name, mode="RGB", channel_count=3):
        path = os.path.join(folder, name)
        img = Image.open(path).convert(mode)
        arr = np.array(img).reshape(-1, channel_count)
        return arr[:count]

    # 4. POSITIONS
    m_u = load_img("means_u.webp", "RGB", 3).astype(np.uint16)
    m_l = load_img("means_l.webp", "RGB", 3).astype(np.uint16)
    packed = (m_u * 256 + m_l).astype(np.float32) / 65535.0
    
    mins = np.array(meta["means"]["mins"], dtype=np.float32)
    maxs = np.array(meta["means"]["maxs"], dtype=np.float32)
    positions = mins + packed * (maxs - mins)

    # 5. SCALES (Anisotropic)
    s_arr = load_img("scales.webp", "RGB", 3)
    s_cb = np.array(meta["scales"]["codebook"], dtype=np.float32)
    sx = s_cb[s_arr[:, 0]]
    sy = s_cb[s_arr[:, 1]]
    sz = s_cb[s_arr[:, 2]]
    scales = np.stack([sx, sy, sz], axis=-1)

    # 6. ROTATIONS (Smart Reconstruction 255->W)
    q_raw = load_img("quats.webp", "RGBA", 4)
    rgb = q_raw[:, :3].astype(np.float32)
    alpha = q_raw[:, 3]
    
    limit = 0.70710678
    q_stored = (rgb / 255.0) * (2 * limit) - limit
    sq_sum = np.clip(np.sum(q_stored**2, axis=1), 0, 1.0)
    q_missing = np.sqrt(1.0 - sq_sum)
    
    quat = np.zeros((count, 4), dtype=np.float32)
    
    # 255->W (Standard largest)
    idx_w = (alpha == 255) | (alpha == 0) # Treat 0 as default W drop
    idx_z = (alpha == 254)
    idx_y = (alpha == 253)
    idx_x = (alpha <= 252) & (alpha > 0)
    
    quat[idx_w] = np.stack([q_stored[idx_w,0], q_stored[idx_w,1], q_stored[idx_w,2], q_missing[idx_w]], axis=1)
    quat[idx_z] = np.stack([q_stored[idx_z,0], q_stored[idx_z,1], q_missing[idx_z], q_stored[idx_z,2]], axis=1)
    quat[idx_y] = np.stack([q_stored[idx_y,0], q_missing[idx_y], q_stored[idx_y,1], q_stored[idx_y,2]], axis=1)
    quat[idx_x] = np.stack([q_missing[idx_x], q_stored[idx_x,0], q_stored[idx_x,1], q_stored[idx_x,2]], axis=1)
    
    # Standardize PLY: W, X, Y, Z
    rot_ply = np.stack([quat[:,3], quat[:,0], quat[:,1], quat[:,2]], axis=-1)
    
    # Normalize
    norms = np.linalg.norm(rot_ply, axis=1, keepdims=True)
    rot_ply = rot_ply / (norms + 1e-8)

    # 7. COLOR & OPACITY
    c_raw = load_img("sh0.webp", "RGBA", 4)
    rgb_idx = c_raw[:, :3]
    op_raw = c_raw[:, 3]
    
    dc_cb = np.array(meta["sh0"]["codebook"], dtype=np.float32)
    f_dc = np.stack([dc_cb[rgb_idx[:,0]], dc_cb[rgb_idx[:,1]], dc_cb[rgb_idx[:,2]]], axis=-1)
    
    op_logit = inverse_sigmoid(op_raw.astype(np.float32) / 255.0).reshape(-1, 1)

    # 8. WRITE PLY
    output_ply = os.path.join(folder, f"{model_id}.ply")
    print(f"Saving {output_ply}...")
    
    data = np.hstack([positions, f_dc, op_logit, scales, rot_ply]).astype(np.float32)
    
    with open(output_ply, 'wb') as f:
        f.write(b"ply\nformat binary_little_endian 1.0\n")
        f.write(f"element vertex {count}\n".encode())
        f.write(b"property float x\nproperty float y\nproperty float z\n")
        f.write(b"property float f_dc_0\nproperty float f_dc_1\nproperty float f_dc_2\n")
        f.write(b"property float opacity\n")
        f.write(b"property float scale_0\nproperty float scale_1\nproperty float scale_2\n")
        f.write(b"property float rot_0\nproperty float rot_1\nproperty float rot_2\nproperty float rot_3\n")
        f.write(b"end_header\n")
        f.write(data.tobytes())

    # 9. CLEANUP
    print("Cleaning up temp files...")
    keep_files = [f"{model_id}.ply", "xl.webp", "xl.png", "meta.json"] 
    # Also allow xl.png if user converted it
    
    for f in os.listdir(folder):
        if f not in keep_files:
            try:
                os.remove(os.path.join(folder, f))
            except: pass
            
    print(f"Done! Files saved in: {folder}/")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mid = sys.argv[1]
    else:
        # Default fallback or interactive
        mid = input("Enter Model ID (e.g. 0101ad57): ").strip()
    
    if mid:
        process_model(mid)
