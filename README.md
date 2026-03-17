# Ollama Model Efficiency Comparator

Compare Ollama models by token speed, intelligency, and model size to find the best model for your use case.

## Features

- **Token Speed** - Measures tokens/second for each model
- **Intelligency Score** - User-rated quality score (1-5)
- **Model Size** - Smaller models score higher (more efficient)
- **Weighted Scoring** - Customize importance of each factor

## Installation

```bash
git clone https://github.com/bopalvelut-prog/model-efficiency.git
cd model-efficiency
pip install -r requirements.txt
```

## Usage

```bash
python model_efficiency_comparator.py -p "Your prompt here"
```

### Custom Weights

Adjust the importance of each factor (weights must sum to 1):

```bash
python model_efficiency_comparator.py -p "Hello world" --w_ts 0.5 --w_is 0.3 --w_ms 0.2
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--w_ts` | Token Speed weight | 0.4 |
| `--w_is` | Intelligency weight | 0.4 |
| `--w_ms` | Model Size weight | 0.2 |

## Example Output

```
--- Results Summary ---
Model                      Tokens/Sec   Size       Intell.   Norm TS   Norm IS   Norm MS   Combined   
------------------------- ------------ ---------- --------- --------- --------- --------- ----------
moondream:latest          3.80         1.7GB      5.0       1.00      1.00      0.24      1.00       
qwen2.5:0.5b              2.65         397MB      5.0       0.70      1.00      1.00      0.85       
Qwen3:0.6b                2.48         522MB      5.0       0.65      1.00      0.76      0.83       
qwen3.5:0.8b              2.42         1.0GB      5.0       0.64      1.00      0.40      0.82       
qwen2.5:3b                0.95         1.8GB      5.0       0.25      1.00      0.22      0.62       
```

## How It Works

1. Fetches all installed Ollama models
2. Runs each model with your prompt and measures performance
3. Prompts you to rate each model's output quality (1-5)
4. Calculates normalized scores and combined efficiency
5. Ranks models by combined score

## Requirements

- Python 3.x
- [Ollama](https://ollama.ai) running locally
- `requests` library

## License

MIT
