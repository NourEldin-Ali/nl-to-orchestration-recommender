
## Environment Setup

```bash
conda create -n .venv python=3.11 -y
conda activate .venv
pip install -r requirements.txt
```

If you prefer `.venv`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the `root` directory with the following variables:

```env
LLM_TYPE=nvidia # Options: openai, groq, ollama, nvidia
OPENAI_API_KEY=
OLLAMA_API_KEY=
NVIDIA_API_KEY=
GROQ_API_KEY=
NVIDIA_ENDPOINT=
OLLAMA_ENDPOINT=
LLM_TEMPERATURE=
LLM_MODEL_NAME=
```

## LLM-as-Judge

Edit `DEFAULT_GROUND_TRUTH` and `DEFAULT_JUDGE_LLM_CONFIGS` directly in `src/llm_as_judge.py`.
Each ground-truth entry only needs:

- `user_query`
- `expected_answer`

Run it from the `backend` directory:

```bash
python -m src.llm_as_judge \
  --input-excel ../output/evaluation_results_20260312_092928.xlsx
```

You can also pass judge models explicitly:

```bash
python -m src.llm_as_judge \
  --input-excel ../output/evaluation_results_20260312_092928.xlsx \
  --llm openai:gpt-4.1-mini \
  --llm nvidia:qwen/qwen2-7b-instruct
```

The output workbook contains:

- original evaluation sheets
- `judge_runs`
- `judge_summary`
- `judge_config`
