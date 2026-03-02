from enum import Enum

class LLMType(Enum):
    OPEN_AI = 1
    GROQ_AI = 2
    OLLAMA_AI = 3
    NVIDIA_AI = 4
    
    @classmethod
    def from_string(cls, name: str):
        """Convert string (case-insensitive) to LLMType."""
        normalized = name.strip().lower()
        mapping = {
            "openai": cls.OPEN_AI,
            "groq": cls.GROQ_AI,
            "ollama": cls.OLLAMA_AI,
            "nvidia": cls.NVIDIA_AI,
        }
        if normalized not in mapping:
            raise ValueError(f"Unknown LLM type: {name}")
        return mapping[normalized]