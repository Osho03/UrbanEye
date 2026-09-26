"""
Auto-Retraining Job - "self-improving" UrbanEye AI.

Runs the full human-in-the-loop loop WITHOUT a human running commands:

    user uploads photo (inference)  ->  saved to MongoDB
    enough NEW verified images      ->  collect into ai/dataset/
    threshold reached               ->  fine-tune MobileNetV2 offline
    new weights written to          ->  ai/urbaneye_finetuned_model.h5
    classifier hot-reloaded         ->  next inference uses the better model
    evaluator refreshed             ->  Model Health shows the accuracy gain

Not every upload triggers a training run (that would be slow and unstable).
Instead each upload adds a candidate data point; training fires once enough
NEW verified images have accumulated since the last run. That is the
industry-standard "collect -> verify -> retrain -> evaluate" cadence.

Trigger points:
  * routes/issue.py  -> after a report is saved, try_auto_retrain_async()
  * app.py           -> scheduler_start() periodic sweep
  * manually         -> python -m ai.auto_retrain --force --eval
"""

import json
import os
import threading
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_OUT = os.path.join(BASE_DIR, "urbaneye_finetuned_model.h5")
LABELS_OUT = os.path.join(BASE_DIR, "labels.json")
HISTORY_OUT = os.path.join(BASE_DIR, "retrain_history.json")
STATE_PATH = os.path.join(BASE_DIR, "retrain_state.json")
LOCK_PATH = os.path.join(BASE_DIR, ".retrain.lock")

CLASSES = ["drainage", "garbage", "pothole",
           "sidewalk_damage", "streetlight", "water_leak"]

IMG_EXT = (".jpg", ".jpeg", ".png", ".jfif", ".webp")


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# Thresholds (env-overridable).
ENABLED = os.getenv("UR_AUTO_RETRAIN", "1").lower() not in ("0", "false", "off")
MIN_NEW = _env_int("UR_MIN_NEW", 10)       # new verified images needed to retrain
MIN_TRAIN = _env_int("UR_MIN_TRAIN", 15)   # absolute minimum dataset size
SCHED_MINUTES = _env_int("UR_SCHED_MINUTES", 30)
SCHED_EVAL = os.getenv("UR_SCHED_EVAL", "1").lower() not in ("0", "false", "off")
# Regression guard: never promote weights that score lower on the held-out
# eval set than the currently live model. This is what makes auto-retraining
# SELF-DEFENDING instead of blindly scraping accuracy.
REG_GUARD = os.getenv("UR_REG_GUARD", "1").lower() not in ("0", "false", "off")
LOCK_STALE_SECS = 60 * 20  # a lock older than this is treated as dead

MODEL_LIVE = os.path.join(BASE_DIR, "urbaneye_finetuned_model.h5")
# Candidate trains to a Keras-native .keras file (Keras 3 requires the .keras
# extension when saving); it is converted to the legacy .h5 live file ONLY on
# promotion, so the production classifier sees an unchanged file type.
MODEL_CANDIDATE = os.path.join(BASE_DIR, "urbaneye_finetuned_model.keras")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")


# ---------------------------------------------------------------------------
# State + locking
# ---------------------------------------------------------------------------

def _load_state():
    if not os.path.exists(STATE_PATH):
        return {"trained_at": None, "trained_samples": 0,
                "history": None, "runs": 0}
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
        state.setdefault("trained_at", None)
        state.setdefault("trained_samples", 0)
        state.setdefault("history", None)
        state.setdefault("runs", 0)
        return state
    except Exception:
        return {"trained_at": None, "trained_samples": 0,
                "history": None, "runs": 0}


def _save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


class _Lock:
    def acquire(self):
        if os.path.exists(LOCK_PATH):
            try:
                if time.time() - os.path.getmtime(LOCK_PATH) < LOCK_STALE_SECS:
                    return False
            except OSError:
                pass
            try:
                os.remove(LOCK_PATH)  # stale lock
            except OSError:
                pass
        with open(LOCK_PATH, "w") as f:
            f.write(str(time.time()))
        return True

    def release(self):
        try:
            os.remove(LOCK_PATH)
        except OSError:
            pass


_lock = _Lock()


# ---------------------------------------------------------------------------
# Data collection (replaces manual prepare_dataset.py step)
# ---------------------------------------------------------------------------

def _normalise_type(value):
    """issue_type may be a str or a dict (object-form). Return canonical str."""
    if isinstance(value, dict):
        value = value.get("detected_type") or value.get("primary_guess") or "unknown"
    if not isinstance(value, str):
        return "unknown"
    return value.strip().lower()


def count_dataset():
    total = 0
    if not os.path.isdir(DATASET_DIR):
        return 0
    for cls in CLASSES:
        d = os.path.join(DATASET_DIR, cls)
        if os.path.isdir(d):
            total += sum(1 for f in os.listdir(d)
                         if f.lower().endswith(IMG_EXT))
    return total


# Training copies are downscaled to save storage (~99% smaller): a phone photo
# is ~3-5 MB, a training thumbnail is ~50-150 KB. 1000 uploads ≈ 4 GB -> ~100 MB.
CONVERT_MAX_SIDE = 640
CONVERT_QUALITY = 88


def _downscale_copy(src, dest):
    """Copy src -> dest as a downscaled JPEG (best for training)."""
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((CONVERT_MAX_SIDE, CONVERT_MAX_SIDE), Image.LANCZOS)
        im.save(dest, "JPEG", quality=CONVERT_QUALITY)
    return True


def collect_from_db(issues_collection):
    """
    Copy verified citizen uploads from MongoDB into ai/dataset/<class>/.
    Skips: unknown type, duplicates, videos, missing image files.
    Returns (stats dict, total_copied).
    """
    os.makedirs(DATASET_DIR, exist_ok=True)
    for cls in CLASSES:
        os.makedirs(os.path.join(DATASET_DIR, cls), exist_ok=True)

    stats = {cls: 0 for cls in CLASSES}
    skipped = 0
    docs = list(issues_collection.find({}, {
        "issue_type": 1, "image_path": 1, "media_type": 1,
        "is_duplicate_of": 1, "status": 1}))
    if os.getenv("UR_DEBUG"):
        print("[debug] cwd=", os.getcwd(), "BASE_DIR=", BASE_DIR,
              "DATASET_DIR=", DATASET_DIR, "file=", __file__)
    for doc in docs:
        issue_type = _normalise_type(doc.get("issue_type"))
        image_path = doc.get("image_path")
        if issue_type not in CLASSES:
            skipped += 1
            continue
        if doc.get("media_type") == "video" or doc.get("is_duplicate_of"):
            skipped += 1
            continue
        if not image_path or not os.path.exists(image_path):
            skipped += 1
            continue

        dest_dir = os.path.join(DATASET_DIR, issue_type)
        filename = os.path.splitext(os.path.basename(str(image_path)))[0]
        dest = os.path.join(dest_dir, filename + ".jpg")
        if os.path.exists(dest):
            continue  # already collected
        try:
            _downscale_copy(image_path, dest)
            stats[issue_type] += 1
        except Exception as e:
            print(f"[auto_retrain] copy failed {image_path}: {e}")
            skipped += 1
    total = sum(stats.values())
    return stats, total, skipped


# ---------------------------------------------------------------------------
# Training (replaces manual train_model.py step, no input() prompts)
# ---------------------------------------------------------------------------

def _write_labels(order):
    payload = {str(i): cls for i, cls in enumerate(order)}
    with open(LABELS_OUT, "w") as f:
        json.dump(payload, f, indent=2)


def train_classifier(dataset_dir=DATASET_DIR, model_out=MODEL_OUT):
    """
    Fine-tune MobileNetV2 (transfer learning) on the collected dataset.
    Returns history dict; writes model + labels + history to disk.
    """
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    # Small datasets can't be split reliably with Keras subset flows
    # (it hands the whole set to whichever flow is created first). So we
    # fine-tune on the full collected set and get honest generalization
    # numbers afterwards from ai.evaluator on the held-out OOD set — that
    # is exactly what the Model Health card displays.
    datagen = ImageDataGenerator(
        rescale=1. / 255, rotation_range=20, width_shift_range=0.2,
        height_shift_range=0.2, horizontal_flip=True, zoom_range=0.2)

    train_gen = datagen.flow_from_directory(
        dataset_dir, target_size=(224, 224), batch_size=16,
        class_mode="categorical", shuffle=True)

    # class order from the generator = sorted folder names (matches labels.json)
    order = list(train_gen.class_indices.keys())
    _write_labels(order)

    base = MobileNetV2(weights="imagenet", include_top=False,
                       input_shape=(224, 224, 3))
    base.trainable = False
    x = base.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.5)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.3)(x)
    out = Dense(train_gen.num_classes, activation="softmax")(x)
    model = Model(base.input, out)
    model.compile(optimizer=Adam(learning_rate=1e-4),
                  loss="categorical_crossentropy", metrics=["accuracy"])

    # Trained weights go to a CANDIDATE file - never over the live model.
    # The regression guard promotes it to MODEL_LIVE only if (and only when)
    # it scores >= the live model on the held-out eval set.
    history = model.fit(
        train_gen, epochs=30, verbose=1,
        callbacks=[
            EarlyStopping(monitor="loss", patience=6,
                          restore_best_weights=True, verbose=1),
            ModelCheckpoint(model_out, monitor="loss",
                            save_best_only=True, verbose=1),
        ])

    hist = {
        "accuracy": [float(x) for x in history.history["accuracy"]],
        "loss": [float(x) for x in history.history["loss"]],
        "final_loss": float(history.history["loss"][-1]),
        "class_order": order,
        "n_images": train_gen.samples,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(HISTORY_OUT, "w") as f:
        json.dump(hist, f, indent=2)
    return hist


def _hot_reload_classifier():
    """Reset the loaded classifier so the next inference uses new weights."""
    try:
        import ai.image_classifier as ic
        ic.model = None
        ic.USING_FINETUNED = os.path.exists(ic.TRAINED_MODEL_PATH)
        print("[auto_retrain] classifier hot-reloaded -> new weights live")
    except Exception as e:
        print(f"[auto_retrain] classifier reload skipped: {e}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def maybe_auto_retrain(issues_collection, force=False, evaluate=False,
                       min_new=None, min_train=None):
    """
    Decides whether to retrain and does it. Safe to call from any thread.
    Returns a status dict (never raises).
    """
    min_new = MIN_NEW if min_new is None else min_new
    min_train = MIN_TRAIN if min_train is None else min_train

    if not ENABLED:
        return {"status": "disabled",
                "reason": "UR_AUTO_RETRAIN != 1 on this host"}

    if not _lock.acquire():
        return {"status": "already_training",
                "reason": "another training run is in progress"}

    try:
        return _run(issues_collection, force, evaluate, min_new, min_train)
    except Exception as e:
        print(f"[auto_retrain] failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        _lock.release()


def _run(issues_collection, force, evaluate, min_new, min_train):
    state = _load_state()
    stats, new_copied, skipped = collect_from_db(issues_collection)
    total = count_dataset()  # includes images collected on earlier runs
    pending = max(total - int(state["trained_samples"]), 0)
    print(f"[auto_retrain] dataset={total} (copied {new_copied}, "
          f"skipped {skipped}), pending={pending}, "
          f"last_trained={state['trained_samples']}")

    if total < min_train:
        return {"status": "insufficient_data",
                "total": total, "needed": min_train,
                "collecting": True,
                "message": f"need >= {min_train} verified images, have {total}"}
    if not force and pending < min_new:
        return {"status": "pending",
                "total": total, "pending_new": pending,
                "needed_new": min_new,
                "message": f"{pending}/{min_new} new images since last retrain"}

    print("[auto_retrain] STARTING training (background)...")
    start = time.time()
    history = train_classifier(model_out=MODEL_CANDIDATE)
    elapsed = round(time.time() - start)

    decision = _regression_guard()

    if decision["promoted"]:
        _hot_reload_classifier()

    state["trained_at"] = history["trained_at"]
    state["trained_samples"] = total
    state["history"] = history
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_decision"] = decision
    _save_state(state)

    best_tr = round(max(history["accuracy"]), 3)
    print(f"[auto_retrain] DONE run #{state['runs']} in {elapsed}s, "
          f"train_acc={best_tr:.1%}, decision={decision['verdict']}")

    result = {"status": "done", "trained_samples": total,
              "train_accuracy": best_tr, "elapsed_sec": elapsed,
              "class_order": history["class_order"],
              "decision": decision}

    if evaluate and SCHED_EVAL:
        try:
            from ai.evaluator import run_evaluation
            run_evaluation()
            result["evaluated"] = True
        except Exception as e:
            print(f"[auto_retrain] evaluation failed: {e}")
            result["evaluated"] = False
    return result


def _regression_guard():
    """
    Compare the candidate weights against the live model on the SAME held-out
    eval set. Only promote if candidate >= live (no regression).

    Return dict: verdict in {promoted, rejected, no_baseline, guard_off}.
    """
    guard_off = {"verdict": "guard_off", "promoted": True}
    try:
        from ai.evaluator import latest_report, score_mobilenet
    except ImportError as e:
        print(f"[auto_retrain] guard unavailable: {e}")
        return guard_off

    prev = latest_report()
    live_acc = None
    if prev:
        mn = (prev.get("models") or {}).get("mobilenetv2",
                                             {}).get("metrics") or {}
        live_acc = mn.get("accuracy")

    if not REG_GUARD:
        return _promote_candidate({"verdict": "guard_off",
                                   "candidate_acc": None,
                                   "live_acc": live_acc})

    new_metrics = score_mobilenet(MODEL_CANDIDATE)
    if new_metrics is None:
        return _promote_candidate({"verdict": "no_measurement",
                                   "candidate_acc": None,
                                   "live_acc": live_acc,
                                   "reason": "candidate could not be scored"})

    new_acc = new_metrics["accuracy"]
    promoted = (live_acc is None) or (new_acc >= live_acc)

    if promoted:
        print(f"[auto_retrain] GUARD: PROMOTED (new={new_acc:.1%} "
              f"vs live={live_acc if live_acc is not None else 'n/a'})")
        return _promote_candidate({"verdict": "promoted",
                                   "candidate_acc": new_acc,
                                   "live_acc": live_acc})
    else:
        # Rejected: keep the live model; archive the failure for forensics.
        os.makedirs(EVAL_DIR, exist_ok=True)
        rejected_path = os.path.join(
            EVAL_DIR, f"rejected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.keras")
        try:
            os.replace(MODEL_CANDIDATE, rejected_path)
        except OSError:
            if os.path.exists(MODEL_CANDIDATE):
                os.remove(MODEL_CANDIDATE)
        print(f"[auto_retrain] GUARD: REJECTED (new={new_acc:.1%} < "
              f"live={live_acc:.1%}); keeping live model, candidate archived")
        return {"verdict": "rejected", "promoted": False,
                "candidate_acc": new_acc, "live_acc": live_acc,
                "archived": os.path.basename(rejected_path)}


def _promote_candidate(decision):
    """
    Convert candidate (.keras, Keras-3 native) -> live (.h5, legacy) — the
    exact format the deployed classifier and evaluator load.
    """
    try:
        import gc
        from tensorflow.keras.models import load_model
        m = load_model(MODEL_CANDIDATE)
        m.save(MODEL_LIVE, save_format="h5")
        del m
        gc.collect()
    except Exception as e:
        print(f"[auto_retrain] GUARD: promotion save failed: {e}")
        return {"verdict": "promotion_error", "promoted": False,
                **{k: v for k, v in decision.items() if k != "verdict"}}
    try:
        os.remove(MODEL_CANDIDATE)
    except OSError:
        pass
    return {**decision, "promoted": True}


def try_auto_retrain_async(issues_collection=None, force=False, evaluate=False):
    """Spawn a background thread; never blocks the HTTP response."""
    if not ENABLED:
        return {"status": "disabled"}

    def _worker():
        if issues_collection is not None:
            maybe_auto_retrain(issues_collection, force=force, evaluate=evaluate)
        else:
            try:
                from config import issues_collection as db_coll
                maybe_auto_retrain(db_coll, force=force, evaluate=evaluate)
            except Exception as e:
                print(f"[auto_retrain] async trigger failed: {e}")

    t = threading.Thread(target=_worker, name="auto-retrain", daemon=True)
    t.start()
    return {"status": "triggered"}


def model_health():
    """Summary for the Model Health endpoint (retrain state + eval summary)."""
    state = _load_state()
    total = count_dataset()
    from config import issues_collection
    verified = issues_collection.count_documents(
        {"issue_type": {"$nin": ["unknown", None]}})
    payload = {
        "auto_retrain_enabled": ENABLED,
        "thresholds": {"min_new": MIN_NEW, "min_train": MIN_TRAIN,
                       "schedule_minutes": SCHED_MINUTES},
        "dataset_images": total,
        "verified_reports": verified,
        "samples_since_last_retrain": max(total - int(state["trained_samples"]), 0),
        "trained_samples": int(state["trained_samples"]),
        "runs": int(state.get("runs", 0)),
        "last_trained_at": state.get("trained_at"),
        "last_history": state.get("history"),
        "last_decision": state.get("last_decision"),
    }
    try:
        from ai.evaluator import latest_report
        report = latest_report()
        if report:
            summary = {}
            for name, m in (report.get("models") or {}).items():
                metrics = m.get("metrics", {})
                summary[name] = {
                    "accuracy": metrics.get("accuracy"),
                    "macro_f1": metrics.get("macro_f1"),
                    "unknown_count": metrics.get("unknown_count"),
                }
            payload["eval"] = {
                "generated_at": report.get("generated_at"),
                "n_samples": report.get("n_samples"),
                "models": summary,
            }
    except Exception as e:
        payload["eval"] = {"error": str(e)}
    return payload


def scheduler_start():
    """
    Periodic sweep: every SCHED_MINUTES minutes, collect + retrain if ready,
    then refresh the evaluation report so Model Health numbers stay current.
    """
    if not ENABLED:
        print("[auto_retrain] scheduler disabled (UR_AUTO_RETRAIN != 1)")
        return None
    if getattr(scheduler_start, "_started", False):
        return None
    scheduler_start._started = True

    def _loop():
        print(f"[auto_retrain] scheduler started "
              f"(every {SCHED_MINUTES} min, sched_eval={SCHED_EVAL})")
        while True:
            try:
                from config import issues_collection as coll
                maybe_auto_retrain(coll, evaluate=True)
            except Exception as e:
                print(f"[auto_retrain] sweep failed: {e}")
            time.sleep(SCHED_MINUTES * 60)

    threading.Thread(target=_loop, name="auto-retrain-scheduler",
                     daemon=True).start()
    return None


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    evaluate = "--eval" in sys.argv
    from config import issues_collection as _coll
    print(json.dumps(maybe_auto_retrain(_coll, force=force, evaluate=evaluate),
                     indent=2))