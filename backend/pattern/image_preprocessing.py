import os
import shutil


def process_images(raw_dir: str, processed_dir: str) -> list[str]:
    """
    Copies images from raw_dir to processed_dir, renaming them to
    sequential integers (1.jpg, 2.jpg, …) while preserving file extension.

    Returns:
        A list of new filenames in the order they were processed.
        This list is consumed by label_preprocessing to maintain alignment.
    """
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f"Raw image directory not found: {raw_dir}")

    os.makedirs(processed_dir, exist_ok=True)

    images = sorted([
        f for f in os.listdir(raw_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if not images:
        print("No images found — nothing to process.")
        return []

    name_map: list[str] = []   # [(original_stem, new_filename), …]

    for i, name in enumerate(images, start=1):
        ext = os.path.splitext(name)[1].lower()
        new_name = f"{i}{ext}"
        shutil.copy2(
            os.path.join(raw_dir, name),
            os.path.join(processed_dir, new_name)
        )
        name_map.append((os.path.splitext(name)[0], new_name))

    print(f"Processed {len(images)} image(s) → '{processed_dir}'")
    return name_map


if __name__ == "__main__":
    process_images(
        raw_dir="data/raw/pattern/train/images",
        processed_dir="data/processed/pattern/train_images",
    )