
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
