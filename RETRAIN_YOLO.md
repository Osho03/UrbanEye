# Retrain the UrbanEye Civic YOLOv8 Model

This guide fixes the **streetlight → pothole** (and similar) misclassification
permanently. It explains exactly why the current model fails and gives a
copy-paste Colab workflow to train a better one.

## Why the current model makes this mistake

Evidence pulled from the live model (`civic_yolov8.pt` training args):

| Setting | Value | Consequence |
|---|---|---|
| `model` | `yolov8n.pt` | **Nano** = smallest, weakest YOLOv8 (accuracy is sacrificed for speed) |
| `epochs` | 50 (patience 10) | Very short training, underfitted classes |
| confidence floor | `0.25` | Let junk boxes through (a dark road patch can score ~0.3 as "pothole") |
| primary pick | highest-confidence box | One junk box outranks the real (tiny) streetlight box |
| dataset | merged, contains near-duplicates | Duplicate photos inflate the same images and waste capacity |

A real photo came in that the nano model read as "$best" with a slightly
higher score than it gave to the actual streetlight. Because we asserted the
top-1 box, the app confidently printed the wrong class.

## The 3-part fix

1. **Already shipped** (no retraining): per-class confidence floors +
   "min 0.40 to assert" + "report `unknown` when two classes are too close".
   This stops confidently-wrong labels today (`backend/ai/yolo_onnx.py`,
   `backend/ai/yolo_detector.py`).
2. **This guide**: retrain on more/better data with a larger model so the
   model itself stops confusing the classes.
3. **Deploy check**: replace the deployed `.onnx`, then re-verify.

## Step 1 — Fix the data (most important)

The model can only be as good as its data.

- **Per class, ~100–150 images minimum** (streetlight especially):
  - streetlight: NIGHT photos (lit lamp heads), DAY photos (poles with lamps),
    distant + close, light-on + light-off, lamp on pole WITHOUT visible glow.
  - pothole: photos where a dark road patch is NOT a pothole, wet/dry/dark/light
    asphalt, so the model learns texture, not darkness.
  - Add "confuser" examples (poles, dark shadows, road patches) — this is what
    teaches the model the difference.
- **Remove exact/near-duplicate images.** The current dataset has pairs like
  `1770537476`/`1770537495` that are the same photo — the model memorizes them.
- **Class order MUST stay:** `0 garbage, 1 pothole, 2 water_leak, 3 streetlight,
  4 drainage, 5 sidewalk_damage` (matches `yolo_onnx.CLASS_NAMES`). Renumber
  your labels if needed so `data.yaml` names are exactly in that order.

## Step 2 — Train in Google Colab (free T4)

New notebook or a fresh cell block, running in that exact order:

```python
# 0) Install
!pip install -q ultralytics

# 1) Upload your dataset zip (YOLO format) and extract
from google.colab import files
import zipfile, os
uploaded = files.upload()            # pick your dataset.zip (images + labels/)
for name in uploaded:
    with zipfile.ZipFile(name, "r") as z:
        z.extractall("/content/merged")
!head -20 /content/merged/data.yaml  # must list names in the order above

# 2) Train with a LARGER model + many more epochs
!yolo detect train \
    model=yolov8m.pt \
    data=/content/merged/data.yaml \
    epochs=150 \
    imgsz=640 \
    batch=16 \
    patience=20 \
    project=/content/runs \
    name=civic_v3 \
    cos_lr=True

# 3) Check results (rates + confusion matrix)
from IPython.display import Image
!ls /content/runs/civic_v3
Image("/content/runs/civic_v3/confusion_matrix.png")

# 4) Save best model & export ONNX (opset 12, same as the deployed file)
!cp /content/runs/civic_v3/weights/best.pt /content/civic_yolov8.pt
!yolo export model=/content/civic_yolov8.pt format=onnx opset=12 simplify=True
!cp /content/civic_yolov8.onnx /content/civic_yolov8_final.onnx
from google.colab import files
files.download("/content/civic_yolov8.pt")
files.download("/content/civic_yolov8_final.onnx")
```

### Before you download, sanity-check it inside Colab

```python
from ultralytics import YOLO
m = YOLO("/content/civic_yolov8.pt")
# Upload 3-4 photos: a NIGHT streetlight (the one that failed), a day
# streetlight, a pure pothole, a dark road patch. Pose each as the test:
for path in ["/content/t1.jpg", "/content/t2.jpg", "/content/t3.jpg", "/content/t4.jpg"]:
    r = m.predict(path, conf=0.30)[0]
    print(path, [(m.names[int(b.cls[0])], round(float(b.conf[0]), 2)) for b in r.boxes])
```

If the failing streetlight photo now shows `streetlight` (and no `pothole`
above it), the fix is real.

## Step 3 — Deploy the new weights

1. Replace these two files in the repo (keep the same names):
   - `backend/ai/models/civic_yolov8.onnx`  (from `civic_yolov8_final.onnx`)
   - `backend/ai/models/civic_yolov8.pt`    (from `civic_yolov8.pt`)
2. Commit and push. Say "model updated" and the live backend will be
   re-verified automatically (the ONNX detect path picks up the new file on
   restart).
3. If the new model is confident enough, the per-class floors in
   `yolo_onnx.py` can be relaxed back toward 0.25 — retraining redeploy
   includes the floor values, so mention that when you want them tuned.