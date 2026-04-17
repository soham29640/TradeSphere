import os
import csv
import shutil
import pandas as pd

NUM_CLASSES = 20

raw_image_dir = os.path.join("data", "raw", "train", "images")
label_dir = os.path.join("data", "raw", "train", "labels")
processed_image_dir = os.path.join("data", "processed", "train_images")
output_csv = os.path.join("data", "processed", "train_labels.csv")

os.makedirs(processed_image_dir, exist_ok=True)

label_data = []
original_images = sorted([
    f for f in os.listdir(raw_image_dir)
    if f.lower().endswith(('.jpg', '.png', '.jpeg'))
])

for i, original_image in enumerate(original_images, start=1):
    base_name = os.path.splitext(original_image)[0]
    label_file = os.path.join(label_dir, base_name + ".txt")

    ext = os.path.splitext(original_image)[1].lower()
    new_image_name = f"{i}{ext}"
    new_image_path = os.path.join(processed_image_dir, new_image_name)

    shutil.copy2(os.path.join(raw_image_dir, original_image), new_image_path)

    label_vector = [0] * NUM_CLASSES
    if os.path.exists(label_file):
        with open(label_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    class_id = int(line.split()[0])
                    if 0 <= class_id < NUM_CLASSES:
                        label_vector[class_id] = 1
        label_data.append([new_image_name] + label_vector)
    else:
        print(f"[WARN] Missing label for: {original_image}")

header = ["Filename"] + [f"Class{i}" for i in range(NUM_CLASSES)]
df = pd.DataFrame(label_data, columns=header)

df.to_csv(output_csv, index=False)

print(f"[INFO] Saved {len(df)} entries to {output_csv}")
print("[INFO] Label distribution:")
print(df.iloc[:, 1:].sum())
