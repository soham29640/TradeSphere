import sys
import time
import subprocess
import os

# ── Intervals ──────────────────────────────────────────────────────────────────
UPDATE_INTERVAL = 86400      # 24 hours — data refresh
TRAIN_INTERVAL  = 86400      # 24 hours — model retraining

last_update_time = 0
last_train_time  = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Helpers ────────────────────────────────────────────────────────────────────

def run_script(label: str, script_name: str) -> bool:
    """
    Run a script as a subprocess, capture output, print it live.
    Returns True on success, False on failure.
    """
    script_path = os.path.join(BASE_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False

    print(f"\n{'─' * 50}")
    print(f"▶  {label}")
    print(f"{'─' * 50}")

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if result.returncode == 0:
        print(f"✅ {label} completed.")
        return True
    else:
        print(f"❌ {label} failed (exit code {result.returncode})")
        return False


def run_update():
    print(f"\n{'═' * 50}")
    print("📡  Fetching latest volatility data...")
    print(f"{'═' * 50}")
    run_script("Data Update (data_loader.py)", "data_loader.py")


def run_training():
    """Run all three model training scripts + evaluation sequentially."""
    print(f"\n{'═' * 50}")
    print("🧠  Starting volatility model training...")
    print(f"{'═' * 50}")

    scripts = [
        ("GARCH Model",          "model_garch.py"),
        ("LSTM Model",           "model_lstm.py"),
        ("Attention-LSTM Model", "model_attention.py"),
    ]

    results = {}
    for label, script in scripts:
        ok = run_script(label, script)
        results[label] = ok

    # Always evaluate after training
    print(f"\n🕐  [{time.strftime('%Y-%m-%d %H:%M:%S')}] Running post-training evaluation...")
    eval_ok = run_script("Model Evaluation (evaluate_models.py)", "evaluate_models.py")
    results["Evaluation"] = eval_ok

    print(f"\n{'─' * 50}")
    print("📋  Training Summary:")
    for label, ok in results.items():
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"   {label:<28} {status}")
    print(f"{'─' * 50}")


def fmt_time(seconds: float) -> str:
    """Format seconds into hh:mm:ss."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║   Trade Sphere · Volatility Scheduler        ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  Data update  : every 24h                    ║")
    print("║  Training     : every 24h (after data)       ║")
    print("║  Evaluation   : after every training run     ║")
    print("╚══════════════════════════════════════════════╝\n")

    tick = 0

    while True:
        current_time = time.time()

        # ── Data update + training (both every 24h, training runs after data) ──
        if current_time - last_update_time >= UPDATE_INTERVAL:
            print(f"\n🕐  [{time.strftime('%Y-%m-%d %H:%M:%S')}] Daily cycle triggered.")

            run_update()
            last_update_time = current_time

            # Training always follows data update
            run_training()
            last_train_time = current_time

        # ── Heartbeat every 10 minutes ─────────────────────────────────────────
        tick += 1
        if tick % 10 == 0:
            next_cycle = max(0, UPDATE_INTERVAL - (current_time - last_update_time))
            print(
                f"💓  [{time.strftime('%H:%M:%S')}] "
                f"Next cycle in: {fmt_time(next_cycle)}"
            )

        time.sleep(60)