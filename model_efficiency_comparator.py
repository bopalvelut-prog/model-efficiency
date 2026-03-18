import requests
import json
import argparse
import time

OLLAMA_API_BASE_URL = "http://localhost:11434/api"


def list_ollama_models():
    """Lists available Ollama models with their sizes."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags")
        response.raise_for_status()
        models = []
        for m in response.json()["models"]:
            models.append({"name": m["name"], "size": m.get("size", 0)})
        return models
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        print("Please ensure Ollama is running.")
        return []


def chat_with_model(model_name, prompt):
    """Sends a prompt to an Ollama model and returns response and metrics."""
    try:
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,  # We want the full response and metrics at once
        }
        start_time = time.time()
        response = requests.post(f"{OLLAMA_API_BASE_URL}/generate", json=data)
        response.raise_for_status()
        end_time = time.time()

        response_data = response.json()

        full_response = response_data.get("response", "")

        # Ollama's API provides metrics in the 'eval_duration' and 'eval_count' fields
        # which are part of the top-level response for non-streaming requests.
        eval_duration = response_data.get("eval_duration", 0)  # Nanoseconds
        eval_count = response_data.get("eval_count", 0)  # Tokens generated

        tokens_per_second = 0
        if eval_duration > 0:
            # Convert eval_duration from nanoseconds to seconds
            eval_duration_seconds = eval_duration / 1_000_000_000
            tokens_per_second = eval_count / eval_duration_seconds

        return {
            "response": full_response,
            "tokens_per_second": tokens_per_second,
            "total_duration": end_time - start_time,
            "eval_duration_ns": eval_duration,
            "eval_count": eval_count,
        }
    except requests.exceptions.RequestException as e:
        print(f"Error chatting with {model_name}: {e}")
        return None


def get_intelligency_score():
    """Prompts the user for an intelligency score."""
    while True:
        try:
            score = float(input("Enter intelligency score (1-5, or 0 to skip): "))
            if 0 <= score <= 5:
                return score
            else:
                print("Score must be between 1 and 5, or 0 to skip.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def pull_model(model_name):
    """Pulls a model from Ollama."""
    print(f"\n📥 Pulling {model_name}...")
    try:
        response = requests.post(f"{OLLAMA_API_BASE_URL}/pull", json={"name": model_name, "stream": False})
        response.raise_for_status()
        print(f"✅ Successfully pulled {model_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to pull {model_name}: {e}")
        return False


def suggest_quantization(model_name, tokens_per_second):
    """Suggests a higher or lower quantization based on speed threshold."""
    if tokens_per_second is None:
        return "N/A", None

    quants = ["q2_K", "q3_K_S", "q3_K_M", "q3_K_L", "q4_0", "q4_K_S", "q4_K_M", "q5_0", "q5_K_S", "q5_K_M", "q6_K", "q8_0", "fp16"]
    
    current_quant = None
    base_name = model_name
    for q in quants:
        if q.lower() in model_name.lower():
            current_quant = q
            if "-" + q.lower() in model_name.lower():
                base_name = model_name.lower().split("-" + q.lower())[0]
            elif ":" + q.lower() in model_name.lower():
                base_name = model_name.lower().split(":" + q.lower())[0]
            break
    
    # If no explicit quant found, assume we suggest based on base name
    if not current_quant:
        if tokens_per_second < 5:
            suggested = "q3_K_M"
            return f"Too slow. Try {suggested}", f"{model_name}-{suggested}"
        else:
            suggested = "q8_0"
            return f"Fast. Try {suggested}", f"{model_name}-{suggested}"

    idx = quants.index(current_quant)
    if tokens_per_second < 5:
        if idx > 0:
            suggested = quants[idx-1]
            return f"Too slow (<5t/s). Try {suggested}", f"{base_name}-{suggested}"
        else:
            return "Too slow, but already at lowest quantization.", None
    else:
        if idx < len(quants) - 1:
            suggested = quants[idx+1]
            return f"Fast (>=5t/s). Try {suggested} for quality", f"{base_name}-{suggested}"
        else:
            return "Fast, and already at highest quantization.", None


def calculate_combined_efficiency(results, w_ts, w_is, w_ms):
    """Calculates normalized token speed, intelligency, model size, and combined efficiency."""
    if not results:
        return []

    token_speeds = [
        r["tokens_per_second"] for r in results if r["tokens_per_second"] is not None
    ]
    intelligency_scores = [
        r["intelligency_score"]
        for r in results
        if r["intelligency_score"] is not None and r["intelligency_score"] > 0
    ]
    model_sizes = [
        r["model_size"]
        for r in results
        if r["model_size"] is not None and r["model_size"] > 0
    ]

    max_ts = max(token_speeds) if token_speeds else 1
    max_is = 5
    min_ms = min(model_sizes) if model_sizes else 1

    processed_results = []
    for r in results:
        model_name = r["model_name"]
        ts = r["tokens_per_second"]
        is_score = r["intelligency_score"]
        ms = r["model_size"]

        normalized_ts = (ts / max_ts) if ts is not None and max_ts > 0 else 0
        normalized_is = (
            (is_score / max_is) if is_score is not None and is_score > 0 else 0
        )
        normalized_ms = (min_ms / ms) if ms is not None and ms > 0 else 0

        combined_efficiency_score = (
            (normalized_ts * w_ts) + (normalized_is * w_is) + (normalized_ms * w_ms)
        )

        suggestion_text, suggested_tag = suggest_quantization(model_name, ts)

        processed_results.append(
            {
                "model_name": model_name,
                "tokens_per_second": ts,
                "intelligency_score": is_score,
                "model_size": ms,
                "normalized_ts": normalized_ts,
                "normalized_is": normalized_is,
                "normalized_ms": normalized_ms,
                "combined_efficiency_score": combined_efficiency_score,
                "suggestion": suggestion_text,
                "suggested_tag": suggested_tag
            }
        )
    return processed_results


def main():
    parser = argparse.ArgumentParser(description="Compare Ollama model efficiency.")
    parser.add_argument(
        "-p", "--prompt", required=True, help="The prompt to send to the models."
    )
    parser.add_argument(
        "--w_ts",
        type=float,
        default=0.4,
        help="Weight for Token Speed in combined score (default: 0.4).",
    )
    parser.add_argument(
        "--w_is",
        type=float,
        default=0.4,
        help="Weight for Intelligency Score in combined score (default: 0.4).",
    )
    parser.add_argument(
        "--w_ms",
        type=float,
        default=0.2,
        help="Weight for Model Size in combined score (default: 0.2).",
    )

    args = parser.parse_args()

    if not (
        0 <= args.w_ts <= 1
        and 0 <= args.w_is <= 1
        and 0 <= args.w_ms <= 1
        and (args.w_ts + args.w_is + args.w_ms == 1)
    ):
        print("Error: Weights (w_ts, w_is, w_ms) must be between 0 and 1 and sum to 1.")
        return

    print("Fetching available Ollama models...")
    models = list_ollama_models()
    if not models:
        print("No Ollama models found or connection error. Exiting.")
        return

    model_dict = {m["name"]: m["size"] for m in models}
    model_names = list(model_dict.keys())
    print(f"Found models: {', '.join(model_names)}")
    print("\n--- Running Models ---")

    raw_results = []
    for model_name in model_names:
        print(f"\n--- Model: {model_name} ---")
        print(f"Prompt: {args.prompt}")

        response_metrics = chat_with_model(model_name, args.prompt)
        if response_metrics:
            print(f"Response: {response_metrics['response']}")
            print(f"Tokens/second: {response_metrics['tokens_per_second']:.2f}")

            intelligency_score = get_intelligency_score()
            if intelligency_score == 0:
                print(f"Skipping intelligency score for {model_name}.")
                intelligency_score = None

            raw_results.append(
                {
                    "model_name": model_name,
                    "tokens_per_second": response_metrics["tokens_per_second"],
                    "intelligency_score": intelligency_score,
                    "model_size": model_dict.get(model_name, 0),
                }
            )
        else:
            print(f"Skipping {model_name} due to chat error.")

    print("\n--- Calculating Efficiency Scores ---")
    processed_results = calculate_combined_efficiency(
        raw_results, args.w_ts, args.w_is, args.w_ms
    )

    print("\n--- Results Summary ---")
    print(
        f"{'Model':<25} {'Tokens/Sec':<12} {'Size':<10} {'Intell.':<8} {'Combined':<10} {'Recommendation'}"
    )
    print(
        f"{'-' * 25:<25} {'-' * 12:<12} {'-' * 10:<10} {'-' * 8:<8} {'-' * 10:<10} {'-' * 30}"
    )

    # Sort results by combined efficiency score in descending order
    processed_results_sorted = sorted(
        processed_results, key=lambda x: x["combined_efficiency_score"], reverse=True
    )

    suggested_models = []
    for res in processed_results_sorted:
        ts_str = (
            f"{res['tokens_per_second']:.2f}"
            if res["tokens_per_second"] is not None
            else "N/A"
        )

        ms = res.get("model_size")
        if ms:
            if ms >= 1_000_000_000:
                ms_str = f"{ms / 1_000_000_000:.1f}GB"
            else:
                ms_str = f"{ms / 1_000_000:.0f}MB"
        else:
            ms_str = "N/A"

        is_str = (
            f"{res['intelligency_score']:.1f}"
            if res["intelligency_score"] is not None
            else "N/A"
        )
        combined_str = f"{res['combined_efficiency_score']:.2f}"
        suggestion = res.get("suggestion", "N/A")
        
        if res.get("suggested_tag"):
            suggested_models.append(res["suggested_tag"])

        print(
            f"{res['model_name']:<25} {ts_str:<12} {ms_str:<10} {is_str:<8} {combined_str:<10} {suggestion}"
        )

    print("\n--- End of Report ---")

    if suggested_models:
        print("\n--- Model Downloader ---")
        print("Suggested models for download:")
        for idx, m in enumerate(suggested_models):
            print(f"[{idx+1}] {m}")
        
        choice = input("\nEnter model numbers to download (e.g. 1,3) or Enter to skip: ")
        if choice:
            try:
                indices = [int(i.strip()) - 1 for i in choice.split(",")]
                for idx in indices:
                    if 0 <= idx < len(suggested_models):
                        pull_model(suggested_models[idx])
            except ValueError:
                print("Invalid input. Skipping downloads.")


if __name__ == "__main__":
    main()
