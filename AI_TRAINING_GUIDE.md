# 🎓 How to Train the AI Classifier

## Problem
The AI is misclassifying issues because it's using a **pretrained model** not trained on civic infrastructure images.

**Example**: "Damaged traffic light" → Detected as "Water Leak" ❌

## Solution: Train Your Own Model

### Step 1: Prepare Training Images

1. **Create folder structure**:
   ```
   backend/training_data/
   ├── pothole/          (20+ images of potholes)
   ├── garbage/          (20+ images of garbage dumps)
   ├── water_leak/       (20+ images of water leaks)
   ├── streetlight/      (20+ images of damaged streetlights)
   ├── sidewalk_damage/  (20+ images of broken sidewalks)
   └── drainage/         (20+ images of drainage issues)
   ```

2. **Collect images**:
   - Use your phone camera
   - Download from Google Images
   - Use images from past reports
   - **Minimum**: 20 images per category
   - **Recommended**: 50+ images per category for better accuracy

### Step 2: Run Training Script

```bash
cd d:\UrbanEye\backend\ai
python train_classifier.py
```

**What happens:**
1. Script checks for training data
2. Creates folders if they don't exist
3. Trains the model (takes 5-15 minutes)
4. Saves fine-tuned model as `urbaneye_finetuned_model.h5`

### Step 3: Backend Auto-Loads the Model

The backend automatically checks for `urbaneye_finetuned_model.h5`:
- If found → Uses your fine-tuned model ✅
- If not found → Uses pretrained model (current behavior)

**Just restart the backend** after training:
```bash
cd d:\UrbanEye\backend
.\start.bat
```

## Quick Start (First Time)

### Option A: Auto-Setup
```bash
cd d:\UrbanEye\backend\ai
python train_classifier.py
```
This creates the folders. Then manually add images.

### Option B: Manual Setup
1. Create `d:\UrbanEye\backend\training_data`
2. Create subfolders for each category
3. Add 20+ images to each folder
4. Run `python train_classifier.py`

## Expected Results

**Before Training**: ~60% accuracy (generic object detection)  
**After Training**: ~85-95% accuracy (civic issue specific)

## Example Training Output

```
📊 Found 6 categories
📊 Training samples: 120
📊 Validation samples: 30

Epoch 1/10
8/8 [==============================] - 15s 2s/step - loss: 1.2345 - accuracy: 0.6500
Epoch 10/10
8/8 [==============================] - 12s 1s/step - loss: 0.3214 - accuracy: 0.9200

✅ Model saved to: urbaneye_finetuned_model.h5
📊 Final training accuracy: 92.00%
📊 Final validation accuracy: 87.50%
```

## Tips for Better Accuracy

1. **Diverse Images**: Different angles, lighting, weather
2. **Clear Photos**: Avoid blurry images
3. **Correct Labels**: Put streetlight images in `streetlight/` folder, not `water_leak/`
4. **Balanced Data**: Similar number of images per category
5. **More Data**: 50+ images > 20 images

## Troubleshooting

**Error: "No training data found"**
→ Add images to the training_data folders

**Error: "Not enough images"**
→ Add at least 20 images per category

**Low accuracy (<70%)**
→ Add more diverse training images

**Model not loading**
→ Check `urbaneye_finetuned_model.h5` exists in `backend/ai/`
