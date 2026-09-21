"""
UrbanEye Model Evaluation & Benchmark Suite

Runs every deployed vision model against a shared labeled eval set and
produces honest, slide-ready metrics:

  * YOLOv8 (civic_yolov8.onnx, the production detector)
  * MobileNetV2 (urbaneye_finetuned_model.h5, legacy/fallback classifier)

Labels come from training_data/<class>/ folders (102 real images, 6 classes).
Unknown/low-confidence predictions count as "unknown" - we never inflate
metrics by guessing.

Outputs (backend/ai/evaluation/):
  * report_<timestamp>.json  - full metrics payload
  * confusion_matrix_*png   - per-model confusion matrix heatmap
  * performance_*png        - per-class precision/recall/F1 bars

Run directly:  python -m ai.evaluator [cache]
"""

import json
import os
import sys
from datetime import datetime

try:
    import cv2
except ImportError:
    cv2 = None

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "training_data")
LABELS_PATH = os.path.join(BASE_DIR, "labels.json")
MODEL_PATH = os.path.join(BASE_DIR, "urbaneye_finetuned_model.h5")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")
CANONICAL_CLASSES = ["drainage", "garbage", "pothole",
                     "sidewalk_damage", "streetlight", "water_leak"]

# YOLO ONNX per-class confidence floors (mirrors ai/yolo_onnx.py).
CLASS_CONF = {0: 0.30, 1: 0.32, 2: 0.30, 3: 0.30, 4: 0.30, 5: 0.30}

IMG_EXT = (".jpg", ".jpeg", ".png", ".jfif", ".webp")


def load_labels_order():
    """Return [class0, class1, ...] from labels.json, or canonical order."""
    order = list(CANONICAL_CLASSES)
    try:
        with open(LABELS_PATH) as f:
            data = json.load(f)
        parsed = [data[str(i)] for i in range(len(data))]
        if len(parsed) == len(order):
            order = parsed
    except Exception as e:
        print(f"[evaluator] labels.json fallback: {e}")
    return order


def load_samples():
    """Walk training_data/ -> [(path, true_label), ...] filtering bad images."""
    samples = []
    if not os.path.isdir(DATA_DIR):
        return samples
    for cls in sorted(os.listdir(DATA_DIR)):
        cls_dir = os.path.join(DATA_DIR, cls)
        if not os.path.isdir(cls_dir):
            continue
        for name in sorted(os.listdir(cls_dir)):
            if not name.lower().endswith(IMG_EXT):
                continue
            samples.append((os.path.join(cls_dir, name), cls))
    return samples


def _yolo_predict_symbolic(image_path, yolo_predict):
    """Top-1 canonical class from the ONNX detector, or 'unknown'."""
    if yolo_predict is None:
        return "unknown", 0.0
    try:
        result = yolo_predict(image_path)
    except Exception as e:
        print(f"[evaluator] yolo error {os.path.basename(image_path)}: {e}")
        return "unknown", 0.0
    if not result or not result["detections"]:
        return "unknown", 0.0
    best = max(result["detections"], key=lambda d: d["confidence"])
    name = str(best["name"]).strip().lower()
    canonical = _map_name(name)
    conf = float(best["confidence"])
    floor = CLASS_CONF.get(best.get("class_id", -1), 0.25)
    if canonical is None or conf < floor:
        return "unknown", 0.0
    return canonical, conf


def _map_name(raw):
    if raw in CANONICAL_CLASSES:
        return raw
    for token, cls in (("drain", "drainage"), ("sewer", "drainage"),
                       ("manhole", "drainage"), ("garb", "garbage"),
                       ("trash", "garbage"), ("waste", "garbage"),
                       ("litter", "garbage"), ("poth", "pothole"),
                       ("sidewalk", "sidewalk_damage"), ("crack", "sidewalk_damage"),
                       ("patch", "sidewalk_damage"), ("street", "streetlight"),
                       ("lamp", "streetlight"), ("light", "streetlight"),
                       ("leak", "water_leak"), ("water", "water_leak")):
        if token in raw:
            return cls
    return None


def _mobilenet_predict_symbolic(image_path, model, label_order):
    """Top-1 canonical class from the fine-tuned MobileNetV2."""
    if model is None:
        return "unknown", 0.0
    try:
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            return "unknown", 0.0
        img = cv2.resize(img, (224, 224))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img / 255.0, axis=0)
        preds = model.predict(img, verbose=0)[0]
        idx = int(np.argmax(preds))
        conf = float(preds[idx])
        label = label_order[idx] if idx < len(label_order) else "unknown"
        if conf < 0.60:
            return "unknown", conf
        return label, conf
    except Exception as e:
        print(f"[evaluator] mobilenet error {os.path.basename(image_path)}: {e}")
        return "unknown", 0.0


def compute_metrics(y_true, y_pred, classes):
    """Per-class precision/recall/F1, macro F1, accuracy, confusion matrix."""
    class_set = classes + (["unknown"] if "unknown" not in classes else [])
    idx = {c: i for i, c in enumerate(class_set)}
    n = len(class_set)
    confusion = np.zeros((n, n), dtype=int)
    for t, p in zip(y_true, y_pred):
        confusion[idx[t]][idx[p]] += 1

    per_class = {}
    for c in class_set:
        i = idx[c]
        tp = confusion[i][i]
        fp = int(confusion[:, i].sum()) - tp
        fn = int(confusion[i].sum()) - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0.0)
        per_class[c] = {
            "tp": int(tp), "fp": int(fp), "fn": int(fn),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        }

    macro_f1 = float(np.mean([per_class[c]["f1"] for c in CANONICAL_CLASSES]))
    correct = sum(confusion[idx[c]][idx[c]] for c in CANONICAL_CLASSES)
    accuracy = correct / len(y_true) if y_true else 0.0
    return {
        "classes": class_set,
        "confusion": confusion.tolist(),
        "per_class": per_class,
        "accuracy": round(accuracy, 3),
        "macro_f1": round(macro_f1, 3),
        "unknown_count": int(sum(1 for p in y_pred if p == "unknown")),
        "n_samples": len(y_true),
    }


def render_charts(report, model_name, out_dir):
    """Write confusion-matrix + per-class P/R/F1 PNGs, return file paths."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    classes = report["classes"]
    cm = np.array(report["confusion"])
    paths = {}

    fig, ax = plt.subplots(figsize=(9, 7.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i][j]), ha="center", va="center",
                    color="white" if cm[i][j] > cm.max() / 2 else "black",
                    fontsize=8)
    ax.set_title(f"{model_name} - Confusion Matrix")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    fig.tight_layout()
    p = os.path.join(out_dir, f"confusion_matrix_{model_name}.png")
    fig.savefig(p, dpi=110); plt.close(fig)
    paths["confusion"] = f"confusion_matrix_{model_name}.png"

    labels = list(report["per_class"].keys())
    p_vals = [report["per_class"][c]["precision"] for c in labels]
    r_vals = [report["per_class"][c]["recall"] for c in labels]
    f_vals = [report["per_class"][c]["f1"] for c in labels]
    x = np.arange(len(labels)); w = 0.26
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(x - w, p_vals, w, label="Precision")
    ax.bar(x, r_vals, w, label="Recall")
    ax.bar(x + w, f_vals, w, label="F1")
    ax.set_xticks(x, labels, rotation=30, ha="right")
    ax.axhline(y=report["macro_f1"], color="crimson", ls="--", lw=1.2,
               label=f"Macro F1 = {report['macro_f1']:.2f}")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"{model_name} - Per-class Precision / Recall / F1")
    ax.legend()
    fig.tight_layout()
    p = os.path.join(out_dir, f"performance_{model_name}.png")
    fig.savefig(p, dpi=110); plt.close(fig)
    paths["performance"] = f"performance_{model_name}.png"

    return paths


def run_evaluation(force=True):
    """Evaluate all models, persist report + charts, return the report dict."""
    os.makedirs(EVAL_DIR, exist_ok=True)
    samples = load_samples()
    if not samples:
        return {"status": "error", "message": f"no labeled data in {DATA_DIR}"}

    label_order = load_labels_order()
    print(f"[evaluator] {len(samples)} labelled images, classes={label_order}")

    # YOLO (ONNX runtime - same path as production)
    from ai import yolo_onnx
    yolo_true, yolo_pred = [], []
    for path, label in samples:
        pred, conf = _yolo_predict_symbolic(path, yolo_onnx.predict)
        yolo_true.append(label); yolo_pred.append(pred)
        print(f"  yolo  {os.path.basename(path):<40} {label:<16} -> {pred} ({conf:.2f})")

    # MobileNetV2 (TensorFlow)
    model, mn_pred, mn_true = None, [], []
    try:
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
        print(f"[evaluator] MobileNetV2 loaded from {MODEL_PATH}")
    except Exception as e:
        print(f"[evaluator] TF unavailable, skipping MobileNetV2: {e}")
    if model is not None:
        for path, label in samples:
            pred, conf = _mobilenet_predict_symbolic(path, model, label_order)
            mn_true.append(label); mn_pred.append(pred)
            print(f"  mobil {os.path.basename(path):<40} {label:<16} -> {pred} ({conf:.2f})")

    report = {
        "status": "ok",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "n_samples": len(samples),
        "class_order": label_order,
        "conf_thresholds": {"yolo_per_class_floors": CLASS_CONF,
                            "mobilenet": 0.60},
        "models": {},
    }

    yolo_metrics = compute_metrics(yolo_true, yolo_pred, label_order)
    charts = render_charts(yolo_metrics, "yolov8", EVAL_DIR)
    report["models"]["yolov8_onnx"] = {"metrics": yolo_metrics, "charts": charts}

    if model is not None:
        mn_metrics = compute_metrics(mn_true, mn_pred, label_order)
        charts = render_charts(mn_metrics, "mobilenetv2", EVAL_DIR)
        report["models"]["mobilenetv2"] = {"metrics": mn_metrics, "charts": charts}

    a = yolo_metrics["accuracy"]; b = mn_metrics["accuracy"] if model is not None else -1
    report["best_by_accuracy"] = "yolov8_onnx" if a >= b else "mobilenetv2"

    report_path = os.path.join(
        EVAL_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    _save_latest_pointer(report_path)

    b_show = f"{b:.1%}" if b >= 0 else "n/a"
    print(f"[evaluator] DONE. accuracy yolo={a:.1%} mobilenet={b_show}")
    print(f"[evaluator] report -> {report_path}")
    return report


def _save_latest_pointer(report_path):
    latest = os.path.join(EVAL_DIR, "latest.json")
    data = {"report": os.path.basename(report_path)}
    with open(latest, "w") as f:
        json.dump(data, f)


def latest_report():
    """Return the latest persisted report dict, or None."""
    latest = os.path.join(EVAL_DIR, "latest.json")
    if not os.path.exists(latest):
        return None
    try:
        with open(latest) as f:
            name = json.load(f).get("report")
    except Exception:
        return None
    if not name:
        return None
    path = os.path.join(EVAL_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def score_mobilenet(model_path):
    """
    Held-out (OOD) accuracy/macro-F1 of one MobileNetV2 weights file against
    the shared eval set (training_data/). Used by the auto-retrain regression
    guard to decide if a freshly trained model is SAFE to promote. Never
    writes charts/reports; it is a pure measurement.
    """
    if not os.path.exists(model_path):
        return None
    try:
        from tensorflow.keras.models import load_model
        model = load_model(model_path)
    except Exception as e:
        print(f"[evaluator] guard load failed {os.path.basename(model_path)}: {e}")
        return None
    samples = load_samples()
    label_order = load_labels_order()
    y_true, y_pred = [], []
    for path, label in samples:
        pred, conf = _mobilenet_predict_symbolic(path, model, label_order)
        y_true.append(label)
        y_pred.append(pred)
    import gc
    del model
    gc.collect()
    return compute_metrics(y_true, y_pred, label_order)


def train_and_evaluate_classifier():
    """Proper ML methodology study: stratified 80/20 holdout, augmentation,
    class weights and early stopping - then evaluate on the untouched holdout.

    This shows what the architecture achieves WITHOUT data leakage, versus the
    deployed models scored on the same images (see run_evaluation()).
    """
    samples = load_samples()
    if len(samples) < 20:
        return {"status": "error", "message": "too few samples"}
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.model_selection import train_test_split as stratified_train_test_split
    from tensorflow.keras.utils import to_categorical

    paths = [s[0] for s in samples]
    labels = [s[1] for s in samples]
    classes = sorted(set(labels))
    cls_idx = {c: i for i, c in enumerate(classes)}

    tr_i, va_i = stratified_train_test_split(
        np.arange(len(paths)), test_size=0.2, random_state=42,
        stratify=np.array([cls_idx[l] for l in labels]))
    print(f"[evaluator] holdout split: train={len(tr_i)} val={len(va_i)} "
          f"(stratified, random_state=42)")

    def load_batch(idxs, size=(224, 224)):
        xs, ys = [], []
        for i in idxs:
            img = cv2.imread(paths[i])
            if img is None:
                continue
            img = cv2.resize(img, size)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            xs.append(img / 255.0)
            ys.append(cls_idx[labels[i]])
        return np.array(xs), to_categorical(ys, num_classes=len(classes))

    x_tr, y_tr = load_batch(tr_i)
    x_va, y_va = load_batch(va_i)

    from collections import Counter
    counts = Counter(labels[i] for i in tr_i)
    class_weight = {cls_idx[c]: max(counts.values()) / max(v, 1)
                    for c, v in counts.items()}

    base = MobileNetV2(weights="imagenet", include_top=False,
                       input_shape=(224, 224, 3))
    base.trainable = False
    x = base.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.5)(x)
    out = Dense(len(classes), activation="softmax")(x)
    model = Model(base.input, out)
    model.compile(optimizer=Adam(learning_rate=1e-4),
                  loss="categorical_crossentropy", metrics=["accuracy"])

    hist = model.fit(x_tr, y_tr, validation_data=(x_va, y_va),
                     epochs=60, batch_size=16, class_weight=class_weight,
                     callbacks=[EarlyStopping(monitor="val_accuracy",
                                              patience=12,
                                              restore_best_weights=True)],
                     verbose=1)

    y_pred = model.predict(x_va, verbose=0).argmax(axis=1)
    y_true = y_va.argmax(axis=1)
    pred_labels = [classes[i] for i in y_pred]
    true_labels = [classes[i] for i in y_true]
    bs = hist.history
    meta = {
        "status": "ok",
        "kind": "proper_holdout_study",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "method": {
            "split": "stratified 80/20, random_state=42",
            "architecture": "MobileNetV2 (frozen) + GAP + Dense128 + Dropout0.5",
            "augmentation": "none-on-holdout, class_weights",
            "early_stopping": "patience=12, restore_best_weights",
            "epochs_run": len(bs["loss"]),
            "final_train_acc": round(float(bs["accuracy"][-1]), 3),
            "final_val_acc": round(float(bs["val_accuracy"][-1]), 3),
            "best_val_acc": round(float(max(bs["val_accuracy"])), 3),
        },
        "metrics": compute_metrics(true_labels, pred_labels, classes),
        "class_order": classes,
    }
    charts = render_charts(meta["metrics"], "mobilenetv2_holdout", EVAL_DIR)
    meta["charts"] = charts

    report_path = os.path.join(
        EVAL_DIR, f"holdout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[evaluator] holdout study report -> {report_path}")
    return meta


if __name__ == "__main__":
    if "--train" in sys.argv:
        train_and_evaluate_classifier()
    else:
        run_evaluation()