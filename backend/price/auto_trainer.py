import sys
import time
import subprocess
import os

TRAIN_INTERVAL = 86400
UPDATE_INTERVAL = 3600

last_train_time = 0
last_update_time = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def run_training():
    script_path = os.path.join(BASE_DIR, "train_price_model.py")
    print("🧠 Starting training...")
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Training completed.")
    else:
        print(f"❌ Training failed ({result.returncode})")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

def run_update():
    script_path = os.path.join(BASE_DIR, "update_data.py")

    print("📡 Updating data...")
    result = subprocess.run([sys.executable, script_path])

    if result.returncode == 0:
        print("✅ Data updated.")
    else:
        print(f"❌ Update failed ({result.returncode})")


if __name__ == "__main__":
    print("🚀 Scheduler started")
    print("⏱ Data update: every 1 hour")
    print("⏱ Training: every 24 hours\n")

    while True:
        current_time = time.time()

        if current_time - last_update_time >= UPDATE_INTERVAL:
            run_update()
            last_update_time = current_time

        if current_time - last_train_time >= TRAIN_INTERVAL:
            run_training()
            last_train_time = current_time

        time.sleep(60)