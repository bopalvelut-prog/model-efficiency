import requests
import json
import argparse
import time

OLLAMA_API_BASE_URL = "http://localhost:11434/api"

def list_ollama_models():
    """Lists available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags")
        response.raise_for_status()
        models = [m['name'] for m in response.json()['models']]
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
            "stream": False # We want the full response and metrics at once
        }
        start_time = time.time()
        response = requests.post(f"{OLLAMA_API_BASE_URL}/generate", json=data)
        response.raise_for_status()
        end_time = time.time()
        
        response_data = response.json()
        
        full_response = response_data.get("response", "")
        eval_duration = response_data.get("eval_duration", 0) # Nanoseconds
        eval_count = response_data.get("eval_count", 0) # Tokens generated
        
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
            "eval_count": eval_count
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

def calculate_combined_efficiency(results, w_ts, w_is):
    """Calculates normalized token speed, intelligency, and combined efficiency."""
    if not results:
        return []

    # Extract raw data for normalization
    token_speeds = [r['tokens_per_second'] for r in results if r['tokens_per_second'] is not None]
    intelligency_scores = [r['intelligency_score'] for r in results if r['intelligency_score'] is not None and r['intelligency_score'] > 0]

    max_ts = max(token_speeds) if token_speeds else 1
    max_is = 5 # Intelligency score is on a 1-5 scale

    processed_results = []
    for r in results:
        model_name = r['model_name']
        ts = r['tokens_per_second']
        is_score = r['intelligency_score']

        normalized_ts = (ts / max_ts) if ts is not None and max_ts > 0 else 0
        normalized_is = (is_score / max_is) if is_score is not None and is_score > 0 else 0

        combined_efficiency_score = (normalized_ts * w_ts) + (normalized_is * w_is)

        processed_results.append({
            "model_name": model_name,
            "tokens_per_second": ts,
            "intelligency_score": is_score,
            "normalized_ts": normalized_ts,
            "normalized_is": normalized_is,
            "combined_efficiency_score": combined_efficiency_score
        })
    return processed_results

def main():
    parser = argparse.ArgumentParser(description="Compare Ollama model efficiency.")
    parser.add_argument("-p", "--prompt", required=True, help="The prompt to send to the models.")
    parser.add_argument("--w_ts", type=float, default=0.5,
                        help="Weight for Token Speed in combined score (default: 0.5).")
    parser.add_argument("--w_is", type=float, default=0.5,
                        help="Weight for Intelligency Score in combined score (default: 0.5).")
    
    args = parser.parse_args()

    if not (0 <= args.w_ts <= 1 and 0 <= args.w_is <= 1 and (args.w_ts + args.w_is == 1)):
        print("Error: Weights (w_ts, w_is) must be between 0 and 1 and sum to 1.")
        return

    print("Fetching available Ollama models...")
    models = list_ollama_models()
    if not models:
        print("No Ollama models found or connection error. Exiting.")
        return

    print(f"Found models: {', '.join(models)}")
    print("
--- Running Models ---")

    raw_results = []
    for model_name in models:
        print(f"
--- Model: {model_name} ---")
        print(f"Prompt: {args.prompt}")
        
        response_metrics = chat_with_model(model_name, args.prompt)
        if response_metrics:
            print(f"Response: {response_metrics['response']}")
            print(f"Tokens/second: {response_metrics['tokens_per_second']:.2f}")
            
            intelligency_score = get_intelligency_score()
            if intelligency_score == 0:
                print(f"Skipping intelligency score for {model_name}.")
                intelligency_score = None # Indicate it was skipped/not provided
            
            raw_results.append({
                "model_name": model_name,
                "tokens_per_second": response_metrics['tokens_per_second'],
                "intelligency_score": intelligency_score
            })
        else:
            print(f"Skipping {model_name} due to chat error.")

    print("
--- Calculating Efficiency Scores ---")
    processed_results = calculate_combined_efficiency(raw_results, args.w_ts, args.w_is)

    print("
--- Results Summary ---")
    print(f"{'Model':<25} {'Tokens/Sec':<15} {'Intell. Score':<15} {'Normalized TS':<15} {'Normalized IS':<15} {'Combined Score':<15}")
    print(f"{'-'*25:<25} {'-'*15:<15} {'-'*15:<15} {'-'*15:<15} {'-'*15:<15} {'-'*15:<15}")

    # Sort results by combined efficiency score in descending order
    processed_results_sorted = sorted(processed_results, key=lambda x: x['combined_efficiency_score'], reverse=True)

    for res in processed_results_sorted:
        ts_str = f"{res['tokens_per_second']:.2f}" if res['tokens_per_second'] is not None else "N/A"
        is_str = f"{res['intelligency_score']:.1f}" if res['intelligency_score'] is not None else "N/A"
        norm_ts_str = f"{res['normalized_ts']:.2f}"
        norm_is_str = f"{res['normalized_is']:.2f}"
        combined_str = f"{res['combined_efficiency_score']:.2f}"
        
        print(f"{res['model_name']:<25} {ts_str:<15} {is_str:<15} {norm_ts_str:<15} {norm_is_str:<15} {combined_str:<15}")

    print("
--- End of Report ---")

if __name__ == "__main__":
    main()
