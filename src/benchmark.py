import os
import subprocess
import re
import csv
import psutil
import platform
import time
from pathlib import Path

# --- Configuration ---
MODEL_PATH = Path.home() / "Lataukset" / "qwen2.5-coder-3b-instruct-q6_k.gguf"
BINARY_PATH = Path.home() / "prima.cpp" / "llama-server"
MODEL_NAME = "Qwen2.5-Coder-3B-Instruct"
MODEL_QUANT = "Q6_K"
MODEL_RAM_MB = 450  # Estimated for 3B Q6
CSV_FILE = Path.home() / "model-efficiency" / "benchmarks.csv"
REPO_NAME = "e727-local-ai"


def get_hardware_name():
    """Detect hardware model name."""
    try:
        # Linux dmi
        with open("/sys/class/dmi/id/product_name", "r") as f:
            return f.read().strip()
    except:
        try:
            # macOS/Linux fallback
            output = subprocess.check_output(["hostnamectl"], text=True)
            for line in output.splitlines():
                if "Hardware Model" in line:
                    return line.split(":")[1].strip()
        except:
            return platform.node()


def get_cpu_info():
    """Extract CPU name and frequency."""
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except:
        return platform.processor()
    return "Unknown CPU"


def get_total_ram():
    """Get total RAM in GB."""
    return round(psutil.virtual_memory().total / (1024**3), 1)


def run_benchmark(dry_run=False):
    """Run prima.cpp benchmark and parse output."""
    if not BINARY_PATH.exists():
        print(f"❌ Binary not found: {BINARY_PATH}")
        return None

    if not MODEL_PATH.exists():
        print(f"❌ Model not found: {MODEL_PATH}")
        return None

    print(
        f"🚀 Benchmarking {MODEL_PATH.name} (this may take up to 20 minutes on old hardware)..."
    )

    cmd = [
        str(BINARY_PATH),
        "-m",
        str(MODEL_PATH),
        "-p",
        "Hi",
        "-n",
        "32",  # Even fewer tokens for testing
        "-ngl",
        "0",
    ]

    start_time = time.time()
    try:
        # Stream output if dry_run is true
        if dry_run:
            print("--- LOGS START ---")
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            output_lines = []
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
            process.wait(timeout=1200)  # 20 minute timeout
            output = "".join(output_lines)
            print("--- LOGS END ---")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            output = result.stdout + result.stderr

        end_time = time.time()

        # Search for tokens per second in prima.cpp / llama.cpp output
        # Format: "llama_perf_context_print:        eval time =  ... ( ... ms per token,     0.04 tokens per second)"
        tps_match = re.search(r"(\d+\.\d+) tokens per second", output)

        # If tps_match failed, try to parse from the llama_perf_context_print line specifically
        if not tps_match:
            # Look for: "eval time = ... / ... runs ( ... ms per token, ... tokens per second)"
            tps_match = re.search(
                r"eval time = .*? (\d+\.\d+) tokens per second", output
            )

        tps = float(tps_match.group(1)) if tps_match else 0.0

        # Fallback: estimate TPS if not printed
        if tps == 0.0:
            # Simple estimate: (tokens / time)
            # We don't know exact token count but we can approximate
            tps = round(128 / (end_time - start_time), 2)

        return {
            "hardware": get_hardware_name(),
            "cpu": get_cpu_info(),
            "ram_gb": get_total_ram(),
            "model": MODEL_NAME,
            "quant": MODEL_QUANT,
            "ram_mb": MODEL_RAM_MB,  # Fixed for this Model on idle
            "tokens_per_s": tps,
            "ctx_size": 32768,
            "repo": REPO_NAME,
        }
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return None


def save_to_csv(data):
    """Append data to benchmarks.csv."""
    file_exists = CSV_FILE.exists()

    fieldnames = [
        "hardware",
        "cpu",
        "ram_gb",
        "model",
        "quant",
        "ram_mb",
        "tokens_per_s",
        "ctx_size",
        "repo",
    ]

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
        print(f"✅ Result saved to {CSV_FILE}")


def git_commit():
    """Auto-commit and push the benchmark."""
    try:
        os.chdir(CSV_FILE.parent)
        subprocess.run(["git", "add", "benchmarks.csv"], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"docs: update benchmarks for {get_hardware_name()}",
            ],
            check=True,
        )
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🌍 Result pushed to GitHub!")
    except Exception as e:
        print(f"⚠️ Git push failed: {e}")


import sys


def main():
    dry_run = "--dry-run" in sys.argv

    result = run_benchmark(dry_run=dry_run)
    if result:
        print("\n--- Benchmark Results ---")
        for key, value in result.items():
            print(f"{key}: {value}")
        print("-------------------------\n")

        if dry_run:
            print("🧪 Dry-run mode: skipping CSV save and Git push.")
        else:
            save_to_csv(result)
            git_commit()


if __name__ == "__main__":
    main()
