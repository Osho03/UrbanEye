"""
UrbanEye AI Training Script
Trains a custom MobileNetV2 model on YOUR infrastructure images
"""

import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import json

# Paths
TRAINING_DATA_DIR = "training_data"
MODEL_OUTPUT_PATH = "ai/urbaneye_finetuned_model.h5"
LABELS_OUTPUT_PATH = "ai/labels.json"

# Training parameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 50
LEARNING_RATE = 0.0001

print("=" * 60)
print("🚀 URBANEYE AI TRAINING SYSTEM")
print("=" * 60)

# Step 1: Check if training data exists
if not os.path.exists(TRAINING_DATA_DIR):
    print(f"\n❌ ERROR: {TRAINING_DATA_DIR} folder not found!")
    print("Create it first and add images.")
    exit(1)

# Count images per category
categories = os.listdir(TRAINING_DATA_DIR)
categories = [c for c in categories if os.path.isdir(os.path.join(TRAINING_DATA_DIR, c))]

print(f"\n📂 Found {len(categories)} categories:")
total_images = 0
for cat in categories:
    cat_path = os.path.join(TRAINING_DATA_DIR, cat)
    images = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    count = len(images)
    total_images += count
    
    status = "✅" if count >= 15 else "⚠️"
    print(f"  {status} {cat}: {count} images")
    
    if count < 15:
        print(f"     ⚠️  WARNING: At least 15 images recommended, you have {count}")

print(f"\n📊 Total images: {total_images}")

if total_images < 50:
    print("\n⚠️  WARNING: Less than 50 total images!")
    print("   Model accuracy may be low. Recommended: 100+ images")
    response = input("\n   Continue anyway? (yes/no): ")
    if response.lower() != 'yes':
        print("Training cancelled.")
        exit(0)

print("\n" + "=" * 60)
print("📚 STEP 1: PREPARING DATA")
print("=" * 60)

# Data augmentation - create more variations from your images
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    zoom_range=0.2,
    validation_split=0.2  # 80% train, 20% validation
)

# Load training data
train_generator = train_datagen.flow_from_directory(
    TRAINING_DATA_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

# Load validation data
validation_generator = train_datagen.flow_from_directory(
    TRAINING_DATA_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)

num_classes = len(train_generator.class_indices)
print(f"\n✅ Data loaded:")
print(f"   Training samples: {train_generator.samples}")
print(f"   Validation samples: {validation_generator.samples}")
print(f"   Classes: {num_classes}")

# Save label mapping
label_map = {v: k for k, v in train_generator.class_indices.items()}
with open(LABELS_OUTPUT_PATH, 'w') as f:
    json.dump(label_map, f, indent=2)
print(f"\n✅ Labels saved to: {LABELS_OUTPUT_PATH}")

print("\n" + "=" * 60)
print("🏗️  STEP 2: BUILDING MODEL")
print("=" * 60)

# Load pretrained MobileNetV2 (without top layer)
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)

# Freeze base model layers (we'll only train the top)
base_model.trainable = False

# Add custom top layers for YOUR categories
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(num_classes, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)

# Compile model
model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"\n✅ Model built with {num_classes} output classes")
print(f"   Total layers: {len(model.layers)}")
print(f"   Trainable params: {model.count_params():,}")

print("\n" + "=" * 60)
print("🎓 STEP 3: TRAINING MODEL")
print("=" * 60)
print("\nThis will take 5-15 minutes depending on your CPU/GPU...")
print("You'll see progress bars for each epoch.\n")

# Callbacks
callbacks = [
    EarlyStopping(
        monitor='val_accuracy',
        patience=10,
        restore_best_weights=True,
        verbose=1
    ),
    ModelCheckpoint(
        MODEL_OUTPUT_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]

# Train!
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)

# Display results
final_train_acc = history.history['accuracy'][-1]
final_val_acc = history.history['val_accuracy'][-1]

print(f"\n📊 Final Results:")
print(f"   Training Accuracy: {final_train_acc*100:.1f}%")
print(f"   Validation Accuracy: {final_val_acc*100:.1f}%")

if final_val_acc >= 0.85:
    print("\n🎉 EXCELLENT! Model accuracy is 85%+")
elif final_val_acc >= 0.70:
    print("\n👍 GOOD! Model accuracy is 70%+")
else:
    print("\n⚠️  Model accuracy is below 70%. Consider adding more images.")

print(f"\n💾 Model saved to: {MODEL_OUTPUT_PATH}")
print(f"   File size: {os.path.getsize(MODEL_OUTPUT_PATH) / 1024 / 1024:.1f} MB")

print("\n" + "=" * 60)
print("🔄 NEXT STEPS")
print("=" * 60)
print("\n1. Restart the backend:")
print("   cd d:\\UrbanEye\\backend")
print("   .\\start.bat")
print("\n2. The AI will automatically use your trained model!")
print("3. Test by uploading images on http://localhost:3000")
print("\n" + "=" * 60)
