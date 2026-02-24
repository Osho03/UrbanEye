# 🎯 Complete AI Training Guide for UrbanEye

## What You'll Achieve
✅ **Perfect AI Classification** - Traffic lights detected correctly (90%+ accuracy)  
✅ **Voice Assistant** - AI reads results aloud to admin  
✅ **Detailed Analysis** - Complete breakdown shown in admin panel  

---

## Step 1: Install Required Packages ⚙️

```bash
cd d:\UrbanEye\backend
pip install numpy tensorflow keras pillow scikit-learn matplotlib
```

**Wait** for installation to complete (~5 minutes). You'll see:
```
Successfully installed tensorflow-2.x.x numpy-1.x.x keras-2.x.x...
```

---

## Step 2: Collect Training Images 📸

### How Many Images?
- **Minimum**: 50 images per category
- **Recommended**: 100+ images per category
- **Best**: 200+ images per category

### Where to Get Images?

#### Option A: Download from Google Images (Fastest)
1. Google: "pothole india" → Download 50+ different pothole images
2. Google: "broken streetlight mumbai" → Download 50+ traffic light images
3. Google: "water leak pipe" → Download 50+ water leak images
4. Repeat for all categories

#### Option B: Use Stock Photo Sites
- Unsplash.com → Search "infrastructure damage"
- Pexels.com → Search "road damage", "pothole"
- Pixabay.com → Free high-quality images

#### Option C: Take Your Own Photos
- Walk around your city
- Take photos of real civic issues
- Most authentic training data!

### Image Requirements
✅ **Format**: JPEG or PNG  
✅ **Quality**: Clear, well-lit  
✅ **Size**: Any size (will be auto-resized to 224×224)  
✅ **Variety**: Different angles, weather, time of day  

---

## Step 3: Organize Images 📁

Put images in these folders:

```
d:\UrbanEye\backend\training_data\
├── pothole\           ← 50+ pothole images
├── streetlight\       ← 50+ traffic light/streetlight images ⚡
├── water_leak\        ← 50+ water leak images
├── garbage\           ← 50+ garbage dump images
├── sidewalk_damage\   ← 50+ broken sidewalk images
└── drainage\          ← 50+ drainage issue images
```

**CRITICAL**: Traffic light images go in `streetlight/` folder!

### Example Filenames
```
streetlight/
  ├── traffic_light_broken_1.jpg
  ├── streetlight_damaged_2.jpg
  ├── signal_not_working_3.png
  └── ... (47 more images)
```

---

## Step 4: Run Training Script 🎓

```bash
cd d:\UrbanEye\backend\ai
python train_classifier.py
```

### What Happens:

1. **Script checks images**:
   ```
   ============================================================
   📊 TRAINING DATA SUMMARY
   ============================================================
      pothole             :  52 images ✓ GOOD
      streetlight         :  58 images ✓ GOOD
      water_leak          :  45 images ⚠️  MINIMUM
      garbage             :  63 images ✓ GOOD
      sidewalk_damage     :  51 images ✓ GOOD
      drainage            :  48 images ⚠️  MINIMUM
   
      TOTAL               : 317 images
   ============================================================
   ```

2. **Confirms training**:
   ```
   ✅ Ready to train!
   
      Start training now? (y/n): 
   ```
   Type: `y` and press Enter

3. **Training begins** (~10-20 minutes):
   ```
   🎯 STARTING TRAINING
   ============================================================
   ⏱️  Expected time: ~50 minutes
   📊 Tracking: Training accuracy & Validation accuracy
   
   🚀 Training in progress...
   
   Epoch 1/25
   20/20 [==============================] - 45s 2s/step - loss: 1.5432 - accuracy: 0.4500 - val_loss: 1.2345 - val_accuracy: 0.5800
   Epoch 2/25
   20/20 [==============================] - 38s 2s/step - loss: 1.1234 - accuracy: 0.6200 - val_loss: 0.9876 - val_accuracy: 0.7100
   ...
   Epoch 25/25
   20/20 [==============================] - 36s 2s/step - loss: 0.2345 - accuracy: 0.9200 - val_loss: 0.3456 - val_accuracy: 0.8800
   ```

4. **Training completes**:
   ```
   ============================================================
   🎉 TRAINING COMPLETE!
   ============================================================
   📊 Final Training Accuracy:   92.00%
   📊 Final Validation Accuracy: 88.00%
   💾 Model saved to: urbaneye_finetuned_model.h5
   📝 Labels saved to: class_labels.txt
   📈 Training plot saved to: training_plot_20260208_195230.png
   ```

---

## Step 5: Restart Backend 🔄

```bash
cd d:\UrbanEye\backend
.\start.bat
```

Backend will automatically detect and load the new model:
```
ℹ️  Fine-tuned model found! Loading: urbaneye_finetuned_model.h5
✅ Custom model loaded successfully
   Classes: pothole, streetlight, water_leak, garbage, sidewalk_damage, drainage
   Accuracy: 88.00%
```

---

## Step 6: Test AI 🧪

### Upload Test Image:
1. Open citizen app: http://localhost:3000
2. Upload a traffic light photo
3. Submit report

### Check Admin Dashboard:
1. Open admin dashboard: http://localhost:3001
2. Click the new issue
3. See **CORRECT** detection:
   ```
   Detected Type: Streetlight ✅
   Confidence: 92.5%
   ```

### Voice Assistant Reads Results:
🔊 "Issue detected: Streetlight. Confidence: 92 percent. Severity: 7 out of 10. Recommended action: Immediate repair required."

---

## Expected Results 📊

### Before Training (Pretrained Model):
```
Image: Traffic Light
AI Says: "Water Leak" ❌
Confidence: 56%
Accuracy: ~60%
```

### After Training (Your Custom Model):
```
Image: Traffic Light  
AI Says: "Streetlight" ✅
Confidence: 92%
Accuracy: ~90%
```

---

## Troubleshooting 🔧

### "ModuleNotFoundError: No module named 'tensorflow'"
**Fix**: Run `pip install tensorflow keras pillow numpy matplotlib scikit-learn`

### "Not enough images" error
**Fix**: Add more images - minimum 20 per category, 50+ recommended

### Low accuracy (<70%)
**Causes**:
- Not enough images
- Images are blurry/unclear
- Mixed images in wrong folders
**Fix**: Add 50+ clear images per category

### Training very slow (>2 hours)
**Cause**: No GPU
**Fix**: Use CPU mode (it's slower but works) OR install CUDA for GPU acceleration

---

## Tips for Best Accuracy 🎯

1. **More is better**: 100 images > 50 images
2. **Variety matters**: Different angles, lighting, weather
3. **Clear photos**: Avoid blurry or dark images
4. **Correct labeling**: Streetlight images in `streetlight/` folder!
5. **Balance dataset**: Similar number of images per category
6. **Real-world data**: Photos of actual Indian civic issues work best

---

## What Happens Next? 🚀

Once training is complete:

1. ✅ **Traffic lights detected correctly**
2. ✅ **Voice assistant reads results**
3. ✅ **Detailed AI analysis in admin panel**
4. ✅ **90%+ accuracy on civic issues**
5. ✅ **Production-ready AI model**

---

## Need Help Getting Images?

I can guide you to download images from Google Images or suggest specific search terms for each category!
