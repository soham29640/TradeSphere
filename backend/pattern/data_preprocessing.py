import os


def clean_empty_labels(image_dir: str, label_dir: str) -> None:
    """
    Removes label files that have no annotations and deletes their
    corresponding images. Keeps the dataset free of unannotated samples.

    Args:
        image_dir : Directory that holds the raw images.
        label_dir : Directory that holds the YOLO-format .txt label files.
    """
    if not os.path.isdir(label_dir):
        raise FileNotFoundError(f"Label directory not found: {label_dir}")
    if not os.path.isdir(image_dir):
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    deleted = 0
    skipped = 0

    for label_file in sorted(os.listdir(label_dir)):
        if not label_file.endswith(".txt"):
            continue

        label_path = os.path.join(label_dir, label_file)

        # Keep any label file that has at least one non-blank line
        with open(label_path, "r") as f:
            has_annotation = any(line.strip() for line in f)

        if has_annotation:
            skipped += 1
            continue

        # Delete matching image (try common extensions)
        base = os.path.splitext(label_file)[0]
        image_deleted = False
        for ext in (".jpg", ".jpeg", ".png"):
            img_path = os.path.join(image_dir, base + ext)
            if os.path.exists(img_path):
                os.remove(img_path)
                image_deleted = True
                break

        if not image_deleted:
            print(f"  [WARN] No image found for label: {label_file}")

        os.remove(label_path)
        deleted += 1

    print(f"Removed {deleted} empty sample(s). Kept {skipped} annotated sample(s).")


if __name__ == "__main__":
    clean_empty_labels(
        image_dir="data/raw/pattern/train/images",
        label_dir="data/raw/pattern/train/labels",
    )