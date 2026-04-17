import os
from PIL import Image
import shutil

image_folder = "data/raw/train/images"
count = 0
size = (0,0)
for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
        image_path = os.path.join(image_folder, filename)
        count+=1
        with Image.open(image_path) as img:
            size = img.size
            
print(count)
print(img.size)

raw_images_folder = os.path.join("data", "raw", "train", "images")
processed_images_folder = os.path.join("data", "processed", "train_images")  

os.makedirs(processed_images_folder, exist_ok=True)

images = sorted(os.listdir(raw_images_folder))
images = [f for f in images if f.endswith(('.jpg', '.png', '.jpeg'))]

for i, original_name in enumerate(images, start=1):
    ext = os.path.splitext(original_name)[1]
    new_name = f"{i}{ext}"
    src = os.path.join(raw_images_folder, original_name)
    dst = os.path.join(processed_images_folder, new_name)
    shutil.copy2(src, dst) 

print(f"Copied and renamed {len(images)} images to '{processed_images_folder}'")
