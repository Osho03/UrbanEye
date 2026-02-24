"""
Model Training Script for UrbanEye AI
Human-in-the-Loop Learning System

This script fine-tunes MobileNetV2 on domain-specific civic issue images
collected from verified user uploads. This is the second phase of the
two-phase ML system: offline training on labeled data.

Prerequisites:
    1. Run prepare_dataset.py first to organize images
    2. Ensure ai/dataset/ has sufficient images per class

Usage:
    python ai/train_model.py

Output:
    ai/civic_issue_model.h5 - Fine-tuned model
    ai/training_history.json - Training metrics
"""

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import json
import os

print("🚀 Starting UrbanEye AI Model Training")
print("=" * 60)

# Configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 20
LEARNING_RATE = 0.001

DATASET_DIR = "ai/dataset"
MODEL_PATH = "ai/civic_issue_model.h5"
HISTORY_PATH = "ai/training_history.json"

# Check if dataset exists
if not os.path.exists(DATASET_DIR):
    print(f"❌ Error: Dataset directory not found: {DATASET_DIR}")
    print("   Please run 'python ai/prepare_dataset.py' first")
    exit(1)

# Data augmentation for training
print("\n📊 Setting up data generators...")
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    zoom_range=0.2,
    validation_split=0.2
)

# Validation data (no augmentation)
val_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

# Load training data
print(f"Loading training data from {DATASET_DIR}...")
train_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training",
    shuffle=True
)

# Load validation data
print(f"Loading validation data from {DATASET_DIR}...")
val_generator = val_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation",
    shuffle=False
)

# Display dataset info
print("\n📈 Dataset Information:")
print(f"  Training samples:   {train_generator.samples}")
print(f"  Validation samples: {val_generator.samples}")
print(f"  Number of classes:  {train_generator.num_classes}")
print(f"  Class labels:       {list(train_generator.class_indices.keys())}")

# Check if dataset is too small
if train_generator.samples < 20:
    print("\n⚠️  WARNING: Very small dataset!")
    print("   Training may not be effective with < 20 images")
    response = input("   Continue anyway? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled.")
        exit(0)

# Build model
print("\n🧠 Building model architecture...")
base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)

# Freeze base model initially
base_model.trainable = False

# Custom classification head
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(256, activation="relu")(x)
x = Dropout(0.5)(x)
x = Dense(128, activation="relu")(x)
x = Dropout(0.3)(x)
outputs = Dense(train_generator.num_classes, activation="softmax")(x)

model = Model(inputs=base_model.input, outputs=outputs)

# Compile model
print("Compiling model...")
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

print(f"\nModel Summary:")
print(f"  Total parameters: {model.count_params():,}")
print(f"  Trainable parameters: {sum([tf.size(w).numpy() for w in model.trainable_weights]):,}")

# Callbacks
callbacks = [
    EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    ModelCheckpoint(
        MODEL_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]

# Train model
print("\n🔥 Starting training...")
print("=" * 60)

history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

print("=" * 60)
print("✅ Training complete!")

# Save training history
print(f"\n💾 Saving training history to {HISTORY_PATH}...")
history_dict = {
    "accuracy": [float(x) for x in history.history['accuracy']],
    "val_accuracy": [float(x) for x in history.history['val_accuracy']],
    "loss": [float(x) for x in history.history['loss']],
    "val_loss": [float(x) for x in history.history['val_loss']],
    "class_labels": list(train_generator.class_indices.keys())
}

with open(HISTORY_PATH, 'w') as f:
    json.dump(history_dict, f, indent=2)

# Final evaluation
print("\n📊 Final Model Performance:")
train_loss, train_acc = model.evaluate(train_generator, verbose=0)
val_loss, val_acc = model.evaluate(val_generator, verbose=0)

print(f"  Training Accuracy:   {train_acc*100:.2f}%")
print(f"  Validation Accuracy: {val_acc*100:.2f}%")

if val_acc > 0.8:
    print("\n🎉 Excellent! Model achieved >80% validation accuracy")
elif val_acc > 0.6:
    print("\n✅ Good! Model achieved >60% validation accuracy")
else:
    print("\n⚠️  Model accuracy is low. Consider:")
    print("   - Collecting more training images")
    print("   - Ensuring images are correctly labeled")
    print("   - Increasing training epochs")

print(f"\n✅ Model saved to: {MODEL_PATH}")
print("\nNext step: Update image_classifier.py to use the trained model")
print("   The trained model will now be used for inference!")
