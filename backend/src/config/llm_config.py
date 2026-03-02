import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_nvidia import ChatNVIDIA
from langchain_ollama import ChatOllama

from src.enums.llm_type import LLMType
from langchain_core.language_models import BaseChatModel


class LLMConnector:
    """
    Connector for various language models (LLMs) such as OpenAI GPT, GROQ AI, OLLAMA, and NVIDIA AI Endpoints.

    Attributes:
        model (object): The language model to be used.
        temperature (float): The creativity level of the model. Default is 0.0.
        api_key (str): The API key for OpenAI/GROQ/NVIDIA/OLLAMA. Default is None.
        llm_type (LLMType): The type of language model to be used. Default is LLMType.GROQ_AI.
    """
    def __init__(self, model_name: object = None,
                temperature: float = 0.0,
                llm_type: LLMType | str | None = None,
                api_key: str | None = None,
                endpoint: str | None = None,
                max_retries: int=20,
                ):
        load_dotenv()
        
        self.model = model_name
        if self.model is None:
            self.model = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
        resolved_llm_type = llm_type if llm_type is not None else os.getenv("LLM_TYPE")
        if isinstance(resolved_llm_type, str) and not resolved_llm_type.strip():
            resolved_llm_type = None
        if resolved_llm_type is None:
            resolved_llm_type = LLMType.GROQ_AI
        elif isinstance(resolved_llm_type, str):
            resolved_llm_type = LLMType.from_string(resolved_llm_type)

        if not isinstance(resolved_llm_type, LLMType):
            raise ValueError("llm_type must be an instance of LLMType or a valid string value")

        self.llm_type = resolved_llm_type
        if api_key is None:
            
            if self.llm_type == LLMType.OPEN_AI:
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.llm_type == LLMType.OLLAMA_AI:
                self.api_key = os.getenv("OLLAMA_API_KEY")
            elif self.llm_type == LLMType.NVIDIA_AI:
                self.api_key = os.getenv("NVIDIA_API_KEY")
            else:
                self.api_key =  os.getenv("GROQ_API_KEY")
        else:
            self.api_key = api_key
        if os.getenv("LLM_TEMPERATURE") is not None:
            self.temperature = os.getenv("LLM_TEMPERATURE")
        else:
            self.temperature = temperature
            
        if endpoint is None:
            if self.llm_type == LLMType.NVIDIA_AI:
                self.endpoint = os.getenv("NVIDIA_ENDPOINT") 
                if self.endpoint and not self.endpoint.endswith('/v1'):
                    self.endpoint = f"{self.endpoint}/v1"
            elif self.llm_type == LLMType.OLLAMA_AI:
                self.endpoint = os.getenv("OLLAMA_ENDPOINT")
            else:
                self.endpoint = None
        else:
            self.endpoint = endpoint
        
        self.max_retries = max_retries

    
    def __call__(self) -> BaseChatModel:
        if not self.model:
            raise ValueError("Model is not defined")

        if not self.api_key:
            raise ValueError("API key is not defined")
        
        try:
            if self.llm_type == LLMType.OPEN_AI:
                return self.get_openai_llm()
            elif self.llm_type == LLMType.OLLAMA_AI:
                return self.get_ollama_llm()
            elif self.llm_type == LLMType.NVIDIA_AI:
                return self.get_nvidia_llm()
            else:
                return self.get_groq_llm()
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM: {e}")
    
    def get_openai_llm(self) -> BaseChatModel:
        return ChatOpenAI(
            model_name=self.model,
            openai_api_key=self.api_key,
            temperature=self.temperature,
            max_retries=self.max_retries,
            model_kwargs={"seed": 1234}
        )
    
    def get_groq_llm(self) -> BaseChatModel:
        return ChatGroq(
            model=self.model, 
            temperature=self.temperature,
            api_key=self.api_key,
            max_retries=self.max_retries,
            model_kwargs={"seed": 1234}
        )
        
    def get_ollama_llm(self) -> BaseChatModel:
        return ChatOllama(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key,
            endpoint=self.endpoint,
            max_retries=self.max_retries,
            seed=1234
        )
    
    def get_nvidia_llm(self) -> BaseChatModel:
        return ChatNVIDIA(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key,
            base_url=self.endpoint,
            max_retries=self.max_retries,
            max_tokens=8192,
            seed=1234
        )
