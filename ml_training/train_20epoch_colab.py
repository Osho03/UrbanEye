"""
UrbanEye - Colab 20-epoch retrain script
========================================
Fits inside free Google Colab's daily GPU quota (~45 min on T4).

HOW TO USE:
  1. Open https://colab.research.google.com
  2. Runtime > Change runtime type > T4 GPU
  3. Create a new notebook, paste this file's content into one cell
     (or upload it: click "Files" and run it from a notebook with
     `!python train_20epoch_colab.py`)
  4. Put your free Roboflow key in RF_API_KEY below
     (get it free at: https://app.roboflow.com/settings/api)
  5. Run the cell. When it finishes it downloads:
       /content/civic_yolov8.pt
       /content/civic_yolov8.onnx
  6. Replace these files in your project:
       UrbanEye/backend/ai/models/civic_yolov8.onnx
       UrbanEye/backend/ai/models/civic_yolov8.pt
     then restart the backend. Your app will now show the correct
     class text (streetlight, pothole, garbage, water_leak,
     drainage, sidewalk_damage) when you capture a photo.

IMPORTANT: If Colab says "GPU limit exceeded", your daily free GPU
quota is used up. Wait ~24h, use another Google account, or run this
same script on Kaggle (free ~30h GPU/week).

Class order MUST stay (matches backend/ai/yolo_onnx.py):
0 garbage, 1 pothole, 2 water_leak, 3 streetlight, 4 drainage,
5 sidewalk_damage
"""

# ================= CONFIG =================
RF_API_KEY = "PASTE_YOUR_FREE_ROBOFLOW_API_KEY_HERE"

DATASETS = [
    {"tag": "ph", "workspace": "new-workspace-kj87b", "project": "road-damage-detection-iicdh", "version": 1},
    {"tag": "gb", "workspace": "garbage-detection-j813v", "project": "garbage-detection-8hmsd", "version": 1},
    {"tag": "wl", "workspace": "new-workspace-0bgj4", "project": "pipe-leak-yp6il", "version": 1},
    {"tag": "sl", "workspace": "street-lamps", "project": "street-lamps-dpeqc", "version": 1},
    {"tag": "dr", "workspace": "sakib-t1srr", "project": "objection-detection-1yrwu", "version": 1},
    {"tag": "sw", "workspace": "street-cqv2u", "project": "sidewalk-32xvi", "version": 1},
]

UNIFIED_CLASSES = ["garbage", "pothole", "water_leak", "streetlight", "drainage", "sidewalk_damage"]

MODEL = "yolov8s.pt"       # small - stronger than the old nano, still trains fast
EPOCHS = 20                # enough for a working 6-class demo (pretrained start)
PATIENCE = 10              # early stopping
IMGSZ = 640
BATCH = 16                 # fits T4 15GB VRAM comfortably
BALANCE_CAP = 500          # max images per class
BALANCE_FLOOR = 400        # oversample minority classes to at least this many

assert not RF_API_KEY.startswith("PASTE"), (
    "Paste your Roboflow API key! Free key at: https://app.roboflow.com/settings/api"
)


def install():
    """Install packages. Only needed on Colab/Kaggle (this machine)."""
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
                           "ultralytics", "roboflow"])


def check_gpu():
    import torch
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)} "
              f"({torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB) - OK")
        return True
    print("WARNING: No GPU! 'GPU limit exceeded' = free Colab locked you out for today.")
    print("Wait ~24h, switch Google account, or use Kaggle. CPU training is too slow.")
    return False


def download_datasets():
    """Download all 6 Roboflow datasets. Returns list of (location, tag)."""
    import time
    from roboflow import Roboflow

    t0 = time.time()
    rf = Roboflow(api_key=RF_API_KEY)
    downloaded = []
    total_raw = 0

    for spec in DATASETS:
        ds = (rf.workspace(spec["workspace"])
                .project(spec["project"])
                .version(spec["version"])
                .download("yolov8"))
        downloaded.append({"spec": spec, "location": ds.location})

        import glob
        n = len(glob.glob(ds.location + "/train/images/[!labels]*.[jJ][pP][gG]")) + \
            len(glob.glob(ds.location + "/train/images/[!labels]*.[jP][nN][gG]")) + \
            len(glob.glob(ds.location + "/train/images/[!labels]*.[wW][eE][bB][pP]"))
        total_raw += n
        print(f"[{spec['tag']}] {n} train images -> {ds.location}")

    print(f"Download time: {(time.time() - t0) / 60:.0f} min")
    print(f"Total raw train images: {total_raw}")
    return downloaded


def merge_datasets(downloaded):
    """Merge all datasets into one unified YOLO dataset with correct class IDs."""
    import os, shutil, yaml, glob

    MERGED = "/content/merged"
    IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")

    KEYWORD_TO_UNIFIED = {
        "garb": "garbage", "trash": "garbage", "waste": "garbage", "litter": "garbage",
        "poth": "pothole", "crack": "pothole", "road damage": "pothole",
        "leak": "water_leak", "pipe leak": "water_leak", "water": "water_leak",
        "street-lamp": "streetlight", "street light": "streetlight",
        "lightpost": "streetlight", "asimetrica": "streetlight",
        "drain": "drainage", "sewer": "drainage", "manhole": "drainage", "hole": "drainage",
        "sidewalk": "sidewalk_damage", "edge break": "sidewalk_damage",
        "joint": "sidewalk_damage", "metal grate": "sidewalk_damage", "patch": "sidewalk_damage",
    }

    def unify_index(raw_name):
        n = str(raw_name).lower()
        for kw, unified in KEYWORD_TO_UNIFIED.items():
            if kw in n:
                return UNIFIED_CLASSES.index(unified)
        return None

    def resolve_split_dirs(root, split):
        img_candidates = [os.path.join(root, split, "images"), os.path.join(root, split)]
        img_dir = next((d for d in img_candidates if os.path.isdir(d)), None)
        if img_dir is None:
            return None, None
        lbl_candidates = [os.path.join(root, split, "labels"), img_dir]
        lbl_dir = next((d for d in lbl_candidates if os.path.isdir(d)), None)
        return img_dir, lbl_dir

    for split in ("train", "valid"):
        os.makedirs(f"{MERGED}/images/{split}", exist_ok=True)
        os.makedirs(f"{MERGED}/labels/{split}", exist_ok=True)

    stats = {c: 0 for c in UNIFIED_CLASSES}
    skipped_boxes = 0

    for entry in downloaded:
        tag = entry["spec"]["tag"]
        root = entry["location"]
        with open(os.path.join(root, "data.yaml")) as f:
            names = yaml.safe_load(f)["names"]
        if isinstance(names, dict):
            names = [names[k] for k in sorted(names)]
        id_map = [unify_index(n) for n in names]
        print(f"[{tag}] source -> unified: {list(zip(names, id_map))}")

        for split in ("train", "valid", "test"):
            src_img, src_lbl = resolve_split_dirs(root, split)
            if src_img is None or src_lbl is None:
                continue
            for fname in os.listdir(src_img):
                stem, ext = os.path.splitext(fname)
                if ext.lower() not in IMG_EXTS:
                    continue
                src_path = os.path.join(src_img, fname)
                if not os.path.isfile(src_path):
                    continue
                lbl_path = os.path.join(src_lbl, stem + ".txt")
                if not os.path.isfile(lbl_path):
                    continue

                new_lines = []
                skip = False
                with open(lbl_path) as lf:
                    for line in lf:
                        parts = line.strip().split()
                        if len(parts) < 5:
                            continue
                        old_id = int(parts[0])
                        if old_id >= len(id_map) or id_map[old_id] is None:
                            skip = True
                            skipped_boxes += 1
                            continue
                        new_id = id_map[old_id]
                        new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
                        stats[UNIFIED_CLASSES[new_id]] += 1
                if skip and not new_lines:
                    continue

                dst_split = "train" if split == "train" else "valid"
                dst_img = f"{MERGED}/images/{dst_split}/{tag}_{fname}"
                dst_lbl = f"{MERGED}/labels/{dst_split}/{tag}_{stem}.txt"
                shutil.copy2(src_path, dst_img)
                with open(dst_lbl, "w") as f:
                    f.writelines(new_lines)

    print("\nMerged totals (all splits, before balancing):")
    for c in UNIFIED_CLASSES:
        print(f"  {c:16s} {stats[c]:6d} boxes")
    print(f"  skipped boxes: {skipped_boxes}")
    return MERGED


def balance_dataset(MERGED):
    """Cap big classes at BALANCE_CAP, oversample minority classes."""
    import os, shutil, math, random, glob, collections

    train_img_dir = f"{MERGED}/images/train"

    def label_path_for(img, split="train"):
        stem = os.path.splitext(os.path.basename(img))[0]
        return f"{MERGED}/labels/{split}/{stem}.txt"

    groups = {c: [] for c in UNIFIED_CLASSES}
    for img in sorted(glob.glob(train_img_dir + "/*")):
        lbl = label_path_for(img, "train")
        if not os.path.exists(lbl):
            continue
        ids = set()
        with open(lbl) as f:
            for l in f:
                parts = l.split()
                if len(parts) >= 5:
                    ids.add(int(parts[0]))
        present = {UNIFIED_CLASSES[i] for i in ids if i < len(UNIFIED_CLASSES)}
        if len(present) == 1:
            groups[list(present)[0]].append(img)
        elif len(present) > 1:
            groups["multi"] = groups.get("multi", []) + [img]

    for c in UNIFIED_CLASSES:
        random.shuffle(groups[c])
        for img in groups[c][BALANCE_CAP:]:
            os.remove(img)
            lbl = label_path_for(img, "train")
            if os.path.exists(lbl):
                os.remove(lbl)
        groups[c] = groups[c][:BALANCE_CAP]
        print(f"[cap] {c:16s} kept {len(groups[c])}")

    for c in UNIFIED_CLASSES:
        n = len(groups[c])
        if n < BALANCE_FLOOR and n > 0:
            copies_needed = math.ceil(BALANCE_FLOOR / n) - 1
            orig = list(groups[c])
            for i in range(copies_needed):
                for img in orig:
                    stem, ext = os.path.splitext(os.path.basename(img))
                    new_stem = f"{stem}_bal{i}"
                    shutil.copy(img, f"{train_img_dir}/{new_stem}{ext}")
                    shutil.copy(label_path_for(img, "train"),
                                f"{MERGED}/labels/train/{new_stem}.txt")
            print(f"[up]  {c:16s} oversampled x{copies_needed + 1} -> ~{len(groups[c]) * (copies_needed + 1)} images")
        else:
            print(f"[ok]  {c:16s} already at {n} images")

    return len(glob.glob(train_img_dir + "/*"))


def write_data_yaml(MERGED):
    import os, glob, yaml
    data_yaml = {
        "path": MERGED,
        "train": "images/train",
        "val": "images/valid",
        "names": {i: c for i, c in enumerate(UNIFIED_CLASSES)},
    }
    with open(f"{MERGED}/data.yaml", "w") as f:
        yaml.dump(data_yaml, f)
    train_n = len(glob.glob(f"{MERGED}/images/train/*"))
    val_n = len(glob.glob(f"{MERGED}/images/valid/*"))
    print(f"data.yaml written | train={train_n}  valid={val_n}")
    assert train_n > 300 and val_n > 50, "Too few images - check merge/balance steps."
    return train_n, val_n


def train(MERGED, train_n, val_n):
    """Train 20 epochs with keep-alive + auto-resume."""
    import os, time, threading
    from ultralytics import YOLO

    keep_alive_running = True

    def heartbeat():
        while keep_alive_running:
            try:
                with open("/content/.heartbeat", "w") as f:
                    f.write(str(time.time()))
            except Exception:
                pass
            time.sleep(300)

    threading.Thread(target=heartbeat, daemon=True).start()
    print("Keep-alive heartbeat started.")

    CKPT_DIR = "/content/runs/civic_v5"
    LAST_CKPT = f"{CKPT_DIR}/weights/last.pt"
    BEST_PATH = f"{CKPT_DIR}/weights/best.pt"

    if os.path.exists(LAST_CKPT):
        print(f"Found previous checkpoint: {LAST_CKPT} -> resuming...")
        model = YOLO(LAST_CKPT)
        model.train(
            data=f"{MERGED}/data.yaml",
            epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, patience=PATIENCE,
            cos_lr=True, seed=7, name="civic_v5", project="/content/runs",
            resume=True,
        )
    else:
        print(f"Starting fresh training: {MODEL}, {EPOCHS} epochs, batch={BATCH}")
        print(f"Images: ~{train_n} train, ~{val_n} valid")
        model = YOLO(MODEL)
        model.train(
            data=f"{MERGED}/data.yaml",
            epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, patience=PATIENCE,
            cos_lr=True, seed=7, name="civic_v5", project="/content/runs",
        )

    keep_alive_running = False
    print(f"\nBest weights: {BEST_PATH}")
    print("If Colab disconnected mid-run, just re-run this script to auto-resume.")
    return BEST_PATH


def validate(BEST_PATH, MERGED):
    import glob
    from ultralytics import YOLO
    from IPython.display import Image as IPyImage, display

    best = YOLO(BEST_PATH)
    m = best.val(data=f"{MERGED}/data.yaml", conf=0.30)

    print("\n=== MODEL METRICS ===")
    print(f"mAP@50    : {m.box.map50:.3f}")
    print(f"mAP@50-95 : {m.box.map:.3f}")
    print("\nPer-class mAP@50:")
    n = len(m.box.ap50) if hasattr(m.box, "ap50") else 0
    for i in range(n):
        print(f"  {UNIFIED_CLASSES[i]:16s} mAP50={m.box.ap50[i]:.3f}")

    cm_paths = (glob.glob("/content/runs/civic_v5/*/confusion_matrix.png") +
                glob.glob("/content/runs/civic_v5/confusion_matrix.png") +
                glob.glob("/content/runs/val*/confusion_matrix.png"))
    if cm_paths:
        display(IPyImage(cm_paths[-1], width=520))
    else:
        print("confusion_matrix.png not found")


def sanity_check(BEST_PATH):
    """Upload photos and print the exact text the app will show."""
    from ultralytics import YOLO
    from google.colab import files
    from PIL import Image
    from IPython.display import display

    best = YOLO(BEST_PATH)
    print("Upload test photos (night streetlight, pothole, garbage, etc.):")
    uploaded = files.upload()
    for name in uploaded:
        r = best.predict(source=name, conf=0.30, verbose=False)[0]
        dets = sorted([(best.names[int(b.cls[0])], round(float(b.conf[0]), 2))
                       for b in r.boxes], key=lambda t: -t[1])
        print(f"\n{name} -> {dets if dets else 'NO DETECTION'}")
        if len(r.boxes):
            display(Image.fromarray(r.plot()[:, :, ::-1]))


def export_and_download(BEST_PATH):
    """Export ONNX (the file the app loads) and download both files."""
    import os, shutil
    from ultralytics import YOLO

    shutil.copy(BEST_PATH, "/content/civic_yolov8.pt")
    best = YOLO(BEST_PATH)
    best.export(format="onnx", opset=12, simplify=True)
    onnx_src = BEST_PATH.replace(".pt", ".onnx")
    shutil.copy(onnx_src, "/content/civic_yolov8.onnx")

    print("Files ready:")
    print(f"  /content/civic_yolov8.pt   ({os.path.getsize('/content/civic_yolov8.pt')/1e6:.1f} MB)")
    print(f"  /content/civic_yolov8.onnx ({os.path.getsize('/content/civic_yolov8.onnx')/1e6:.1f} MB)")

    try:
        from google.colab import files
        files.download("/content/civic_yolov8.pt")
        files.download("/content/civic_yolov8.onnx")
    except Exception:
        print("\nNot in Colab? Files are at /content/civic_yolov8.pt and .onnx - download them manually.")

    print("\nNOW DEPLOY:")
    print("  1. Overwrite UrbanEye/backend/ai/models/civic_yolov8.onnx")
    print("  2. Overwrite UrbanEye/backend/ai/models/civic_yolov8.pt")
    print("  3. Restart the backend. Capture a photo -> app shows correct class text.")


def main():
    install()
    if not check_gpu():
        return

    downloaded = download_datasets()
    MERGED = merge_datasets(downloaded)
    train_n = balance_dataset(MERGED)
    train_n, val_n = write_data_yaml(MERGED)
    BEST_PATH = train(MERGED, train_n, val_n)
    validate(BEST_PATH, MERGED)
    sanity_check(BEST_PATH)
    export_and_download(BEST_PATH)


if __name__ == "__main__":
    main()