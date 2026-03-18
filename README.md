# (OpenAI)-compatible Model Efficiency Comparator

Compare (OpenAI)-compatible models by token speed, intelligency, security, and model size to find the best model for your use case.

## Features

- **Token Speed** - Measures tokens/second for each model
- **Intelligency Score** - User-rated quality score (1-5)
- **Security Check** - Automatic prompt injection resistance testing
- **Compliance Metadata** - Displays Origin Country and License type
- **Model Size** - Smaller models score higher (more efficient)
- **Automatic Downloader** - Suggests and downloads better quantization versions
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

Adjust the importance of each factor (weights must sum to 1.0):

```bash
python model_efficiency_comparator.py -p "Hello world" --w_ts 0.3 --w_is 0.3 --w_ms 0.2 --w_sec 0.2
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--w_ts` | Token Speed weight | 0.3 |
| `--w_is` | Intelligency weight | 0.3 |
| `--w_ms` | Model Size weight | 0.2 |
| `--w_sec` | Security weight | 0.2 |

## Example Output

```
--- Results Summary ---
Model                     Tokens/s   Origin     License            Sec.  Score   Recommendation
---------------------------------------------------------------------------------------------------
moondream:latest          3.8        USA        Apache 2.0         5.0   0.88    Too slow. Try q3_K_M
qwen2.5:0.5b              2.6        China      Apache 2.0         1.0   0.75    Too slow. Try q3_K_M
```

## Requirements

- Python 3.x
- A local inference engine (e.g. Ollama, vLLM) running on port 11434
- `requests` library

## License

MIT
