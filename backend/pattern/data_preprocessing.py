import os

original_images = sorted([
    f for f in os.listdir(os.path.join("data", "raw", "train", "images"))
    if f.lower().endswith(('.jpg', '.png', '.jpeg'))
])

label_dir = os.path.join("data", "raw", "train", "labels")

count = 0
count1 = 0
count2 = 0

for i, original_image in enumerate(original_images, start=1):

    base_name = os.path.splitext(original_image)[0]
    label_file = os.path.join(label_dir, base_name + ".txt")

    if os.path.exists(label_file):
        with open(label_file, 'r') as file:
            first_line = file.readline().strip()
            if first_line:
                count+=1
            else:
                count1+=1
    else:
        count2+=1

print(count)        
print(count1)
print(count2)

image_dir = "data/raw/train/images"

deleted = 0

for label_file in os.listdir(label_dir):
    if label_file.endswith(".txt"):
        label_path = os.path.join(label_dir, label_file)
        with open(label_path, 'r') as f:
            first_line = f.readline().strip()
        
        if not first_line:
            base_name = os.path.splitext(label_file)[0]
            
            for ext in ['.jpg', '.png', '.jpeg']:
                image_path = os.path.join(image_dir, base_name + ext)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"[INFO] Deleted image: {image_path}")
                    break
            
            os.remove(label_path)
            print(f"[INFO] Deleted empty label: {label_path}")
            deleted += 1

print(f"\nCleanup complete. {deleted} images + labels removed.")
