import time
import subprocess

INTERVAL = 3600  # 1 hour

while True:
    print("🔄 Training model...")

    subprocess.run(["python", "src/train/train_price_model.py"])

    print("✅ Training done. Sleeping...")

    time.sleep(INTERVAL)