import os
import pandas as pd
from image_preprocessing import process_images

NUM_CLASSES = 20


def create_labels_csv(
    raw_img_dir: str,
    label_dir: str,
    processed_img_dir: str,
    output_csv: str,
) -> None:
    """
    Builds a multi-label CSV aligned with the processed (renamed) images.

    Pipeline:
        1. Calls process_images() to copy + rename images and get the mapping.
        2. For each renamed image, reads its original label file.
        3. Writes a CSV with columns: Filename, Class0 … Class{N-1}.

    Args:
        raw_img_dir      : Raw images (before renaming).
        label_dir        : YOLO-format .txt label files (named after raw images).
        processed_img_dir: Destination for renamed images.
        output_csv       : Where to write the final label CSV.
    """
    # Step 1 — copy & rename images; get (original_stem → new_filename) map
    name_map = process_images(raw_img_dir, processed_img_dir)

    if not name_map:
        print("No images to label — aborting CSV creation.")
        return

    rows = []
    missing_labels = 0

    for original_stem, new_filename in name_map:
        label_path = os.path.join(label_dir, original_stem + ".txt")
        label_vector = [0] * NUM_CLASSES

        if os.path.exists(label_path):
            with open(label_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        class_id = int(line.split()[0])
                        if 0 <= class_id < NUM_CLASSES:
                            label_vector[class_id] = 1
                    except (ValueError, IndexError):
                        print(f"  [WARN] Malformed line in {label_path}: '{line}'")
        else:
            missing_labels += 1
            print(f"  [WARN] Label file missing for '{original_stem}' — defaulting to all zeros.")

        rows.append([new_filename] + label_vector)

    columns = ["Filename"] + [f"Class{i}" for i in range(NUM_CLASSES)]
    df = pd.DataFrame(rows, columns=columns)

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    df.to_csv(output_csv, index=False)

    print(f"Saved '{output_csv}' with {len(df)} row(s). ({missing_labels} label file(s) missing.)")


if __name__ == "__main__":
    create_labels_csv(
        raw_img_dir="data/raw/pattern/train/images",
        label_dir="data/raw/pattern/train/labels",
        processed_img_dir="data/processed/pattern/train_images",
        output_csv="data/processed/pattern/train_labels.csv",
    )