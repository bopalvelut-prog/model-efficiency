# Model Efficiency Benchmarks 📈

**Small models → Old hardware → Real benchmarks**

## 🤖 Zero-Human Automation
We follow the **bopalvelut-prog** principle of automation. You can now run the benchmark with zero human intervention:

```bash
python3 src/benchmark.py
```

This script will:
1.  **Auto-detect** your hardware (CPU, RAM, Model name).
2.  **Run** a standardized inference test using `prima.cpp`.
3.  **Calculate** tokens per second and efficiency.
4.  **Save** the results to `benchmarks.csv`.
5.  **Push** the updates directly to GitHub.

## Current Records
| Hardware | CPU | RAM | Model | Speed | RAM | Link |
|----------|-----|-----|-------|-------|-----|------|
| eMachines E727 | Pentium T4500 2.1GHz | 4GB DDR2 | Qwen2.5-1.5B Q4 | 1 tok/s | 145MB | [e727-local-ai](https://github.com/bopalvelut-prog/e727-local-ai) |

**Submit yours → Beat Pentium T4500!**
